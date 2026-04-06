"""
同步股票详细信息（行业、板块、股本等）
"""
import asyncio
import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.sqlite import get_session, StockInfo


class StockDetailSync:
    """股票详细信息同步工具"""
    
    def __init__(self):
        self.source_name = "akshare"
    
    async def fetch_stock_details(self) -> List[Dict[str, Any]]:
        """
        获取股票详细信息（行业、板块、股本、上市日期等）
        
        Returns:
            股票详细信息列表
        """
        try:
            logger.info(f"从 {self.source_name} 获取股票详细信息...")
            
            # 方法 1：使用 stock_individual_info_em 获取详细信息
            # 这个方法可以获取行业、地区、股本等信息
            logger.info("获取个股基本信息...")
            
            # 先获取股票列表
            df_list = ak.stock_info_a_code_name()
            
            if df_list.empty:
                logger.warning(f"{self.source_name} 返回空数据")
                return []
            
            # 兼容不同的列名
            code_col = 'code' if 'code' in df_list.columns else '股票代码'
            name_col = 'name' if 'name' in df_list.columns else '股票名称'
            
            stock_details = []
            total = len(df_list)
            failed = 0
            
            # 逐个获取详细信息（限流，每 1 个休息 2-3 秒，避免被封）
            for idx, row in df_list.iterrows():
                code = row.get(code_col, '')
                name = row.get(name_col, '')
                
                if not code or not name:
                    continue
                
                try:
                    # 获取个股详细信息
                    import random
                    # 随机延迟 3-5 秒（增加延迟时间）
                    delay = random.uniform(3.0, 5.0)
                    await asyncio.sleep(delay)
                    
                    detail = await self._fetch_single_stock_detail_with_retry(code, name)
                    if detail:
                        stock_details.append(detail)
                    else:
                        failed += 1
                    
                    # 每 30 个休息 10 秒，避免被封 IP（更频繁的休息）
                    if (idx + 1) % 30 == 0:
                        logger.info(f"进度：{idx + 1}/{total} ({(idx + 1) / total * 100:.1f}%)，失败：{failed}")
                        logger.info("休息 10 秒...")
                        await asyncio.sleep(10)
                    
                    # 进度日志
                    if (idx + 1) % 100 == 0:
                        logger.info(f"进度：{idx + 1}/{total} ({(idx + 1) / total * 100:.1f}%)，失败：{failed}")
                        
                except Exception as e:
                    logger.warning(f"获取 {code} 详细信息失败：{e}")
                    failed += 1
                    continue
            
            logger.info(f"成功获取 {len(stock_details)}/{total} 只股票的详细信息，失败：{failed}")
            return stock_details
            
        except Exception as e:
            logger.error(f"获取股票详细信息失败：{e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _fetch_single_stock_detail_with_retry(self, code: str, name: str, max_retries: int = 5) -> Dict[str, Any]:
        """
        带重试的获取单只股票详细信息
        
        Args:
            code: 股票代码
            name: 股票名称
            max_retries: 最大重试次数
            
        Returns:
            详细信息字典
        """
        for attempt in range(max_retries):
            try:
                return await self._fetch_single_stock_detail(code, name)
            except Exception as e:
                if attempt < max_retries - 1:
                    # 递增等待时间：3, 6, 12, 24 秒
                    wait_time = 3 * (2 ** attempt)
                    logger.warning(f"获取 {code} 失败，{wait_time}秒后重试（{attempt + 1}/{max_retries}）: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"获取 {code} 失败，已达最大重试次数：{e}")
                    return None
        
        return None
    
    async def _fetch_single_stock_detail(self, code: str, name: str) -> Dict[str, Any]:
        """
        获取单只股票的详细信息
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            详细信息字典
        """
        try:
            # 使用 stock_individual_info_em 获取基本信息
            df = ak.stock_individual_info_em(symbol=code)
            
            if df.empty:
                return None
            
            # 转换为字典
            info = {}
            for _, row in df.iterrows():
                item = row.get('item', '')
                value = row.get('value', '')
                info[item] = value
            
            # 提取行业
            industry = info.get('行业', None)
            if industry and industry != '暂无' and industry != '':
                industry = str(industry).strip()
            else:
                industry = None
            
            # 地区信息这个接口没有，留空
            area = None
            
            # 上市日期
            list_date = info.get('上市时间', None)
            if list_date and list_date != '暂无' and list_date != '':
                list_date = str(list_date).strip()
            else:
                list_date = None
            
            # 提取股本（已经是数值，单位是股）
            total_shares = None
            float_shares = None
            
            # 总股本
            total = info.get('总股本', None)
            if total and total != '暂无' and total != '':
                try:
                    total_shares = float(total)
                except:
                    total_shares = None
            
            # 流通股本
            float_total = info.get('流通股', None)
            if float_total and float_total != '暂无' and float_total != '':
                try:
                    float_shares = float(float_total)
                except:
                    float_shares = None
            
            # 判断市场
            market = self._infer_market(code)
            
            return {
                'code': code,
                'name': name,
                'market': market,
                'industry': industry,
                'sector': None,  # 板块信息需要另外获取
                'area': area,
                'list_date': list_date,
                'total_shares': total_shares,
                'float_shares': float_shares,
            }
            
        except Exception as e:
            logger.warning(f"获取 {code} 详细信息失败：{e}")
            return None
    
    def _infer_market(self, code: str) -> str:
        """根据股票代码推断市场"""
        if code.startswith('6') or code.startswith('9'):
            return 'SH'
        elif code.startswith('0') or code.startswith('3'):
            return 'SZ'
        elif code.startswith('4') or code.startswith('8'):
            return 'BJ'
        else:
            return 'UNKNOWN'
    
    async def sync_to_database(
        self, 
        stock_details: List[Dict[str, Any]],
        session: AsyncSession
    ) -> int:
        """
        同步详细信息到数据库
        
        Args:
            stock_details: 股票详细信息列表
            session: 数据库会话
            
        Returns:
            更新的股票数量
        """
        try:
            count = 0
            updated = 0
            
            for detail in stock_details:
                code = detail['code']
                
                # 查找现有记录
                result = await session.execute(
                    select(StockInfo).where(StockInfo.code == code)
                )
                stock = result.scalar_one_or_none()
                
                if stock:
                    # 更新详细信息
                    if detail.get('industry'):
                        stock.industry = detail['industry']
                    if detail.get('sector'):
                        stock.sector = detail['sector']
                    if detail.get('area'):
                        stock.area = detail['area']
                    if detail.get('list_date'):
                        stock.list_date = detail['list_date']
                    if detail.get('total_shares'):
                        stock.total_shares = detail['total_shares']
                    if detail.get('float_shares'):
                        stock.float_shares = detail['float_shares']
                    
                    stock.updated_at = datetime.now()
                    updated += 1
                    count += 1
            
            await session.commit()
            
            logger.info(f"详细信息同步完成：更新 {updated}/{count} 只股票")
            return updated
            
        except Exception as e:
            logger.error(f"同步详细信息失败：{e}")
            await session.rollback()
            return 0
    
    async def auto_sync(self) -> bool:
        """
        自动同步股票详细信息
        
        Returns:
            是否成功同步
        """
        logger.info("开始同步股票详细信息...")
        
        # 获取详细信息
        stock_details = await self.fetch_stock_details()
        
        if not stock_details:
            logger.error("获取股票详细信息失败")
            return False
        
        # 同步到数据库
        async with get_session() as session:
            updated = await self.sync_to_database(stock_details, session)
        
        if updated > 0:
            logger.info(f"✅ 成功更新 {updated} 只股票的详细信息")
            return True
        else:
            logger.error("同步失败")
            return False


# 全局实例
stock_detail_sync = StockDetailSync()


# 命令行执行
if __name__ == '__main__':
    import asyncio
    asyncio.run(stock_detail_sync.auto_sync())
