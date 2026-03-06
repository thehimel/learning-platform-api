"""rating 1-5, one decimal place

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alter courses.rating: Numeric(3,2) -> Numeric(3,1), add check 1-5
    op.alter_column(
        'courses',
        'rating',
        existing_type=sa.Numeric(3, 2),
        type_=sa.Numeric(3, 1),
        existing_nullable=True,
    )
    op.create_check_constraint(
        'ck_courses_rating_range',
        'courses',
        'rating IS NULL OR (rating >= 1 AND rating <= 5)',
    )

    # Alter course_ratings.rating: Numeric(3,2) -> Numeric(3,1), add check 1-5
    op.alter_column(
        'course_ratings',
        'rating',
        existing_type=sa.Numeric(3, 2),
        type_=sa.Numeric(3, 1),
        existing_nullable=False,
    )
    op.create_check_constraint(
        'ck_course_rating_range',
        'course_ratings',
        'rating >= 1 AND rating <= 5',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_course_rating_range', 'course_ratings', type_='check')
    op.alter_column(
        'course_ratings',
        'rating',
        existing_type=sa.Numeric(3, 1),
        type_=sa.Numeric(3, 2),
        existing_nullable=False,
    )

    op.drop_constraint('ck_courses_rating_range', 'courses', type_='check')
    op.alter_column(
        'courses',
        'rating',
        existing_type=sa.Numeric(3, 1),
        type_=sa.Numeric(3, 2),
        existing_nullable=True,
    )
