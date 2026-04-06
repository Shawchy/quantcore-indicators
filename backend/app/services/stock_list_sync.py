"""
股票列表同步工具

独立于数据源适配器的股票列表同步工具，直接使用 akshare 库
避免凭证注入问题，确保同步的可靠性
"""
import akshare as ak
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.sqlite import StockInfo, get_session


class StockListSync:
    """股票列表同步工具"""
    
    def __init__(self):
        self.source_name = "akshare"
    
    async def fetch_stock_list(self) -> List[Dict[str, Any]]:
        """
        获取 A 股股票列表
        
        Returns:
            股票列表，每个元素包含 code, name, market 等字段
        """
        try:
            logger.info(f"从 {self.source_name} 获取 A 股股票列表...")
            
            # 使用 akshare 直接获取股票列表
            df = ak.stock_info_a_code_name()
            
            if df.empty:
                logger.warning(f"{self.source_name} 返回空数据")
                return []
            
            # 兼容不同的列名
            code_col = 'code' if 'code' in df.columns else '股票代码'
            name_col = 'name' if 'name' in df.columns else '股票名称'
            
            stock_list = []
            for _, row in df.iterrows():
                code = row.get(code_col, '')
                name = row.get(name_col, '')
                
                if not code or not name:
                    continue
                
                # 判断市场
                market = self._infer_market(code)
                
                stock_list.append({
                    'code': code,
                    'name': name,
                    'market': market,
                    'industry': None,  # 后续可扩展获取行业信息
                    'sector': None,
                    'area': None,
                    'list_date': None,
                    'total_shares': None,
                    'float_shares': None,
                })
            
            logger.info(f"从 {self.source_name} 获取到 {len(stock_list)} 只股票")
            return stock_list
            
        except Exception as e:
            logger.error(f"从 {self.source_name} 获取股票列表失败：{e}")
            return []
    
    def _infer_market(self, code: str) -> str:
        """
        根据股票代码推断市场
        
        Args:
            code: 股票代码
            
        Returns:
            市场标识（SH/SZ/BJ）
        """
        if code.startswith('6') or code.startswith('9'):
            return 'SH'  # 沪市
        elif code.startswith('0') or code.startswith('3'):
            return 'SZ'  # 深市
        elif code.startswith('4') or code.startswith('8'):
            return 'BJ'  # 北交所
        else:
            return 'UNKNOWN'
    
    async def sync_to_database(
        self, 
        stock_list: List[Dict[str, Any]],
        session: AsyncSession
    ) -> int:
        """
        同步股票列表到数据库
        
        Args:
            stock_list: 股票列表
            session: 数据库会话
            
        Returns:
            同步的股票数量
        """
        try:
            count = 0
            updated = 0
            inserted = 0
            
            for stock_data in stock_list:
                code = stock_data['code']
                
                # 检查是否已存在
                result = await session.execute(
                    select(StockInfo).where(StockInfo.code == code)
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 更新现有记录
                    existing.name = stock_data['name']
                    existing.market = stock_data['market']
                    existing.industry = stock_data.get('industry')
                    existing.sector = stock_data.get('sector')
                    existing.area = stock_data.get('area')
                    existing.list_date = stock_data.get('list_date')
                    existing.total_shares = stock_data.get('total_shares')
                    existing.float_shares = stock_data.get('float_shares')
                    existing.updated_at = datetime.now()
                    updated += 1
                else:
                    # 插入新记录
                    new_stock = StockInfo(
                        code=code,
                        name=stock_data['name'],
                        market=stock_data['market'],
                        industry=stock_data.get('industry'),
                        sector=stock_data.get('sector'),
                        area=stock_data.get('area'),
                        list_date=stock_data.get('list_date'),
                        total_shares=stock_data.get('total_shares'),
                        float_shares=stock_data.get('float_shares'),
                    )
                    session.add(new_stock)
                    inserted += 1
                
                count += 1
            
            await session.commit()
            
            logger.info(
                f"股票列表同步完成：总计 {count} 只，"
                f"新增 {inserted} 只，更新 {updated} 只"
            )
            
            return count
            
        except Exception as e:
            logger.error(f"同步股票列表到数据库失败：{e}")
            await session.rollback()
            return 0
    
    async def check_database_status(self) -> Dict[str, Any]:
        """
        检查数据库中股票列表的状态
        
        Returns:
            包含股票数量、最后更新时间等信息的字典
        """
        async with get_session() as session:
            # 获取股票总数
            result = await session.execute(
                select(func.count()).select_from(StockInfo)
            )
            total_count = result.scalar() or 0
            
            # 获取最后更新时间
            result = await session.execute(
                select(func.max(StockInfo.updated_at))
            )
            last_update = result.scalar()
            
            # 判断是否需要更新（超过 7 天）
            needs_update = False
            days_since_update = None
            
            if last_update:
                days_since_update = (datetime.now() - last_update).days
                needs_update = days_since_update > 7
            else:
                needs_update = total_count == 0  # 没有数据时需要更新
            
            return {
                'total_count': total_count,
                'last_update': last_update,
                'days_since_update': days_since_update,
                'needs_update': needs_update,
            }
    
    async def auto_sync(self) -> bool:
        """
        自动同步股票列表
        
        检查数据库状态，如果需要更新则自动同步
        
        Returns:
            是否成功同步
        """
        # 检查数据库状态
        status = await self.check_database_status()
        
        logger.info(
            f"股票列表数据库状态：{status['total_count']}只股票，"
            f"最后更新：{status['last_update'] or '从未'}，"
            f"距今：{status['days_since_update'] or 'N/A'}天"
        )
        
        if not status['needs_update']:
            logger.info("股票列表数据较新，无需同步")
            return True
        
        logger.info("开始自动同步股票列表...")
        
        # 获取股票列表
        stock_list = await self.fetch_stock_list()
        
        if not stock_list:
            logger.error("获取股票列表失败")
            return False
        
        # 同步到数据库
        async with get_session() as session:
            count = await self.sync_to_database(stock_list, session)
        
        if count > 0:
            logger.info(f"自动同步完成：{count}只股票")
            return True
        else:
            logger.error("自动同步失败")
            return False


# 全局实例
stock_list_sync = StockListSync()
