"""Add descriptor fields to RecipeIngredient

Revision ID: a9abff80dadd
Revises: 52e90eeecc0b
Create Date: 2025-03-05 17:36:20.409617

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9abff80dadd'
down_revision = '52e90eeecc0b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe_ingredient', schema=None) as batch_op:
        batch_op.add_column(sa.Column('size', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('descriptor', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('additional_descriptor', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe_ingredient', schema=None) as batch_op:
        batch_op.drop_column('additional_descriptor')
        batch_op.drop_column('descriptor')
        batch_op.drop_column('size')

    # ### end Alembic commands ###
