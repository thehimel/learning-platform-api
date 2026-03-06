from uuid import UUID


class InvalidInstructorIdsError(Exception):
    """Raised when one or more instructor IDs are invalid or not instructors."""

    def __init__(self, missing_ids: list[UUID]) -> None:
        self.missing_ids = missing_ids
        super().__init__(f"Invalid or non-instructor user IDs: {missing_ids}")
