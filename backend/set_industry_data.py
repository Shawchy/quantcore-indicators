"""
批量设置股票行业信息（示例数据）
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import random

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, StockInfo

# 行业列表（申万一级行业）
INDUSTRIES = [
    "农林牧渔", "基础化工", "钢铁", "有色金属", "电子", "家用电器", "食品饮料", "纺织服饰",
    "轻工制造", "医药生物", "公用事业", "交通运输", "房地产", "商贸零售", "社会服务",
    "银行", "非银金融", "综合", "汽车", "机械设备", "国防军工", "计算机", "传媒",
    "通信", "建筑材料", "建筑装饰", "石油石化", "煤炭", "电力设备", "环保", "美容护理"
]

async def set_industry_data():
    """批量设置行业信息"""
    print("=" * 80, flush=True)
    print("批量设置股票行业信息")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("-" * 80, flush=True)
    
    random.seed(42)  # 固定随机种子以便复现
    
    async with get_session() as session:
        # 获取所有股票
        result = await session.execute(select(StockInfo))
        stocks = result.scalars().all()
        
        print(f"📊 数据库共有 {len(stocks)} 只股票\n", flush=True)
        
        # 批量更新
        print("💾 正在设置行业信息...", flush=True)
        updated_count = 0
        
        for stock in stocks:
            # 根据股票代码分配行业（模拟真实分布）
            if not stock.industry:
                # 使用代码后两位作为索引，使同一行业的股票相对集中
                code_num = int(stock.code[-2:]) if stock.code[-2:].isdigit() else random.randint(0, len(INDUSTRIES)-1)
                stock.industry = INDUSTRIES[code_num % len(INDUSTRIES)]
                updated_count += 1
        
        await session.commit()
        
        print(f"\n✅ 更新完成", flush=True)
        print(f"   更新股票数：{updated_count} 只", flush=True)
    
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
    success = asyncio.run(set_industry_data())
    sys.exit(0 if success else 1)
