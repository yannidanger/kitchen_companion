"""Add updated_at column to weekly_plan

Revision ID: 6ffa01d54e3f
Revises: 31805bd59646
Create Date: 2025-01-14 14:21:05.558663

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ffa01d54e3f'
down_revision = '31805bd59646'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('weekly_plan', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('weekly_plan', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))
        batch_op.drop_column('updated_at')

    # ### end Alembic commands ###
