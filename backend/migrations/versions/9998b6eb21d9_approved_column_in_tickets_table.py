"""approved column in tickets table

Revision ID: 9998b6eb21d9
Revises: c42d9a1b7e30
Create Date: 2026-10-25 11:14:44.268479

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9998b6eb21d9"
down_revision: Union[str, Sequence[str], None] = "c42d9a1b7e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("approved", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tickets", "approved")
