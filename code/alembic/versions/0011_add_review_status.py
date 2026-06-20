"""Add review_status column to synthesis table.

Replaces the binary confirmed BOOLEAN with a four-way status:
  strong    — confirmed strong signal, high confidence
  weak      — confirmed but weak or uncertain signal
  unsure    — reviewer is not sure, needs follow-up
  discarded — noise, not a real signal

The confirmed column is kept for backwards compatibility and is derived:
  strong / weak  → confirmed = true
  discarded      → confirmed = false
  unsure         → confirmed = null (still treated as unreviewed in old queries)

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-07
"""

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from alembic import op
    op.execute(
        "ALTER TABLE synthesis ADD COLUMN IF NOT EXISTS "
        "review_status TEXT CHECK (review_status IN ('strong', 'weak', 'unsure', 'discarded'))"
    )


def downgrade() -> None:
    from alembic import op
    op.execute("ALTER TABLE synthesis DROP COLUMN IF EXISTS review_status")
