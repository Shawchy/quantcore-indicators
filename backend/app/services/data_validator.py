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
    
    使用方式：
        valid_data, errors = data_validator.validate_kline_data(klines)
    """
    
    # K 线数据的必填字段
    KLINE_REQUIRED_FIELDS = ['code', 'date', 'open', 'high', 'low', 'close', 'volume']
    
    # 数值字段（必须为数字）
    KLINE_NUMERIC_FIELDS = ['open', 'high', 'low', 'close', 'volume']
    
    # 可选数值字段
    KLINE_OPTIONAL_FIELDS = ['amount', 'turnover_rate', 'pre_close']
    
    @staticmethod
    def validate_kline_data(klines: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        校验 K 线数据
        
        Args:
            klines: K 线数据列表
            
        Returns:
            (有效数据列表, 错误消息列表)
            
        示例:
            >>> data = [{"code": "000001", "date": "2024-01-01", "open": 10.0, ...}]
            >>> valid_data, errors = DataValidator.validate_kline_data(data)
            >>> print(f"有效: {len(valid_data)}, 错误: {len(errors)}")
        """
        if not klines:
            return [], ["空数据"]
        
        valid_data = []
        errors = []
        
        for i, k in enumerate(klines):
            try:
                # 1. 必填字段检查
                missing_fields = [f for f in DataValidator.KLINE_REQUIRED_FIELDS if f not in k]
                if missing_fields:
                    raise ValueError(f"缺少必填字段: {missing_fields}")
                
                # 2. 数据类型和范围检查
                DataValidator._validate_numeric_fields(k)
                
                # 3. 逻辑一致性检查
                DataValidator._validate_logic_consistency(k)
                
                # 通过所有校验
                valid_data.append(k)
                
            except ValueError as e:
                error_msg = f"第{i}条: {str(e)}"
                errors.append(error_msg)
                
                # 只记录前 10 条错误，避免日志过多
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
        """校验数值字段"""
        # 检查必填数值字段
        for field in DataValidator.KLINE_NUMERIC_FIELDS:
            val = k.get(field)
            
            if val is None:
                continue  # 允许为 None
            
            # 类型检查
            if not isinstance(val, (int, float)):
                raise ValueError(f"{field} 不是数值类型: {type(val).__name__}")
            
            # 范围检查 - 价格相关字段不能为负数
            if field in ['open', 'high', 'low', 'close']:
                if val < 0:
                    raise ValueError(f"{field} 不能为负数: {val}")
            
            # 成交量不能为负数
            if field == 'volume':
                if val < 0:
                    raise ValueError(f"成交量不能为负数: {val}")
        
        # 检查可选数值字段
        for field in DataValidator.KLINE_OPTIONAL_FIELDS:
            val = k.get(field)
            
            if val is None:
                continue  # 可选字段允许为 None
            
            if not isinstance(val, (int, float)):
                raise ValueError(f"{field} 不是数值类型: {type(val).__name__}")
            
            # 检查非负性
            if val < 0:
                raise ValueError(f"{field} 不能为负数: {val}")
    
    @staticmethod
    def _validate_logic_consistency(k: Dict[str, Any]):
        """校验逻辑一致性"""
        high = k.get('high')
        low = k.get('low')
        open_price = k.get('open')
        close = k.get('close')
        
        if all([high, low, open_price, close]):
            # 最高价必须 >= 最低价
            if high < low:
                raise ValueError(
                    f"最高价({high})不能低于最低价({low})"
                )
            
            # 开盘价必须在高低价范围内
            if not (low <= open_price <= high):
                raise ValueError(
                    f"开盘价({open_price})不在高低价范围[{low}, {high}]内"
                )
            
            # 收盘价必须在高低价范围内
            if not (low <= close <= high):
                raise ValueError(
                    f"收盘价({close})不在高低价范围[{low}, {high}]内"
                )
    
    @staticmethod
    def validate_stock_code(code: str) -> bool:
        """
        校验股票代码格式
        
        Args:
            code: 股票代码（如 "000001", "600001"）
            
        Returns:
            是否有效
        """
        if not code or not isinstance(code, str):
            return False
        
        code = code.strip()
        
        # A股代码通常是6位数字
        if len(code) != 6:
            return False
        
        if not code.isdigit():
            return False
        
        return True
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """
        校验日期格式
        
        Args:
            date_str: 日期字符串 (YYYY-MM-DD 或 YYYYMMDD)
            
        Returns:
            是否有效
        """
        from datetime import datetime
        
        if not date_str or not isinstance(date_str, str):
            return False
        
        date_str = date_str.strip()
        
        # 尝试解析不同格式
        formats = ['%Y-%m-%d', '%Y%m%d']
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False


# 全局实例
data_validator = DataValidator()
