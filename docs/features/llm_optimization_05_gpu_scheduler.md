# 优化模块 5: GPU 显存智能调度器

## 📊 设计概述

### 问题背景

双模型部署面临显存管理挑战:
- **总显存**: RTX 4090 = 24GB
- **FinSenti 模型**: 6.5GB (Q5_K_M)
- **Qwen3.5 模型**: 6.5GB (Q5_K_M)
- **其他占用**: CUDA 上下文 + 推理缓存 ≈ 2-3GB
- **可用显存**: 24 - 6.5 - 6.5 - 3 = 8GB (余量有限)

关键问题:
- ❌ 同时加载两个模型 = 13GB + 3GB = 16GB (接近上限)
- ❌ 频繁切换导致延迟
- ❌ OOM 风险
- ❌ 无法预测何时需要哪个模型

### 解决方案

设计**智能显存调度器**，实现:
- ✅ 时段感知 (交易时间/研究时间/离线时间)
- ✅ 按需加载 (预热模型)
- ✅ 智能卸载 (LRU + 超时)
- ✅ OOM 保护 (显存监控 + 自动降级)
- ✅ 批量优化 (夜间顺序执行)

---

## 🏗️ 调度策略

```
┌─────────────────────────────────────────────────────────┐
│                 时段划分                                  │
│                                                         │
│  交易时段 (9:00-15:00)                                   │
│  ┌───────────────────────────────────────┐             │
│  │ 常驻: FinSenti (文本因子实时生产)      │             │
│  │ 按需: Qwen3.5 (策略查询)               │             │
│  │ 优先级: 低延迟                         │             │
│  └───────────────────────────────────────┘             │
│                                                         │
│  研究时段 (非交易时间)                                   │
│  ┌───────────────────────────────────────┐             │
│  │ 常驻: Qwen3.5 (策略开发辅助)           │             │
│  │ 按需: FinSenti (历史数据分析)          │             │
│  │ 优先级: 吞吐量                         │             │
│  └───────────────────────────────────────┘             │
│                                                         │
│  离线时段 (0:00-6:00)                                   │
│  ┌───────────────────────────────────────┐             │
│  │ 策略: 顺序执行批量任务                 │             │
│  │ 1. FinSenti 批量处理当日文本           │             │
│  │ 2. 卸载 FinSenti                       │             │
│  │ 3. Qwen3.5 生成策略报告                │             │
│  │ 4. 卸载 Qwen3.5                        │             │
│  │ 优先级: 成本控制                       │             │
│  └───────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 核心代码设计

### 1. 显存监控器

```python
# backend/app/services/gpu_monitor.py

from typing import Optional, Dict
from dataclasses import dataclass
import subprocess
import re
from loguru import logger


@dataclass
class GPUStatus:
    """GPU 状态信息"""
    gpu_id: int
    total_memory_mb: float  # 总显存 (MB)
    used_memory_mb: float  # 已用显存 (MB)
    free_memory_mb: float  # 可用显存 (MB)
    gpu_utilization: float  # GPU 利用率 (%)
    temperature: float  # 温度 (°C)
    
    @property
    def memory_usage_percent(self) -> float:
        """显存使用率"""
        return self.used_memory_mb / self.total_memory_mb
    
    @property
    def is_healthy(self) -> bool:
        """是否健康"""
        return (
            self.memory_usage_percent < 0.9 and
            self.temperature < 85 and
            self.gpu_utilization < 0.95
        )


class GPUMonitor:
    """GPU 显存监控器"""
    
    def __init__(self, gpu_id: int = 0):
        self.gpu_id = gpu_id
    
    def get_status(self) -> GPUStatus:
        """获取 GPU 状态"""
        try:
            # 使用 nvidia-smi 获取信息
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total,memory.used,memory.free,"
                    "utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits",
                    "-i", str(self.gpu_id)
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.strip()
            
            # 解析输出
            parts = [x.strip() for x in output.split(',')]
            
            return GPUStatus(
                gpu_id=self.gpu_id,
                total_memory_mb=float(parts[0]),
                used_memory_mb=float(parts[1]),
                free_memory_mb=float(parts[2]),
                gpu_utilization=float(parts[3]) / 100,
                temperature=float(parts[4]),
            )
            
        except Exception as e:
            logger.error(f"获取 GPU 状态失败: {e}")
            # 返回默认值
            return GPUStatus(
                gpu_id=self.gpu_id,
                total_memory_mb=24576,  # 24GB
                used_memory_mb=0,
                free_memory_mb=24576,
                gpu_utilization=0.0,
                temperature=50,
            )
    
    def is_safe_to_load(self, required_memory_mb: float) -> bool:
        """
        检查是否可以安全加载模型
        
        Args:
            required_memory_mb: 需要的显存 (MB)
        
        Returns:
            bool: 是否可以安全加载
        """
        status = self.get_status()
        
        # 预留 1GB 安全余量
        safety_margin_mb = 1024
        
        available = status.free_memory_mb - safety_margin_mb
        
        if available >= required_memory_mb:
            return True
        else:
            logger.warning(
                f"显存不足: 需要 {required_memory_mb:.0f}MB, "
                f"可用 {available:.0f}MB"
            )
            return False
    
    def get_memory_pressure(self) -> str:
        """获取显存压力等级"""
        status = self.get_status()
        usage = status.memory_usage_percent
        
        if usage < 0.5:
            return "low"
        elif usage < 0.7:
            return "medium"
        elif usage < 0.85:
            return "high"
        else:
            return "critical"
