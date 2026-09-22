"""Constants for the courses module: pagination, validation limits, DB constraint names, and route names."""

from enum import StrEnum

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_OFFSET = 0

TITLE_MAX_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000
MAX_INSTRUCTORS_PER_COURSE = 10

RATING_MIN = 1
RATING_MAX = 5
RATING_DECIMAL_PLACES = 1
RATING_NUMERIC_PRECISION = 3
RATING_NUMERIC_SCALE = 1

CK_COURSES_RATING_RANGE = "ck_courses_rating_range"
CK_COURSE_RATING_RANGE = "ck_course_rating_range"
UQ_COURSE_INSTRUCTOR = "uq_course_instructor"
UQ_COURSE_RATING = "uq_course_rating"
UQ_COURSE_ENROLLMENT = "uq_course_enrollment"
IX_COURSES_PUBLISHED_CREATED_AT_ID = "ix_courses_published_created_at_id"

AT_LEAST_ONE_INSTRUCTOR_REQUIRED_MESSAGE = (
    "At least one instructor required: set add_me_as_instructor=true or provide instructor_ids"
)
TOO_MANY_INSTRUCTORS_TOTAL_MESSAGE = (
    "At most {max_total} instructors total; provide at most {max_others} in instructor_ids"
)


class RouteName(StrEnum):
    courses_get = "courses_get"
    courses_get_by_id = "courses_get_by_id"
    courses_update = "courses_update"
    courses_create = "courses_create"
    courses_delete = "courses_delete"
    courses_enroll = "courses_enroll"
    courses_unenroll = "courses_unenroll"
    courses_rate = "courses_rate"
