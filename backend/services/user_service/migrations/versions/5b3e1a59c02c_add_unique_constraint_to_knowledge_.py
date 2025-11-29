"""add_unique_constraint_to_knowledge_states

Revision ID: 5b3e1a59c02c
Revises: 961dd67ecd76
Create Date: 2025-11-25 10:28:03.598211

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b3e1a59c02c"
down_revision: str | Sequence[str] | None = "961dd67ecd76"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_student_concept", "knowledge_states", ["student_id", "concept_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_student_concept", "knowledge_states", type_="unique")
