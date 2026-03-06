"""Route names for users endpoints — used by url_path_for and router."""

from enum import StrEnum


class RouteName(StrEnum):
    users_get_me = "users_get_me"
    users_update_me = "users_update_me"
    users_get_by_id = "users_get_by_id"
    users_update_by_id = "users_update_by_id"
    users_delete_by_id = "users_delete_by_id"
