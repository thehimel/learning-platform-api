from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.exceptions import InvalidInstructorIdsError
from app.courses.models import Course, CourseInstructor
from app.courses.schemas import CourseCreate, CourseInstructorRead, CourseRead
from app.users.models import User, UserRole


async def create_course(
    payload: CourseCreate,
    current_user: User,
    session: AsyncSession,
) -> CourseRead:
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
    await session.refresh(course)

    instructor_reads = [
        CourseInstructorRead(id=instructor.id, email=instructor.email, is_primary=(index == 0))
        for index, instructor in enumerate(instructors)
    ]

    return CourseRead(
        id=course.id,
        title=course.title,
        description=course.description,
        published=course.published,
        rating=float(course.rating) if course.rating is not None else None,
        created_at=course.created_at,
        updated_at=course.updated_at,
        instructors=instructor_reads,
        enrolled_count=0,
    )


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
