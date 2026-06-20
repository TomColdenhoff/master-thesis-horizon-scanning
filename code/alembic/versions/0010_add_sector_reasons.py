"""Add sector_reasons JSONB column to synthesis table.

Maps each affected sector to a one-sentence explanation of why the signal
affects that sector. Populated by the synthesis LLM prompt.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-07
"""

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute(
        "ALTER TABLE synthesis ADD COLUMN IF NOT EXISTS "
        "sector_reasons JSONB NOT NULL DEFAULT '{}'::jsonb"
    )


def downgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE synthesis DROP COLUMN IF EXISTS sector_reasons")
