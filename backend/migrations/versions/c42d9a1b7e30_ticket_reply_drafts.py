"""Store reply drafts, retrieved sources and review reasons."""
from alembic import op
import sqlalchemy as sa

revision = "c42d9a1b7e30"
down_revision = "a7b481d7948f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("reply_draft", sa.JSON(), nullable=True))
    op.add_column("tickets", sa.Column("knowledge_sources", sa.JSON(), nullable=True))
    op.add_column("tickets", sa.Column("review_reason", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("tickets", "review_reason")
    op.drop_column("tickets", "knowledge_sources")
    op.drop_column("tickets", "reply_draft")
