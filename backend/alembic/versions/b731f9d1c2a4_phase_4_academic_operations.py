"""Complete academic operations workflows.

Revision ID: b731f9d1c2a4
Revises: f54c14450324
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b731f9d1c2a4"
down_revision: Union[str, None] = "f54c14450324"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("attendance_sessions", sa.Column("status", sa.String(length=20), server_default="published", nullable=False))
    op.create_check_constraint("ck_attendance_session_status", "attendance_sessions", "status IN ('draft', 'published', 'closed')")
    op.add_column("assignments", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE assignments SET published_at = created_at WHERE status = 'published'")
    op.drop_constraint("ck_submissions_status", "submissions", type_="check")
    op.create_check_constraint("ck_submissions_status", "submissions", "status IN ('draft', 'submitted', 'late', 'graded', 'returned')")
    op.add_column("exam_schedules", sa.Column("max_marks", sa.Numeric(8, 2), server_default="100", nullable=False))
    op.add_column("results", sa.Column("is_final", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.execute("UPDATE results SET is_final = true WHERE lower(assessment_name) = 'final'")


def downgrade() -> None:
    op.drop_column("results", "is_final")
    op.drop_column("exam_schedules", "max_marks")
    op.execute("UPDATE submissions SET status = 'submitted' WHERE status = 'late'")
    op.drop_constraint("ck_submissions_status", "submissions", type_="check")
    op.create_check_constraint("ck_submissions_status", "submissions", "status IN ('draft', 'submitted', 'graded', 'returned')")
    op.drop_column("assignments", "published_at")
    op.drop_constraint("ck_attendance_session_status", "attendance_sessions", type_="check")
    op.drop_column("attendance_sessions", "status")
