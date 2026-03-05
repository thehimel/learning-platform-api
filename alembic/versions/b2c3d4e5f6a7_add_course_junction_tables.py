"""add course_instructors course_ratings course_enrollments and rating updated_at to courses

Revision ID: b2c3d4e5f6a7
Revises: 1701d2f56b43
Create Date: 2026-03-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '1701d2f56b43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add rating and updated_at to courses
    op.add_column('courses', sa.Column('rating', sa.Numeric(3, 2), nullable=True))
    op.add_column(
        'courses',
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # course_instructors: many-to-many course ↔ instructor
    op.create_table(
        'course_instructors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), server_default='FALSE', nullable=False),
        sa.Column('added_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'user_id', name='uq_course_instructor'),
    )
    op.create_index(op.f('ix_course_instructors_course_id'), 'course_instructors', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_instructors_user_id'), 'course_instructors', ['user_id'], unique=False)

    # course_ratings: one rating per user per course
    op.create_table(
        'course_ratings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('rating', sa.Numeric(3, 2), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'user_id', name='uq_course_rating'),
    )
    op.create_index(op.f('ix_course_ratings_course_id'), 'course_ratings', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_ratings_user_id'), 'course_ratings', ['user_id'], unique=False)

    # course_enrollments: users can enroll in any course
    op.create_table(
        'course_enrollments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('enrolled_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'user_id', name='uq_course_enrollment'),
    )
    op.create_index(op.f('ix_course_enrollments_course_id'), 'course_enrollments', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_enrollments_user_id'), 'course_enrollments', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_course_enrollments_user_id'), table_name='course_enrollments')
    op.drop_index(op.f('ix_course_enrollments_course_id'), table_name='course_enrollments')
    op.drop_table('course_enrollments')

    op.drop_index(op.f('ix_course_ratings_user_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_course_id'), table_name='course_ratings')
    op.drop_table('course_ratings')

    op.drop_index(op.f('ix_course_instructors_user_id'), table_name='course_instructors')
    op.drop_index(op.f('ix_course_instructors_course_id'), table_name='course_instructors')
    op.drop_table('course_instructors')

    op.drop_column('courses', 'updated_at')
    op.drop_column('courses', 'rating')
