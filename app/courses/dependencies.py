from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.repository import CourseRepository
from app.infra.database import get_db


async def get_course_repository(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[CourseRepository, None]:
    yield CourseRepository(session)
