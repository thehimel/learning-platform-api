from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.auth.backend import current_active_user, current_instructor, current_user_optional
from app.courses.constants import DEFAULT_OFFSET, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, RouteName
from app.courses.dependencies import get_course_repository
from app.courses.models import Course, CourseEnrollment, CourseRating
from app.courses.repository import CourseRepository
from app.courses.schemas import (
    CourseCreate,
    CourseListResponse,
    CourseRead,
    CourseRate,
    CourseUpdate,
    EnrollmentRead,
    RatingRead,
)
from app.courses.service import (
    create_course as create_course_service,
    delete_course as delete_course_service,
    enroll_course as enroll_course_service,
    get_course as get_course_service,
    get_courses as get_courses_service,
    rate_course as rate_course_service,
    recompute_course_rating,
    update_course as update_course_service,
    unenroll_course as unenroll_course_service,
)
from app.infra.config import settings
from app.infra.database import AsyncSessionLocal
from app.users.models import User

router = APIRouter()


async def _recompute_course_rating_background(course_id: int) -> None:
    """Run outside the request's session scope, so it opens its own session."""
    async with AsyncSessionLocal() as session:
        await recompute_course_rating(course_id, CourseRepository(session))


@router.get("/", response_model=CourseListResponse, name=RouteName.courses_get)
async def get_courses(
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = DEFAULT_OFFSET,
    published: bool | None = None,
    q: str | None = None,
    current_user: User | None = Depends(current_user_optional),
    repository: CourseRepository = Depends(get_course_repository),
) -> CourseListResponse:
    """Get courses with pagination and optional filters.

    Unauthenticated: published only.
    Admin: all courses.
    Instructor: published + unpublished courses where they are instructor.

    - limit: Max items per page (default 20, max 100).
    - offset: Number of items to skip.
    - published: Filter by published status (true/false).
    - q: Case-insensitive partial match on title.
    """
    limit = min(max(1, limit), MAX_PAGE_SIZE)
    offset = max(DEFAULT_OFFSET, offset)
    courses, total = await get_courses_service(
        repository,
        limit=limit,
        offset=offset,
        current_user=current_user,
        published=published,
        q=q,
    )
    return CourseListResponse(items=courses, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=CourseRead, name=RouteName.courses_get_by_id)
async def get_course(
    id: int,
    current_user: User | None = Depends(current_user_optional),
    repository: CourseRepository = Depends(get_course_repository),
) -> Course:
    """Fetch a single course by ID.

    Public for published courses. Unpublished courses require instructor or admin role.
    """
    return await get_course_service(id, repository, current_user=current_user)


@router.patch("/{id}", response_model=CourseRead, name=RouteName.courses_update)
async def update_course(
    id: int,
    payload: CourseUpdate,
    current_user: User = Depends(current_instructor),
    repository: CourseRepository = Depends(get_course_repository),
) -> Course:
    """Update course (title, description, published, instructors). Must be instructor of course or admin."""
    return await update_course_service(id, payload, current_user, repository)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, name=RouteName.courses_delete)
async def delete_course(
    id: int,
    current_user: User = Depends(current_instructor),
    repository: CourseRepository = Depends(get_course_repository),
) -> None:
    """Delete course. Admin can delete any; instructor can delete only if they instruct it."""
    await delete_course_service(id, current_user, repository)


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED, name=RouteName.courses_create)
async def create_course(
    payload: CourseCreate,
    current_user: User = Depends(current_instructor),
    repository: CourseRepository = Depends(get_course_repository),
) -> Course:
    """Create a course with one or more instructors.

    Set add_me_as_instructor=true to add yourself as instructor. Use instructor_ids to add others. At least one
    instructor required. All instructor_ids must be valid users with role instructor or admin.
    """
    return await create_course_service(payload, current_user, repository)


@router.post(
    "/{id}/enroll", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED, name=RouteName.courses_enroll
)
async def enroll(
    id: int,
    current_user: User = Depends(current_active_user),
    repository: CourseRepository = Depends(get_course_repository),
) -> CourseEnrollment:
    """Enroll current user in a course. Returns 201 with full enrollment resource."""
    return await enroll_course_service(id, current_user, repository)


@router.delete("/{id}/enroll", status_code=status.HTTP_204_NO_CONTENT, name=RouteName.courses_unenroll)
async def unenroll(
    id: int,
    current_user: User = Depends(current_active_user),
    repository: CourseRepository = Depends(get_course_repository),
) -> None:
    """Unenroll current user from a course. Requires authentication."""
    await unenroll_course_service(id, current_user, repository)


@router.post("/{id}/rate", response_model=RatingRead, status_code=status.HTTP_201_CREATED, name=RouteName.courses_rate)
async def rate(
    id: int,
    payload: CourseRate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    repository: CourseRepository = Depends(get_course_repository),
) -> CourseRating:
    """Rate a course (1–5). Upserts if user already rated. Returns 201 with full rating resource."""
    rating = await rate_course_service(id, payload, current_user, repository)
    if settings.rating_recompute_async:
        background_tasks.add_task(_recompute_course_rating_background, id)
    else:
        await recompute_course_rating(id, repository)
    return rating
