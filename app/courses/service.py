from uuid import UUID

from decimal import Decimal

from app.courses.constants import DEFAULT_OFFSET, DEFAULT_PAGE_SIZE, MAX_INSTRUCTORS_PER_COURSE, RATING_DECIMAL_PLACES
from app.courses.errors import (
    CannotRemoveLastInstructorError,
    CourseNotFoundError,
    InvalidInstructorIdsError,
    NotEnrolledError,
    NotInstructorOfCourseError,
    TooManyInstructorsError,
)
from app.courses.models import Course, CourseEnrollment, CourseRating
from app.courses.repository import CourseRepository
from app.courses.schemas import CourseCreate, CourseRate, CourseUpdate
from app.users.models import User, UserRole


def _is_admin(user: User) -> bool:
    return user.role == UserRole.admin


async def _ensure_can_modify_course(repository: CourseRepository, course_id: int, current_user: User) -> None:
    """Raise NotInstructorOfCourseError unless current_user is admin or an instructor of the course."""
    if _is_admin(current_user):
        return
    if not await repository.is_instructor(course_id, current_user.id):
        raise NotInstructorOfCourseError()


async def get_course(id: int, repository: CourseRepository, current_user: User | None = None) -> Course:
    """Fetch a single course by ID with instructors and enrolled count.

    Unpublished courses are only visible to instructors of the course or admins.
    Others receive CourseNotFoundError (avoids IDOR enumeration).

    Raises:
        CourseNotFoundError: If course does not exist or is unpublished and user lacks access.
    """
    course = await repository.get_by_id(id)
    if course is None:
        raise CourseNotFoundError()

    if not course.published:
        if current_user is None:
            raise CourseNotFoundError()
        is_instructor = any(ci.user_id == current_user.id for ci in course.instructors)
        if not _is_admin(current_user) and not is_instructor:
            raise CourseNotFoundError()

    return course


async def get_courses(
    repository: CourseRepository,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = DEFAULT_OFFSET,
    current_user: User | None = None,
    published: bool | None = None,
    q: str | None = None,
) -> tuple[list[Course], int]:
    """Get courses with pagination and optional filters.

    Unauthenticated: published only.
    Admin: all courses.
    Instructor: published + unpublished courses where they are instructor.

    Filters (optional):
    - published: when True/False, filter by published status
    - q: case-insensitive partial match on title

    Returns (courses, total_count). ORM objects; CourseRead auto-transforms.
    """
    include_all = current_user is not None and _is_admin(current_user)
    own_instructor_id = (
        current_user.id if current_user is not None and current_user.role == UserRole.instructor else None
    )
    return await repository.list_courses(
        limit=limit,
        offset=offset,
        published=published,
        q=q,
        include_all=include_all,
        own_instructor_id=own_instructor_id,
    )


async def create_course(
    payload: CourseCreate,
    current_user: User,
    repository: CourseRepository,
) -> Course:
    """Create a course with one or more instructors.

    When add_me_as_instructor is True, current_user is added as an instructor.
    instructor_ids can add other instructors. At least one instructor required.

    Raises:
        InvalidInstructorIdsError: If any instructor_ids are invalid or do not have instructor/admin role.
    """
    instructor_ids = _resolve_instructor_ids(payload, current_user.id)
    instructors = await _validate_instructors(repository, instructor_ids)

    course = await repository.create_course(
        title=payload.title,
        description=payload.description,
        published=payload.published,
        instructor_ids=[instructor.id for instructor in instructors],
    )
    await repository.commit()
    return course


