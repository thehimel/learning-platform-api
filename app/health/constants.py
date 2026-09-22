"""Constants for the health module: the DB liveness query, response status, and route name."""

from enum import StrEnum

HEALTH_CHECK_QUERY = "SELECT 1"
HEALTH_OK_STATUS = "ok"


class RouteName(StrEnum):
    health_db = "health_db"
