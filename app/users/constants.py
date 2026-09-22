"""Constants for the users module: password policy, privileged fields, and route names."""

from enum import StrEnum

PASSWORD_MIN_LENGTH = 8
PASSWORD_MIN_UPPERCASE = 1
PASSWORD_MIN_NUMBERS = 1
PASSWORD_MIN_SPECIAL = 1
PASSWORD_MIN_NONLETTERS = 1

PASSWORD_POLICY_MESSAGES: dict[str, str] = {
    "Length": f"Password must be at least {PASSWORD_MIN_LENGTH} characters.",
    "Uppercase": f"Password must contain at least {PASSWORD_MIN_UPPERCASE} uppercase letter.",
    "Numbers": f"Password must contain at least {PASSWORD_MIN_NUMBERS} digit.",
    "Special": f"Password must contain at least {PASSWORD_MIN_SPECIAL} special character.",
    "NonLetters": f"Password must contain at least {PASSWORD_MIN_NONLETTERS} non-letter character.",
}
PASSWORD_CONTAINS_EMAIL_MESSAGE = "Password must not contain your email address."

ROLE_UPDATE_FIELD = "role"
PRIVILEGE_CHANGE_EVENT = "privilege_change"
USER_REGISTERED_EVENT = "user_registered"
USER_LOGGED_IN_EVENT = "user_logged_in"
PASSWORD_RESET_REQUESTED_EVENT = "password_reset_requested"
PASSWORD_RESET_EVENT = "password_reset"
USER_DELETE_STARTED_EVENT = "user_delete_started"
USER_DELETED_EVENT = "user_deleted"

IS_ACTIVE_FIELD = "is_active"
IS_SUPERUSER_FIELD = "is_superuser"
IS_VERIFIED_FIELD = "is_verified"
EMAIL_FIELD = "email"
PRIVILEGED_FIELDS = (IS_ACTIVE_FIELD, IS_SUPERUSER_FIELD, IS_VERIFIED_FIELD)
PRIVILEGED_UPDATE_FIELDS = (*PRIVILEGED_FIELDS, ROLE_UPDATE_FIELD, EMAIL_FIELD)


class RouteName(StrEnum):
    users_get_me = "users_get_me"
    users_update_me = "users_update_me"
    users_get_by_id = "users_get_by_id"
    users_update_by_id = "users_update_by_id"
    users_delete_by_id = "users_delete_by_id"
