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
PRIVILEGE_CHANGE_LOG_MESSAGE = "Privilege change: user %s role set to '%s'."
USER_REGISTERED_LOG_MESSAGE = "User %s registered with role '%s'."
USER_LOGGED_IN_LOG_MESSAGE = "User %s logged in."
PASSWORD_RESET_REQUESTED_LOG_MESSAGE = "User %s requested a password reset."
PASSWORD_RESET_LOG_MESSAGE = "User %s reset their password."
USER_DELETE_STARTED_LOG_MESSAGE = "User %s is about to be deleted."
USER_DELETED_LOG_MESSAGE = "User %s has been deleted."

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
