"""Exception classes and error codes for the courses domain."""

from enum import Enum
from typing import Any
from uuid import UUID


class CourseErrorCode(str, Enum):
    invalid_instructor_ids = "invalid_instructor_ids"
    too_many_instructors = "too_many_instructors"
    cannot_remove_last_instructor = "cannot_remove_last_instructor"
    already_enrolled = "already_enrolled"
    not_enrolled = "not_enrolled"
    course_not_found = "course_not_found"
    not_instructor_of_course = "not_instructor_of_course"


class CourseError(Exception):
    """Base for course domain exceptions. Subclasses define status_code, error_code, message."""

    status_code: int = 500
    error_code: CourseErrorCode
    message: str = ""

    def get_http_message(self) -> str:
        """Message for HTTP response. Uses str(self) when exception was raised with custom message."""
        return str(self) if self.args else self.message

    def get_extra_detail(self) -> dict[str, Any]:
        """Extra fields for error_detail (e.g. missing_ids). Override in subclasses as needed."""
        return {}


class InvalidInstructorIdsError(CourseError):
    """Raised when one or more instructor IDs are invalid or not instructors."""

    status_code = 400
    error_code = CourseErrorCode.invalid_instructor_ids
    message = "Invalid or non-instructor user IDs."

    def __init__(self, missing_ids: list[UUID]) -> None:
        self.missing_ids = missing_ids
        super().__init__(f"Invalid or non-instructor user IDs: {missing_ids}")

    def get_extra_detail(self) -> dict[str, Any]:
        return {"missing_ids": [str(mid) for mid in self.missing_ids]}


class TooManyInstructorsError(CourseError):
    """Raised when instructor_ids exceeds MAX_INSTRUCTORS_PER_COURSE."""

    status_code = 400
    error_code = CourseErrorCode.too_many_instructors
    message = "Too many instructors for this course."


class CannotRemoveLastInstructorError(CourseError):
    """Raised when updating instructor_ids would leave the course with no instructors."""

    status_code = 400
    error_code = CourseErrorCode.cannot_remove_last_instructor
    message = "Cannot remove the last instructor. At least one instructor required."


class AlreadyEnrolledError(CourseError):
    """Raised when user is already enrolled in the course."""

    status_code = 409
    error_code = CourseErrorCode.already_enrolled
    message = "Already enrolled in this course."


class NotEnrolledError(CourseError):
    """Raised when user is not enrolled in the course."""

    status_code = 409
    error_code = CourseErrorCode.not_enrolled
    message = "Not enrolled in this course."


class CourseNotFoundError(CourseError):
    """Raised when a course does not exist."""

    status_code = 404
    error_code = CourseErrorCode.course_not_found
    message = "Course not found."


class NotInstructorOfCourseError(CourseError):
    """Raised when user is not an instructor of the course and cannot modify it."""

    status_code = 403
    error_code = CourseErrorCode.not_instructor_of_course
    message = "Not an instructor of this course."
