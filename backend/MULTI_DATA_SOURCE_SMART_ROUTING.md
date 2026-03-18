# 多数据源智能切换方案

## 一、当前架构分析

### 1.1 现有数据源架构

```python
# app/adapters/factory.py 已实现的核心功能

class DataSourceManager:
    """数据源管理器"""
    
    # ✅ 已实现
    - 多适配器支持：efinance/tushare/akshare/baostock
    - 优先级配置：DATA_SOURCE_PRIORITY
    - 自动故障转移：_get_stock_info_with_fallback()
    - 方法级数据源参数：source_type
    
    # ❌ 缺失
    - 统一的 API 路由层
    - 数据源健康检查
    - 实时性能监控
    - 智能路由策略
```

### 1.2 现有路由结构

```
app/api/v1/endpoints/
├── stock.py          # 股票相关（混合使用多个数据源）
├── market.py         # 市场行情
├── realtime.py       # 实时盘口
├── shareholder.py    # 股东信息
└── ...               # 其他业务模块
```

**问题**：
- 路由没有明确数据源标识
- 前端无法指定数据源
- 无法查看数据源状态

---

## 二、改进方案设计

### 2.1 路由命名优化（推荐方案）

#### 方案 A：统一路由 + 数据源参数（推荐）

**优点**：
- ✅ 路由简洁统一
- ✅ 前端可灵活选择数据源
- ✅ 支持自动故障转移
- ✅ 向后兼容

```python
# 统一路由结构
GET /api/v1/stock/list?source=efinance
GET /api/v1/stock/{code}/kline?source=auto&period=daily
GET /api/v1/stock/{code}/realtime?source=tushare

# source 参数说明
- auto: 自动选择（默认，按优先级）
- efinance: 强制使用 efinance
- tushare: 强制使用 tushare
- akshare: 强制使用 akshare
```

**实现代码**：

```python
# app/api/v1/endpoints/stock.py
from fastapi import APIRouter, Query
from typing import Optional, Literal

router = APIRouter()

DataSourceType = Literal["auto", "efinance", "tushare", "akshare", "baostock"]

@router.get("/list", response_model=ResponseModel[List[StockBasicInfo]])
async def get_stock_list(
    source: DataSourceType = Query("auto", description="数据源：auto=自动选择")
):
    """获取股票列表（支持多数据源）"""
    # source="auto" 时自动选择最优数据源
    stocks = await data_source_manager.get_stock_list(
        source_type=None if source == "auto" else source
    )
    return ResponseModel(data=stocks)


@router.get("/{code}/kline", response_model=ResponseModel[List[KLineData]])
async def get_kline(
    code: str,
    period: str = Query("daily", description="周期"),
    source: DataSourceType = Query("auto", description="数据源"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    adjust: str = Query("qfq"),
):
    """获取 K 线数据（支持多数据源智能切换）"""
    klines = await data_source_manager.get_kline(
        code=code,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
        source_type=None if source == "auto" else source
    )
    return ResponseModel(data=klines)
```

#### 方案 B：独立数据源路由（备选）

```python
# 独立路由，每个数据源单独端点
GET /api/v1/data-source/efinance/stock/list
GET /api/v1/data-source/tushare/stock/list
GET /api/v1/data-source/auto/stock/list  # 自动选择

# 优点：路由清晰
# 缺点：路由冗余，维护成本高
```

### 2.2 数据源健康检查

