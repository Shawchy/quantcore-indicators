"""
股票信息管理服务层
负责从适配器获取数据，清洗处理后存储到数据库
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.baostock_adapter import BaostockAdapter
from app.adapters.base import StockBasicInfo
from app.storage.sqlite import get_session, StockInfo


class StockInfoService:
    """
    股票信息服务
    
    职责：
    1. 从 Baostock 适配器获取股票数据
    2. 数据清洗和验证
    3. 同步到数据库
    4. 提供查询接口
    """
    
    def __init__(self):
        self.adapter = BaostockAdapter()
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化适配器"""
        if not self._initialized:
            success = await self.adapter.initialize()
            if success:
                self._initialized = True
                logger.info("StockInfoService 初始化成功")
            return success
        return True
    
    async def close(self):
        """关闭适配器"""
        if self._initialized:
            await self.adapter.close()
            self._initialized = False
            logger.info("StockInfoService 已关闭")
    
    async def sync_all_stocks(self, clear_first: bool = False) -> bool:
        """
        同步所有股票信息到数据库
        
        Args:
            clear_first: 是否先清空数据库
            
        Returns:
            bool: 同步是否成功
        """
        logger.info("="*60)
        logger.info("开始同步股票信息")
        logger.info("="*60)
        
        try:
            # 初始化适配器
            if not await self.initialize():
                logger.error("适配器初始化失败")
                return False
            
            # 清空数据库（可选）
            if clear_first:
                logger.info("清空现有数据...")
                async with get_session() as session:
                    await session.execute(text("DELETE FROM stock_info"))
                    await session.commit()
                logger.info("数据库已清空")
            
            # 从适配器获取数据
            logger.info("从 Baostock 获取股票列表...")
            stock_list = await self.adapter.get_stock_list()
            
            if not stock_list:
                logger.error("未获取到股票数据")
                return False
            
            logger.info(f"成功获取 {len(stock_list)} 只股票")
            
            # 数据清洗和验证
            logger.info("数据清洗和验证...")
            cleaned_stocks = self._clean_stock_data(stock_list)
            logger.info(f"清洗后有效数据：{len(cleaned_stocks)} 只")
            
            # 同步到数据库
            async with get_session() as session:
                created, updated = await self._save_to_database(session, cleaned_stocks)
            
            logger.info(f"\n同步完成:")
            logger.info(f"  新增：{created} 只")
            logger.info(f"  更新：{updated} 只")
            logger.info(f"  总计：{created + updated} 只")
            
            return True
            
        except Exception as e:
            logger.error(f"同步失败：{e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.close()
    
    def _clean_stock_data(self, stock_list: List[StockBasicInfo]) -> List[StockBasicInfo]:
        """
        数据清洗
        
        Args:
            stock_list: 原始股票列表
            
        Returns:
            List[StockBasicInfo]: 清洗后的股票列表
        """
        cleaned = []
        
        for stock in stock_list:
            try:
                # 验证必填字段
                if not stock.code or not stock.name:
                    logger.warning(f"跳过无效记录：{stock}")
                    continue
                
                # 代码格式标准化（补齐 6 位）
                stock.code = stock.code.zfill(6)
                
                # 市场标识标准化
                if stock.market not in ['SH', 'SZ', 'BJ']:
                    if stock.code.startswith('6') or stock.code.startswith('9'):
                        stock.market = 'SH'
                    elif stock.code.startswith('0') or stock.code.startswith('3'):
                        stock.market = 'SZ'
                    elif stock.code.startswith('8'):
                        stock.market = 'BJ'
                    else:
                        logger.warning(f"未知市场：{stock.code}")
                        continue
                
                # 日期格式验证
                if stock.list_date:
                    stock.list_date = self._validate_date(stock.list_date)
                
                if stock.delist_date:
                    stock.delist_date = self._validate_date(stock.delist_date)
                
                # 类型和状态验证
                if stock.type not in [1, 2, 3, 4, 5]:
                    stock.type = 1
                
                if stock.status not in [0, 1]:
                    stock.status = 1
                
                cleaned.append(stock)
                
            except Exception as e:
                logger.warning(f"清洗股票 {stock.code} 失败：{e}")
                continue
        
        return cleaned
    
    def _validate_date(self, date_str: str) -> Optional[str]:
        """
        验证日期格式
        
        Args:
            date_str: 日期字符串
            
        Returns:
            Optional[str]: 验证后的日期字符串，格式为 YYYY-MM-DD
        """
        if not date_str:
            return None
        
        # 尝试多种格式
        formats = ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d']
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"无效日期格式：{date_str}")
        return None
    
    async def _save_to_database(
        self, 
        session: AsyncSession, 
        stock_list: List[StockBasicInfo]
    ) -> tuple[int, int]:
        """
        保存到数据库
        
        Args:
            session: 数据库会话
            stock_list: 股票列表
            
        Returns:
            tuple[int, int]: (新增数量，更新数量)
        """
        created = 0
        updated = 0
        
        for stock in stock_list:
            try:
                # 查询现有记录
                result = await session.execute(
                    select(StockInfo).where(StockInfo.code == stock.code)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 更新记录
                    existing.name = stock.name
                    existing.market = stock.market
                    existing.type = stock.type
                    existing.status = stock.status
                    if stock.list_date and not existing.list_date:
                        existing.list_date = stock.list_date
                    if stock.delist_date and not existing.delist_date:
                        existing.delist_date = stock.delist_date
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
                    # 新增记录
                    new_stock = StockInfo(
                        code=stock.code,
                        name=stock.name,
                        market=stock.market,
                        type=stock.type,
                        status=stock.status,
                        list_date=stock.list_date,
                        delist_date=stock.delist_date,
                        industry=stock.industry,
                        sector=stock.sector,
                        area=stock.area,
                        total_shares=stock.total_shares,
                        float_shares=stock.float_shares
                    )
                    session.add(new_stock)
                    created += 1
                
                # 批量提交（每 1000 条）
                if (created + updated) % 1000 == 0:
                    await session.commit()
                    logger.info(f"进度：{created + updated} (新增：{created}, 更新：{updated})")
                    
            except Exception as e:
                logger.warning(f"保存股票 {stock.code} 失败：{e}")
                continue
        
        # 最后提交
        await session.commit()
        
        return created, updated
    
    async def get_stock_count(self) -> int:
        """获取股票总数"""
        async with get_session() as session:
            result = await session.execute(select(StockInfo))
            stocks = result.fetchall()
            return len(stocks)
    
    async def get_stock_by_code(self, code: str) -> Optional[StockInfo]:
        """
        根据代码查询股票
        
        Args:
            code: 股票代码
            
        Returns:
            Optional[StockInfo]: 股票信息
        """
        async with get_session() as session:
            result = await session.execute(
                select(StockInfo).where(StockInfo.code == code)
            )
            return result.scalar_one_or_none()


# 全局服务实例
_stock_info_service = None


def get_stock_info_service() -> StockInfoService:
    """获取全局服务实例"""
    global _stock_info_service
    if _stock_info_service is None:
        _stock_info_service = StockInfoService()
    return _stock_info_service


# 命令行执行
if __name__ == '__main__':
    import sys
    from sqlalchemy import text
    
    clear_first = '--clear' in sys.argv
    
    async def main():
        service = get_stock_info_service()
        success = await service.sync_all_stocks(clear_first=clear_first)
        
        if success:
            logger.success("✅ 同步成功")
            count = await service.get_stock_count()
            logger.info(f"数据库共有 {count} 只股票")
        else:
            logger.error("❌ 同步失败")
            sys.exit(1)
    
    asyncio.run(main())
