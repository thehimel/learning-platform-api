"""HTTP handlers for course domain exceptions."""

from fastapi import Request
from fastapi.responses import JSONResponse

from .types import (
    AlreadyEnrolledError,
    CannotRemoveLastInstructorError,
    CourseError,
    CourseNotFoundError,
    InvalidInstructorIdsError,
    NotEnrolledError,
    NotInstructorOfCourseError,
    TooManyInstructorsError,
)
from app.exceptions import error_detail


def _json_response(status_code: int, detail: dict) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def course_error_handler(_request: Request, exc: CourseError) -> JSONResponse:
    """Generic handler for all CourseError subclasses. Metadata lives on the exception."""
    detail = error_detail(exc.error_code, exc.get_http_message(), **exc.get_extra_detail())
    return _json_response(exc.status_code, detail)


def register_course_exception_handlers(app) -> None:
    """Register all course domain exception handlers on the FastAPI app."""
    for exc_cls in (
        AlreadyEnrolledError,
        CannotRemoveLastInstructorError,
        CourseNotFoundError,
        InvalidInstructorIdsError,
        NotEnrolledError,
        NotInstructorOfCourseError,
        TooManyInstructorsError,
    ):
        app.add_exception_handler(exc_cls, course_error_handler)
