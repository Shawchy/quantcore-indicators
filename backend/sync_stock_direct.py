"""
直接同步股票列表到数据库（不使用凭证注入）
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.storage.sqlite import get_session, StockInfo
from sqlalchemy import select
from loguru import logger

try:
    import efinance as ef
    USE_EFINANCE = True
    logger.info("使用 efinance 库直接获取股票列表")
except ImportError:
    USE_EFINANCE = False
    logger.warning("efinance 库未安装")

async def sync_stock_list():
    """同步股票列表"""
    logger.info("=" * 60)
    logger.info("开始同步股票列表（直接模式）")
    logger.info("=" * 60)
    
    if not USE_EFINANCE:
        logger.error("efinance 库未安装，无法同步")
        return
    
    try:
        # 使用 efinance 直接获取股票列表
        logger.info("获取股票列表...")
        
        # 获取沪深 A 股列表
        df = ef.stock.get_stock_list()
        logger.info(f"获取到 {len(df)} 只股票")
        
        if df.empty:
            logger.error("未获取到股票数据")
            return
        
        # 转换并保存到数据库
        logger.info("保存到数据库...")
        
        async with get_session() as session:
            count = 0
            for _, row in df.iterrows():
                try:
                    code = row.get('股票代码', '')
                    if not code:
                        continue
                    
                    # 检查是否已存在
                    existing = await session.execute(
                        select(StockInfo).where(StockInfo.code == code)
                    )
                    stock = existing.scalar_one_or_none()
                    
                    if stock:
                        # 更新
                        stock.name = row.get('股票名称', '')
                        stock.market = 'SH' if code.startswith('6') else 'SZ'
                        stock.industry = row.get('行业', '')
                        stock.sector = row.get('板块', '')
                        stock.area = row.get('地区', '')
                        stock.total_shares = row.get('总股本', None)
                        stock.float_shares = row.get('流通股本', None)
                        stock.updated_at = datetime.now()
                    else:
                        # 插入
                        stock = StockInfo(
                            code=code,
                            name=row.get('股票名称', ''),
                            market='SH' if code.startswith('6') else 'SZ',
                            industry=row.get('行业', ''),
                            sector=row.get('板块', ''),
                            area=row.get('地区', ''),
                            total_shares=row.get('总股本', None),
                            float_shares=row.get('流通股本', None),
                            updated_at=datetime.now()
                        )
                        session.add(stock)
                    
                    count += 1
                    
                    # 每 100 条提交一次
                    if count % 100 == 0:
                        await session.commit()
                        logger.info(f"已保存 {count} 只股票...")
                        
                except Exception as e:
                    logger.warning(f"处理股票 {code} 失败：{e}")
                    continue
            
            # 最终提交
            await session.commit()
            logger.info(f"同步成功：{count} 只股票")
        
        logger.info("=" * 60)
        logger.info("股票列表同步完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"同步失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(sync_stock_list())
