"""
创建市场成交额历史数据表

用于存储每日的市场总成交额数据，避免重复调用 akshare
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from sqlalchemy import text
from app.storage.sqlite import get_session

async def create_market_turnover_table():
    """创建市场成交额历史表"""
    
    async with get_session() as session:
        try:
            # 创建表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS market_turnover (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date TEXT UNIQUE NOT NULL,
                    sh_turnover REAL NOT NULL,
                    sz_turnover REAL NOT NULL,
                    total_turnover REAL NOT NULL,
                    stock_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await session.commit()
            
            # 创建索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_market_turnover_date 
                ON market_turnover(trade_date)
            """))
            await session.commit()
            
            print("✅ 市场成交额历史表创建成功！")
            print("\n表结构:")
            print("  - trade_date: 交易日期 (YYYYMMDD, 唯一索引)")
            print("  - sh_turnover: 沪市成交额 (元)")
            print("  - sz_turnover: 深市成交额 (元)")
            print("  - total_turnover: 总成交额 (元)")
            print("  - stock_count: 股票总数")
            print("  - created_at: 创建时间")
            print("  - updated_at: 更新时间")
            
            # 验证表是否存在
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='market_turnover'")
            )
            if result.fetchone():
                print("\n✅ 表验证成功！")
            else:
                print("\n❌ 表验证失败！")
                
        except Exception as e:
            print(f"❌ 创建表失败：{e}")
            await session.rollback()

if __name__ == '__main__':
    asyncio.run(create_market_turnover_table())
