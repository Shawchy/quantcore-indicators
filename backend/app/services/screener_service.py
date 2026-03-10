from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from loguru import logger


class ConditionType(Enum):
    PRICE = "price"
    VOLUME = "volume"
    CHANGE_PCT = "change_pct"
    PE = "pe"
    PB = "pb"
    MARKET_CAP = "market_cap"
    TURNOVER = "turnover"
    RSI = "rsi"
    MACD = "macd"
    MA_CROSS = "ma_cross"
    BOLLINGER = "bollinger"
    CONTROL_DEGREE = "control_degree"
    SHAREHOLDER_COUNT = "shareholder_count"
    INDUSTRY = "industry"
    MARKET = "market"


class CompareOperator(Enum):
    GT = ">"  # greater than
    LT = "<"  # less than
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NEQ = "!="


@dataclass
class FilterCondition:
    field: str
    operator: str
    value: Any
    
    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }


class Screener:
    def __init__(self):
        self.conditions: List[FilterCondition] = []
    
    def add_condition(
        self,
        field: str,
        operator: str,
        value: Any
    ) -> 'Screener':
        self.conditions.append(FilterCondition(field, operator, value))
        return self
    
    def price_gt(self, value: float) -> 'Screener':
        return self.add_condition("price", ">", value)
    
    def price_lt(self, value: float) -> 'Screener':
        return self.add_condition("price", "<", value)
    
    def change_pct_gt(self, value: float) -> 'Screener':
        return self.add_condition("change_pct", ">", value)
    
    def change_pct_lt(self, value: float) -> 'Screener':
        return self.add_condition("change_pct", "<", value)
    
    def pe_lt(self, value: float) -> 'Screener':
        return self.add_condition("pe", "<", value)
    
    def pe_gt(self, value: float) -> 'Screener':
        return self.add_condition("pe", ">", value)
    
    def market_cap_lt(self, value: float) -> 'Screener':
        return self.add_condition("market_cap", "<", value)
    
    def market_cap_gt(self, value: float) -> 'Screener':
        return self.add_condition("market_cap", ">", value)
    
    def turnover_rate_gt(self, value: float) -> 'Screener':
        return self.add_condition("turnover_rate", ">", value)
    
    def volume_gt(self, value: float) -> 'Screener':
        return self.add_condition("volume", ">", value)
    
    def rsi_oversold(self) -> 'Screener':
        return self.add_condition("rsi", "<", 30)
    
    def rsi_overbought(self) -> 'Screener':
        return self.add_condition("rsi", ">", 70)
    
    def control_degree_gt(self, value: float) -> 'Screener':
        return self.add_condition("control_degree", ">", value)
    
    def industry(self, industry: str) -> 'Screener':
        return self.add_condition("industry", "==", industry)
    
    def build_from_dict(conditions: Dict[str, Any]) -> 'Screener':
        screener = Screener()
        
        mapping = {
            "price_min": ("price", ">="),
            "price_max": ("price", "<="),
            "volume_min": ("volume", ">="),
            "volume_max": ("volume", "<="),
            "change_pct_min": ("change_pct", ">="),
            "change_pct_max": ("change_pct", "<="),
            "pe_min": ("pe", ">="),
            "pe_max": ("pe", "<="),
            "pb_min": ("pb", ">="),
            "pb_max": ("pb", "<="),
            "market_cap_min": ("market_cap", ">="),
            "market_cap_max": ("market_cap", "<="),
            "turnover_rate_min": ("turnover_rate", ">="),
            "turnover_rate_max": ("turnover_rate", "<="),
            "control_degree_min": ("control_degree", ">="),
            "control_degree_max": ("control_degree", "<="),
            "rsi_min": ("rsi", ">="),
            "rsi_max": ("rsi", "<="),
            "industry": ("industry", "=="),
            "market": ("market", "=="),
        }
        
        for key, (field, op) in mapping.items():
            if key in conditions and conditions[key] is not None:
                screener.add_condition(field, op, conditions[key])
        
        return screener
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conditions": [c.to_dict() for c in self.conditions]
        }
    
    def get_filter_fields(self) -> List[str]:
        return list(set(c.field for c in self.conditions))
    
    def needs_indicator(self) -> bool:
        indicator_fields = {"rsi", "macd", "ma_cross", "bollinger"}
        return bool(set(self.get_filter_fields()) & indicator_fields)
    
    def needs_chip(self) -> bool:
        chip_fields = {"control_degree", "shareholder_count"}
        return bool(set(self.get_filter_fields()) & chip_fields)


class StockScreener:
    def __init__(self):
        self.screener = Screener()
    
    def filter_stocks(
        self,
        stocks: List[Dict[str, Any]],
        quotes: Optional[Dict[str, Dict[str, Any]]] = None,
        indicators: Optional[Dict[str, Dict[str, Any]]] = None,
        chip_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        if not self.screener.conditions:
            return stocks
        
        results = []
        
        for stock in stocks:
            code = stock.get("code")
            
            stock_data = {"code": code}
            
            if quotes and code in quotes:
                stock_data.update(quotes[code])
            
            if indicators and code in indicators:
                stock_data.update(indicators[code])
            
            if chip_data and code in chip_data:
                stock_data.update(chip_data[code])
            
            if self._match_conditions(stock_data):
                results.append(stock)
        
        return results
    
    def _match_conditions(self, stock_data: Dict[str, Any]) -> bool:
        for condition in self.screener.conditions:
            field = condition.field
            operator = condition.operator
            expected_value = condition.value
            
            if field not in stock_data:
                return False
            
            actual_value = stock_data[field]
            
            if actual_value is None:
                return False
            
            try:
                if operator == ">":
                    if not (float(actual_value) > float(expected_value)):
                        return False
                elif operator == "<":
                    if not (float(actual_value) < float(expected_value)):
                        return False
                elif operator == ">=":
                    if not (float(actual_value) >= float(expected_value)):
                        return False
                elif operator == "<=":
                    if not (float(actual_value) <= float(expected_value)):
                        return False
                elif operator == "==":
                    if str(actual_value) != str(expected_value):
                        return False
                elif operator == "!=":
                    if str(actual_value) == str(expected_value):
                        return False
            except (ValueError, TypeError):
                return False
        
        return True
    
    def sort_results(
        self,
        stocks: List[Dict[str, Any]],
        sort_by: str = "change_pct",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        if not sort_by:
            return stocks
        
        return sorted(
            stocks,
            key=lambda x: x.get(sort_by, 0) or 0,
            reverse=not ascending
        )


screener = StockScreener()
