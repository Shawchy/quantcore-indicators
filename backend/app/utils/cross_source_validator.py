"""
跨数据源数据校验器

比对多个数据源的数据，确保数据一致性
"""
from typing import List, Dict, Any, Tuple, Optional
from app.models.unified_models import UnifiedKLine, DataSourceType, DataQualityReport
from loguru import logger
import numpy as np
from datetime import datetime


class CrossSourceValidator:
    """跨数据源数据校验器"""
    
    def __init__(self, tolerance: float = 0.01):
        """
        Args:
            tolerance: 容差率（默认 1%）
        """
        self.tolerance = tolerance
        
        # 数据源优先级（数字越小优先级越高）
        self.priority = {
            DataSourceType.EFINANCE: 1,
            DataSourceType.AKSHARE: 2,
            DataSourceType.BAOSTOCK: 3,
            DataSourceType.TICKFLOW: 4
        }
    
    def validate_multi_source(
        self,
        klines_from_sources: Dict[DataSourceType, List[UnifiedKLine]]
    ) -> Tuple[List[UnifiedKLine], DataQualityReport]:
        """
        校验多个数据源的数据一致性
        
        Args:
            klines_from_sources: {数据源：K 线列表}
        
        Returns:
            (最佳 K 线列表，数据质量报告)
        """
        if not klines_from_sources:
            report = DataQualityReport(
                date=datetime.now().strftime("%Y-%m-%d"),
                code="",
                total_sources=0,
                consistent_sources=0,
                consistency_rate=0.0,
                completeness_rate=0.0,
                has_anomalies=False,
                overall_score=0.0
            )
            return [], report
        
        # 获取第一个数据源的 code 作为参考
        first_source = next(iter(klines_from_sources.keys()))
        code = first_source  # 临时使用
        
        # 1. 按日期对齐所有数据源的数据
        aligned_data = self._align_by_date(klines_from_sources)
        
        # 2. 对每个日期的数据进行比对
        best_klines = []
        total_dates = len(aligned_data)
        consistent_dates = 0
        inconsistent_dates = 0
        anomaly_details = []
        
        for date, klines_by_source in aligned_data.items():
            if len(klines_by_source) < 2:
                # 只有一个数据源有数据
                best_kline = list(klines_by_source.values())[0]
                best_klines.append(best_kline)
                continue
            
            # 多个数据源都有数据，进行比对
            best_kline, consistency_report = self._select_best_kline(
                klines_by_source, date
            )
            best_klines.append(best_kline)
            
            if consistency_report["is_consistent"]:
                consistent_dates += 1
            else:
                inconsistent_dates += 1
                anomaly_details.append({
                    "date": date,
                    "report": consistency_report
                })
        
        # 3. 计算一致性评分
        consistency_rate = consistent_dates / max(total_dates, 1)
        overall_score = consistency_rate
        
        # 4. 生成报告
        report = DataQualityReport(
            date=datetime.now().strftime("%Y-%m-%d"),
            code=code,
            total_sources=len(klines_from_sources),
            consistent_sources=consistent_dates,
            consistency_rate=consistency_rate,
            completeness_rate=1.0,  # 简化处理
            has_anomalies=inconsistent_dates > 0,
            anomaly_details=anomaly_details,
            overall_score=overall_score,
            recommendations=self._generate_recommendations(consistency_rate, inconsistent_dates)
        )
        
        return best_klines, report
    
    def _align_by_date(
        self,
        klines_from_sources: Dict[DataSourceType, List[UnifiedKLine]]
    ) -> Dict[str, Dict[DataSourceType, UnifiedKLine]]:
        """按日期对齐数据"""
        aligned = {}
        
        for source, klines in klines_from_sources.items():
            for kline in klines:
                date = kline.date
                if date not in aligned:
                    aligned[date] = {}
                aligned[date][source] = kline
        
        return aligned
    
    def _select_best_kline(
        self,
        klines_by_source: Dict[DataSourceType, UnifiedKLine],
        date: str
    ) -> Tuple[UnifiedKLine, Dict[str, Any]]:
        """
        选择最佳的 K 线数据
        
        策略:
        1. 检查数据一致性
        2. 计算数据质量评分
        3. 选择优先级最高的数据源
        """
        # 检查一致性
        prices = {
            source: kline.close 
            for source, kline in klines_by_source.items()
        }
        
        price_values = list(prices.values())
        avg_price = np.mean(price_values)
        
        if avg_price > 0:
            max_diff = max(abs(p - avg_price) / avg_price for p in price_values)
        else:
            max_diff = 0
        
        is_consistent = max_diff <= self.tolerance
        
        # 如果不一致，标记所有数据源的质量评分
        if not is_consistent:
            for kline in klines_by_source.values():
                kline.quality_score = 0.5  # 降低质量评分
        
        # 选择优先级最高的数据源
        best_source = min(
            klines_by_source.keys(),
            key=lambda s: self.priority.get(s, 999)
        )
        
        report = {
            "date": date,
            "is_consistent": is_consistent,
            "max_difference": max_diff,
            "sources_count": len(klines_by_source),
            "best_source": best_source.value,
            "prices": {k.value: v for k, v in prices.items()}
        }
        
        return klines_by_source[best_source], report
    
    def _generate_recommendations(
        self,
        consistency_rate: float,
        inconsistent_count: int
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if consistency_rate < 0.9:
            recommendations.append("数据一致性较低，建议检查数据源质量")
        
        if inconsistent_count > 10:
            recommendations.append(f"发现{inconsistent_count}个日期数据不一致，建议人工核查")
        
        if consistency_rate >= 0.99:
            recommendations.append("数据一致性良好")
        
        return recommendations
    
    def detect_anomalies(
        self,
        klines: List[UnifiedKLine]
    ) -> List[Dict[str, Any]]:
        """
        检测异常值
        
        Args:
            klines: K 线数据列表
        
        Returns:
            异常检测报告列表
        """
        anomalies = []
        
        for i, kline in enumerate(klines):
            # 检查价格合理性
            if kline.high < kline.low:
                anomalies.append({
                    "date": kline.date,
                    "type": "price_inversion",
                    "description": "最高价低于最低价",
                    "severity": "high"
                })
            
            # 检查涨跌幅是否异常（超过 20%）
            if kline.pre_close and kline.pre_close > 0:
                change_pct = (kline.close - kline.pre_close) / kline.pre_close
                if abs(change_pct) > 0.2:
                    anomalies.append({
                        "date": kline.date,
                        "type": "extreme_change",
                        "description": f"涨跌幅异常：{change_pct*100:.2f}%",
                        "severity": "medium"
                    })
            
            # 检查成交量是否异常
            if i > 0:
                avg_volume = np.mean([k.volume for k in klines[max(0, i-5):i+1]])
                if avg_volume > 0 and kline.volume > avg_volume * 10:
                    anomalies.append({
                        "date": kline.date,
                        "type": "volume_spike",
                        "description": f"成交量异常放大：{kline.volume/avg_volume:.1f}倍",
                        "severity": "medium"
                    })
        
        return anomalies
