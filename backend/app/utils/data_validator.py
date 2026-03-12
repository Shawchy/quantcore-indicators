"""
数据完整性验证工具
用于验证从数据源拉取的数据质量
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
from loguru import logger

from app.adapters.base import KLineData, StockBasicInfo


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_kline(klines: List[KLineData], code: str) -> Tuple[bool, List[str]]:
        """
        验证 K 线数据完整性
        :param klines: K 线数据列表
        :param code: 股票代码
        :return: (是否有效，错误列表)
        """
        errors = []
        
        if not klines:
            errors.append(f"股票 {code} 的 K 线数据为空")
            return False, errors
        
        # 检查基本字段
        required_fields = ['open', 'high', 'low', 'close', 'volume']
        for i, kline in enumerate(klines):
            for field in required_fields:
                value = getattr(kline, field, None)
                if value is None:
                    errors.append(f"第{i}条数据缺少字段：{field}")
                elif value < 0:
                    errors.append(f"第{i}条数据 {field} 为负数：{value}")
        
        # 检查价格逻辑：high >= low
        for i, kline in enumerate(klines):
            if kline.high < kline.low:
                errors.append(f"第{i}条数据最高价 {kline.high} < 最低价 {kline.low}")
            
            # 检查收盘价是否在最高最低价之间
            if not (kline.low <= kline.close <= kline.high):
                errors.append(f"第{i}条数据收盘价 {kline.close} 不在 [{kline.low}, {kline.high}] 范围内")
            
            # 检查开盘价是否在最高最低价之间
            if not (kline.low <= kline.open <= kline.high):
                errors.append(f"第{i}条数据开盘价 {kline.open} 不在 [{kline.low}, {kline.high}] 范围内")
        
        # 检查日期连续性（可选，因为可能有停牌）
        dates = [kline.date for kline in klines]
        if len(dates) != len(set(dates)):
            errors.append(f"存在重复日期")
        
        # 检查数据量
        if len(klines) < 10:
            errors.append(f"数据量过少：{len(klines)}条")
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.debug(f"股票 {code} 的 K 线数据验证通过，共{len(klines)}条")
        else:
            logger.warning(f"股票 {code} 的 K 线数据验证失败：{errors}")
        
        return is_valid, errors
    
    @staticmethod
    def validate_stock_info(stock: Optional[StockBasicInfo]) -> Tuple[bool, List[str]]:
        """
        验证股票基本信息
        :param stock: 股票信息
        :return: (是否有效，错误列表)
        """
        errors = []
        
        if not stock:
            return False, ["股票信息为空"]
        
        if not stock.code:
            errors.append("股票代码为空")
        
        if not stock.name:
            errors.append("股票名称为空")
        
        if stock.code and len(stock.code) != 6:
            errors.append(f"股票代码长度错误：{stock.code}")
        
        if stock.total_shares is not None and stock.total_shares < 0:
            errors.append(f"总股本为负数：{stock.total_shares}")
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.debug(f"股票 {stock.code} 信息验证通过")
        else:
            logger.warning(f"股票 {stock.code} 信息验证失败：{errors}")
        
        return is_valid, errors
    
    @staticmethod
    def validate_realtime_quote(quote: Dict[str, Any], code: str) -> Tuple[bool, List[str]]:
        """
        验证实时行情数据
        :param quote: 行情数据
        :param code: 股票代码
        :return: (是否有效，错误列表)
        """
        errors = []
        
        if not quote:
            return False, ["行情数据为空"]
        
        # 检查价格字段
        price_fields = ['price', 'high', 'low', 'open', 'prev_close']
        for field in price_fields:
            if field in quote and quote[field] is not None:
                if quote[field] < 0:
                    errors.append(f"{field} 为负数：{quote[field]}")
        
        # 检查涨跌幅逻辑
        if 'change_pct' in quote and quote['change_pct'] is not None:
            if abs(quote['change_pct']) > 100:
                errors.append(f"涨跌幅异常：{quote['change_pct']}%")
        
        # 检查成交量
        if 'volume' in quote and quote['volume'] is not None:
            if quote['volume'] < 0:
                errors.append(f"成交量为负数：{quote['volume']}")
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.debug(f"股票 {code} 行情数据验证通过")
        else:
            logger.warning(f"股票 {code} 行情数据验证失败：{errors}")
        
        return is_valid, errors
    
    @staticmethod
    def check_data_quality(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
        """
        检查 DataFrame 数据质量
        :param df: 数据框
        :param required_columns: 必需的列名
        :return: 质量报告
        """
        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_columns': [],
            'null_counts': {},
            'duplicate_rows': 0,
            'quality_score': 100.0
        }
        
        # 检查缺失列
        for col in required_columns:
            if col not in df.columns:
                report['missing_columns'].append(col)
        
        # 计算每列空值数量
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                report['null_counts'][col] = int(null_count)
        
        # 检查重复行
        report['duplicate_rows'] = int(df.duplicated().sum())
        
        # 计算质量分数
        if report['total_rows'] > 0:
            penalty = 0
            # 缺失列惩罚
            penalty += len(report['missing_columns']) * 10
            # 空值惩罚
            for col, count in report['null_counts'].items():
                penalty += (count / report['total_rows']) * 100 * 0.1
            # 重复行惩罚
            penalty += (report['duplicate_rows'] / report['total_rows']) * 100 * 0.1
            
            report['quality_score'] = max(0, 100 - penalty)
        
        return report
    
    @staticmethod
    def validate_date_range(
        start_date: str,
        end_date: str,
        max_days: int = 365 * 3
    ) -> Tuple[bool, str]:
        """
        验证日期范围是否合理
        :param start_date: 开始日期 (YYYY-MM-DD)
        :param end_date: 结束日期 (YYYY-MM-DD)
        :param max_days: 最大天数（默认 3 年）
        :return: (是否有效，错误信息)
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start > end:
                return False, "开始日期不能晚于结束日期"
            
            days = (end - start).days
            if days > max_days:
                return False, f"日期范围过大：{days}天（最大允许{max_days}天）"
            
            return True, ""
        except ValueError as e:
            return False, f"日期格式错误：{e}"


# 全局验证器实例
validator = DataValidator()
