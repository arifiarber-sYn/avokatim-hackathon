"""Add case_requests.structured_answers (D-059 F5).

Category-specific intake questionnaire answers ({question_key: value});
questions themselves are seed data in app/seeds/case_intake_questions.py.

Revision ID: d2e3f4a5b6c7
Revises: c9d1e2f3a4b5
Create Date: 2026-08-04
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "d2e3f4a5b6c7"
down_revision = "c9d1e2f3a4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("case_requests", sa.Column("structured_answers", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("case_requests", "structured_answers")
