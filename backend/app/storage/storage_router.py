"""
存储路由器

根据数据特征自动选择最佳存储位置
热数据 → SQLite，冷数据 → Parquet
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from app.storage.parquet_manager import ParquetManager
from app.storage.sqlite import get_session, KLine, TechnicalIndicatorDB as IndicatorDB
from sqlalchemy import select, and_
from loguru import logger


class StorageRouter:
    """存储路由器 - 根据数据特征自动选择存储位置"""
    
    def __init__(self, hot_threshold_days: int = 90):
        """
        Args:
            hot_threshold_days: 热数据阈值（天），默认 90 天
        """
        self.parquet_manager = ParquetManager()
        self.hot_threshold_days = hot_threshold_days
    
    async def save_kline(
        self,
        code: str,
        kline_data: Dict[str, Any],
        adjust_type: str = "qfq"
    ):
        """
        智能保存 K 线数据
        
        策略:
        - 最近 90 天：SQLite（热数据）
        - 90 天以上：Parquet（冷数据）
        """
        kline_date = datetime.strptime(kline_data['date'], "%Y-%m-%d")
        days_old = (datetime.now() - kline_date).days
        
        if days_old <= self.hot_threshold_days:
            # 热数据：保存到 SQLite
            await self._save_to_sqlite(code, kline_data, adjust_type)
            logger.debug(f"保存热数据 {code} {kline_data['date']} 到 SQLite")
        else:
            # 冷数据：保存到 Parquet
            self.parquet_manager.save_klines(code, [kline_data], adjust_type)
            logger.debug(f"保存冷数据 {code} {kline_data['date']} 到 Parquet")
    
    async def save_klines_batch(
        self,
        code: str,
        klines: List[Dict[str, Any]],
        adjust_type: str = "qfq"
    ):
        """
        批量智能保存 K 线数据
        
        自动将数据按时间分别存储到 SQLite 和 Parquet
        """
        if not klines:
            return
        
        # 分类数据
        hot_klines = []
        cold_klines = []
        
        for kline_data in klines:
            kline_date = datetime.strptime(kline_data['date'], "%Y-%m-%d")
            days_old = (datetime.now() - kline_date).days
            
            if days_old <= self.hot_threshold_days:
                hot_klines.append(kline_data)
            else:
                cold_klines.append(kline_data)
        
        # 分别存储
        if hot_klines:
            await self._save_batch_to_sqlite(code, hot_klines, adjust_type)
            logger.info(f"批量保存热数据 {code} 到 SQLite: {len(hot_klines)} 条")
        
        if cold_klines:
            self.parquet_manager.save_klines(code, cold_klines, adjust_type)
            logger.info(f"批量保存冷数据 {code} 到 Parquet: {len(cold_klines)} 条")
    
    async def load_klines(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str = "qfq"
    ) -> List[Dict[str, Any]]:
        """
        智能加载 K 线数据
        
        自动从 SQLite 和 Parquet 中加载并合并
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        threshold_dt = datetime.now() - timedelta(days=self.hot_threshold_days)
        
        all_klines = []
        
        # 1. 从 SQLite 加载热数据
        if start_dt <= threshold_dt <= end_dt:
            sqlite_klines = await self._load_from_sqlite(
                code, start_date, threshold_dt.strftime("%Y-%m-%d"), adjust_type
            )
            all_klines.extend(sqlite_klines)
            logger.debug(f"从 SQLite 加载 {len(sqlite_klines)} 条热数据")
        
        # 2. 从 Parquet 加载冷数据
        if threshold_dt <= end_dt:
            # 确定 Parquet 需要加载的年份范围
            parquet_start = start_date if start_dt > threshold_dt else threshold_dt.strftime("%Y-%m-%d")
            parquet_klines = await self._load_from_parquet(
                code, parquet_start, end_date, adjust_type
            )
            all_klines.extend(parquet_klines)
            logger.debug(f"从 Parquet 加载 {len(parquet_klines)} 条冷数据")
        
        # 3. 合并和排序
        all_klines.sort(key=lambda x: x['date'])
        
        return all_klines
    
    async def migrate_old_data(self, code: str, adjust_type: str = "qfq"):
        """
        将旧数据从 SQLite 迁移到 Parquet
        
        用于定期归档历史数据
        """
        threshold_date = (datetime.now() - timedelta(days=self.hot_threshold_days)).strftime("%Y-%m-%d")
        
        async with get_session() as session:
            # 查询需要迁移的数据
            query = select(KLine).where(
                and_(
                    KLine.code == code,
                    KLine.date < threshold_date,
                    KLine.adjust_type == adjust_type
                )
            )
            result = await session.execute(query)
            old_klines = result.scalars().all()
            
            if not old_klines:
                logger.debug(f"股票 {code} 无需迁移的数据")
                return
            
            # 转换为字典格式
            kline_dicts = []
            for kline in old_klines:
                kline_dicts.append({
                    'date': kline.date,
                    'open': kline.open,
                    'high': kline.high,
                    'low': kline.low,
                    'close': kline.close,
                    'volume': kline.volume,
                    'amount': kline.amount,
                    'turnover_rate': kline.turnover_rate,
                    'pre_close': kline.pre_close
                })
            
            # 保存到 Parquet
            self.parquet_manager.save_klines(code, kline_dicts, adjust_type)
            
            # 从 SQLite 删除
            for kline in old_klines:
                await session.delete(kline)
            await session.commit()
            
            logger.info(f"迁移 {code} {len(old_klines)} 条数据到 Parquet")
    
    async def _save_to_sqlite(
        self,
        code: str,
        kline_data: Dict[str, Any],
        adjust_type: str
    ):
        """保存到 SQLite"""
        async with get_session() as session:
            # 检查是否已存在
            query = select(KLine).where(
                and_(
                    KLine.code == code,
                    KLine.date == kline_data['date'],
                    KLine.adjust_type == adjust_type
                )
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新
                for key, value in kline_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # 插入
                new_kline = KLine(
                    code=code,
                    date=kline_data['date'],
                    open=kline_data['open'],
                    high=kline_data['high'],
                    low=kline_data['low'],
                    close=kline_data['close'],
                    volume=kline_data['volume'],
                    amount=kline_data.get('amount'),
                    turnover_rate=kline_data.get('turnover_rate'),
                    pre_close=kline_data.get('pre_close'),
                    adjust_type=adjust_type
                )
                session.add(new_kline)
            
            await session.commit()
    
    async def _save_batch_to_sqlite(
        self,
        code: str,
        klines: List[Dict[str, Any]],
        adjust_type: str
    ):
        """批量保存到 SQLite"""
        async with get_session() as session:
            # 批量查询已存在的记录
            dates = [k['date'] for k in klines]
            query = select(KLine.date).where(
                and_(
                    KLine.code == code,
                    KLine.date.in_(dates),
                    KLine.adjust_type == adjust_type
                )
            )
            result = await session.execute(query)
            existing_dates = set(result.scalars().all())
            
            # 批量插入
            to_insert = []
            for kline_data in klines:
                if kline_data['date'] not in existing_dates:
                    new_kline = KLine(
                        code=code,
                        date=kline_data['date'],
                        open=kline_data['open'],
                        high=kline_data['high'],
                        low=kline_data['low'],
                        close=kline_data['close'],
                        volume=kline_data['volume'],
                        amount=kline_data.get('amount'),
                        turnover_rate=kline_data.get('turnover_rate'),
                        pre_close=kline_data.get('pre_close'),
                        adjust_type=adjust_type
                    )
                    to_insert.append(new_kline)
            
            if to_insert:
                session.add_all(to_insert)
                await session.commit()
    
    async def _load_from_sqlite(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str
    ) -> List[Dict[str, Any]]:
        """从 SQLite 加载"""
        async with get_session() as session:
            query = select(KLine).where(
                and_(
                    KLine.code == code,
                    KLine.date >= start_date,
                    KLine.date <= end_date,
                    KLine.adjust_type == adjust_type
                )
            ).order_by(KLine.date)
            
            result = await session.execute(query)
            return [self._kline_to_dict(k) for k in result.scalars().all()]
    
    async def _load_from_parquet(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str
    ) -> List[Dict[str, Any]]:
        """从 Parquet 加载"""
        df = self.parquet_manager.load_klines(code, start_date, end_date, adjust_type)
        return df.to_dict('records') if not df.empty else []
    
    def _kline_to_dict(self, kline: KLine) -> Dict[str, Any]:
        """KLine 对象转字典"""
        return {
            'code': kline.code,
            'date': kline.date,
            'open': kline.open,
            'high': kline.high,
            'low': kline.low,
            'close': kline.close,
            'volume': kline.volume,
            'amount': kline.amount,
            'turnover_rate': kline.turnover_rate,
            'pre_close': kline.pre_close
        }


_storage_router: Optional[StorageRouter] = None

def get_storage_router() -> StorageRouter:
    """获取全局存储路由器实例"""
    global _storage_router
    if _storage_router is None:
        _storage_router = StorageRouter()
    return _storage_router