async def update_course(
    id: int,
    payload: CourseUpdate,
    current_user: User,
    repository: CourseRepository,
) -> Course:
    """Update a course. User must be instructor of the course or admin.

    Raises:
        CourseNotFoundError: If course does not exist.
        NotInstructorOfCourseError: If user is not instructor of course and not admin.
        InvalidInstructorIdsError: If instructor_ids are invalid when provided.
    """
    if not await repository.exists(id):
        raise CourseNotFoundError()

    await _ensure_can_modify_course(repository, id, current_user)

    update_data: dict = {}
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.published is not None:
        update_data["published"] = payload.published

    if update_data:
        await repository.update_fields(id, update_data)

    if payload.instructor_ids is not None:
        if len(payload.instructor_ids) > MAX_INSTRUCTORS_PER_COURSE:
            raise TooManyInstructorsError()
        if len(payload.instructor_ids) == 0:
            raise CannotRemoveLastInstructorError()
        instructors = await _validate_instructors(repository, payload.instructor_ids)
        await repository.replace_instructors(id, [instructor.id for instructor in instructors])

    # Same transaction sees the uncommitted update; expire_on_commit=False skips a re-fetch after commit.
    course = await repository.get_by_id(id)
    await repository.commit()
    return course


async def delete_course(
    id: int,
    current_user: User,
    repository: CourseRepository,
) -> None:
    """Delete a course. Admin can delete any course; instructor can delete only if they instruct it.

    Cascades to course_instructors, course_ratings, course_enrollments.

    Raises:
        CourseNotFoundError: If course does not exist.
        NotInstructorOfCourseError: If user is not instructor of course and not admin.
    """
    if not await repository.exists(id):
        raise CourseNotFoundError()

    await _ensure_can_modify_course(repository, id, current_user)

    await repository.delete(id)
    await repository.commit()


def _resolve_instructor_ids(payload: CourseCreate, current_user_id: UUID) -> list[UUID]:
    """Build deduplicated instructor list with creator first when add_me_as_instructor."""
    ids: list[UUID] = []
    if payload.add_me_as_instructor:
        ids.append(current_user_id)
    ids.extend(payload.instructor_ids)

    return list(dict.fromkeys(ids))


async def _validate_instructors(
    repository: CourseRepository,
    instructor_ids: list[UUID],
) -> list[User]:
    """Fetch users by IDs and ensure all exist and have instructor or admin role."""
    fetched = await repository.find_instructors(instructor_ids)

    user_by_id = {user.id: user for user in fetched}
    users = [user_by_id[instructor_id] for instructor_id in instructor_ids if instructor_id in user_by_id]

    if len(users) != len(instructor_ids):
        missing = [instructor_id for instructor_id in instructor_ids if instructor_id not in user_by_id]
        raise InvalidInstructorIdsError(missing)
    return users


async def enroll_course(id: int, current_user: User, repository: CourseRepository) -> CourseEnrollment:
    """Enroll current user in a course.

    Raises:
        CourseNotFoundError: If course does not exist.
        AlreadyEnrolledError: If user is already enrolled.
    """
    if not await repository.exists(id):
        raise CourseNotFoundError()

    enrollment = await repository.add_enrollment(id, current_user.id)
    await repository.commit()
    await repository.refresh(enrollment)
    return enrollment


async def unenroll_course(id: int, current_user: User, repository: CourseRepository) -> None:
    """Unenroll current user from a course.

    Raises:
        CourseNotFoundError: If course does not exist.
        NotEnrolledError: If user is not enrolled.
    """
    if not await repository.exists(id):
        raise CourseNotFoundError()

    removed = await repository.remove_enrollment(id, current_user.id)
    if not removed:
        raise NotEnrolledError()
    await repository.commit()


async def rate_course(
    id: int,
    payload: CourseRate,
    current_user: User,
    repository: CourseRepository,
) -> CourseRating:
    """Rate a course (upsert). One rating per user per course; updates if already rated.

    Raises:
        CourseNotFoundError: If course does not exist.
    """
    if not await repository.exists(id):
        raise CourseNotFoundError()

    rating_value = Decimal(str(round(payload.rating, RATING_DECIMAL_PLACES)))
    rating = await repository.upsert_rating(id, current_user.id, rating_value)
    await repository.commit()
    return rating


async def recompute_course_rating(course_id: int, repository: CourseRepository) -> None:
    """Recompute and update course aggregate rating."""
    average = await repository.compute_average_rating(course_id)
    await repository.update_average_rating(course_id, average)
    await repository.commit()
