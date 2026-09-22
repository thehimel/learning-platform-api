"""Constants for the limiter module: the default rate limit and its error code/message."""

RATE_LIMIT = "60/minute"
RATE_LIMIT_EXCEEDED_CODE = "rate_limit_exceeded"
RATE_LIMIT_EXCEEDED_MESSAGE = "Rate limit exceeded. {detail}"
