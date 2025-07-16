"""Create test_table

Revision ID: initial_migration
Revises: 
Create Date: 2025-07-16 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_table
    op.create_table('test_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_table_id'), 'test_table', ['id'], unique=False)
    op.create_index(op.f('ix_test_table_name'), 'test_table', ['name'], unique=False)


def downgrade() -> None:
    # Drop test_table
    op.drop_index(op.f('ix_test_table_name'), table_name='test_table')
    op.drop_index(op.f('ix_test_table_id'), table_name='test_table')
    op.drop_table('test_table')