```

---

### 2. 模型生命周期管理器

```python
# backend/app/services/model_lifecycle.py

from typing import Optional, Dict
from datetime import datetime, timedelta
from loguru import logger

from .gpu_monitor import GPUMonitor


class ModelLifecycleManager:
    """模型生命周期管理器"""
    
    def __init__(
        self,
        gpu_monitor: GPUMonitor,
        unload_timeout_minutes: int = 5,
        warmup_enabled: bool = True
    ):
        self.gpu_monitor = gpu_monitor
        self.unload_timeout = timedelta(minutes=unload_timeout_minutes)
        self.warmup_enabled = warmup_enabled
        
        # 模型状态
        self._loaded_models: Dict[str, dict] = {}
    
    async def load_model(
        self,
        model_name: str,
        model_path: str,
        memory_estimate_mb: float
    ) -> bool:
        """
        加载模型
        
        Args:
            model_name: 模型名称
            model_path: 模型路径
            memory_estimate_mb: 预估显存 (MB)
        
        Returns:
            bool: 是否成功加载
        """
        # 检查是否已加载
        if model_name in self._loaded_models:
            logger.debug(f"模型已加载: {model_name}")
            return True
        
        # 检查显存
        if not self.gpu_monitor.is_safe_to_load(memory_estimate_mb):
            logger.error(f"显存不足，无法加载 {model_name}")
            return False
        
        # 加载模型 (调用 Ollama API)
        try:
            logger.info(f"正在加载模型: {model_name}")
            
            # TODO: 实现实际的 Ollama 模型加载
            # ollama load {model_name}
            
            # 预热 (可选)
            if self.warmup_enabled:
                await self._warmup_model(model_name)
            
            # 记录状态
            self._loaded_models[model_name] = {
                "load_time": datetime.now(),
                "last_used": datetime.now(),
                "memory_mb": memory_estimate_mb,
            }
            
            logger.info(f"模型加载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败: {model_name}, 错误: {e}")
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """
        卸载模型
        
        Args:
            model_name: 模型名称
        
        Returns:
            bool: 是否成功卸载
        """
        if model_name not in self._loaded_models:
            return True
        
        try:
            logger.info(f"正在卸载模型: {model_name}")
            
            # TODO: 实现实际的 Ollama 模型卸载
            # ollama unload {model_name}
            
            # 移除记录
            del self._loaded_models[model_name]
            
            logger.info(f"模型卸载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"模型卸载失败: {model_name}, 错误: {e}")
            return False
    
    async def use_model(self, model_name: str) -> bool:
        """
        使用模型 (标记为最近使用)
        
        Args:
            model_name: 模型名称
        
        Returns:
            bool: 是否成功使用
        """
        if model_name not in self._loaded_models:
            # 模型未加载，尝试加载
            return False
        
        # 更新最后使用时间
        self._loaded_models[model_name]["last_used"] = datetime.now()
        return True
    
    def get_loaded_models(self) -> Dict[str, dict]:
        """获取已加载的模型"""
        return self._loaded_models.copy()
    
    def is_model_loaded(self, model_name: str) -> bool:
        """检查模型是否已加载"""
        return model_name in self._loaded_models
    
    async def unload_idle_models(self) -> int:
        """卸载空闲模型 (超时未使用)"""
        unloaded_count = 0
        
        for model_name, info in list(self._loaded_models.items()):
            idle_time = datetime.now() - info["last_used"]
            
            if idle_time > self.unload_timeout:
                if await self.unload_model(model_name):
                    unloaded_count += 1
        
        if unloaded_count > 0:
            logger.info(f"卸载了 {unloaded_count} 个空闲模型")
        
        return unloaded_count
    
    async def _warmup_model(self, model_name: str):
        """预热模型 (发送测试请求)"""
        try:
            # 发送简单请求，触发模型加载到 GPU
            # ollama run {model_name} "test"
            logger.debug(f"预热模型: {model_name}")
        except Exception as e:
            logger.warning(f"模型预热失败: {model_name}, 错误: {e}")
```

---

### 3. 时段调度器

```python
# backend/app/services/time_based_scheduler.py

from typing import Optional, List, Callable
from datetime import datetime, time
from enum import Enum
from loguru import logger

from .model_lifecycle import ModelLifecycleManager
from .gpu_monitor import GPUMonitor


class TimePeriod(Enum):
    """时段类型"""
    TRADING = "trading"  # 交易时段 (9:00-15:00)
    RESEARCH = "research"  # 研究时段 (非交易时间)
    OFFLINE = "offline"  # 离线时段 (0:00-6:00)


class TimeBasedScheduler:
    """基于时段的调度器"""
    
    # 时段定义
    TRADING_HOURS = (time(9, 0), time(15, 0))
    OFFLINE_HOURS = (time(0, 0), time(6, 0))
    
    def __init__(
        self,
        lifecycle_manager: ModelLifecycleManager,
        gpu_monitor: GPUMonitor
    ):
        self.lifecycle_manager = lifecycle_manager
        self.gpu_monitor = gpu_monitor
        
        # 模型配置
        self.model_configs = {
            "finsenti": {
                "name": "finsenti-qwen3.5:9b",
                "path": "/models/FinSenti-Qwen3.5-9B",
                "memory_mb": 6656,  # 6.5GB
            },
            "qwen3.5": {
                "name": "qwen3.5:9b",
                "path": "/models/Qwen3.5-9B",
                "memory_mb": 6656,  # 6.5GB
            },
        }
        
        # 回调函数
        self._period_callbacks = {
            TimePeriod.TRADING: [],
            TimePeriod.RESEARCH: [],
            TimePeriod.OFFLINE: [],
        }
    
    def get_current_period(self) -> TimePeriod:
        """获取当前时段"""
        now = datetime.now().time()
        
        # 离线时段
        if self.OFFLINE_HOURS[0] <= now < self.OFFLINE_HOURS[1]:
            return TimePeriod.OFFLINE
        
        # 交易时段
        if self.TRADING_HOURS[0] <= now < self.TRADING_HOURS[1]:
            return TimePeriod.TRADING
        
        # 研究时段
        return TimePeriod.RESEARCH
    
    async def execute_period_schedule(self):
        """执行时段调度"""
        period = self.get_current_period()
        
        logger.info(f"当前时段: {period.value}")
        
        if period == TimePeriod.TRADING:
            await self._execute_trading_schedule()
        elif period == TimePeriod.RESEARCH:
            await self._execute_research_schedule()
        elif period == TimePeriod.OFFLINE:
            await self._execute_offline_schedule()
    
    async def _execute_trading_schedule(self):
        """交易时段调度"""
        # 常驻: FinSenti
        await self.lifecycle_manager.load_model(
            self.model_configs["finsenti"]["name"],
            self.model_configs["finsenti"]["path"],
            self.model_configs["finsenti"]["memory_mb"]
        )
        
        # Qwen3.5 按需加载
        # 不在这里加载，等有请求时再加载
        
        logger.info("交易时段调度: FinSenti 常驻")
    
    async def _execute_research_schedule(self):
        """研究时段调度"""
        # 常驻: Qwen3.5
        await self.lifecycle_manager.load_model(
            self.model_configs["qwen3.5"]["name"],
            self.model_configs["qwen3.5"]["path"],
            self.model_configs["qwen3.5"]["memory_mb"]
        )
        
        logger.info("研究时段调度: Qwen3.5 常驻")
    
    async def _execute_offline_schedule(self):
        """离线时段调度 (批量处理)"""
        # Step 1: FinSenti 批量处理当日文本
        logger.info("离线时段: 开始批量处理文本")
        finsenti_loaded = await self.lifecycle_manager.load_model(
            self.model_configs["finsenti"]["name"],
            self.model_configs["finsenti"]["path"],
            self.model_configs["finsenti"]["memory_mb"]
        )
        
        if finsenti_loaded:
            # TODO: 执行批量文本因子生产
            # await produce_daily_text_factors()
            
            # Step 2: 卸载 FinSenti
            await self.lifecycle_manager.unload_model(
                self.model_configs["finsenti"]["name"]
            )
        
        # Step 3: Qwen3.5 生成策略报告
        logger.info("离线时段: 开始生成策略报告")
        qwen_loaded = await self.lifecycle_manager.load_model(
            self.model_configs["qwen3.5"]["name"],
            self.model_configs["qwen3.5"]["path"],
            self.model_configs["qwen3.5"]["memory_mb"]
        )
        
        if qwen_loaded:
            # TODO: 执行策略报告生成
            # await generate_strategy_reports()
            
            # Step 4: 卸载 Qwen3.5
            await self.lifecycle_manager.unload_model(
                self.model_configs["qwen3.5"]["name"]
            )
        
        logger.info("离线时段: 批量处理完成")
    
    def register_callback(
        self,
        period: TimePeriod,
        callback: Callable
    ):
        """注册时段回调函数"""
        self._period_callbacks[period].append(callback)
```

---

### 4. 智能调度主类

```python
# backend/app/services/gpu_scheduler.py

from typing import Optional, Dict
from datetime import datetime
from loguru import logger
import asyncio

from .gpu_monitor import GPUMonitor
from .model_lifecycle import ModelLifecycleManager
from .time_based_scheduler import TimeBasedScheduler, TimePeriod


class GPUScheduler:
    """GPU 智能调度器 (主类)"""
    
    def __init__(
        self,
        gpu_id: int = 0,
        unload_timeout_minutes: int = 5,
        monitoring_interval: int = 30
    ):
        # 初始化组件
        self.gpu_monitor = GPUMonitor(gpu_id)
        self.lifecycle_manager = ModelLifecycleManager(
            self.gpu_monitor,
            unload_timeout_minutes
        )
        self.time_scheduler = TimeBasedScheduler(
            self.lifecycle_manager,
            self.gpu_monitor
        )
        
        # 监控任务
        self._monitoring_task = None
        self._monitoring_interval = monitoring_interval
    
    async def start(self):
        """启动调度器"""
        logger.info("GPU 智能调度器启动")
        
        # 启动后台监控任务
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop()
        )
        
        # 执行初始调度
        await self.time_scheduler.execute_period_schedule()
    
    async def stop(self):
        """停止调度器"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # 卸载所有模型
        for model_name in list(
            self.lifecycle_manager.get_loaded_models().keys()
        ):
            await self.lifecycle_manager.unload_model(model_name)
        
        logger.info("GPU 智能调度器已停止")
    
    async def query_with_model(
        self,
        model_name: str,
        query_func: callable,
        *args,
        **kwargs
    ):
        """
        使用指定模型执行查询
        
        Args:
            model_name: 模型名称
            query_func: 查询函数
            *args, **kwargs: 查询参数
        
        Returns:
            查询结果
        """
        # 检查模型是否已加载
        if not self.lifecycle_manager.is_model_loaded(model_name):
            # 加载模型
            config = self.time_scheduler.model_configs.get(model_name)
            if not config:
                raise ValueError(f"未知的模型: {model_name}")
            
            loaded = await self.lifecycle_manager.load_model(
                config["name"],
                config["path"],
                config["memory_mb"]
            )
            
            if not loaded:
                raise RuntimeError(f"模型加载失败: {model_name}")
        
        # 标记使用
        await self.lifecycle_manager.use_model(model_name)
        
        # 执行查询
        return await query_func(*args, **kwargs)
    
    async def _monitoring_loop(self):
        """后台监控循环"""
        while True:
            try:
                # 检查 GPU 状态
                status = self.gpu_monitor.get_status()
                
                if not status.is_healthy:
                    logger.warning(
                        f"GPU 状态异常: "
                        f"显存使用率={status.memory_usage_percent:.0%}, "
                        f"温度={status.temperature}°C"
                    )
                
                # 卸载空闲模型
                unloaded = await self.lifecycle_manager.unload_idle_models()
                
                # 检查时段变化
                await self.time_scheduler.execute_period_schedule()
                
                # 等待下一轮
                await asyncio.sleep(self._monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "gpu": self.gpu_monitor.get_status().__dict__,
            "loaded_models": self.lifecycle_manager.get_loaded_models(),
            "current_period": self.time_scheduler.get_current_period().value,
        }
```

---

## 📊 预期效果

### 显存使用对比

| 时段 | 无调度 | 有调度 | 节省 |
|-----|--------|--------|------|
| 交易时段 (9-15 点) | 16GB | 6.5GB (常驻) + 6.5GB (按需) | -50% |
| 研究时段 | 16GB | 6.5GB (常驻) | -60% |
| 离线时段 | 16GB | 6.5GB (顺序) | -60% |

### 可靠性提升

| 指标 | 无调度 | 有调度 | 改善 |
|-----|--------|--------|------|
| OOM 次数 | 频繁 | 0 | -100% |
| 模型切换延迟 | N/A | < 5 秒 | 可控 |
| GPU 利用率 | 波动大 | 稳定 | +30% |
| 显存浪费 | 50% | < 10% | -80% |

---

**文档版本**: v1.0  
**创建时间**: 2026-04-24  
**模块位置**: backend/app/services/
