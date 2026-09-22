"""Constants for the index module: the root endpoint's message and route name."""

from enum import StrEnum

ROOT_MESSAGE = "Hello World"


class RouteName(StrEnum):
    root = "root"
