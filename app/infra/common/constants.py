"""Constants shared across the whole app: route wiring, CORS, security headers, and the error envelope."""

API_PREFIX = "/api"

CORS_ALLOW_ALL = "*"
CORS_ORIGIN_SEPARATOR = ","

HTTP_ERROR_CODE = "http_error"
VALIDATION_ERROR_CODE = "validation_error"
VALIDATION_ERROR_MESSAGE = "Request validation failed."
INTERNAL_SERVER_ERROR_CODE = "internal_server_error"
INTERNAL_SERVER_ERROR_MESSAGE = "Internal server error."
UNHANDLED_EXCEPTION_EVENT = "unhandled_exception"
HANDLED_EXCEPTION_EVENT = "handled_exception"

HSTS_MAX_AGE_SECONDS = 31536000

REQUEST_COMPLETED_EVENT = "request_completed"
REQUEST_DURATION_DECIMAL_PLACES = 2
