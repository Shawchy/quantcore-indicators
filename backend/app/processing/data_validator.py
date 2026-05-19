"""
数据校验服务

提供标准化的数据校验功能，防止无效数据进入系统
"""
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger


class DataValidator:
    
    KLINE_REQUIRED_FIELDS = ['code', 'date', 'open', 'high', 'low', 'close', 'volume']
    KLINE_NUMERIC_FIELDS = ['open', 'high', 'low', 'close', 'volume']
    KLINE_OPTIONAL_FIELDS = ['amount', 'turnover_rate', 'pre_close']
    
    PRICE_LIMIT_DEFAULT = 0.10
    PRICE_LIMIT_ST = 0.05
    PRICE_LIMIT_KC = 0.20
    PRICE_LIMIT_CY = 0.20
    
    @staticmethod
    def validate_kline_data(klines: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not klines:
            return [], ["空数据"]
        
        valid_data = []
        errors = []
        prev_close_map = {}
        
        for i, k in enumerate(klines):
            try:
                missing_fields = [f for f in DataValidator.KLINE_REQUIRED_FIELDS if f not in k]
                if missing_fields:
                    raise ValueError(f"缺少必填字段: {missing_fields}")
                
                DataValidator._validate_numeric_fields(k)
                DataValidator._validate_logic_consistency(k)
                DataValidator._validate_price_limit(k, prev_close_map)
                
                valid_data.append(k)
                
                code = k.get('code', '')
                if code:
                    prev_close_map[code] = k.get('close', 0)
                
            except ValueError as e:
                error_msg = f"第{i}条: {str(e)}"
                errors.append(error_msg)
                
                if len(errors) <= 10:
                    logger.debug(f"K线数据校验失败: {error_msg}")
        
        if errors:
            logger.warning(
                f"K线数据校验完成：{len(valid_data)}/{len(klines)} 条通过，"
                f"{len(errors)} 条失败"
            )
        
        return valid_data, errors
    
    @staticmethod
    def _validate_numeric_fields(k: Dict[str, Any]):
        for field in DataValidator.KLINE_NUMERIC_FIELDS:
            val = k.get(field)
            
            if val is None:
                continue
            
            if not isinstance(val, (int, float)):
                raise ValueError(f"{field} 不是数值类型: {type(val).__name__}")
            
            if field in ['open', 'high', 'low', 'close']:
                if val < 0:
                    raise ValueError(f"{field} 不能为负数: {val}")
            
            if field == 'volume':
                if val < 0:
                    raise ValueError(f"成交量不能为负数: {val}")
        
        for field in DataValidator.KLINE_OPTIONAL_FIELDS:
            val = k.get(field)
            
            if val is None:
                continue
            
            if not isinstance(val, (int, float)):
                raise ValueError(f"{field} 不是数值类型: {type(val).__name__}")
            
            if val < 0:
                raise ValueError(f"{field} 不能为负数: {val}")
    
    @staticmethod
    def _validate_logic_consistency(k: Dict[str, Any]):
        high = k.get('high')
        low = k.get('low')
        open_price = k.get('open')
        close = k.get('close')
        
        if all([high, low, open_price, close]):
            if high < low:
                raise ValueError(f"最高价({high})不能低于最低价({low})")
            
            if not (low <= open_price <= high):
                raise ValueError(f"开盘价({open_price})不在高低价范围[{low}, {high}]内")
            
            if not (low <= close <= high):
                raise ValueError(f"收盘价({close})不在高低价范围[{low}, {high}]内")
    
    @staticmethod
    def _validate_price_limit(k: Dict[str, Any], prev_close_map: Dict[str, float]):
        code = k.get('code', '')
        close = k.get('close', 0)
        pre_close = k.get('pre_close')
        
        if not pre_close and code in prev_close_map:
            pre_close = prev_close_map[code]
        
        if not pre_close or pre_close <= 0 or close <= 0:
            return
        
        limit_ratio = DataValidator.PRICE_LIMIT_DEFAULT
        if code.startswith('688') or code.startswith('30'):
            limit_ratio = DataValidator.PRICE_LIMIT_KC
        elif code.startswith('8') or code.startswith('4'):
            limit_ratio = DataValidator.PRICE_LIMIT_DEFAULT
        
        change_pct = abs(close - pre_close) / pre_close
        
        if change_pct > limit_ratio * 1.02:
            raise ValueError(
                f"涨跌幅{change_pct:.2%}超过涨跌停限制{limit_ratio:.0%}"
            )
    
    @staticmethod
    def validate_stock_code(code: str) -> bool:
        if not code or not isinstance(code, str):
            return False
        
        code = code.strip()
        
        if len(code) != 6:
            return False
        
        if not code.isdigit():
            return False
        
        return True
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        from datetime import datetime
        
        if not date_str or not isinstance(date_str, str):
            return False
        
        date_str = date_str.strip()
        
        formats = ['%Y-%m-%d', '%Y%m%d']
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    @staticmethod
    def validate_kline_continuity(klines: List[Dict[str, Any]], max_gap_days: int = 10) -> List[str]:
        if len(klines) < 2:
            return []
        
        warnings = []
        from datetime import datetime, timedelta
        
        for i in range(1, len(klines)):
            try:
                curr_date = klines[i].get('date', '')
                prev_date = klines[i-1].get('date', '')
                
                if not curr_date or not prev_date:
                    continue
                
                fmt = '%Y-%m-%d' if '-' in curr_date else '%Y%m%d'
                curr = datetime.strptime(curr_date, fmt)
                prev = datetime.strptime(prev_date, fmt)
                
                gap = (curr - prev).days
                if gap > max_gap_days:
                    warnings.append(f"日期间隔过大: {prev_date} -> {curr_date} ({gap}天)")
            except (ValueError, TypeError):
                continue
        
        return warnings


data_validator = DataValidator()
