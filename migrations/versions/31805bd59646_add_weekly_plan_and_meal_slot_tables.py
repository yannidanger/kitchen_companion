"""Add weekly_plan and meal_slot tables

Revision ID: 31805bd59646
Revises: a9a797fe08d3
Create Date: 2025-01-12 15:26:32.510944

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31805bd59646'
down_revision = 'a9a797fe08d3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('weekly_plan',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('meal_slot',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('weekly_plan_id', sa.Integer(), nullable=False),
    sa.Column('day', sa.String(length=20), nullable=False),
    sa.Column('meal_type', sa.String(length=20), nullable=False),
    sa.Column('recipe_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ),
    sa.ForeignKeyConstraint(['weekly_plan_id'], ['weekly_plan.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ingredient', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=False,
               autoincrement=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ingredient', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=True,
               autoincrement=True)

    op.drop_table('meal_slot')
    op.drop_table('weekly_plan')
    # ### end Alembic commands ###
