import enum

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Enum as SAEnum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    Inherits from SQLAlchemyBaseUserTableUUID which provides:
      id, email, hashed_password, is_active, is_verified

    is_superuser is intentionally removed from the DB. It is replaced by a
    hybrid_property derived from role so fastapi-users internals keep working
    without a real column.

    Custom fields:
      role — platform role used for RBAC (student | instructor | admin)
    """

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole"),
        default=UserRole.student,
        server_default=UserRole.student.value,
        nullable=False,
    )

    @hybrid_property
    def is_superuser(self) -> bool:  # type: ignore[override]
        return self.role == UserRole.admin

    @is_superuser.setter
    def is_superuser(self, value: bool) -> None:  # type: ignore[override]
        # Intentionally a no-op — superuser status is derived from role, not stored separately.
        pass

    @is_superuser.expression
    @classmethod
    def is_superuser(cls):  # type: ignore[override]
        return cls.role == UserRole.admin

    # Course relationships (string references to avoid circular imports)
    instructed_courses = relationship("CourseInstructor", back_populates="user")
    course_ratings = relationship("CourseRating", back_populates="user")
    course_enrollments = relationship("CourseEnrollment", back_populates="user")
