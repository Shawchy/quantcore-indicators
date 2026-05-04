"""
增量更新服务 (Incremental Update Service)

核心功能：
- 只传输变化的数据字段，减少带宽消耗
- 智能阈值检测（数值型字段变化超过阈值才更新）
- 变更日志记录（用于调试和审计）
- 前端友好的delta格式输出

使用场景：
- 实时行情推送（只传输价格变动）
- 深度数据更新（只刷新变化的财务指标）
- 节省网络带宽60-80%
"""

import json
import copy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


@dataclass
class FieldThreshold:
    """字段变化阈值配置"""
    field_name: str
    threshold: float
    unit: str = ""
    description: str = ""


@dataclass
class DeltaRecord:
    """变更记录"""
    timestamp: str
    code: str
    changed_fields: List[str]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    change_magnitude: Dict[str, float]


class IncrementalUpdateService:
    """
    增量更新服务
    
    对比新旧数据，只返回发生变化的字段，
    大幅减少数据传输量和前端渲染开销。
    
    使用示例：
        >>> updater = IncrementalUpdateService()
        >>> old_data = {"000001": {"price": 12.50, "volume": 1000000}}
        >>> new_data = {"000001": {"price": 12.55, "volume": 1050000}}
        >>> delta = updater.compute_delta(old_data, new_data)
        >>> # delta = {"changed_fields": ["price", "volume"], ...}
    """
    
    DEFAULT_THRESHOLDS = {
        "price": FieldThreshold("price", 0.01, "元", "价格变化>1分钱"),
        "change_pct": FieldThreshold("change_pct", 0.05, "%", "涨跌幅>0.05%"),
        "change_amount": FieldThreshold("change_amount", 0.01, "元", "涨跌额>1分钱"),
        "volume": FieldThreshold("volume", 100, "手", "成交量>100手"),
        "amount": FieldThreshold("amount", 10000, "元", "成交额>1万元"),
        "turnover_rate": FieldThreshold("turnover_rate", 0.01, "%", "换手率>0.01%"),
        "high": FieldThreshold("high", 0.01, "元", "最高价>1分钱"),
        "low": FieldThreshold("low", 0.01, "元", "最低价>1分钱"),
        "open": FieldThreshold("open", 0.01, "元", "开盘价>1分钱"),
        "prev_close": FieldThreshold("prev_close", 0.00, "元", "昨收价（任何变化）"),
        "pe_ratio": FieldThreshold("pe_ratio", 0.1, "", "市盈率>0.1"),
        "pb_ratio": FieldThreshold("pb_ratio", 0.01, "", "市净率>0.01"),
        "total_market_cap": FieldThreshold("total_market_cap", 1000000, "元", "总市值>100万"),
        "float_market_cap": FieldThreshold("float_market_cap", 1000000, "元", "流通市值>100万"),
        "speed": FieldThreshold("speed", 0.1, "", "涨速>0.1%"),
        "amplitude": FieldThreshold("amplitude", 0.05, "%", "振幅>0.05%"),
        "volume_ratio": FieldThreshold("volume_ratio", 0.1, "", "量比>0.1"),
    }
    
    STRING_FIELDS = {
        "name", "code", "date", "time", "timestamp",
        "market_type", "industry", "sector"
    }
    
    def __init__(self):
        self._last_snapshot: Dict[str, Dict] = {}
        self._change_history: List[DeltaRecord] = []
        self._custom_thresholds: Dict[str, FieldThreshold] = {}
        
        logger.info("IncrementalUpdateService 初始化完成")
    
    def set_custom_threshold(
        self,
        field_name: str,
        threshold: float,
        unit: str = "",
        description: str = ""
    ):
        """
        设置自定义阈值
        
        Args:
            field_name: 字段名
            threshold: 阈值
            unit: 单位
            description: 描述
        """
        self._custom_thresholds[field_name] = FieldThreshold(
            field_name=field_name,
            threshold=threshold,
            unit=unit,
            description=description
        )
    
    def compute_delta(
        self,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """
        计算数据增量（核心方法）
        
        对比新旧数据，识别出变化的字段和对应的值。
        
        Args:
            old_data: 旧数据 {code: {field: value}}
            new_data: 新数据 {code: {field: value}}
            strict_mode: 严格模式（True=所有变化都记录，False=超过阈值才记录）
            
        Returns:
            Dict: {
                "timestamp": "ISO时间戳",
                "total_changes": int,
                "changed_codes": [list],
                "changed_fields": [list],
                "delta": {
                    "code": {
                        "field": {"old": val, "new": val},
                        ...
                    }
                },
                "summary": {
                    "price_up": [codes],
                    "price_down": [codes],
                    "volume_surge": [codes],
                    "significant_changes": [codes]
                }
            }
        """
        now = datetime.now().isoformat()
        
        delta_result = {
            "timestamp": now,
            "total_changes": 0,
            "changed_codes": [],
            "changed_fields": set(),
            "delta": {},
            "summary": {
                "price_up": [],
                "price_down": [],
                "volume_surge": [],
                "significant_changes": []
            }
        }
        
        all_codes = set(list(old_data.keys()) + list(new_data.keys()))
        
        for code in all_codes:
            old_record = old_data.get(code, {})
            new_record = new_data.get(code, {})
            
            if not old_record:
                delta_result["delta"][code] = {
                    "_action": "added",
                    **new_record
                }
                delta_result["changed_codes"].append(code)
                delta_result["total_changes"] += len(new_record)
                continue
            
            if not new_record:
                delta_result["delta"][code] = {
                    "_action": "removed"
                }
                delta_result["changed_codes"].append(code)
                continue
            
            code_delta = {}
            change_magnitude = {}
            
            all_fields = set(list(old_record.keys()) + list(new_record.keys()))
            
            for field_name in all_fields:
                old_val = old_record.get(field_name)
                new_val = new_record.get(field_name)
                
                is_changed = self._is_field_changed(
                    field_name, old_val, new_val, strict_mode
                )
                
                if is_changed:
                    code_delta[field_name] = {
                        "old": old_val,
                        "new": new_val
                    }
                    
                    delta_result["changed_fields"].add(field_name)
                    
                    if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
                        if old_val != 0:
                            magnitude = abs((new_val - old_val) / old_val * 100)
                        else:
                            magnitude = 100.0 if new_val != 0 else 0.0
                        change_magnitude[field_name] = round(magnitude, 2)
                    
                    self._classify_change(
                        field_name, old_val, new_val, 
                        code, delta_result["summary"]
                    )
            
            if code_delta:
                delta_result["delta"][code] = code_delta
                delta_result["changed_codes"].append(code)
                delta_result["total_changes"] += len(code_delta)
                
                record = DeltaRecord(
                    timestamp=now,
                    code=code,
                    changed_fields=list(code_delta.keys()),
                    old_values={k: v["old"] for k, v in code_delta.items()},
                    new_values={k: v["new"] for k, v in code_delta.items()},
                    change_magnitude=change_magnitude
                )
                self._change_history.append(record)
        
        delta_result["changed_fields"] = list(delta_result["changed_fields"])
        
        self._last_snapshot = copy.deepcopy(new_data)
        
        self._trim_history(max_records=500)
        
        return delta_result
    
    def _is_field_changed(
        self,
        field_name: str,
        old_val: Any,
        new_val: Any,
        strict_mode: bool
    ) -> bool:
        """
        判断字段是否发生变化
        
        Args:
            field_name: 字段名
            old_val: 旧值
            new_val: 新值
            strict_mode: 是否严格模式
            
        Returns:
            bool: 是否变化
        """
        if field_name in self.STRING_FIELDS:
            return str(old_val).strip() != str(new_val).strip()
        
        thresholds = {**self.DEFAULT_THRESHOLDS, **self._custom_thresholds}
        
        if field_name in thresholds:
            threshold_config = thresholds[field_name]
            
            try:
                old_num = float(old_val) if old_val is not None else 0.0
                new_num = float(new_val) if new_val is not None else 0.0
                
                diff = abs(new_num - old_num)
                
                if strict_mode:
                    return diff > 0
                else:
                    return diff > threshold_config.threshold
                    
            except (ValueError, TypeError):
                return str(old_val) != str(new_val)
        
        if strict_mode:
            return old_val != new_val
        
        if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
            try:
                old_num = float(old_val) if old_val else 0.0
                new_num = float(new_val) if new_val else 0.0
                
                if old_num == 0:
                    return new_num != 0
                
                percent_change = abs((new_num - old_num) / old_num)
                return percent_change > 0.001
                
            except (ValueError, TypeError):
                pass
        
        return old_val != new_val
    
    def _classify_change(
        self,
        field_name: str,
        old_val: Any,
        new_val: Any,
        code: str,
        summary: Dict[str, List]
    ):
        """分类变更类型"""
        if field_name == "price":
            try:
                old_price = float(old_val) if old_val else 0
                new_price = float(new_val) if new_val else 0
                
                if new_price > old_price:
                    summary["price_up"].append(code)
                elif new_price < old_price:
                    summary["price_down"].append(code)
                    
            except (ValueError, TypeError):
                pass
        
        elif field_name == "volume":
            try:
                old_vol = float(old_val) if old_val else 0
                new_vol = float(new_val) if new_val else 0
                
                if old_vol > 0:
                    growth = (new_vol - old_vol) / old_vol
                    if growth > 0.5:
                        summary["volume_surge"].append(code)
                        
            except (ValueError, TypeError):
                pass
        
        if field_name in ("price", "change_pct"):
            try:
                change = abs(float(new_val) - float(old_val)) if (old_val and new_val) else 0
                if change > 1.0 or (field_name == "change_pct" and change > 2.0):
                    if code not in summary["significant_changes"]:
                        summary["significant_changes"].append(code)
                        
            except (ValueError, TypeError):
                pass
    
    def apply_delta_to_frontend_state(
        self,
        current_state: Dict[str, Any],
        delta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将增量应用到前端状态（辅助方法）
        
        前端调用此方法来更新本地状态，
        只修改变化的字段，避免全量替换。
        
        Args:
            current_state: 当前前端状态
            delta: 增量数据（compute_delta的返回值）
            
        Returns:
            Dict: 更新后的完整状态
        """
        updated_state = dict(current_state)
        
        for code, changes in delta.get("delta", {}).items():
            if "_action" in changes:
                if changes["_action"] == "added":
                    updated_state[code] = {
                        k: v for k, v in changes.items() 
                        if not k.startswith("_")
                    }
                elif changes["_action"] == "removed":
                    if code in updated_state:
                        del updated_state[code]
                continue
            
            if code not in updated_state:
                updated_state[code] = {}
            
            for field_name, values in changes.items():
                if "new" in values:
                    updated_state[code][field_name] = values["new"]
        
        return updated_state
    
    def get_change_history(
        self,
        code: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取变更历史
        
        Args:
            code: 股票代码（可选，不传则返回全部）
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 变更记录列表
        """
        if code:
            history = [
                record.__dict__ for record in self._change_history
                if record.code == code
            ]
        else:
            history = [record.__dict__ for record in self._change_history]
        
        return history[-limit:]
    
    def _trim_history(self, max_records: int = 500):
        """裁剪历史记录"""
        if len(self._change_history) > max_records:
            self._change_history = self._change_history[-max_records//2:]
    
    def get_last_snapshot(self) -> Dict[str, Dict]:
        """
        获取最后一次快照数据
        
        Returns:
            Dict[str, Dict]: 上次保存的快照数据
        """
        return dict(self._last_snapshot)
    
    def export_delta_for_frontend(self, delta: Dict[str, Any]) -> str:
        """
        导出前端友好的JSON格式
        
        将delta转换为紧凑格式，减少传输大小。
        
        Args:
            delta: 增量数据
            
        Returns:
            str: JSON字符串
        """
        compact = {
            "t": delta["timestamp"],
            "c": delta["total_changes"],
            "d": {}
        }
        
        for code, changes in delta.get("delta", {}).items():
            if "_action" in changes:
                compact["d"][code] = {"_a": changes["_action"]}
                if changes["_action"] == "added":
                    compact["d"][code].update({
                        k: v for k, v in changes.items() 
                        if not k.startswith("_")
                    })
                continue
            
            compact_d = {}
            for field, values in changes.items():
                if "new" in values:
                    compact_d[field] = values["new"]
            
            if compact_d:
                compact["d"][code] = compact_d
        
        return json.dumps(compact, ensure_ascii=False, separators=(',', ':'))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计"""
        recent_changes = [
            r for r in self._change_history
            if (datetime.now() - datetime.fromisoformat(r.timestamp)).total_seconds() < 3600
        ]
        
        total_fields_changed = sum(len(r.changed_fields) for r in recent_changes)
        unique_codes = len(set(r.code for r in recent_changes))
        
        return {
            "snapshot_size": len(self._last_snapshot),
            "history_records": len(self._change_history),
            "changes_last_hour": len(recent_changes),
            "fields_updated_last_hour": total_fields_changed,
            "unique_codes_touched": unique_codes,
            "avg_changes_per_code": (
                f"{total_fields_changed/unique_codes:.1f}"
                if unique_codes > 0 else "N/A"
            ),
            "custom_thresholds": len(self._custom_thresholds)
        }


# 全局单例
incremental_updater = IncrementalUpdateService()


async def demo():
    """演示用法"""
    print("=" * 70)
    print("📊 IncrementalUpdateService 增量更新演示")
    print("=" * 70)
    
    updater = IncrementalUpdateService()
    
    old_data = {
        "000001": {
            "name": "平安银行",
            "price": 12.50,
            "change_pct": 1.20,
            "volume": 1000000,
            "amount": 12500000,
            "turnover_rate": 0.85,
            "high": 12.68,
            "low": 12.35,
            "open": 12.40,
            "prev_close": 12.35
        },
        "600000": {
            "name": "浦发银行",
            "price": 8.90,
            "change_pct": -0.55,
            "volume": 800000,
            "amount": 7120000,
            "turnover_rate": 0.45,
            "high": 8.95,
            "low": 8.82,
            "open": 8.93,
            "prev_close": 8.95
        }
    }
    
    new_data = {
        "000001": {
            "name": "平安银行",
            "price": 12.55,      # +0.05 (变化)
            "change_pct": 1.60,   # +0.40 (变化)
            "volume": 1050000,    # +50000 (变化)
            "amount": 13177500,   # 变化
            "turnover_rate": 0.89, # +0.04 (变化)
            "high": 12.68,        # 无变化
            "low": 12.35,         # 无变化
            "open": 12.40,        # 无变化
            "prev_close": 12.35   # 无变化
        },
        "600000": {
            "name": "浦发银行",
            "price": 8.90,         # 无变化
            "change_pct": -0.55,   # 无变化
            "volume": 800000,      # 无变化
            "amount": 7120000,     # 无变化
            "turnover_rate": 0.45, # 无变化
            "high": 8.95,
            "low": 8.82,
            "open": 8.93,
            "prev_close": 8.95
        },
        "300001": {
            "name": "特锐德",
            "price": 25.80,
            "change_pct": 2.35,
            "volume": 500000,
            "amount": 12900000,
            "turnover_rate": 1.23,
            "high": 26.10,
            "low": 25.20,
            "open": 25.50,
            "prev_close": 25.21
        }
    }
    
    print("\n📥 计算增量...")
    delta = updater.compute_delta(old_data, new_data)
    
    print(f"\n✅ 增量计算结果:")
    print(f"   时间戳: {delta['timestamp']}")
    print(f"   总变更数: {delta['total_changes']}")
    print(f"   变更股票: {delta['changed_codes']}")
    print(f"   变更字段: {delta['changed_fields']}")
    
    print(f"\n📝 详细Delta:")
    for code, changes in delta['delta'].items():
        print(f"\n   📌 {code}:")
        for field, values in changes.items():
            if isinstance(values, dict) and 'old' in values:
                print(f"      {field}: {values['old']} → {values['new']}")
    
    print(f"\n📈 变更摘要:")
    summary = delta['summary']
    print(f"   🔴 上涨股票: {summary['price_up']}")
    print(f"   🟢 下跌股票: {summary['price_down']}")
    print(f"   📊 放量股票: {summary['volume_surge']}")
    print(f"   ⚡ 显著变化: {summary['significant_changes']}")
    
    print("\n💾 应用增量到前端状态...")
    frontend_state = {"000001": old_data["000001"]}
    updated_state = updater.apply_delta_to_frontend_state(frontend_state, delta)
    print(f"   更新后 000001 价格: {updated_state['000001']['price']}")
    
    print("\n📤 前端友好格式 (JSON大小对比):")
    full_json = json.dumps(new_data, ensure_ascii=True)
    compact_json = updater.export_delta_for_frontend(delta)
    print(f"   完整数据: {len(full_json)} 字节")
    print(f"   增量数据: {len(compact_json)} 字节")
    print(f"   压缩比: {len(compact_json)/len(full_json)*100:.1f}%")
    
    stats = updater.get_statistics()
    print(f"\n📊 服务统计:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