```python
# app/api/v1/endpoints/data_source.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime

router = APIRouter(prefix="/data-source", tags=["数据源管理"])


class DataSourceHealth(BaseModel):
    name: str
    status: str  # "healthy", "degraded", "unavailable"
    response_time_ms: float
    success_rate: float  # 0-100
    last_check: datetime
    error_message: Optional[str] = None


class DataSourceStats(BaseModel):
    total_requests: int
    failed_requests: int
    avg_response_time_ms: float
    cache_hit_rate: float


@router.get("/health", response_model=Dict[str, DataSourceHealth])
async def get_data_source_health():
    """获取所有数据源健康状态"""
    from app.adapters.factory import data_source_manager
    
    health_status = {}
    for source_name in data_source_manager.get_available_sources():
        adapter = data_source_manager.get_adapter(source_name)
        
        # 获取统计数据
        stats = adapter.get_stats() if hasattr(adapter, 'get_stats') else {}
        
        # 健康检查（简单 ping 测试）
        try:
            start_time = datetime.now()
            # 执行一个简单请求
            await adapter.get_stock_info("000001")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health_status[source_name] = DataSourceHealth(
                name=source_name,
                status="healthy" if response_time < 2000 else "degraded",
                response_time_ms=response_time,
                success_rate=stats.get("success_rate", 100.0),
                last_check=datetime.now(),
                error_message=None
            )
        except Exception as e:
            health_status[source_name] = DataSourceHealth(
                name=source_name,
                status="unavailable",
                response_time_ms=0,
                success_rate=0,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    return health_status


@router.get("/stats/{source_name}", response_model=DataSourceStats)
async def get_data_source_stats(source_name: str):
    """获取指定数据源统计信息"""
    adapter = data_source_manager.get_adapter(source_name)
    stats = adapter.get_stats() if hasattr(adapter, 'get_stats') else {}
    
    return DataSourceStats(
        total_requests=stats.get("total_requests", 0),
        failed_requests=stats.get("failed_requests", 0),
        avg_response_time_ms=stats.get("avg_response_time", 0),
        cache_hit_rate=stats.get("cache_hit_rate", 0)
    )


@router.post("/switch", response_model=ResponseModel[dict])
async def switch_data_source(
    source_name: str,
    set_as_default: bool = True
):
    """切换默认数据源"""
    from app.config import settings
    
    available_sources = data_source_manager.get_available_sources()
    
    if source_name not in available_sources:
        return ResponseModel(
            success=False,
            code="NOT_AVAILABLE",
            message=f"数据源 {source_name} 不可用，可用数据源：{available_sources}"
        )
    
    # 更新配置（临时）
    if set_as_default:
        settings.DEFAULT_DATA_SOURCE = source_name
    
    return ResponseModel(
        success=True,
        message=f"已切换默认数据源为：{source_name}",
        data={"current_source": source_name}
    )


@router.get("/sources", response_model=ResponseModel[List[str]])
async def get_available_sources():
    """获取所有可用数据源列表"""
    sources = data_source_manager.get_available_sources()
    return ResponseModel(data=sources)
```

### 2.3 智能路由策略

```python
# app/adapters/smart_router.py
from typing import Optional, Dict, List
from enum import Enum
import asyncio
from loguru import logger


class RoutingStrategy(Enum):
    """路由策略"""
    AUTO = "auto"              # 自动选择（默认）
    FASTEST = "fastest"        # 响应最快
    MOST_RELIABLE = "reliable" # 最可靠（成功率最高）
    ROUND_ROBIN = "round"      # 轮询
    PRIORITY = "priority"      # 优先级


class SmartDataSourceRouter:
    """智能数据源路由器"""
    
    def __init__(self):
        self._response_times: Dict[str, List[float]] = {}  # 历史响应时间
        self._success_rates: Dict[str, float] = {}  # 成功率
        self._last_used: Dict[str, float] = {}  # 最后使用时间
        self._strategy = RoutingStrategy.AUTO
    
    def set_strategy(self, strategy: RoutingStrategy):
        """设置路由策略"""
        self._strategy = strategy
    
    def record_request(self, source: str, response_time_ms: float, success: bool):
        """记录请求统计"""
        # 记录响应时间（保留最近 100 次）
        if source not in self._response_times:
            self._response_times[source] = []
        self._response_times[source].append(response_time_ms)
        if len(self._response_times[source]) > 100:
            self._response_times[source].pop(0)
        
        # 更新成功率（指数移动平均）
        current_success_rate = self._success_rates.get(source, 100.0)
        new_success_rate = 100.0 if success else 0.0
        self._success_rates[source] = current_success_rate * 0.9 + new_success_rate * 0.1
        
        # 记录最后使用时间
        import time
        self._last_used[source] = time.time()
    
    async def select_source(
        self,
        operation: str,
        available_sources: List[str]
    ) -> str:
        """根据策略选择最优数据源"""
        
        if not available_sources:
            raise ValueError("没有可用数据源")
        
        if len(available_sources) == 1:
            return available_sources[0]
        
        if self._strategy == RoutingStrategy.AUTO:
            return await self._select_auto(available_sources)
        elif self._strategy == RoutingStrategy.FASTEST:
            return self._select_fastest(available_sources)
        elif self._strategy == RoutingStrategy.MOST_RELIABLE:
            return self._select_reliable(available_sources)
        elif self._strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_sources)
        else:  # PRIORITY
            return available_sources[0]
    
    async def _select_auto(self, available_sources: List[str]) -> str:
        """自动选择：综合响应时间和成功率"""
        best_score = -1
        best_source = available_sources[0]
        
        for source in available_sources:
            # 计算综合得分（响应时间 60% + 成功率 40%）
            avg_time = self._get_avg_response_time(source)
            success_rate = self._success_rates.get(source, 100.0)
            
            # 归一化得分（响应时间越短越好，成功率越高越好）
            time_score = max(0, 100 - avg_time)  # 假设 100ms 为满分
            score = time_score * 0.6 + success_rate * 0.4
            
            if score > best_score:
                best_score = score
                best_source = source
        
        logger.debug(f"智能路由选择：{best_source} (得分：{best_score:.2f})")
        return best_source
    
    def _select_fastest(self, available_sources: List[str]) -> str:
        """选择响应最快的数据源"""
        fastest_source = available_sources[0]
        fastest_time = float('inf')
        
        for source in available_sources:
            avg_time = self._get_avg_response_time(source)
            if avg_time < fastest_time:
                fastest_time = avg_time
                fastest_source = source
        
        return fastest_source
    
    def _select_reliable(self, available_sources: List[str]) -> str:
        """选择最可靠的数据源"""
        return max(
            available_sources,
            key=lambda s: self._success_rates.get(s, 0)
        )
    
    def _select_round_robin(self, available_sources: List[str]) -> str:
        """轮询选择"""
        import time
        current_time = time.time()
        
        # 选择最久未使用的数据源
        return min(
            available_sources,
            key=lambda s: self._last_used.get(s, 0)
        )
    
    def _get_avg_response_time(self, source: str) -> float:
        """获取平均响应时间"""
        times = self._response_times.get(source, [])
        if not times:
            return 0.0
        return sum(times) / len(times)


# 全局智能路由器实例
smart_router = SmartDataSourceRouter()
```

