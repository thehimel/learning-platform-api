"""Domain error classes for the courses module."""

from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import status

from app.infra.common.errors import DomainError


class CourseErrorCode(str, Enum):
    invalid_instructor_ids = "invalid_instructor_ids"
    too_many_instructors = "too_many_instructors"
    cannot_remove_last_instructor = "cannot_remove_last_instructor"
    already_enrolled = "already_enrolled"
    not_enrolled = "not_enrolled"
    course_not_found = "course_not_found"
    not_instructor_of_course = "not_instructor_of_course"


class CourseError(DomainError):
    """Base for course domain exceptions. Subclasses define status_code, error_code, message."""

    error_code: CourseErrorCode


class InvalidInstructorIdsError(CourseError):
    """Raised when one or more instructor IDs are invalid or not instructors."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = CourseErrorCode.invalid_instructor_ids
    message = "Invalid or non-instructor user IDs."

    def __init__(self, missing_ids: list[UUID]) -> None:
        self.missing_ids = missing_ids
        super().__init__(f"Invalid or non-instructor user IDs: {missing_ids}")

    def get_extra_detail(self) -> dict[str, Any]:
        return {"missing_ids": [str(mid) for mid in self.missing_ids]}


class TooManyInstructorsError(CourseError):
    """Raised when instructor_ids exceeds MAX_INSTRUCTORS_PER_COURSE."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = CourseErrorCode.too_many_instructors
    message = "Too many instructors for this course."


class CannotRemoveLastInstructorError(CourseError):
    """Raised when updating instructor_ids would leave the course with no instructors."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = CourseErrorCode.cannot_remove_last_instructor
    message = "Cannot remove the last instructor. At least one instructor required."


class AlreadyEnrolledError(CourseError):
    """Raised when user is already enrolled in the course."""

    status_code = status.HTTP_409_CONFLICT
    error_code = CourseErrorCode.already_enrolled
    message = "Already enrolled in this course."


class NotEnrolledError(CourseError):
    """Raised when user is not enrolled in the course."""

    status_code = status.HTTP_409_CONFLICT
    error_code = CourseErrorCode.not_enrolled
    message = "Not enrolled in this course."


class CourseNotFoundError(CourseError):
    """Raised when a course does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = CourseErrorCode.course_not_found
    message = "Course not found."


class NotInstructorOfCourseError(CourseError):
    """Raised when user is not an instructor of the course and cannot modify it."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = CourseErrorCode.not_instructor_of_course
    message = "Not an instructor of this course."
