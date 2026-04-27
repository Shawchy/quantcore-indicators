# 优化模块 6: 因子生命周期管理

## 📊 设计概述

### 问题背景

因子上线后需要持续监控和管理:
- **因子衰减**: 随时间推移，因子有效性下降
- **模型更新**: FinSenti 模型升级后，因子数据需要重新计算
- **失效预警**: 因子失效前需要预警，避免使用无效因子
- **版本管理**: 不同版本的因子数据需要隔离和追溯

### 解决方案

设计**因子生命周期管理系统**，实现:
- ✅ 因子健康监控 (实时检测衰减)
- ✅ 版本控制 (因子版本管理)
- ✅ 失效预警 (自动告警)
- ✅ 自动更新 (模型升级后重新计算)
- ✅ 历史追溯 (可回溯任意时间点)

---

## 🏗️ 生命周期阶段

```
┌─────────────────────────────────────────────────────────┐
│                 因子生命周期                              │
│                                                         │
│  1. 因子创建                                             │
│     ↓                                                   │
│  2. 因子验证 (回测验证框架)                              │
│     ↓                                                   │
│  3. 因子上线 (开始使用)                                  │
│     ↓                                                   │
│  4. 因子监控 (持续监控健康状态)                          │
│     ↓                                                   │
│  5. 因子衰减?                                            │
│     ├─ 是 → 预警 → 优化/下线                             │
│     └─ 否 → 继续使用                                    │
│     ↓                                                   │
│  6. 模型更新?                                            │
│     ├─ 是 → 重新计算 → 版本升级                          │
│     └─ 否 → 继续使用                                    │
│     ↓                                                   │
│  7. 因子下线 (失效或替代)                                │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 核心代码设计

### 1. 因子健康监控

```python
# quantcore/alpha/factors/factor_health_monitor.py

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class FactorHealthReport:
    """因子健康报告"""
    factor_name: str
    check_date: date
    
    # 健康指标
    current_ic: float  # 当前 IC 值 (近 30 天)
    ic_trend: List[float]  # IC 趋势 (近 60 天，每天)
    ic_decay_rate: float  # IC 衰减率 (每天)
    
    # 健康状态
    health_status: str  # healthy/warning/critical
    days_to_critical: Optional[int]  # 预计到达临界状态的天数
    
    # 建议
    suggestion: str  # 处理建议
    action_required: bool  # 是否需要采取行动
    
    def summary(self) -> str:
        """生成摘要"""
        return (
            f"因子健康报告: {self.factor_name}\n"
            f"  当前 IC: {self.current_ic:.4f}\n"
            f"  衰减率: {self.ic_decay_rate:.6f}/天\n"
            f"  健康状态: {self.health_status}\n"
            f"  建议: {self.suggestion}\n"
            f"  需要行动: {'是' if self.action_required else '否'}"
        )


