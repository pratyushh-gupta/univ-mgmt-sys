"""Constrain scheduled exam maximum marks.

Revision ID: c84a9f2160d3
Revises: b731f9d1c2a4
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c84a9f2160d3"
down_revision: Union[str, None] = "b731f9d1c2a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint("ck_exam_schedule_max_marks_positive", "exam_schedules", "max_marks > 0")


def downgrade() -> None:
    op.drop_constraint("ck_exam_schedule_max_marks_positive", "exam_schedules", type_="check")
