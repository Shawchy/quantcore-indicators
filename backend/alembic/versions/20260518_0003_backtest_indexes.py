"""Add backtest_record indexes

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('backtest_record', schema=None) as batch_op:
        batch_op.create_index('idx_backtest_strategy_status', ['strategy_id', 'status'])
        batch_op.create_index('idx_backtest_created_at', ['created_at'])
        batch_op.create_index('idx_backtest_sharpe', ['sharpe_ratio'])


def downgrade() -> None:
    with op.batch_alter_table('backtest_record', schema=None) as batch_op:
        batch_op.drop_index('idx_backtest_sharpe')
        batch_op.drop_index('idx_backtest_created_at')
        batch_op.drop_index('idx_backtest_strategy_status')
