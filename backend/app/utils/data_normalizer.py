"""
数据标准化转换器

将不同数据源的原始数据转换为统一格式
"""
from typing import Dict, Any, Optional, List
from app.models.unified_models import (
    UnifiedKLine, UnifiedStockInfo, UnifiedRealtimeQuote,
    DataSourceType, AdjustType, MarketType
)
from loguru import logger


class DataNormalizer:
    """数据标准化转换器"""
    
    @staticmethod
    def normalize_code(code: str) -> str:
        """
        统一股票代码格式
        
        支持格式:
        - 600000 -> 600000
        - 600000.SH -> 600000
        - sh600000 -> 600000
        - 平安银行 -> 需要映射表（暂不支持）
        
        Returns:
            6 位数字代码
        """
        # 移除后缀
        if '.' in code:
            code = code.split('.')[0]
        # 移除前缀
        if len(code) >= 2 and code[:2].lower() in ['sh', 'sz', 'bj']:
            code = code[2:]
        return code.zfill(6)
    
    @staticmethod
    def normalize_market(code: str) -> MarketType:
        """
        根据股票代码判断市场类型
        
        Returns:
            MarketType (SH/SZ/BJ)
        """
        code = DataNormalizer.normalize_code(code)
        if code.startswith('6') or code.startswith('9'):
            return MarketType.SH
        elif code.startswith('0') or code.startswith('3'):
            return MarketType.SZ
        elif code.startswith('4') or code.startswith('8'):
            return MarketType.BJ
        else:
            return MarketType.SH  # 默认
    
    @staticmethod
    def normalize_kline(
        raw_data: Dict[str, Any],
        source: DataSourceType,
        adjust_type: AdjustType = AdjustType.QFQ
    ) -> Optional[UnifiedKLine]:
        """
        标准化 K 线数据
        
        Args:
            raw_data: 原始数据（字典格式）
            source: 数据源类型
            adjust_type: 复权类型
        
        Returns:
            标准化后的 K 线数据，失败返回 None
        """
        try:
            # 根据不同数据源提取字段
            if source == DataSourceType.EFINANCE:
                return DataNormalizer._normalize_efinance_kline(raw_data, adjust_type)
            elif source == DataSourceType.AKSHARE:
                return DataNormalizer._normalize_akshare_kline(raw_data, adjust_type)
            elif source == DataSourceType.BAOSTOCK:
                return DataNormalizer._normalize_baostock_kline(raw_data, adjust_type)
            elif source == DataSourceType.TICKFLOW:
                return DataNormalizer._normalize_tickflow_kline(raw_data, adjust_type)
            else:
                logger.error(f"不支持的数据源：{source}")
                return None
                
        except Exception as e:
            logger.error(f"标准化 K 线数据失败：{e}")
            return None
    
    @staticmethod
    def _normalize_efinance_kline(
        data: Dict[str, Any],
        adjust_type: AdjustType
    ) -> UnifiedKLine:
        """转换 EFinance K 线数据"""
        # 支持中文和英文字段名
        code = str(data.get('股票代码', data.get('code', '')))
        date = str(data.get('日期', data.get('date', '')))
        open_price = float(data.get('开盘', data.get('open', 0)))
        high = float(data.get('最高', data.get('high', 0)))
        low = float(data.get('最低', data.get('low', 0)))
        close = float(data.get('收盘', data.get('close', 0)))
        volume = float(data.get('成交量', data.get('volume', 0)))
        amount = data.get('成交额', data.get('amount'))
        turnover_rate = data.get('换手率', data.get('turnover_rate'))
        pre_close = data.get('昨收', data.get('pre_close'))
        
        # 格式化日期（如果是 20260224 格式，转换为 2026-02-24）
        if len(date) == 8 and date.isdigit():
            date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        
        return UnifiedKLine(
            code=DataNormalizer.normalize_code(code),
            date=date,
            open=open_price,
            high=high,
            low=low,
            close=close,
            pre_close=float(pre_close) if pre_close else None,
            volume=volume,
            amount=float(amount) if amount else None,
            turnover_rate=float(turnover_rate) if turnover_rate else None,
            adjust_type=adjust_type,
            source=DataSourceType.EFINANCE,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_akshare_kline(
        data: Dict[str, Any],
        adjust_type: AdjustType
    ) -> UnifiedKLine:
        """转换 AkShare K 线数据"""
        code = str(data.get('code', ''))
        return UnifiedKLine(
            code=DataNormalizer.normalize_code(code),
            date=str(data.get('date', '')),
            open=float(data.get('open', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            close=float(data.get('close', 0)),
            volume=float(data.get('volume', 0)),
            amount=float(data.get('amount', 0)) if data.get('amount') else None,
            turnover_rate=float(data.get('turnover', 0)) if data.get('turnover') else None,
            adjust_type=adjust_type,
            source=DataSourceType.AKSHARE,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_baostock_kline(
        data: Dict[str, Any],
        adjust_type: AdjustType
    ) -> UnifiedKLine:
        """转换 Baostock K 线数据"""
        code = str(data.get('code', ''))
        return UnifiedKLine(
            code=DataNormalizer.normalize_code(code),
            date=str(data.get('date', '')),
            open=float(data.get('open', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            close=float(data.get('close', 0)),
            pre_close=float(data.get('preClose', 0)) if data.get('preClose') else None,
            volume=float(data.get('volume', 0)),
            amount=float(data.get('amount', 0)) if data.get('amount') else None,
            turnover_rate=float(data.get('turn', 0)) if data.get('turn') else None,
            adjust_type=adjust_type,
            source=DataSourceType.BAOSTOCK,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_tickflow_kline(
        data: Dict[str, Any],
        adjust_type: AdjustType
    ) -> UnifiedKLine:
        """转换 TickFlow K 线数据"""
        code = str(data.get('symbol', ''))
        # TickFlow 格式可能是 600000.SH，需要转换
        if '.' in code:
            code = code.split('.')[0]
        
        return UnifiedKLine(
            code=code.zfill(6),
            date=str(data.get('time', '')),
            open=float(data.get('open', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            close=float(data.get('close', 0)),
            pre_close=float(data.get('prev_close', 0)) if data.get('prev_close') else None,
            volume=float(data.get('volume', 0)),
            amount=float(data.get('amount', 0)) if data.get('amount') else None,
            turnover_rate=float(data.get('turnover_rate', 0)) if data.get('turnover_rate') else None,
            adjust_type=adjust_type,
            source=DataSourceType.TICKFLOW,
            quality_score=1.0
        )
    
    @staticmethod
    def validate_kline(kline: UnifiedKLine) -> bool:
        """
        验证 K 线数据的有效性
        
        Args:
            kline: 统一格式的 K 线数据
            
        Returns:
            是否有效
        """
        # 检查是否为 None
        if kline is None:
            return False
        
        # 检查必填字段
        if not kline.code or not kline.date:
            return False
        
        # 检查价格字段
        price_fields = ['open', 'high', 'low', 'close']
        for field in price_fields:
            value = getattr(kline, field)
            if value is None or value < 0:
                return False
        
        # 检查价格逻辑：high >= low, high >= open, high >= close, low <= open, low <= close
        if kline.high < kline.low:
            return False
        if kline.high < kline.open or kline.high < kline.close:
            return False
        if kline.low > kline.open or kline.low > kline.close:
            return False
        
        # 检查成交量
        if kline.volume is not None and kline.volume < 0:
            return False
        
        return True
    
    @staticmethod
    def normalize_stock_info(
        raw_data: Dict[str, Any],
        source: DataSourceType
    ) -> Optional[UnifiedStockInfo]:
        """
        标准化股票基本信息
        
        Args:
            raw_data: 原始数据
            source: 数据源类型
        
        Returns:
            标准化后的股票信息
        """
        try:
            if source == DataSourceType.EFINANCE:
                return DataNormalizer._normalize_efinance_stock_info(raw_data)
            elif source == DataSourceType.AKSHARE:
                return DataNormalizer._normalize_akshare_stock_info(raw_data)
            elif source == DataSourceType.TICKFLOW:
                return DataNormalizer._normalize_tickflow_stock_info(raw_data)
            else:
                logger.error(f"不支持的数据源：{source}")
                return None
        except Exception as e:
            logger.error(f"标准化股票信息失败：{e}")
            return None
    
    @staticmethod
    def _normalize_efinance_stock_info(data: Dict[str, Any]) -> UnifiedStockInfo:
        """转换 EFinance 股票信息"""
        code = str(data.get('股票代码', ''))
        return UnifiedStockInfo(
            code=DataNormalizer.normalize_code(code),
            name=str(data.get('股票名称', '')),
            market=DataNormalizer.normalize_market(code),
            industry=str(data.get('所处行业', '') or ''),
            area='',
            list_date='',
            total_shares=float(data.get('总市值', 0)) / float(data.get('最新价', 1)) if data.get('最新价', 1) > 0 else 0,
            float_shares=float(data.get('流通市值', 0)) / float(data.get('最新价', 1)) if data.get('最新价', 1) > 0 else 0,
            total_market_cap=float(data.get('总市值', 0)),
            float_market_cap=float(data.get('流通市值', 0)),
            pe_ratio=float(data.get('市盈率', 0)) if data.get('市盈率') else None,
            pb_ratio=None,
            dividend_yield=None,
            source=DataSourceType.EFINANCE,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_akshare_stock_info(data: Dict[str, Any]) -> UnifiedStockInfo:
        """转换 AkShare 股票信息"""
        code = str(data.get('code', ''))
        return UnifiedStockInfo(
            code=DataNormalizer.normalize_code(code),
            name=str(data.get('name', '')),
            market=DataNormalizer.normalize_market(code),
            industry=str(data.get('industry', '') or ''),
            area=str(data.get('area', '') or ''),
            list_date=str(data.get('list_date', '') or ''),
            total_shares=float(data.get('total_shares', 0)),
            float_shares=float(data.get('float_shares', 0)),
            total_market_cap=float(data.get('total_market_cap', 0)),
            float_market_cap=float(data.get('float_market_cap', 0)),
            pe_ratio=float(data.get('pe_ratio', 0)) if data.get('pe_ratio') else None,
            pb_ratio=float(data.get('pb_ratio', 0)) if data.get('pb_ratio') else None,
            dividend_yield=float(data.get('dividend_yield', 0)) if data.get('dividend_yield') else None,
            source=DataSourceType.AKSHARE,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_tickflow_stock_info(data: Dict[str, Any]) -> UnifiedStockInfo:
        """转换 TickFlow 股票信息"""
        code = str(data.get('symbol', ''))
        if '.' in code:
            code = code.split('.')[0]
        
        return UnifiedStockInfo(
            code=code.zfill(6),
            name=str(data.get('name', '')),
            market=DataNormalizer.normalize_market(code),
            industry=str(data.get('industry', '') or ''),
            area='',
            list_date=str(data.get('list_date', '') or ''),
            total_shares=float(data.get('total_shares', 0)),
            float_shares=float(data.get('float_shares', 0)),
            total_market_cap=float(data.get('total_market_cap', 0)),
            float_market_cap=float(data.get('float_market_cap', 0)),
            pe_ratio=float(data.get('pe_ratio', 0)) if data.get('pe_ratio') else None,
            pb_ratio=None,
            dividend_yield=None,
            source=DataSourceType.TICKFLOW,
            quality_score=1.0
        )
    
    @staticmethod
    def normalize_realtime_quote(
        raw_data: Dict[str, Any],
        source: DataSourceType
    ) -> Optional[UnifiedRealtimeQuote]:
        """
        标准化实时行情数据
        
        Args:
            raw_data: 原始数据
            source: 数据源类型
        
        Returns:
            标准化后的实时行情
        """
        try:
            if source == DataSourceType.EFINANCE:
                return DataNormalizer._normalize_efinance_quote(raw_data)
            elif source == DataSourceType.AKSHARE:
                return DataNormalizer._normalize_akshare_quote(raw_data)
            elif source == DataSourceType.TICKFLOW:
                return DataNormalizer._normalize_tickflow_quote(raw_data)
            else:
                logger.error(f"不支持的数据源：{source}")
                return None
        except Exception as e:
            logger.error(f"标准化实时行情失败：{e}")
            return None
    
    @staticmethod
    def _normalize_efinance_quote(data: Dict[str, Any]) -> UnifiedRealtimeQuote:
        """转换 EFinance 实时行情"""
        code = str(data.get('股票代码', ''))
        return UnifiedRealtimeQuote(
            code=DataNormalizer.normalize_code(code),
            name=str(data.get('股票名称', '')),
            price=float(data.get('最新价', 0)),
            change=float(data.get('涨跌额', 0)),
            change_pct=float(data.get('涨跌幅', 0)),
            high=float(data.get('最高价', 0)),
            low=float(data.get('最低价', 0)),
            open=float(data.get('开盘价', 0)),
            pre_close=float(data.get('昨收价', 0)),
            volume=float(data.get('成交量', 0)),
            amount=float(data.get('成交额', 0)),
            bid1=float(data.get('买一价', 0)) if data.get('买一价') else None,
            bid1_volume=float(data.get('买一量', 0)) if data.get('买一量') else None,
            ask1=float(data.get('卖一价', 0)) if data.get('卖一价') else None,
            ask1_volume=float(data.get('卖一量', 0)) if data.get('卖一量') else None,
            source=DataSourceType.EFINANCE,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_akshare_quote(data: Dict[str, Any]) -> UnifiedRealtimeQuote:
        """转换 AkShare 实时行情"""
        code = str(data.get('code', ''))
        return UnifiedRealtimeQuote(
            code=DataNormalizer.normalize_code(code),
            name=str(data.get('name', '')),
            price=float(data.get('price', 0)),
            change=float(data.get('change', 0)),
            change_pct=float(data.get('change_pct', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            open=float(data.get('open', 0)),
            pre_close=float(data.get('pre_close', 0)),
            volume=float(data.get('volume', 0)),
            amount=float(data.get('amount', 0)),
            bid1=float(data.get('bid1', 0)) if data.get('bid1') else None,
            bid1_volume=float(data.get('bid1_volume', 0)) if data.get('bid1_volume') else None,
            ask1=float(data.get('ask1', 0)) if data.get('ask1') else None,
            ask1_volume=float(data.get('ask1_volume', 0)) if data.get('ask1_volume') else None,
            source=DataSourceType.AKSHARE,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_tickflow_quote(data: Dict[str, Any]) -> UnifiedRealtimeQuote:
        """转换 TickFlow 实时行情"""
        code = str(data.get('symbol', ''))
        if '.' in code:
            code = code.split('.')[0]
        
        ext = data.get('ext', {})
        return UnifiedRealtimeQuote(
            code=code.zfill(6),
            name=str(data.get('name', '')),
            price=float(data.get('last_price', 0)),
            change=float(ext.get('change', 0)) if ext else float(data.get('change', 0)),
            change_pct=float(ext.get('change_pct', 0)) if ext else float(data.get('change_pct', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            open=float(data.get('open', 0)),
            pre_close=float(data.get('prev_close', 0)),
            volume=float(data.get('volume', 0)),
            amount=float(data.get('amount', 0)),
            bid1=float(ext.get('bid1', 0)) if ext else None,
            bid1_volume=float(ext.get('bid1_volume', 0)) if ext else None,
            ask1=float(ext.get('ask1', 0)) if ext else None,
            ask1_volume=float(ext.get('ask1_volume', 0)) if ext else None,
            source=DataSourceType.TICKFLOW,
            quality_score=1.0
        )
