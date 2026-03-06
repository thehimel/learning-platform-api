from uuid import UUID

from decimal import Decimal

from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert

from app.courses.errors import (
    AlreadyEnrolledError,
    CannotRemoveLastInstructorError,
    CourseNotFoundError,
    InvalidInstructorIdsError,
    NotEnrolledError,
    NotInstructorOfCourseError,
    TooManyInstructorsError,
)
from app.courses.models import Course, CourseEnrollment, CourseInstructor, CourseRating
from app.database import AsyncSessionLocal
from app.courses.schemas import CourseCreate, CourseRate, CourseUpdate, MAX_INSTRUCTORS_PER_COURSE
from app.users.models import User, UserRole

# Eager load options for Course → instructors → user. enrolled_count via column_property (no enrollments load).
_COURSE_LOAD_OPTIONS = (
    selectinload(Course.instructors).selectinload(CourseInstructor.user),
)


async def get_course(id: int, session: AsyncSession) -> Course:
    """
    Fetch a single course by ID with instructors and enrolled count.

    Raises:
        CourseNotFoundError: if course does not exist
    """
    stmt = (
        select(Course)
        .where(Course.id == id)
        .options(*_COURSE_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    course = result.scalars().unique().one_or_none()
    if course is None:
        raise CourseNotFoundError()
    return course


async def get_courses(session: AsyncSession) -> list[Course]:
    """Get all courses with instructors and enrolled count. Returns ORM objects; CourseRead auto-transforms."""
    stmt = (
        select(Course)
        .options(*_COURSE_LOAD_OPTIONS)
        .order_by(Course.created_at.desc(), Course.id.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def create_course(
    payload: CourseCreate,
    current_user: User,
    session: AsyncSession,
) -> Course:
    """
    Create a course with one or more instructors.

    When add_me_as_instructor is True, current_user is added as an instructor.
    instructor_ids can add other instructors. At least one instructor required.

    Raises InvalidInstructorIdsError if any instructor_ids are invalid or
    do not have instructor/admin role.
    """
    instructor_ids = _resolve_instructor_ids(payload, current_user.id)
    instructors = await _validate_instructors(session, instructor_ids)

    course = Course(
        title=payload.title,
        description=payload.description,
    )
    session.add(course)
    await session.flush()

    course_instructors = [
        CourseInstructor(
            course_id=course.id,
            user_id=instructor.id,
            is_primary=(index == 0),
        )
        for index, instructor in enumerate(instructors)
    ]
    session.add_all(course_instructors)
    await session.commit()

    # Re-fetch with relationships for auto-transform via CourseRead
    stmt = select(Course).where(Course.id == course.id).options(*_COURSE_LOAD_OPTIONS)
    result = await session.execute(stmt)
    return result.scalars().one()


async def update_course(
    id: int,
    payload: CourseUpdate,
    current_user: User,
    session: AsyncSession,
) -> Course:
    """
    Update a course. User must be instructor of the course or admin.

    Raises:
        CourseNotFoundError: if course does not exist
        NotInstructorOfCourseError: if user is not instructor of course and not admin
        InvalidInstructorIdsError: if instructor_ids are invalid when provided
    """
    if not await _course_exists(session, id):
        raise CourseNotFoundError()

    is_admin = current_user.role == UserRole.admin
    if not is_admin:
        stmt = select(
            exists().where(
                CourseInstructor.course_id == id,
                CourseInstructor.user_id == current_user.id,
            )
        )
        result = await session.execute(stmt)
        is_instructor_of_course = result.scalar_one()
        if not is_instructor_of_course:
            raise NotInstructorOfCourseError()

    update_data: dict = {}
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.description is not None:
        update_data["description"] = payload.description
    if payload.published is not None:
        update_data["published"] = payload.published

    if update_data:
        await session.execute(update(Course).where(Course.id == id).values(**update_data))

    if payload.instructor_ids is not None:
        if len(payload.instructor_ids) > MAX_INSTRUCTORS_PER_COURSE:
            raise TooManyInstructorsError()
        if len(payload.instructor_ids) == 0:
            raise CannotRemoveLastInstructorError()
        instructors = await _validate_instructors(session, payload.instructor_ids)
        await session.execute(delete(CourseInstructor).where(CourseInstructor.course_id == id))
        if instructors:
            await session.execute(
                insert(CourseInstructor).values([
                    {"course_id": id, "user_id": instructor.id, "is_primary": index == 0}
                    for index, instructor in enumerate(instructors)
                ])
            )

    # Fetch updated course in same transaction (sees uncommitted changes).
    # With expire_on_commit=False, we return this object without re-fetch after commit.
    stmt = select(Course).where(Course.id == id).options(*_COURSE_LOAD_OPTIONS)
    result = await session.execute(stmt)
    course = result.scalars().unique().one()
    await session.commit()
    return course


def _resolve_instructor_ids(payload: CourseCreate, current_user_id: UUID) -> list[UUID]:
    """Build deduplicated instructor list with creator first when add_me_as_instructor."""
    ids: list[UUID] = []
    if payload.add_me_as_instructor:
        ids.append(current_user_id)
    ids.extend(payload.instructor_ids)

    return list(dict.fromkeys(ids))


async def _validate_instructors(
    session: AsyncSession,
    instructor_ids: list[UUID],
) -> list[User]:
    """Fetch users by IDs and ensure all exist and have instructor or admin role."""
    stmt = select(User).where(
        User.id.in_(instructor_ids),
        or_(User.role == UserRole.instructor, User.role == UserRole.admin),
    )
    result = await session.execute(stmt)
    fetched = list(result.scalars().all())

    user_by_id = {user.id: user for user in fetched}
    users = [user_by_id[instructor_id] for instructor_id in instructor_ids if instructor_id in user_by_id]

    if len(users) != len(instructor_ids):
        missing = [instructor_id for instructor_id in instructor_ids if instructor_id not in user_by_id]
        raise InvalidInstructorIdsError(missing)
    return users


async def _course_exists(session: AsyncSession, id: int) -> bool:
    """Check if course exists. Lighter than session.get(Course) — no ORM materialization."""
    stmt = select(exists().where(Course.id == id))
    result = await session.execute(stmt)
    return result.scalar_one()


async def enroll_course(id: int, current_user: User, session: AsyncSession) -> CourseEnrollment:
    """
    Enroll current user in a course.

    Raises:
        CourseNotFoundError: if course does not exist
        AlreadyEnrolledError: if user is already enrolled
    """
    if not await _course_exists(session, id):
        raise CourseNotFoundError()

    enrollment = CourseEnrollment(course_id=id, user_id=current_user.id)
    session.add(enrollment)
    try:
        await session.commit()
        await session.refresh(enrollment)
    except IntegrityError:
        await session.rollback()
        # Unique (course_id, user_id) — already enrolled; course existence already verified
        raise AlreadyEnrolledError from None
    return enrollment


async def unenroll_course(id: int, current_user: User, session: AsyncSession) -> None:
    """
    Unenroll current user from a course.

    Raises:
        CourseNotFoundError: if course does not exist
        NotEnrolledError: if user is not enrolled
    """
    if not await _course_exists(session, id):
        raise CourseNotFoundError()

    stmt = delete(CourseEnrollment).where(
        CourseEnrollment.course_id == id,
        CourseEnrollment.user_id == current_user.id,
    )
    result = await session.execute(stmt)
    if result.rowcount == 0:
        raise NotEnrolledError()
    await session.commit()


async def rate_course(
    id: int,
    payload: CourseRate,
    current_user: User,
    session: AsyncSession,
) -> CourseRating:
    """
    Rate a course (upsert). One rating per user per course; updates if already rated.

    Raises:
        CourseNotFoundError: if course does not exist
    """
    if not await _course_exists(session, id):
        raise CourseNotFoundError()

    rating_value = Decimal(str(round(payload.rating, 1)))
    stmt = (
        insert(CourseRating)
        .values(course_id=id, user_id=current_user.id, rating=rating_value)
        .on_conflict_do_update(
            constraint="uq_course_rating",
            set_={"rating": rating_value},
        )
        .returning(CourseRating)
    )
    result = await session.execute(stmt)
    rating = result.scalars().one()
    await session.commit()
    return rating


async def recompute_course_rating(course_id: int, session: AsyncSession | None = None) -> None:
    """
    Recompute and update course aggregate rating. When session is provided (e.g. in tests),
    uses it; otherwise creates its own (for BackgroundTasks).
    """
    if session is not None:
        avg_stmt = select(func.avg(CourseRating.rating)).where(CourseRating.course_id == course_id)
        avg_result = await session.execute(avg_stmt)
        avg_rating = avg_result.scalar_one_or_none()
        await session.execute(
            update(Course).where(Course.id == course_id).values(rating=avg_rating)
        )
        await session.commit()
        return
    async with AsyncSessionLocal() as session:
        avg_stmt = select(func.avg(CourseRating.rating)).where(CourseRating.course_id == course_id)
        avg_result = await session.execute(avg_stmt)
        avg_rating = avg_result.scalar_one_or_none()
        await session.execute(
            update(Course).where(Course.id == course_id).values(rating=avg_rating)
        )
        await session.commit()