### 2.4 增强的数据源管理器

```python
# app/adapters/factory.py (增强版)
class DataSourceManager:
    def __init__(self, default_source: Optional[str] = None):
        self._default_source = default_source or settings.DEFAULT_DATA_SOURCE
        self._factory = DataSourceFactory
        self._smart_router = SmartDataSourceRouter()  # 新增智能路由
    
    async def get_stock_info(
        self,
        code: str,
        source_type: Optional[str] = None,
        use_smart_routing: bool = True  # 新增参数
    ) -> Optional[StockBasicInfo]:
        """获取股票信息（支持智能路由）"""
        
        start_time = time.time()
        
        try:
            # 智能路由
            if use_smart_routing and source_type == "auto":
                available_sources = self.get_available_sources()
                source_type = await self._smart_router.select_source(
                    operation="get_stock_info",
                    available_sources=available_sources
                )
            
            # 原有逻辑
            if source_type:
                adapter = self.get_adapter(source_type)
                result = await adapter.get_stock_info(code)
            else:
                result = await self._get_stock_info_with_fallback(code)
            
            # 记录统计
            response_time = (time.time() - start_time) * 1000
            self._smart_router.record_request(
                source=source_type or "fallback",
                response_time_ms=response_time,
                success=result is not None
            )
            
            return result
            
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
```

---

## 三、前端集成方案

### 3.1 前端 API 服务增强

```typescript
// frontend/src/services/dataSource.ts
import api from './api'

export interface DataSourceHealth {
  name: string
  status: 'healthy' | 'degraded' | 'unavailable'
  response_time_ms: number
  success_rate: number
  last_check: string
  error_message?: string
}

export const dataSourceApi = {
  /** 获取所有数据源健康状态 */
  getHealth: () =>
    api.get<Record<string, DataSourceHealth>>('/data-source/health'),
  
  /** 获取可用数据源列表 */
  getAvailableSources: () =>
    api.get<string[]>('/data-source/sources'),
  
  /** 切换默认数据源 */
  switchSource: (sourceName: string, setAsDefault = true) =>
    api.post('/data-source/switch', null, {
      params: { source_name: sourceName, set_as_default: setAsDefault }
    }),
  
  /** 获取数据源统计 */
  getStats: (sourceName: string) =>
    api.get(`/data-source/stats/${sourceName}`),
}
```

### 3.2 前端数据源选择组件

