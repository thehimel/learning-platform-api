"""Constants shared across the whole app: route wiring, CORS, security headers, and the error envelope."""

API_PREFIX = "/api"

CORS_ALLOW_ALL = "*"
CORS_ORIGIN_SEPARATOR = ","

HTTP_ERROR_CODE = "http_error"
VALIDATION_ERROR_CODE = "validation_error"
VALIDATION_ERROR_MESSAGE = "Request validation failed."
INTERNAL_SERVER_ERROR_CODE = "internal_server_error"
INTERNAL_SERVER_ERROR_MESSAGE = "Internal server error."
UNHANDLED_EXCEPTION_LOG_MESSAGE = "Unhandled exception on %s %s"
HANDLED_EXCEPTION_LOG_MESSAGE = "Handled exception on %s %s: %s"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Cross-Origin-Opener-Policy": "same-origin",
}

REQUEST_COMPLETED_LOG_MESSAGE = "%s %s -> %s (%.2fms)"
