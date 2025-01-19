"""Add original_quantity field to Ingredient

Revision ID: 177ec7ab0096
Revises: 0001_initial
Create Date: 2025-01-09 16:01:50.435801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '177ec7ab0096'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ingredient', schema=None) as batch_op:
        batch_op.alter_column('quantity', existing_type=sa.Float(), nullable=True)  # Allow NULL values

def downgrade():
    with op.batch_alter_table('ingredient', schema=None) as batch_op:
        batch_op.alter_column('quantity', existing_type=sa.Float(), nullable=False)  # Reinstate NOT NULL constraint

