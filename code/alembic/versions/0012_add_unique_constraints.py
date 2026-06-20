"""Add UNIQUE constraints to silver and gold to prevent duplicate chunk rows.

Without these constraints, running --stage gold more than once (or running
--doc-id without a full clear) can silently insert duplicate (doc_id, chunk_index)
rows. The NOT EXISTS guard in get_unprocessed() is not race-safe and offers no
protection against manual re-runs.

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-17
"""

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_silver_doc_chunk ON silver (doc_id, chunk_index)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_gold_doc_chunk ON gold (doc_id, chunk_index)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_gold_discarded_doc_chunk ON gold_discarded (doc_id, chunk_index)")


def downgrade() -> None:
    from alembic import op
    op.execute("DROP INDEX IF EXISTS uq_silver_doc_chunk")
    op.execute("DROP INDEX IF EXISTS uq_gold_doc_chunk")
    op.execute("DROP INDEX IF EXISTS uq_gold_discarded_doc_chunk")
