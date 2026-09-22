from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import insert

from app.courses.constants import UQ_COURSE_RATING
from app.courses.errors import AlreadyEnrolledError
from app.courses.models import Course, CourseEnrollment, CourseInstructor, CourseRating
from app.users.models import User, UserRole

# enrolled_count is a computed column; no need to load enrollments here.
_COURSE_LOAD_OPTIONS = (selectinload(Course.instructors).selectinload(CourseInstructor.user),)


class CourseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _fetch_with_relations(self, course_id: int, *, required: bool) -> Course | None:
        stmt = select(Course).where(Course.id == course_id).options(*_COURSE_LOAD_OPTIONS)
        result = await self._session.execute(stmt)
        rows = result.scalars().unique()
        return rows.one() if required else rows.one_or_none()

    async def get_by_id(self, course_id: int) -> Course | None:
        return await self._fetch_with_relations(course_id, required=False)

    async def exists(self, course_id: int) -> bool:
        stmt = select(exists().where(Course.id == course_id))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def is_instructor(self, course_id: int, user_id: UUID) -> bool:
        stmt = select(exists().where(CourseInstructor.course_id == course_id, CourseInstructor.user_id == user_id))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_courses(
        self,
        *,
        limit: int,
        offset: int,
        published: bool | None,
        q: str | None,
        include_all: bool,
        own_instructor_id: UUID | None,
    ) -> tuple[list[Course], int]:
        conditions = []
        if not include_all:
            if own_instructor_id is not None:
                instructor_course_ids = select(CourseInstructor.course_id).where(
                    CourseInstructor.user_id == own_instructor_id
                )
                conditions.append(or_(Course.published, Course.id.in_(instructor_course_ids)))
            else:
                conditions.append(Course.published)

        if published is not None:
            conditions.append(Course.published == published)
        if q is not None and q.strip():
            conditions.append(Course.title.ilike(f"%{q.strip()}%"))

        base_stmt = select(Course).options(*_COURSE_LOAD_OPTIONS).order_by(Course.created_at.desc(), Course.id.desc())
        count_stmt = select(func.count()).select_from(Course)
        if conditions:
            where_clause = and_(*conditions)
            base_stmt = base_stmt.where(where_clause)
            count_stmt = count_stmt.where(where_clause)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = base_stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        courses = list(result.scalars().unique().all())
        return courses, total

    async def find_instructors(self, user_ids: Sequence[UUID]) -> list[User]:
        stmt = select(User).where(
            User.id.in_(user_ids),
            or_(User.role == UserRole.instructor, User.role == UserRole.admin),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_course(
        self,
        title: str,
        description: str | None,
        published: bool,
        instructor_ids: Sequence[UUID],
    ) -> Course:
        course = Course(title=title, description=description, published=published)
        self._session.add(course)
        await self._session.flush()

        course_instructors = [
            CourseInstructor(course_id=course.id, user_id=instructor_id, is_primary=(index == 0))
            for index, instructor_id in enumerate(instructor_ids)
        ]
        self._session.add_all(course_instructors)
        await self._session.flush()

        return await self._fetch_with_relations(course.id, required=True)

    async def update_fields(self, course_id: int, fields: dict) -> None:
        await self._session.execute(update(Course).where(Course.id == course_id).values(**fields))

    async def replace_instructors(self, course_id: int, instructor_ids: Sequence[UUID]) -> None:
        await self._session.execute(delete(CourseInstructor).where(CourseInstructor.course_id == course_id))
        if instructor_ids:
            await self._session.execute(
                insert(CourseInstructor).values(
                    [
                        {"course_id": course_id, "user_id": instructor_id, "is_primary": index == 0}
                        for index, instructor_id in enumerate(instructor_ids)
                    ]
                )
            )

    async def delete(self, course_id: int) -> None:
        await self._session.execute(delete(Course).where(Course.id == course_id))

    async def add_enrollment(self, course_id: int, user_id: UUID) -> CourseEnrollment:
        enrollment = CourseEnrollment(course_id=course_id, user_id=user_id)
        self._session.add(enrollment)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise AlreadyEnrolledError from None
        return enrollment

    async def remove_enrollment(self, course_id: int, user_id: UUID) -> bool:
        stmt = delete(CourseEnrollment).where(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def upsert_rating(self, course_id: int, user_id: UUID, rating: Decimal) -> CourseRating:
        stmt = (
            insert(CourseRating)
            .values(course_id=course_id, user_id=user_id, rating=rating)
            .on_conflict_do_update(
                constraint=UQ_COURSE_RATING,
                set_={"rating": rating},
            )
            .returning(CourseRating)
        )
        result = await self._session.execute(stmt)
        return result.scalars().one()

    async def compute_average_rating(self, course_id: int) -> Decimal | None:
        stmt = select(func.avg(CourseRating.rating)).where(CourseRating.course_id == course_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_average_rating(self, course_id: int, average: Decimal | None) -> None:
        await self._session.execute(update(Course).where(Course.id == course_id).values(rating=average))

    async def flush(self) -> None:
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, instance) -> None:
        await self._session.refresh(instance)
