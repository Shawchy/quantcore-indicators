"""Add risk metrics to backtest_record

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('backtest_record', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sortino_ratio', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('calmar_ratio', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('win_rate', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('max_consecutive_losses', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('backtest_record', schema=None) as batch_op:
        batch_op.drop_column('max_consecutive_losses')
        batch_op.drop_column('win_rate')
        batch_op.drop_column('calmar_ratio')
        batch_op.drop_column('sortino_ratio')
