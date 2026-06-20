"""Add synthesis table — fourth pipeline layer.

The synthesis table holds one record per document (UNIQUE on doc_id).
It is produced by the synthesis stage, which reads all gold records for a
document and asks the LLM to produce one unified norm frame.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-07
"""

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS synthesis (
            id                SERIAL PRIMARY KEY,
            doc_id            TEXT NOT NULL UNIQUE REFERENCES bronze(id),
            norm_frame        JSONB NOT NULL DEFAULT '{}'::jsonb,
            expected_date     TEXT NOT NULL DEFAULT '',
            affected_sectors  TEXT[] NOT NULL DEFAULT '{}',
            client_action     TEXT NOT NULL DEFAULT '',
            signal_summary    TEXT NOT NULL DEFAULT '',
            signal_certainty  TEXT NOT NULL DEFAULT '',
            source_type       TEXT NOT NULL DEFAULT '',
            completeness_score INTEGER NOT NULL DEFAULT 0,
            stream_tag        TEXT NOT NULL DEFAULT '',
            confirmed         BOOLEAN,
            timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def downgrade() -> None:
    from alembic import op
    op.execute("DROP TABLE IF EXISTS synthesis")
