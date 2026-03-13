"""
测试数据生成脚本
生成模拟数据用于前端功能测试，无需从外部数据源拉取
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import (
    init_database, get_session, StockInfo, KLine, 
    TechnicalIndicatorDB, SectorInfo, ChipData
)
from loguru import logger


class MockDataGenerator:
    def __init__(self):
        self.stocks = [
            {"code": "000001", "name": "平安银行", "market": "SZ", "industry": "银行"},
            {"code": "000002", "name": "万科A", "market": "SZ", "industry": "房地产"},
            {"code": "000333", "name": "美的集团", "market": "SZ", "industry": "家电"},
            {"code": "000651", "name": "格力电器", "market": "SZ", "industry": "家电"},
            {"code": "000858", "name": "五粮液", "market": "SZ", "industry": "白酒"},
            {"code": "600000", "name": "浦发银行", "market": "SH", "industry": "银行"},
            {"code": "600036", "name": "招商银行", "market": "SH", "industry": "银行"},
            {"code": "600519", "name": "贵州茅台", "market": "SH", "industry": "白酒"},
            {"code": "600887", "name": "伊利股份", "market": "SH", "industry": "食品饮料"},
            {"code": "601318", "name": "中国平安", "market": "SH", "industry": "保险"},
            {"code": "000725", "name": "京东方A", "market": "SZ", "industry": "电子"},
            {"code": "002415", "name": "海康威视", "market": "SZ", "industry": "电子"},
            {"code": "002594", "name": "比亚迪", "market": "SZ", "industry": "汽车"},
            {"code": "300750", "name": "宁德时代", "market": "SZ", "industry": "电池"},
            {"code": "601012", "name": "隆基绿能", "market": "SH", "industry": "光伏"},
        ]
        
        # 扩展板块数据
        self.sectors = [
            # 行业板块
            {"code": "BK0001", "name": "银行", "sector_type": "industry"},
            {"code": "BK0002", "name": "房地产", "sector_type": "industry"},
            {"code": "BK0003", "name": "家电", "sector_type": "industry"},
            {"code": "BK0004", "name": "白酒", "sector_type": "industry"},
            {"code": "BK0005", "name": "电子", "sector_type": "industry"},
            {"code": "BK0006", "name": "汽车", "sector_type": "industry"},
            {"code": "BK0007", "name": "保险", "sector_type": "industry"},
            {"code": "BK0008", "name": "食品饮料", "sector_type": "industry"},
            {"code": "BK0009", "name": "光伏", "sector_type": "industry"},
            {"code": "BK0010", "name": "电池", "sector_type": "industry"},
            # 概念板块
            {"code": "BK0101", "name": "新能源", "sector_type": "concept"},
            {"code": "BK0102", "name": "人工智能", "sector_type": "concept"},
            {"code": "BK0103", "name": "芯片", "sector_type": "concept"},
            {"code": "BK0104", "name": "5G", "sector_type": "concept"},
            {"code": "BK0105", "name": "区块链", "sector_type": "concept"},
            # 地域板块
            {"code": "BK0201", "name": "北京", "sector_type": "area"},
            {"code": "BK0202", "name": "上海", "sector_type": "area"},
            {"code": "BK0203", "name": "深圳", "sector_type": "area"},
            {"code": "BK0204", "name": "广东", "sector_type": "area"},
            {"code": "BK0205", "name": "浙江", "sector_type": "area"},
        ]
    
    def generate_kline_data(self, code: str, days: int = 365) -> List[Dict[str, Any]]:
        """生成K线数据"""
        base_price = random.uniform(10, 500)
        klines = []
        
        end_date = datetime.now()
        
        for i in range(days):
            date = end_date - timedelta(days=days - i - 1)
            
            if date.weekday() >= 5:
                continue
            
            change_pct = random.uniform(-10, 10)
            base_price = base_price * (1 + change_pct / 100)
            
            open_price = base_price * (1 + random.uniform(-2, 2) / 100)
            close_price = base_price
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 3) / 100)
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 3) / 100)
            
            volume = random.randint(1000000, 100000000)
            amount = volume * (open_price + close_price) / 2
            turnover_rate = random.uniform(0.5, 10)
            
            klines.append({
                "code": code,
                "date": date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume,
                "amount": round(amount, 2),
                "turnover_rate": round(turnover_rate, 2),
                "adjust_type": "qfq"
            })
        
        return klines
    
    def generate_technical_indicators(self, klines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成技术指标数据"""
        indicators = []
        
        for i, kline in enumerate(klines):
            if i < 60:
                continue
            
            recent_closes = [k["close"] for k in klines[max(0, i-60):i+1]]
            
            ma5 = sum(recent_closes[-5:]) / 5 if len(recent_closes) >= 5 else None
            ma10 = sum(recent_closes[-10:]) / 10 if len(recent_closes) >= 10 else None
            ma20 = sum(recent_closes[-20:]) / 20 if len(recent_closes) >= 20 else None
            ma60 = sum(recent_closes[-60:]) / 60 if len(recent_closes) >= 60 else None
            
            if i >= 24:
                changes = [recent_closes[j] - recent_closes[j-1] 
                          for j in range(1, len(recent_closes))]
                gains = [c for c in changes if c > 0]
                losses = [-c for c in changes if c < 0]
                avg_gain = sum(gains[-6:]) / 6 if gains else 0
                avg_loss = sum(losses[-6:]) / 6 if losses else 0
                rs = avg_gain / avg_loss if avg_loss > 0 else 0
                rsi6 = 100 - (100 / (1 + rs))
            else:
                rsi6 = None
            
            indicators.append({
                "code": kline["code"],
                "date": kline["date"],
                "ma5": round(ma5, 2) if ma5 else None,
                "ma10": round(ma10, 2) if ma10 else None,
                "ma20": round(ma20, 2) if ma20 else None,
                "ma60": round(ma60, 2) if ma60 else None,
                "rsi6": round(rsi6, 2) if rsi6 else None,
                "rsi12": round(random.uniform(20, 80), 2),
                "rsi24": round(random.uniform(20, 80), 2),
                "macd": round(random.uniform(-1, 1), 4),
                "macd_signal": round(random.uniform(-1, 1), 4),
                "macd_hist": round(random.uniform(-0.5, 0.5), 4)
            })
        
        return indicators
    
    def generate_chip_data(self, code: str, quarters: int = 8) -> List[Dict[str, Any]]:
        """生成筹码数据"""
        chip_data = []
        base_count = random.randint(50000, 500000)
        
        for i in range(quarters):
            date = datetime.now() - timedelta(days=90 * (quarters - i - 1))
            
            shareholder_count = int(base_count * (1 + random.uniform(-0.1, 0.1)))
            avg_shares = random.uniform(1000, 10000)
            control_degree = random.uniform(0.3, 0.8)
            
            chip_data.append({
                "code": code,
                "date": date.strftime("%Y-%m-%d"),
                "shareholder_count": shareholder_count,
                "avg_shares_per_holder": round(avg_shares, 2),
                "control_degree": round(control_degree, 4),
                "concentration": round(random.uniform(0.1, 0.5), 4)
            })
            
            base_count = shareholder_count
        
        return chip_data
    
    def generate_sector_data(self) -> List[Dict[str, Any]]:
        """生成板块数据（带更多字段）"""
        sector_data = []
        
        for sector in self.sectors:
            sector_data.append({
                "code": sector["code"],
                "name": sector["name"],
                "sector_type": sector["sector_type"],
                "change_pct": round(random.uniform(-5, 5), 2),
                "volume": random.randint(10000000, 1000000000),
                "amount": random.uniform(100000000, 10000000000),
                "leading_stocks": random.sample([s["code"] for s in self.stocks], min(3, len(self.stocks)))
            })
        
        return sector_data
    
    async def insert_stock_info(self):
        """插入股票基本信息"""
        async with get_session() as session:
            for stock in self.stocks:
                result = await session.execute(
                    select(StockInfo).where(StockInfo.code == stock["code"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    stock_info = StockInfo(
                        code=stock["code"],
                        name=stock["name"],
                        market=stock["market"],
                        industry=stock["industry"],
                        sector=stock["industry"],
                        area="中国",
                        list_date="2010-01-01",
                        total_shares=random.uniform(1e9, 1e11),
                        float_shares=random.uniform(1e8, 5e10)
                    )
                    session.add(stock_info)
            
            await session.commit()
            logger.info(f"已插入 {len(self.stocks)} 条股票基本信息")
    
    async def insert_kline_data(self, days: int = 365):
        """插入K线数据"""
        total_klines = 0
        
        async with get_session() as session:
            for stock in self.stocks:
                klines = self.generate_kline_data(stock["code"], days)
                
                for kline in klines:
                    result = await session.execute(
                        select(KLine).where(
                            KLine.code == kline["code"],
                            KLine.date == kline["date"],
                            KLine.adjust_type == kline["adjust_type"]
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if not existing:
                        kline_record = KLine(**kline)
                        session.add(kline_record)
                        total_klines += 1
                
                await session.commit()
                logger.info(f"已插入 {stock['code']} {len(klines)} 条K线数据")
        
        logger.info(f"总共插入 {total_klines} 条K线数据")
    
    async def insert_technical_indicators(self):
        """插入技术指标数据"""
        total_indicators = 0
        
        async with get_session() as session:
            for stock in self.stocks:
                klines = self.generate_kline_data(stock["code"], 365)
                indicators = self.generate_technical_indicators(klines)
                
                for ind in indicators:
                    result = await session.execute(
                        select(TechnicalIndicatorDB).where(
                            TechnicalIndicatorDB.code == ind["code"],
                            TechnicalIndicatorDB.date == ind["date"]
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if not existing:
                        indicator_record = TechnicalIndicatorDB(**ind)
                        session.add(indicator_record)
                        total_indicators += 1
                
                await session.commit()
                logger.info(f"已插入 {stock['code']} {len(indicators)} 条技术指标数据")
        
        logger.info(f"总共插入 {total_indicators} 条技术指标数据")
    
    async def insert_sector_info(self):
        """插入板块信息"""
        sector_data = self.generate_sector_data()
        
        async with get_session() as session:
            for sector in sector_data:
                result = await session.execute(
                    select(SectorInfo).where(SectorInfo.code == sector["code"])
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    sector_info = SectorInfo(
                        code=sector["code"],
                        name=sector["name"],
                        sector_type=sector["sector_type"],
                        change_pct=sector["change_pct"],
                        volume=sector["volume"],
                        amount=sector["amount"]
                    )
                    session.add(sector_info)
            
            await session.commit()
            logger.info(f"已插入 {len(sector_data)} 条板块信息")
    
    async def insert_chip_data(self):
        """插入筹码数据"""
        total_chip = 0
        
        async with get_session() as session:
            for stock in self.stocks:
                chip_data = self.generate_chip_data(stock["code"])
                
                for chip in chip_data:
                    result = await session.execute(
                        select(ChipData).where(
                            ChipData.code == chip["code"],
                            ChipData.date == chip["date"]
                        )
                    )
                    existing = result.scalar_one_or_none()
                    
                    if not existing:
                        chip_record = ChipData(**chip)
                        session.add(chip_record)
                        total_chip += 1
                
                await session.commit()
                logger.info(f"已插入 {stock['code']} {len(chip_data)} 条筹码数据")
        
        logger.info(f"总共插入 {total_chip} 条筹码数据")


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始生成测试数据...")
    logger.info("=" * 50)
    
    await init_database()
    
    generator = MockDataGenerator()
    
    await generator.insert_stock_info()
    await generator.insert_kline_data(days=365)
    await generator.insert_technical_indicators()
    await generator.insert_sector_info()
    await generator.insert_chip_data()
    
    logger.info("=" * 50)
    logger.info("测试数据生成完成！")
    logger.info("=" * 50)
    
    print("\n测试数据已成功插入数据库！")
    print("包含：")
    print(f"  - {len(generator.stocks)} 只股票基本信息")
    print(f"  - 每只股票 365 天 K 线数据")
    print(f"  - 技术指标数据")
    print(f"  - {len(generator.sectors)} 个板块信息")
    print(f"  - 筹码数据")


if __name__ == "__main__":
    asyncio.run(main())
