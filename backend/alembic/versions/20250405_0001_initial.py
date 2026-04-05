"""Initial migration - create all tables

Revision ID: 0001
Revises:
Create Date: 2025-04-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for TickFlow Quant Trading System"""
    
    # stock_info table
    op.create_table(
        'stock_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('market', sa.String(length=10), nullable=True),
        sa.Column('industry', sa.String(length=50), nullable=True),
        sa.Column('sector', sa.String(length=50), nullable=True),
        sa.Column('area', sa.String(length=50), nullable=True),
        sa.Column('list_date', sa.String(length=20), nullable=True),
        sa.Column('total_shares', sa.Float(), nullable=True),
        sa.Column('float_shares', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_stock_code', 'stock_info', ['code'], unique=False)
    op.create_index('idx_stock_industry', 'stock_info', ['industry'], unique=False)
    op.create_index('idx_stock_industry_market', 'stock_info', ['industry', 'market'], unique=False)
    op.create_index('idx_stock_sector_market', 'stock_info', ['sector', 'market'], unique=False)
    
    # kline table
    op.create_table(
        'kline',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('date', sa.String(length=20), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('turnover_rate', sa.Float(), nullable=True),
        sa.Column('pre_close', sa.Float(), nullable=True),
        sa.Column('adjust_type', sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'date', 'adjust_type', name='u_kline_code_date')
    )
    op.create_index('idx_kline_code', 'kline', ['code'], unique=False)
    op.create_index('idx_kline_code_date', 'kline', ['code', 'date'], unique=False)
    op.create_index('idx_kline_code_adjust', 'kline', ['code', 'adjust_type'], unique=False)
    op.create_index('idx_kline_volume_date', 'kline', ['volume', 'date'], unique=False)
    op.create_index('idx_kline_turnover_date', 'kline', ['turnover_rate', 'date'], unique=False)
    
    # technical_indicators table
    op.create_table(
        'technical_indicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('date', sa.String(length=20), nullable=False),
        sa.Column('ma5', sa.Float(), nullable=True),
        sa.Column('ma10', sa.Float(), nullable=True),
        sa.Column('ma20', sa.Float(), nullable=True),
        sa.Column('ma60', sa.Float(), nullable=True),
        sa.Column('rsi6', sa.Float(), nullable=True),
        sa.Column('rsi12', sa.Float(), nullable=True),
        sa.Column('rsi24', sa.Float(), nullable=True),
        sa.Column('macd', sa.Float(), nullable=True),
        sa.Column('macd_signal', sa.Float(), nullable=True),
        sa.Column('macd_hist', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'date', name='u_indicator_code_date')
    )
    op.create_index('idx_indicator_code', 'technical_indicators', ['code'], unique=False)
    op.create_index('idx_indicator_code_date', 'technical_indicators', ['code', 'date'], unique=False)
    op.create_index('idx_indicator_ma', 'technical_indicators', ['code', 'ma5', 'ma10', 'ma20'], unique=False)
    op.create_index('idx_indicator_macd', 'technical_indicators', ['code', 'macd', 'macd_signal'], unique=False)
    op.create_index('idx_indicator_rsi', 'technical_indicators', ['code', 'rsi6'], unique=False)
    
    # watchlist table
    op.create_table(
        'watchlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # chip_data table
    op.create_table(
        'chip_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('date', sa.String(length=20), nullable=False),
        sa.Column('shareholder_count', sa.Float(), nullable=True),
        sa.Column('avg_shares_per_holder', sa.Float(), nullable=True),
        sa.Column('control_degree', sa.Float(), nullable=True),
        sa.Column('concentration', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', 'date', name='u_chip_code_date')
    )
    op.create_index('idx_chip_code', 'chip_data', ['code'], unique=False)
    op.create_index('idx_chip_concentration_date', 'chip_data', ['concentration', 'date'], unique=False)
    
    # sector_info table
    op.create_table(
        'sector_info',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('sector_type', sa.String(length=20), nullable=True),
        sa.Column('change_pct', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_sector_code', 'sector_info', ['code'], unique=False)
    op.create_index('idx_sector_type', 'sector_info', ['sector_type'], unique=False)
    
    # strategy table
    op.create_table(
        'strategy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('strategy_type', sa.String(length=50), nullable=True),
        sa.Column('config', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_id')
    )
    
    # backtest_record table
    op.create_table(
        'backtest_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backtest_id', sa.String(length=50), nullable=False),
        sa.Column('strategy_id', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.String(length=20), nullable=True),
        sa.Column('end_date', sa.String(length=20), nullable=True),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('final_capital', sa.Float(), nullable=True),
        sa.Column('total_return', sa.Float(), nullable=True),
        sa.Column('annual_return', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('result_path', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('backtest_id')
    )
    
    # trade_record table
    op.create_table(
        'trade_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backtest_id', sa.String(length=50), nullable=False),
        sa.Column('trade_type', sa.String(length=10), nullable=True),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('commission', sa.Float(), nullable=True),
        sa.Column('trade_date', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trade_backtest_id', 'trade_record', ['backtest_id'], unique=False)
    op.create_index('idx_trade_code', 'trade_record', ['code'], unique=False)
    op.create_index('idx_trade_date', 'trade_record', ['trade_date'], unique=False)
    op.create_index('idx_trade_backtest_date', 'trade_record', ['backtest_id', 'trade_date'], unique=False)
    op.create_index('idx_trade_code_date', 'trade_record', ['code', 'trade_date'], unique=False)
    
    # users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_user_username', 'users', ['username'], unique=False)
    op.create_index('idx_user_username_email', 'users', ['username', 'email'], unique=False)
    
    # realtime_quote table
    op.create_table(
        'realtime_quote',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('change', sa.Float(), nullable=False),
        sa.Column('change_pct', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('prev_close', sa.Float(), nullable=False),
        sa.Column('turnover_rate', sa.Float(), nullable=True),
        sa.Column('quote_time', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='u_quote_code')
    )
    op.create_index('idx_quote_code', 'realtime_quote', ['code'], unique=False)
    op.create_index('idx_quote_code_time', 'realtime_quote', ['code', 'quote_time'], unique=False)
    op.create_index('idx_quote_change_pct', 'realtime_quote', ['change_pct'], unique=False)
    op.create_index('idx_quote_volume', 'realtime_quote', ['volume'], unique=False)
    
    # market_ranking table
    op.create_table(
        'market_ranking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ranking_date', sa.String(length=20), nullable=False),
        sa.Column('ranking_time', sa.String(length=20), nullable=False),
        sa.Column('ts_code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('change', sa.Float(), nullable=True),
        sa.Column('change_pct', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('open', sa.Float(), nullable=True),
        sa.Column('high', sa.Float(), nullable=True),
        sa.Column('low', sa.Float(), nullable=True),
        sa.Column('prev_close', sa.Float(), nullable=True),
        sa.Column('turnover_rate', sa.Float(), nullable=True),
        sa.Column('ranking_type', sa.String(length=20), nullable=False),
        sa.Column('rank_position', sa.Integer(), nullable=True),
        sa.Column('data_source', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ranking_date', 'market_ranking', ['ranking_date'], unique=False)
    op.create_index('idx_ranking_ts_code', 'market_ranking', ['ts_code'], unique=False)
    op.create_index('idx_ranking_date_type', 'market_ranking', ['ranking_date', 'ranking_type'], unique=False)
    op.create_index('idx_ranking_date_position', 'market_ranking', ['ranking_date', 'rank_position'], unique=False)
    op.create_index('idx_ranking_code_date', 'market_ranking', ['ts_code', 'ranking_date'], unique=False)
    
    # market_turnover table
    op.create_table(
        'market_turnover',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trade_date', sa.String(length=8), nullable=False),
        sa.Column('sh_turnover', sa.Float(), nullable=False),
        sa.Column('sz_turnover', sa.Float(), nullable=False),
        sa.Column('total_turnover', sa.Float(), nullable=False),
        sa.Column('stock_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trade_date')
    )
    op.create_index('idx_turnover_date', 'market_turnover', ['trade_date'], unique=False)


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop in reverse order to handle foreign key constraints
    op.drop_table('market_turnover')
    op.drop_table('market_ranking')
    op.drop_table('realtime_quote')
    op.drop_table('users')
    op.drop_table('trade_record')
    op.drop_table('backtest_record')
    op.drop_table('strategy')
    op.drop_table('sector_info')
    op.drop_table('chip_data')
    op.drop_table('watchlist')
    op.drop_table('technical_indicators')
    op.drop_table('kline')
    op.drop_table('stock_info')
