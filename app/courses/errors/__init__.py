"""Course domain errors: codes, exceptions, and HTTP handlers."""

from app.courses.errors.handlers import register_course_exception_handlers
from app.courses.errors.types import (
    AlreadyEnrolledError,
    CannotRemoveLastInstructorError,
    CourseErrorCode,
    CourseNotFoundError,
    InvalidInstructorIdsError,
    NotEnrolledError,
    NotInstructorOfCourseError,
    TooManyInstructorsError,
)

__all__ = [
    "AlreadyEnrolledError",
    "CannotRemoveLastInstructorError",
    "CourseErrorCode",
    "CourseNotFoundError",
    "InvalidInstructorIdsError",
    "NotEnrolledError",
    "NotInstructorOfCourseError",
    "TooManyInstructorsError",
    "register_course_exception_handlers",
]
