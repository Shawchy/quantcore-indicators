"""
使用 AkShare 获取股票行业信息
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, StockInfo
from app.adapters import akshare_adapter
from loguru import logger

async def update_industry_from_akshare():
    """从 AkShare 获取行业信息"""
    print("=" * 80, flush=True)
    print("从 AkShare 获取股票行业信息")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("-" * 80, flush=True)
    
    # 初始化 AkShare 适配器
    akshare_adapter.initialize()
    print(f"✅ AkShare 适配器初始化完成\n", flush=True)
    
    async with get_session() as session:
        # 获取所有股票
        result = await session.execute(select(StockInfo))
        stocks = result.scalars().all()
        
        print(f"📊 数据库共有 {len(stocks)} 只股票\n", flush=True)
        
        # 从 AkShare 获取行业分类
        print("📈 正在从 AkShare 获取行业分类...", flush=True)
        try:
            industry_df = await akshare_adapter._get_stock_info()
            
            if industry_df is not None:
                print(f"✅ 获取到 {len(industry_df)} 条行业信息\n", flush=True)
                
                # 创建代码到行业的映射
                industry_map = {}
                for _, row in industry_df.iterrows():
                    code = row.get('股票代码', row.get('code', ''))
                    industry = row.get('行业', row.get('industry', ''))
                    if code and industry:
                        industry_map[code] = industry
                
                print(f"行业映射表：{len(industry_map)} 条\n", flush=True)
                
                # 更新数据库
                print("💾 正在更新行业信息...", flush=True)
                updated_count = 0
                
                for stock in stocks:
                    if stock.code in industry_map:
                        stock.industry = industry_map[stock.code]
                        updated_count += 1
                
                await session.commit()
                
                print(f"\n✅ 更新完成", flush=True)
                print(f"   更新股票数：{updated_count} 只", flush=True)
            else:
                print("❌ 获取行业信息失败\n", flush=True)
        except Exception as e:
            print(f"❌ 获取行业信息失败：{e}\n", flush=True)
            logger.exception(e)
    
    # 验证结果
    print("\n📊 验证更新结果...", flush=True)
    async with get_session() as session:
        result = await session.execute(select(StockInfo))
        stocks = result.scalars().all()
        
        with_industry = [s for s in stocks if s.industry]
        
        print(f"\n✅ 数据库共有 {len(stocks)} 只股票", flush=True)
        print(f"   有 industry 字段：{len(with_industry)} 只", flush=True)
        
        # 统计 industry 分布
        if with_industry:
            industry_stats = {}
            for s in with_industry:
                ind = s.industry
                if ind not in industry_stats:
                    industry_stats[ind] = 0
                industry_stats[ind] += 1
            
            print(f"\n   Industry 分布 (前 10):", flush=True)
            for ind, count in sorted(industry_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"     {ind:15} {count:5} 只", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("完成", flush=True)
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 80, flush=True)
    
    return len(with_industry) > 0

if __name__ == '__main__':
    success = asyncio.run(update_industry_from_akshare())
    sys.exit(0 if success else 1)
