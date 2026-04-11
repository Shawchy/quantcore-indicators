"""
数据校验服务

提供标准化的数据校验功能，防止无效数据进入系统
"""
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger


class DataValidator:
    """
    数据校验器
    
    校验规则：
    - 必填字段检查
    - 数据类型验证
    - 数值范围合理性检查
    - 逻辑一致性校验
    """
    
    KLINE_REQUIRED_FIELDS = ['code', 'date', 'open', 'high', 'low', 'close', 'volume']
    KLINE_NUMERIC_FIELDS = ['open', 'high', 'low', 'close', 'volume']
    KLINE_OPTIONAL_FIELDS = ['amount', 'turnover_rate', 'pre_close']
    
    @staticmethod
    def validate_kline_data(klines: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not klines:
            return [], ["空数据"]
        
        valid_data = []
        errors = []
        
        for i, k in enumerate(klines):
            try:
                missing_fields = [f for f in DataValidator.KLINE_REQUIRED_FIELDS if f not in k]
                if missing_fields:
                    raise ValueError(f"缺少必填字段: {missing_fields}")
                
                DataValidator._validate_numeric_fields(k)
                DataValidator._validate_logic_consistency(k)
                
                valid_data.append(k)
                
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


data_validator = DataValidator()
