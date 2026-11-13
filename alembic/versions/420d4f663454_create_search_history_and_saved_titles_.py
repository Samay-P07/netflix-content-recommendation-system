"""create search_history and saved_titles tables

Revision ID: 420d4f663454
Revises: 
Create Date: 2026-11-13 18:28:20.501901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '420d4f663454'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create search_history table
    op.create_table(
        'search_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('query', sa.String(length=255), nullable=False),
        sa.Column('selected_title_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_history_id'), 'search_history', ['id'], unique=False)
    op.create_index('idx_search_history_created_at', 'search_history', ['created_at'], unique=False)

    # 2. Create saved_titles table
    op.create_table(
        'saved_titles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('show_id', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_titles_id'), 'saved_titles', ['id'], unique=False)
    op.create_index(op.f('ix_saved_titles_show_id'), 'saved_titles', ['show_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_saved_titles_show_id'), table_name='saved_titles')
    op.drop_index(op.f('ix_saved_titles_id'), table_name='saved_titles')
    op.drop_table('saved_titles')
    op.drop_index('idx_search_history_created_at', table_name='search_history')
    op.drop_index(op.f('ix_search_history_id'), table_name='search_history')
    op.drop_table('search_history')
