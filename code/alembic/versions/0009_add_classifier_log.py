"""Add classifier_log table for per-document silver classification token tracking.

One row per document classified. Stores the decision, reason, and token counts
so silver-stage LLM costs can be queried alongside gold and synthesis.

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-07
"""

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS classifier_log (
            id             SERIAL PRIMARY KEY,
            doc_id         TEXT NOT NULL UNIQUE REFERENCES bronze(id),
            relevant       BOOLEAN NOT NULL,
            reason         TEXT NOT NULL DEFAULT '',
            input_tokens   INTEGER NOT NULL DEFAULT 0,
            output_tokens  INTEGER NOT NULL DEFAULT 0,
            profile_version TEXT NOT NULL DEFAULT '',
            timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def downgrade() -> None:
    from alembic import op
    op.execute("DROP TABLE IF EXISTS classifier_log")
