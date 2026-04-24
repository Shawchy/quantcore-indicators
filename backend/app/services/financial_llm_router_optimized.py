"""
金融 LLM 路由服务 - 显存优化版本
核心策略：按需加载，用完即卸，避免双模型同时占用显存
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
import time
from dataclasses import dataclass, field
from collections import OrderedDict


class ModelType(Enum):
    """模型类型"""
    NUMERICAL = "numerical"  # 数值推理模型
    SENTIMENT = "sentiment"  # 情感分析模型


@dataclass
class ModelInstance:
    """模型实例信息"""
    model_type: ModelType
    model_name: str
    loaded_at: Optional[float] = None
    last_used_at: Optional[float] = None
    use_count: int = 0
    
    def mark_used(self):
        """标记为已使用"""
        now = time.time()
        if self.loaded_at is None:
            self.loaded_at = now
        self.last_used_at = now
        self.use_count += 1


class MemoryOptimizedRouter:
    """
    显存优化的 LLM 路由器
    
    优化策略:
    1. 懒加载：只在需要时加载模型
    2. 单实例：默认只保留一个模型在显存
    3. LRU 淘汰：显存不足时卸载最久未使用的模型
    4. 预加载：对高频模型可选择常驻显存
    """
    
    def __init__(
        self,
        max_concurrent_models: int = 1,
        unload_timeout: float = 300.0,  # 5 分钟未使用自动卸载
        vram_budget_gb: float = 8.0  # 显存预算（GB）
    ):
        """
        Args:
            max_concurrent_models: 最大同时加载的模型数 (1-2)
            unload_timeout: 自动卸载超时时间（秒）
            vram_budget_gb: 显存预算（GB）
        """
        self.max_concurrent_models = max_concurrent_models
        self.unload_timeout = unload_timeout
        self.vram_budget_gb = vram_budget_gb
        
        # 模型实例缓存（LRU 缓存）
        self._model_cache: OrderedDict[ModelType, ModelInstance] = OrderedDict()
        
        # 模型配置
        self._model_configs = {
            ModelType.NUMERICAL: {
                "name": "qwen3:8b-financial",
                "vram_estimate_gb": 5.5,
                "priority": 1  # 优先级高（常用）
            },
            ModelType.SENTIMENT: {
                "name": "finsenti-qwen3.5:9b",
                "vram_estimate_gb": 6.5,
                "priority": 2  # 优先级低（较少用）
            }
        }
        
        # 加载统计
        self._stats = {
            "total_loads": 0,
            "total_unloads": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def _get_required_model(self, task_type: str) -> ModelType:
        """根据任务类型确定需要的模型"""
        # 数值相关任务
        numerical_tasks = [
            "numerical_analysis", "strategy_generation", 
            "code_generation", "indicator_calculation"
        ]
        
        # 情感相关任务
        sentiment_tasks = [
            "sentiment_analysis", "report_summarization",
            "news_analysis"
        ]
        
        if task_type in numerical_tasks:
            return ModelType.NUMERICAL
        elif task_type in sentiment_tasks:
            return ModelType.SENTIMENT
        else:
            # 默认使用数值模型
            return ModelType.NUMERICAL
    
    def _get_loaded_models(self) -> List[ModelType]:
        """获取当前已加载的模型列表"""
        return list(self._model_cache.keys())
    
    def _is_model_loaded(self, model_type: ModelType) -> bool:
        """检查模型是否已加载"""
        return model_type in self._model_cache
    
    def _calculate_vram_usage(self) -> float:
        """计算当前显存使用量（GB）"""
        total = 0.0
        for model_type in self._model_cache:
            config = self._model_configs[model_type]
            total += config["vram_estimate_gb"]
        return total
    
    def _can_load_model(self, model_type: ModelType) -> bool:
        """检查是否可以加载新模型"""
        current_usage = self._calculate_vram_usage()
        new_model_vram = self._model_configs[model_type]["vram_estimate_gb"]
        
        # 检查显存预算
        if current_usage + new_model_vram > self.vram_budget_gb:
            return False
        
        # 检查并发数量限制
        if len(self._model_cache) >= self.max_concurrent_models:
            return False
        
        return True
    
    def _unload_least_recently_used(self):
        """卸载最久未使用的模型"""
        if not self._model_cache:
            return
        
        # 找到最久未使用的模型
        lru_model = None
        lru_time = float('inf')
        
        for model_type, instance in self._model_cache.items():
            if instance.last_used_at and instance.last_used_at < lru_time:
                lru_time = instance.last_used_at
                lru_model = model_type
        
        # 卸载
        if lru_model:
            self._unload_model(lru_model)
    
    def _unload_model(self, model_type: ModelType):
        """卸载指定模型"""
        if model_type not in self._model_cache:
            return
        
        model_name = self._model_configs[model_type]["name"]
        print(f"[显存优化] 卸载模型：{model_name}")
        
        # TODO: 调用 Ollama API 卸载模型
        # ollama unload {model_name}
        
        del self._model_cache[model_type]
        self._stats["total_unloads"] += 1
    
    def _unload_expired_models(self):
        """卸载超时的模型"""
        now = time.time()
        expired_models = []
        
        for model_type, instance in list(self._model_cache.items()):
            if instance.last_used_at:
                idle_time = now - instance.last_used_at
                if idle_time > self.unload_timeout:
                    expired_models.append(model_type)
        
        for model_type in expired_models:
            self._unload_model(model_type)
    
    async def _load_model(self, model_type: ModelType) -> ModelInstance:
        """加载模型"""
        config = self._model_configs[model_type]
        model_name = config["name"]
        
        print(f"[显存优化] 加载模型：{model_name}")
        
        # TODO: 调用 Ollama API 加载模型
        # ollama load {model_name}
        
        # 创建实例
        instance = ModelInstance(
            model_type=model_type,
            model_name=model_name
        )
        instance.mark_used()
        
        # 加入缓存
        self._model_cache[model_type] = instance
        self._stats["total_loads"] += 1
        
        return instance
    
    async def _get_or_load_model(
        self, 
        required_type: ModelType
    ) -> ModelInstance:
        """获取或加载所需模型"""
        # 检查是否已加载
        if self._is_model_loaded(required_type):
            instance = self._model_cache[required_type]
            instance.mark_used()
            self._stats["cache_hits"] += 1
            
            # 移到 LRU 缓存末尾（最近使用）
            self._model_cache.move_to_end(required_type)
            
            return instance
        
        # 需要加载新模型
        self._stats["cache_misses"] += 1
        
        # 检查是否需要卸载其他模型
        while not self._can_load_model(required_type):
            self._unload_least_recently_used()
        
        # 加载模型
        return await self._load_model(required_type)
    
    async def route_query(
        self,
        query: str,
        task_type: str,
        context: Optional[Dict] = None,
        stock_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        路由查询（显存优化版本）
        
        Args:
            query: 用户查询
            task_type: 任务类型
            context: 上下文
            stock_data: 股票数据
        
        Returns:
            Dict: 响应结果
        """
        # 1. 清理超时模型
        self._unload_expired_models()
        
        # 2. 确定需要的模型
        required_model = self._get_required_model(task_type)
        
        # 3. 获取/加载模型
        model_instance = await self._get_or_load_model(required_model)
        
        # 4. 执行查询（占位符）
        result = await self._execute_query(
            model_name=model_instance.model_name,
            query=query,
            context=context,
            stock_data=stock_data
        )
        
        # 5. 返回结果
        return {
            "task_type": task_type,
            "model_used": model_instance.model_name,
            "model_type": required_model.value,
            "response": result,
            "memory_stats": self.get_memory_stats()
        }
    
    async def _execute_query(
        self,
        model_name: str,
        query: str,
        context: Optional[Dict] = None,
        stock_data: Optional[Dict] = None
    ) -> Any:
        """执行查询（占位符，实际需调用模型 API）"""
        # TODO: 实现真实的模型调用
        return {
            "message": f"使用 {model_name} 处理查询",
            "query": query
        }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取显存使用统计"""
        current_usage = self._calculate_vram_usage()
        loaded_models = self._get_loaded_models()
        
        return {
            "current_vram_usage_gb": round(current_usage, 2),
            "vram_budget_gb": self.vram_budget_gb,
            "loaded_models_count": len(loaded_models),
            "loaded_models": [m.value for m in loaded_models],
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "total_loads": self._stats["total_loads"],
            "total_unloads": self._stats["total_unloads"],
            "hit_rate": round(
                self._stats["cache_hits"] / 
                max(1, self._stats["cache_hits"] + self._stats["cache_misses"]),
                2
            )
        }
    
    def unload_all(self):
        """卸载所有模型（释放显存）"""
        for model_type in list(self._model_cache.keys()):
            self._unload_model(model_type)
        print("[显存优化] 已卸载所有模型，释放显存")
    
    def preload_high_priority(self):
        """预加载高优先级模型（可选）"""
        # 只预加载数值模型（常用）
        for model_type, config in self._model_configs.items():
            if config["priority"] == 1:
                # 异步加载
                asyncio.create_task(self._load_model(model_type))
                print(f"[显存优化] 预加载高优先级模型：{config['name']}")


class SmartScheduler:
    """
    智能调度器 - 进一步优化显存使用
    
    策略：
    1. 批量处理：相同模型的请求批量处理
    2. 预测预加载：根据使用模式预测并预加载
    3. 分时复用：低峰期卸载所有模型
    """
    
    def __init__(self, router: MemoryOptimizedRouter):
        self.router = router
        self._request_queue: asyncio.Queue = asyncio.Queue()
        self._usage_pattern: Dict[str, List[float]] = {
            "numerical": [],
            "sentiment": []
        }
    
    async def schedule_query(
        self,
        query: str,
        task_type: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """调度查询请求"""
        # 记录使用时间模式
        hour = time.localtime().tm_hour
        self._usage_pattern[task_type].append(hour)
        
        # 加入队列
        await self._request_queue.put({
            "query": query,
            "task_type": task_type,
            "context": context,
            "timestamp": time.time()
        })
        
        # 处理队列（实际应该由后台任务处理）
        return await self.router.route_query(query, task_type, context)
    
    def get_peak_hours(self) -> Dict[str, List[int]]:
        """分析各任务类型的高峰时段"""
        peak_hours = {}
        
        for task_type, hours in self._usage_pattern.items():
            if not hours:
                continue
            
            # 统计每个小时的出现次数
            hour_counts = {}
            for hour in hours:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            # 找出高峰时段（前 3 个）
            sorted_hours = sorted(
                hour_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            peak_hours[task_type] = [h[0] for h in sorted_hours[:3]]
        
        return peak_hours


# 使用示例
async def demo():
    """演示显存优化路由器"""
    print("=" * 60)
    print("显存优化 LLM 路由器演示")
    print("=" * 60)
    
    # 创建路由器（限制显存 8GB）
    router = MemoryOptimizedRouter(
        max_concurrent_models=1,  # 只允许 1 个模型在显存
        unload_timeout=60.0,      # 1 分钟未使用自动卸载
        vram_budget_gb=8.0        # 显存预算 8GB
    )
    
    # 模拟查询序列
    queries = [
        ("计算 600000.SH 的 MACD", "numerical_analysis"),
        ("分析市场情绪", "sentiment_analysis"),
        ("生成交易策略", "strategy_generation"),
        ("解读券商研报", "report_summarization"),
        ("计算 RSI 指标", "numerical_analysis"),
    ]
    
    print("\n开始处理查询序列...\n")
    
    for query, task_type in queries:
        print(f"查询：{query}")
        result = await router.route_query(query, task_type)
        
        print(f"使用模型：{result['model_used']}")
        print(f"显存使用：{result['memory_stats']['current_vram_usage_gb']}GB")
        print(f"缓存命中率：{result['memory_stats']['hit_rate']:.0%}")
        print("-" * 60)
    
    # 显示最终统计
    print("\n最终统计:")
    final_stats = router.get_memory_stats()
    print(f"  总加载次数：{final_stats['total_loads']}")
    print(f"  总卸载次数：{final_stats['total_unloads']}")
    print(f"  缓存命中率：{final_stats['hit_rate']:.0%}")
    print(f"  当前显存占用：{final_stats['current_vram_usage_gb']}GB")
    
    # 卸载所有模型
    router.unload_all()
    print("\n已卸载所有模型，释放显存")


if __name__ == "__main__":
    asyncio.run(demo())
