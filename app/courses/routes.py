"""Route names for courses endpoints — used by url_path_for and router."""

from enum import StrEnum


class RouteName(StrEnum):
    courses_get = "courses_get"
    courses_get_by_id = "courses_get_by_id"
    courses_update = "courses_update"
    courses_create = "courses_create"
    courses_delete = "courses_delete"
    courses_enroll = "courses_enroll"
    courses_unenroll = "courses_unenroll"
    courses_rate = "courses_rate"
