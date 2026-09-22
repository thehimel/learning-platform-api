from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.courses.constants import (
    CK_COURSES_RATING_RANGE,
    CK_COURSE_RATING_RANGE,
    IX_COURSES_PUBLISHED_CREATED_AT_ID,
    RATING_MAX,
    RATING_MIN,
    RATING_NUMERIC_PRECISION,
    RATING_NUMERIC_SCALE,
    UQ_COURSE_ENROLLMENT,
    UQ_COURSE_INSTRUCTOR,
    UQ_COURSE_RATING,
)
from app.infra.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, server_default="FALSE", nullable=False)
    rating: Mapped[Decimal | None] = mapped_column(
        Numeric(RATING_NUMERIC_PRECISION, RATING_NUMERIC_SCALE), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()")
    )

    __table_args__ = (
        CheckConstraint(
            f"rating IS NULL OR (rating >= {RATING_MIN} AND rating <= {RATING_MAX})",
            name=CK_COURSES_RATING_RANGE,
        ),
        Index(
            IX_COURSES_PUBLISHED_CREATED_AT_ID,
            "created_at",
            "id",
            postgresql_where=text("published = true"),
            postgresql_ops={"created_at": "DESC", "id": "DESC"},
        ),
    )

    instructors = relationship(
        "CourseInstructor",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    ratings = relationship(
        "CourseRating",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    enrollments = relationship(
        "CourseEnrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )


class CourseInstructor(Base):
    __tablename__ = "course_instructors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, server_default="FALSE", nullable=False)
    added_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (UniqueConstraint("course_id", "user_id", name=UQ_COURSE_INSTRUCTOR),)

    course = relationship("Course", back_populates="instructors")
    user = relationship("User", back_populates="instructed_courses")


class CourseRating(Base):
    __tablename__ = "course_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(RATING_NUMERIC_PRECISION, RATING_NUMERIC_SCALE), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name=UQ_COURSE_RATING),
        CheckConstraint(f"rating >= {RATING_MIN} AND rating <= {RATING_MAX}", name=CK_COURSE_RATING_RANGE),
    )

    course = relationship("Course", back_populates="ratings")
    user = relationship("User", back_populates="course_ratings")


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (UniqueConstraint("course_id", "user_id", name=UQ_COURSE_ENROLLMENT),)

    course = relationship("Course", back_populates="enrollments")
    user = relationship("User", back_populates="course_enrollments")


# Avoids loading every enrollment just to count them.
Course.enrolled_count = column_property(
    select(func.count(CourseEnrollment.id))
    .where(CourseEnrollment.course_id == Course.id)
    .correlate(Course)
    .scalar_subquery()
)