```typescript
// frontend/src/components/DataSourceSelector.tsx
import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dataSourceApi } from '../services/dataSource'

export const DataSourceSelector: React.FC = () => {
  const queryClient = useQueryClient()
  
  // 获取数据源健康状态
  const { data: health } = useQuery({
    queryKey: ['dataSourceHealth'],
    queryFn: () => dataSourceApi.getHealth(),
    refetchInterval: 30000, // 30 秒刷新一次
  })
  
  // 切换数据源
  const switchMutation = useMutation({
    mutationFn: (sourceName: string) =>
      dataSourceApi.switchSource(sourceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSourceHealth'] })
    },
  })
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green'
      case 'degraded': return 'yellow'
      case 'unavailable': return 'red'
      default: return 'gray'
    }
  }
  
  return (
    <div className="data-source-selector">
      <h3>数据源状态</h3>
      {health && Object.entries(health).map(([name, info]) => (
        <div key={name} className="source-item">
          <span className={`status-dot ${getStatusColor(info.status)}`} />
          <span className="source-name">{name}</span>
          <span className="source-stats">
            响应：{info.response_time_ms.toFixed(0)}ms | 
            成功率：{info.success_rate.toFixed(1)}%
          </span>
          <button
            onClick={() => switchMutation.mutate(name)}
            disabled={info.status === 'unavailable'}
          >
            切换
          </button>
        </div>
      ))}
    </div>
  )
}
```

---

## 四、实施步骤

### 4.1 第一阶段：基础路由优化（1 天）

1. **修改现有路由** - 添加 `source` 参数
2. **保持向后兼容** - 默认 `source=auto`
3. **更新文档** - API 文档说明

### 4.2 第二阶段：健康检查（1 天）

1. **创建 `/data-source/health` 端点**
2. **实现 ping 测试**
3. **添加统计信息**

### 4.3 第三阶段：智能路由（2 天）

1. **实现 `SmartDataSourceRouter`**
2. **集成到 `DataSourceManager`**
3. **添加路由策略配置**

### 4.4 第四阶段：前端集成（2 天）

1. **创建数据源选择组件**
2. **更新 API 服务层**
3. **UI/UX 优化**

---

## 五、配置示例

### 5.1 环境变量

```bash
# .env
# 数据源优先级（逗号分隔）
DATA_SOURCE_PRIORITY=efinance,tushare,akshare,baostock

# 默认数据源
DEFAULT_DATA_SOURCE=auto

# 路由策略
ROUTING_STRATEGY=auto  # auto/fastest/reliable/round/priority

# 健康检查配置
HEALTH_CHECK_INTERVAL=60  # 秒
HEALTH_CHECK_TIMEOUT=5    # 秒
```

### 5.2 配置文件

```python
# app/config.py
class Settings(BaseSettings):
    # 数据源配置
    DATA_SOURCE_PRIORITY: str = "efinance,tushare,akshare,baostock"
    DEFAULT_DATA_SOURCE: str = "auto"
    ROUTING_STRATEGY: str = "auto"
    
    # 健康检查
    HEALTH_CHECK_INTERVAL: int = 60
    HEALTH_CHECK_TIMEOUT: int = 5
    
    class Config:
        env_file = ".env"
```

---

## 六、测试方案

### 6.1 单元测试

```python
# tests/test_smart_router.py
async def test_smart_router_select_fastest():
    router = SmartDataSourceRouter()
    router.record_request("efinance", 100, True)
    router.record_request("tushare", 500, True)
    router.record_request("akshare", 200, True)
    
    router.set_strategy(RoutingStrategy.FASTEST)
    source = await router.select_source(
        "test",
        ["efinance", "tushare", "akshare"]
    )
    
    assert source == "efinance"


async def test_smart_router_select_reliable():
    router = SmartDataSourceRouter()
    router.record_request("efinance", 100, True)
    router.record_request("efinance", 100, True)
    router.record_request("tushare", 100, False)
    
    router.set_strategy(RoutingStrategy.MOST_RELIABLE)
    source = await router.select_source(
        "test",
        ["efinance", "tushare"]
    )
    
    assert source == "efinance"
```

### 6.2 集成测试

```python
# tests/test_data_source_health.py
async def test_health_check_endpoint(client):
    response = await client.get("/data-source/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "efinance" in data
    assert data["efinance"]["status"] in ["healthy", "degraded", "unavailable"]
```

---

## 七、总结

### 7.1 方案优势

✅ **路由命名准确** - 统一使用 `source` 参数，清晰明了  
✅ **多数据源智能切换** - 支持 5 种路由策略  
✅ **健康检查** - 实时监控数据源状态  
✅ **故障转移** - 自动降级，保证可用性  
✅ **性能优化** - 智能选择最快/最可靠数据源  
✅ **向后兼容** - 默认 `source=auto` 不影响现有代码  

### 7.2 实施建议

1. **立即实施**：第一阶段（路由优化）
2. **短期实施**：第二阶段（健康检查）
3. **中期实施**：第三阶段（智能路由）
4. **长期优化**：根据实际使用情况调整策略

---

**文档版本**：v1.0  
**创建日期**：2026-03-18  
**维护者**：Quant 团队
