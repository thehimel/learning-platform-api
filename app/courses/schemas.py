import html
import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.courses.constants import (
    AT_LEAST_ONE_INSTRUCTOR_REQUIRED_MESSAGE,
    MAX_DESCRIPTION_LENGTH,
    MAX_INSTRUCTORS_PER_COURSE,
    RATING_DECIMAL_PLACES,
    RATING_MAX,
    RATING_MIN,
    TITLE_MAX_LENGTH,
    TOO_MANY_INSTRUCTORS_TOTAL_MESSAGE,
)


def _escape_html(value: str | None) -> str | None:
    """Escape HTML entities to mitigate XSS when content is rendered in HTML."""
    return html.escape(value) if value is not None else None


def _dedupe_instructor_ids(data: object) -> object:
    """Deduplicate instructor_ids in place, preserving order, when present on a dict payload."""
    if isinstance(data, dict) and data.get("instructor_ids"):
        data["instructor_ids"] = list(dict.fromkeys(data["instructor_ids"]))
    return data


def _escape_html_fields(model: BaseModel, *field_names: str) -> None:
    """Escape the given string fields on a frozen model in place for safe HTML rendering."""
    for field_name in field_names:
        value = getattr(model, field_name)
        if value is not None:
            object.__setattr__(model, field_name, _escape_html(value))


class CourseInstructorRead(BaseModel):
    """Minimal instructor info for course responses."""

    id: uuid.UUID
    email: str
    is_primary: bool = False

    model_config = ConfigDict(from_attributes=True, frozen=True)

    @model_validator(mode="before")
    @classmethod
    def from_course_instructor(cls, data: Any) -> Any:
        """Auto-transform from CourseInstructor ORM (with user loaded)."""
        if hasattr(data, "user") and hasattr(data, "is_primary"):
            return {"id": data.user.id, "email": data.user.email, "is_primary": data.is_primary}
        return data


class EnrollmentRead(BaseModel):
    """Schema for enrollment resource (created on enroll)."""

    id: int
    course_id: int
    user_id: uuid.UUID
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True, frozen=True)


class RatingRead(BaseModel):
    """Schema for rating resource (created/updated on rate)."""

    id: int
    course_id: int
    user_id: uuid.UUID
    rating: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, frozen=True)


class CourseRate(BaseModel):
    """Schema for rating a course (1–5, one decimal)."""

    rating: Annotated[float, Field(ge=RATING_MIN, le=RATING_MAX, description="Rating from 1 to 5 (e.g. 2.5)")]

    @model_validator(mode="after")
    def round_to_one_decimal(self) -> "CourseRate":
        self.rating = round(self.rating, RATING_DECIMAL_PLACES)
        return self


class CourseUpdate(BaseModel):
    """Schema for updating a course (partial — all fields optional).

    Intentionally limited to title, description, published, and instructor_ids.
    Sensitive fields (e.g. rating, created_at, internal flags) are omitted to prevent
    mass assignment. Clients sending extra fields receive a validation error.
    """

    model_config = ConfigDict(extra="forbid")

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=TITLE_MAX_LENGTH)] = None
    description: Annotated[str | None, Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)] = None
    published: bool | None = None
    instructor_ids: list[uuid.UUID] | None = Field(
        default=None,
        max_length=MAX_INSTRUCTORS_PER_COURSE,
        description="Replace instructors with these IDs. At least one required when provided.",
    )

    @model_validator(mode="before")
    @classmethod
    def ensure_unique_instructor_ids(cls, data: object) -> object:
        return _dedupe_instructor_ids(data)

    @model_validator(mode="after")
    def escape_html_fields(self) -> "CourseUpdate":
        """Escape title and description for safe HTML rendering."""
        _escape_html_fields(self, "title", "description")
        return self


class CourseCreate(BaseModel):
    """Schema for creating a course."""

    title: Annotated[str, Field(min_length=1, max_length=TITLE_MAX_LENGTH)]
    description: Annotated[str | None, Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)] = None
    add_me_as_instructor: bool = Field(
        default=True,
        description="When true, the authenticated user is added as an instructor (primary if first).",
    )
    instructor_ids: list[uuid.UUID] = Field(
        default_factory=list,
        max_length=MAX_INSTRUCTORS_PER_COURSE,
        description="Other instructor user IDs. Creator is added when add_me_as_instructor=true.",
    )
    published: bool = Field(default=False, description="When true, course appears in public list.")

    @model_validator(mode="after")
    def validate_instructors(self) -> "CourseCreate":
        if not self.add_me_as_instructor and not self.instructor_ids:
            raise ValueError(AT_LEAST_ONE_INSTRUCTOR_REQUIRED_MESSAGE)
        max_others = MAX_INSTRUCTORS_PER_COURSE - 1 if self.add_me_as_instructor else MAX_INSTRUCTORS_PER_COURSE
        if len(self.instructor_ids) > max_others:
            raise ValueError(
                TOO_MANY_INSTRUCTORS_TOTAL_MESSAGE.format(max_total=MAX_INSTRUCTORS_PER_COURSE, max_others=max_others)
            )
        return self

    @model_validator(mode="before")
    @classmethod
    def ensure_unique_instructor_ids(cls, data: object) -> object:
        return _dedupe_instructor_ids(data)

    @model_validator(mode="after")
    def escape_html_fields(self) -> "CourseCreate":
        """Escape title and description for safe HTML rendering."""
        _escape_html_fields(self, "title", "description")
        return self


class CourseListResponse(BaseModel):
    """Paginated list of courses."""

    items: list["CourseRead"]
    total: int
    limit: int
    offset: int


class CourseRead(BaseModel):
    """Schema for course responses."""

    id: int
    title: str
    description: str | None
    published: bool
    rating: float | None = None
    created_at: datetime
    updated_at: datetime
    instructors: list[CourseInstructorRead] = Field(default_factory=list)
    enrolled_count: int = 0

    model_config = ConfigDict(from_attributes=True, frozen=True)

    @model_validator(mode="before")
    @classmethod
    def from_course(cls, data: Any) -> Any:
        """Auto-transform from Course ORM (instructors loaded; enrolled_count from DB subquery)."""
        if hasattr(data, "instructors"):
            sorted_instructors = sorted(
                data.instructors,
                key=lambda x: (not x.is_primary, x.id),
            )
            enrolled_count = (
                data.enrolled_count
                if hasattr(data, "enrolled_count")
                else (len(data.enrollments) if hasattr(data, "enrollments") else 0)
            )
            return {
                "id": data.id,
                "title": data.title,
                "description": data.description,
                "published": data.published,
                "rating": float(data.rating) if data.rating is not None else None,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "instructors": sorted_instructors,
                "enrolled_count": enrolled_count,
            }
        return data