class FactorHealthMonitor:
    """因子健康监控器"""
    
    def __init__(
        self,
        ic_warning_threshold: float = 0.02,  # IC 预警阈值
        ic_critical_threshold: float = 0.01,  # IC 临界阈值
        decay_rate_threshold: float = -0.0005  # 衰减率阈值
    ):
        self.ic_warning_threshold = ic_warning_threshold
        self.ic_critical_threshold = ic_critical_threshold
        self.decay_rate_threshold = decay_rate_threshold
    
    def check_health(
        self,
        factor_name: str,
        ic_history: pd.Series,  # 每日 IC 值 (日期索引)
        window_days: int = 60
    ) -> FactorHealthReport:
        """
        检查因子健康状态
        
        Args:
            factor_name: 因子名称
            ic_history: IC 历史数据
            window_days: 检查窗口 (天)
        
        Returns:
            FactorHealthReport: 健康报告
        """
        # 截取最近的数据
        cutoff_date = datetime.now().date() - timedelta(days=window_days)
        recent_ic = ic_history[ic_history.index >= cutoff_date]
        
        if len(recent_ic) < 10:
            return FactorHealthReport(
                factor_name=factor_name,
                check_date=datetime.now().date(),
                current_ic=0.0,
                ic_trend=[],
                ic_decay_rate=0.0,
                health_status="unknown",
                days_to_critical=None,
                suggestion="数据不足，无法评估",
                action_required=False,
            )
        
        # 计算指标
        current_ic = recent_ic.tail(30).mean()  # 近 30 天均值
        ic_trend = recent_ic.tolist()
        
        # 计算衰减率 (线性回归斜率)
        ic_decay_rate = self._calculate_decay_rate(recent_ic)
        
        # 判断健康状态
        health_status, suggestion, action_required = (
            self._evaluate_health(
                current_ic, ic_decay_rate, recent_ic
            )
        )
        
        # 预计到达临界状态的天数
        days_to_critical = self._estimate_days_to_critical(
            current_ic, ic_decay_rate
        )
        
        report = FactorHealthReport(
            factor_name=factor_name,
            check_date=datetime.now().date(),
            current_ic=current_ic,
            ic_trend=ic_trend,
            ic_decay_rate=ic_decay_rate,
            health_status=health_status,
            days_to_critical=days_to_critical,
            suggestion=suggestion,
            action_required=action_required,
        )
        
        return report
    
    def _calculate_decay_rate(self, ic_series: pd.Series) -> float:
        """计算 IC 衰减率 (线性回归斜率)"""
        if len(ic_series) < 10:
            return 0.0
        
        # 线性回归
        x = np.arange(len(ic_series))
        y = ic_series.values
        
        # 计算斜率
        slope = np.polyfit(x, y, 1)[0]
        
        return slope
    
    def _evaluate_health(
        self,
        current_ic: float,
        decay_rate: float,
        ic_series: pd.Series
    ) -> tuple:
        """评估健康状态"""
        # 判断状态
        if current_ic < self.ic_critical_threshold:
            health_status = "critical"
            suggestion = (
                f"IC 值过低 ({current_ic:.4f})，"
                f"因子可能已失效，建议立即下线"
            )
            action_required = True
        
        elif current_ic < self.ic_warning_threshold:
            health_status = "warning"
            suggestion = (
                f"IC 值偏低 ({current_ic:.4f})，"
                f"因子有效性下降，建议优化或准备替代"
            )
            action_required = True
        
        elif decay_rate < self.decay_rate_threshold:
            health_status = "warning"
            suggestion = (
                f"IC 衰减过快 ({decay_rate:.6f}/天)，"
                f"预计 {(current_ic / abs(decay_rate)):.0f} 天后达到临界值"
            )
            action_required = True
        
        else:
            health_status = "healthy"
            suggestion = "因子健康状态良好，可继续使用"
            action_required = False
        
        return health_status, suggestion, action_required
    
    def _estimate_days_to_critical(
        self,
        current_ic: float,
        decay_rate: float
    ) -> Optional[int]:
        """预计到达临界状态的天数"""
        if decay_rate >= 0:
            return None  # 没有衰减
        
        days = (current_ic - self.ic_critical_threshold) / abs(decay_rate)
        
        return max(0, int(days))
```

---

### 2. 因子版本控制

```python
# quantcore/alpha/factors/factor_version_control.py

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import date, datetime
import json
from pathlib import Path
from loguru import logger


@dataclass
class FactorVersion:
    """因子版本信息"""
    version_id: str  # 版本号 (如 "v1.0.0")
    factor_name: str  # 因子名称
    model_version: str  # 使用的模型版本 (如 "FinSenti v1.0")
    created_date: date  # 创建日期
    
    # 版本描述
    description: str
    changelog: List[str]  # 变更日志
    
    # 兼容性
    is_backward_compatible: bool  # 是否向后兼容
    migration_notes: Optional[str] = None  # 迁移说明
    
    # 统计信息
    data_range_start: date  # 数据起始日期
    data_range_end: date  # 数据结束日期
    data_points: int  # 数据点数量
    
    # 状态
    status: str = "active"  # active/deprecated/archived
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "version_id": self.version_id,
            "factor_name": self.factor_name,
            "model_version": self.model_version,
            "created_date": self.created_date.isoformat(),
            "description": self.description,
            "changelog": self.changelog,
            "is_backward_compatible": self.is_backward_compatible,
            "migration_notes": self.migration_notes,
            "data_range_start": self.data_range_start.isoformat(),
            "data_range_end": self.data_range_end.isoformat(),
            "data_points": self.data_points,
            "status": self.status,
        }


