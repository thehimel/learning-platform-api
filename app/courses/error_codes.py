"""Error codes for the courses domain."""

from enum import Enum


class CourseErrorCode(str, Enum):
    invalid_instructor_ids = "invalid_instructor_ids"
    too_many_instructors = "too_many_instructors"
    cannot_remove_last_instructor = "cannot_remove_last_instructor"
    already_enrolled = "already_enrolled"
    not_enrolled = "not_enrolled"
    course_not_found = "course_not_found"
    not_instructor_of_course = "not_instructor_of_course"
