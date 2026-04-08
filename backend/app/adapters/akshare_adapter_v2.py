"""
AkShare 数据源适配器（重构版）

使用 AntiWindFacade 统一管理反爬策略。
"""

from typing import Optional, List, Dict, Any, Tuple, Callable, Union
import akshare as ak
import pandas as pd
from loguru import logger
from datetime import datetime
import asyncio
import random
import time

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
    MarketQuote
)
from .anti_wind.facade import AntiWindFacade


class AkShareDataAdapterV2(BaseDataAdapter):
    """AkShare 数据源适配器（重构版，使用 AntiWindFacade）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 初始化反爬策略门面
        self.anti_wind = AntiWindFacade({
            'enable_cookie_inject': True,
            'enable_tls_fingerprint': True,
            'enable_rate_limit': True,
            'enable_ua_rotation': True,
            'enable_smart_retry': True,
            'max_retries': self.config.get('max_retries', 3),
            'min_delay': self.config.get('min_delay', 1.0),
            'max_delay': self.config.get('max_delay', 3.0),
            'cookie_storage_dir': self.config.get('cookie_storage_dir', 'data/cookies'),
        })
        
        # 缓存机制
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        
        logger.info("✅ AkShare 适配器 V2 初始化完成（使用 AntiWindFacade）")
    
    async def get_stock_individual_info_em(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取个股详细资料（高危反爬 API）
        
        Args:
            code: 股票代码（6 位）
            
        Returns:
            个股详细资料字典
        """
        logger.info(f"🔍 开始获取个股详细资料：{code}（高危 API，使用 AntiWindFacade）")
        
        # 检查缓存
        cache_key = f"stock_info_{code}"
        cached = self._get_cache(cache_key)
        if cached:
            logger.info(f"✅ 缓存命中：{code}")
            return cached
        
        # 定义请求函数
        async def fetch_stock_info(url: str, method: str, headers: Dict, **kwargs):
            """包装 akshare 调用"""
            try:
                # 在线程池中执行同步调用
                loop = asyncio.get_event_loop()
                df = await loop.run_in_executor(None, ak.stock_individual_info_em, code)
                
                if df is None or df.empty:
                    return None
                
                # 解析数据
                info_dict = dict(zip(df["item"], df["value"]))
                
                # 转换为标准格式
                result = {
                    'code': code,
                    'latest_price': float(info_dict.get('最新价', 0)) if info_dict.get('最新价') else None,
                    'change_pct': float(info_dict.get('涨跌幅', 0)) if info_dict.get('涨跌幅') else None,
                    'change_amount': float(info_dict.get('涨跌额', 0)) if info_dict.get('涨跌额') else None,
                    'total_market_cap': float(info_dict.get('总市值', 0)) if info_dict.get('总市值') else None,
                    'float_market_cap': float(info_dict.get('流通市值', 0)) if info_dict.get('流通市值') else None,
                    'pe_ratio': float(info_dict.get('市盈率 - 动态', 0)) if info_dict.get('市盈率 - 动态') else None,
                    'pb_ratio': float(info_dict.get('市净率', 0)) if info_dict.get('市净率') else None,
                    'eps': float(info_dict.get('每股收益', 0)) if info_dict.get('每股收益') else None,
                    'roe': float(info_dict.get('净资产收益率', 0)) if info_dict.get('净资产收益率') else None,
                    'industry': info_dict.get('所属行业', ''),
                    'area': info_dict.get('地区', ''),
                    'list_date': info_dict.get('上市时间', ''),
                }
                
                logger.info(f"✅ 获取成功：{code} - {info_dict.get('股票简称', 'Unknown')}")
                return result
                
            except Exception as e:
                logger.error(f"❌ 获取失败 {code}: {e}")
                raise
        
        try:
            # 使用 AntiWindFacade 执行（自动应用所有反爬策略）
            result = await self.anti_wind.execute_with_strategies(
                request_func=fetch_stock_info,
                url=f'https://datacenter-web.eastmoney.com/api/data/v1/get?symbol={code}',
                method='GET'
            )
            
            # 保存到缓存（5 分钟）
            if result:
                self._set_cache(cache_key, result, ttl=300)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取个股详细资料失败 {code}（AntiWindFacade 已尝试所有重试）: {e}")
            return {
                'code': code,
                'error': str(e),
                'latest_price': None,
                'change_pct': None,
                'total_market_cap': None,
            }
    
    async def get_sector_list(self, sector_type: str = 'industry') -> Optional[List[SectorInfo]]:
        """
        获取板块列表
        
        Args:
            sector_type: 板块类型（industry/region/concept）
            
        Returns:
            板块列表
        """
        logger.info(f"🔍 开始获取板块列表：{sector_type}")
        
        cache_key = f"sector_list_{sector_type}"
        cached = self._get_cache(cache_key)
        if cached:
            logger.info(f"✅ 缓存命中：{sector_type}")
            return cached
        
        async def fetch_sectors(url: str, method: str, headers: Dict, **kwargs):
            """包装 akshare 调用"""
            try:
                loop = asyncio.get_event_loop()
                
                if sector_type == 'industry':
                    df = await loop.run_in_executor(None, ak.stock_board_industry_name_em)
                elif sector_type == 'region':
                    df = await loop.run_in_executor(None, ak.stock_province_city_em)
                elif sector_type == 'concept':
                    df = await loop.run_in_executor(None, ak.stock_board_concept_name_em)
                else:
                    raise ValueError(f"未知的板块类型：{sector_type}")
                
                if df is None or df.empty:
                    return []
                
                # 转换为 SectorInfo 列表
                sectors = []
                for _, row in df.iterrows():
                    sectors.append(SectorInfo(
                        name=row.get('板块名称', ''),
                        code=row.get('板块代码', ''),
                        type=sector_type,
                    ))
                
                logger.info(f"✅ 获取成功：{sector_type} - 共{len(sectors)}个板块")
                return sectors
                
            except Exception as e:
                logger.error(f"❌ 获取板块列表失败 {sector_type}: {e}")
                raise
        
        try:
            result = await self.anti_wind.execute_with_strategies(
                request_func=fetch_sectors,
                url=f'https://datacenter-web.eastmoney.com/api/data/v1/get?type={sector_type}',
                method='GET'
            )
            
            if result:
                self._set_cache(cache_key, result, ttl=600)  # 10 分钟缓存
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 获取板块列表失败 {sector_type}: {e}")
            return []
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            if time.time() < self._cache_ttl.get(key, 0):
                return self._cache[key]
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any, ttl: float = 300):
        """设置缓存"""
        self._cache[key] = value
        self._cache_ttl[key] = time.time() + ttl
        logger.debug(f"💾 缓存已设置：{key} (TTL={ttl}s)")
    
    def print_strategy_status(self):
        """打印反爬策略状态"""
        self.anti_wind.print_status()