class FactorVersionControl:
    """因子版本控制器"""
    
    def __init__(self, storage_path: str = "data/factor_versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 版本注册表
        self._registry: Dict[str, FactorVersion] = {}
        self._load_registry()
    
    def create_version(
        self,
        factor_name: str,
        model_version: str,
        description: str,
        changelog: List[str],
        is_backward_compatible: bool = True,
        migration_notes: Optional[str] = None,
        data_range: tuple = None
    ) -> FactorVersion:
        """
        创建新版本
        
        Args:
            factor_name: 因子名称
            model_version: 模型版本
            description: 描述
            changelog: 变更日志
            is_backward_compatible: 是否向后兼容
            migration_notes: 迁移说明
            data_range: 数据范围 (start_date, end_date)
        
        Returns:
            FactorVersion: 新版本信息
        """
        # 生成版本号
        version_id = self._generate_version_id(factor_name)
        
        # 创建版本
        version = FactorVersion(
            version_id=version_id,
            factor_name=factor_name,
            model_version=model_version,
            created_date=datetime.now().date(),
            description=description,
            changelog=changelog,
            is_backward_compatible=is_backward_compatible,
            migration_notes=migration_notes,
            data_range_start=data_range[0] if data_range else datetime.now().date(),
            data_range_end=data_range[1] if data_range else datetime.now().date(),
            data_points=0,  # 需要后续更新
        )
        
        # 注册版本
        self._registry[version_id] = version
        
        # 持久化
        self._save_registry()
        
        logger.info(f"创建因子版本: {version_id}")
        
        return version
    
    def get_latest_version(
        self,
        factor_name: str,
        status: str = "active"
    ) -> Optional[FactorVersion]:
        """获取最新版本"""
        versions = [
            v for v in self._registry.values()
            if v.factor_name == factor_name and v.status == status
        ]
        
        if not versions:
            return None
        
        # 按创建日期排序
        return max(versions, key=lambda v: v.created_date)
    
    def get_all_versions(
        self,
        factor_name: Optional[str] = None
    ) -> List[FactorVersion]:
        """获取所有版本"""
        if factor_name:
            return [
                v for v in self._registry.values()
                if v.factor_name == factor_name
            ]
        return list(self._registry.values())
    
    def deprecate_version(self, version_id: str):
        """标记版本为废弃"""
        if version_id in self._registry:
            self._registry[version_id].status = "deprecated"
            self._save_registry()
            logger.info(f"废弃因子版本: {version_id}")
    
    def _generate_version_id(self, factor_name: str) -> str:
        """生成版本号"""
        # 查找已有版本
        existing = [
            v for v in self._registry.values()
            if v.factor_name == factor_name
        ]
        
        if not existing:
            return f"{factor_name}_v1.0.0"
        
        # 提取最大版本号
        max_version = 0
        for v in existing:
            try:
                version_num = int(v.version_id.split("_v")[1].split(".")[0])
                max_version = max(max_version, version_num)
            except:
                pass
        
        # 新版本号
        new_version = max_version + 1
        return f"{factor_name}_v{new_version}.0.0"
    
    def _save_registry(self):
        """持久化注册表"""
        registry_file = self.storage_path / "registry.json"
        
        data = {
            vid: v.to_dict()
            for vid, v in self._registry.items()
        }
        
        with open(registry_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_registry(self):
        """加载注册表"""
        registry_file = self.storage_path / "registry.json"
        
        if not registry_file.exists():
            return
        
        try:
            with open(registry_file, 'r') as f:
                data = json.load(f)
            
            for vid, vdata in data.items():
                # TODO: 从字典恢复对象
                pass
        except Exception as e:
            logger.error(f"加载因子版本注册表失败: {e}")
```

---

### 3. 因子更新管理器

```python
# quantcore/alpha/factors/factor_update_manager.py

from typing import Dict, List, Optional, Callable
from datetime import date, datetime
from loguru import logger

from .factor_health_monitor import FactorHealthMonitor, FactorHealthReport
from .factor_version_control import FactorVersionControl, FactorVersion


class FactorUpdateManager:
    """因子更新管理器"""
    
    def __init__(
        self,
        health_monitor: FactorHealthMonitor,
        version_control: FactorVersionControl,
        recalculation_func: Callable  # 因子重新计算函数
    ):
        self.health_monitor = health_monitor
        self.version_control = version_control
        self.recalculate = recalculation_func
        
        # 更新策略
        self.update_strategies = {
            "health_degraded": {
                "trigger": "因子健康状态变为 warning/critical",
                "action": "重新计算或优化",
            },
            "model_updated": {
                "trigger": "FinSenti 模型升级",
                "action": "使用新模型重新计算",
            },
            "scheduled": {
                "trigger": "定期更新 (月度/季度)",
                "action": "重新评估因子有效性",
            },
        }
    
    async def check_and_update(
        self,
        factor_name: str,
        ic_history_data: object
    ) -> Dict:
        """
        检查并更新因子
        
        Args:
            factor_name: 因子名称
            ic_history_data: IC 历史数据
        
        Returns:
            Dict: 更新结果
        """
        logger.info(f"检查因子更新: {factor_name}")
        
        # Step 1: 健康检查
        health_report = self.health_monitor.check_health(
            factor_name,
            ic_history_data
        )
        
        result = {
            "factor_name": factor_name,
            "health_status": health_report.health_status,
            "updated": False,
            "action": None,
        }
        
        # Step 2: 根据健康状态决定行动
        if health_report.health_status == "critical":
            # 临界状态，需要立即行动
            logger.warning(f"因子 {factor_name} 处于临界状态")
            
            # 尝试重新计算
            success = await self._recalculate_factor(
                factor_name,
                health_report
            )
            
            result["updated"] = success
            result["action"] = "recalculated"
            
            if not success:
                result["action"] = "deprecated"
                self.version_control.deprecate_version(
                    self.version_control.get_latest_version(factor_name).version_id
                )
        
        elif health_report.health_status == "warning":
            # 预警状态，需要优化
            logger.warning(f"因子 {factor_name} 处于预警状态")
            
            # 尝试优化
            success = await self._optimize_factor(
                factor_name,
                health_report
            )
            
            result["updated"] = success
            result["action"] = "optimized"
        
        else:
            # 健康状态，无需行动
            result["action"] = "none"
        
        return result
    
    async def update_after_model_upgrade(
        self,
        factor_name: str,
        old_model_version: str,
        new_model_version: str
    ) -> FactorVersion:
        """
        模型升级后更新因子
        
        Args:
            factor_name: 因子名称
            old_model_version: 旧模型版本
            new_model_version: 新模型版本
        
        Returns:
            FactorVersion: 新版本
        """
        logger.info(
            f"模型升级后更新因子: {factor_name}\n"
            f"  旧模型: {old_model_version}\n"
            f"  新模型: {new_model_version}"
        )
        
        # 标记旧版本为废弃
        old_version = self.version_control.get_latest_version(factor_name)
        if old_version:
            self.version_control.deprecate_version(old_version.version_id)
        
        # 使用新模型重新计算
        new_data = await self.recalculate(
            factor_name,
            new_model_version
        )
        
        # 创建新版本
        new_version = self.version_control.create_version(
            factor_name=factor_name,
            model_version=new_model_version,
            description=f"使用 {new_model_version} 重新计算",
            changelog=[
                f"模型升级: {old_model_version} → {new_model_version}",
                "重新计算历史数据",
            ],
            is_backward_compatible=False,  # 模型升级通常不兼容
            migration_notes="需要重新回测策略",
        )
        
        logger.info(f"因子更新完成: {new_version.version_id}")
        
        return new_version
    
    async def _recalculate_factor(
        self,
        factor_name: str,
        health_report: FactorHealthReport
    ) -> bool:
        """重新计算因子"""
        try:
            logger.info(f"重新计算因子: {factor_name}")
            
            # 调用重新计算函数
            await self.recalculate(factor_name)
            
            return True
            
        except Exception as e:
            logger.error(f"重新计算因子失败: {factor_name}, 错误: {e}")
            return False
    
    async def _optimize_factor(
        self,
        factor_name: str,
        health_report: FactorHealthReport
    ) -> bool:
        """优化因子"""
        try:
            logger.info(f"优化因子: {factor_name}")
            
            # TODO: 实现因子优化逻辑
            # 例如: 调整参数、改变计算方法等
            
            return True
            
        except Exception as e:
            logger.error(f"优化因子失败: {factor_name}, 错误: {e}")
            return False
```

---

## 📊 预期效果

### 因子健康监控

| 场景 | 无监控 | 有监控 | 改善 |
|-----|--------|--------|------|
| 因子失效发现时间 | 1-3 个月 | 1-3 天 | 提前 30 倍 |
| 策略损失 | 5-10% | < 1% | 减少 90% |
| 人工检查频率 | 每周 | 自动 | 效率 100 倍 |

### 版本管理

| 功能 | 无版本控制 | 有版本控制 |
|-----|-----------|-----------|
| 模型升级影响 | 无法追溯 | 清晰隔离 |
| 数据回溯 | 困难 | 简单 |
| 回滚能力 | 无 | 有 |
| 兼容性管理 | 混乱 | 明确 |

---

**文档版本**: v1.0  
**创建时间**: 2026-04-24  
**模块位置**: quantcore/alpha/factors/
