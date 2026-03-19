# 数据源优先级参数方案

## 一、参数设计

### 1.1 参数说明

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `source` | string | `"auto"` | 指定使用的数据源 |
| `source_priority` | string | `""` | 临时指定数据源优先级（逗号分隔） |
| `source_exclude` | string | `""` | 排除的数据源（逗号分隔） |
| `fallback` | boolean | `true` | 是否允许故障转移 |

### 1.2 参数优先级

```
1. source 参数（强制指定）
   ↓
2. source_priority 参数（临时优先级）
   ↓
3. 系统配置的 DATA_SOURCE_PRIORITY
   ↓
4. 默认优先级：efinance → tushare → akshare → baostock
```

---

## 二、后端实现

### 2.1 增强的数据源管理器

```python
# app/adapters/factory.py (增强版)

class DataSourceManager:
    def __init__(self, default_source: Optional[str] = None):
        self._default_source = default_source or settings.DEFAULT_DATA_SOURCE
        self._factory = DataSourceFactory
        self._smart_router = SmartDataSourceRouter()
    
    async def get_stock_info(
        self,
        code: str,
        source_type: Optional[str] = None,
        source_priority: Optional[str] = None,
        source_exclude: Optional[str] = None,
        fallback: bool = True
    ) -> Optional[StockBasicInfo]:
        """
        获取股票信息（支持多参数控制）
        
        Args:
            code: 股票代码
            source_type: 指定数据源（efinance/tushare/akshare），为 None 时自动选择
            source_priority: 临时优先级列表（逗号分隔），如 "efinance,tushare"
            source_exclude: 排除的数据源列表（逗号分隔）
            fallback: 是否允许故障转移（默认 True）
        
        Returns:
            股票基本信息
        """
        try:
            # 1. 如果指定了具体数据源，直接使用
            if source_type and source_type != "auto":
                adapter = self.get_adapter(source_type)
                try:
                    return await adapter.get_stock_info(code)
                except Exception as e:
                    if fallback:
                        logger.warning(f"数据源 {source_type} 失败，尝试故障转移：{e}")
                        # 排除失败的数据源，尝试其他
                        if source_exclude:
                            source_exclude = f"{source_exclude},{source_type}"
                        else:
                            source_exclude = source_type
                        # 继续执行下面的自动选择逻辑
                    else:
                        raise
            
            # 2. 解析优先级列表
            priority_list = self._parse_priority_list(
                source_priority=source_priority,
                source_exclude=source_exclude
            )
            
            # 3. 按优先级尝试所有数据源
            return await self._get_with_priority(
                operation="get_stock_info",
                code=code,
                priority_list=priority_list,
                fallback=fallback
            )
            
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
    def _parse_priority_list(
        self,
        source_priority: Optional[str] = None,
        source_exclude: Optional[str] = None
    ) -> List[str]:
        """解析优先级列表"""
        # 1. 如果提供了临时优先级，使用临时优先级
        if source_priority:
            priority_list = [s.strip() for s in source_priority.split(",") if s.strip()]
        else:
            # 2. 否则使用系统配置的优先级
            priority_list = getattr(
                settings, 
                'DATA_SOURCE_PRIORITY', 
                'efinance,tushare,akshare,baostock'
            ).split(",")
        
        # 3. 排除指定的数据源
        if source_exclude:
            exclude_list = [s.strip() for s in source_exclude.split(",") if s.strip()]
            priority_list = [s for s in priority_list if s not in exclude_list]
        
        # 4. 过滤不可用的数据源
        available_sources = self.get_available_sources()
        priority_list = [s for s in priority_list if s in available_sources]
        
        if not priority_list:
            logger.warning("没有可用的数据源")
            # 保底：使用任意可用数据源
            priority_list = available_sources
        
        return priority_list
    
    async def _get_with_priority(
        self,
        operation: str,
        code: str,
        priority_list: List[str],
        fallback: bool = True
    ):
        """按优先级尝试所有数据源"""
        last_error = None
        
        for source in priority_list:
            try:
                logger.debug(f"尝试从数据源 {source} 获取：{code}")
                adapter = self.get_adapter(source)
                
                # 根据操作调用对应方法
                if operation == "get_stock_info":
                    result = await adapter.get_stock_info(code)
                elif operation == "get_kline":
                    result = await adapter.get_kline(code)
                # ... 其他操作
                
                if result:
                    logger.info(f"从数据源 {source} 成功获取：{code}")
                    return result
                else:
                    logger.debug(f"数据源 {source} 返回空数据：{code}")
                    
            except Exception as e:
                logger.warning(f"数据源 {source} 失败：{code}: {e}")
                last_error = e
                
                if not fallback:
                    # 不允许故障转移，直接抛出
                    raise
        
        # 所有数据源都失败
        if last_error:
            logger.error(f"所有数据源失败：{code}, 最后错误：{last_error}")
            if fallback:
                return None
            raise last_error
        else:
            logger.warning(f"所有数据源返回空数据：{code}")
            return None
```

### 2.2 API 路由实现

```python
# app/api/v1/endpoints/stock.py

from fastapi import APIRouter, Query
from typing import Optional, List

router = APIRouter()


@router.get("/list", response_model=ResponseModel[List[StockBasicInfo]])
async def get_stock_list(
    source: str = Query("auto", description="指定数据源：auto/efinance/tushare/akshare"),
    source_priority: str = Query("", description="临时优先级列表（逗号分隔），如：efinance,tushare"),
    source_exclude: str = Query("", description="排除的数据源（逗号分隔）"),
    fallback: bool = Query(True, description="是否允许故障转移"),
):
    """获取股票列表（支持多参数控制数据源）"""
    stocks = await data_source_manager.get_stock_list(
        source_type=None if source == "auto" else source,
        source_priority=source_priority if source_priority else None,
        source_exclude=source_exclude if source_exclude else None,
        fallback=fallback
    )
    return ResponseModel(data=stocks)


@router.get("/{code}/kline", response_model=ResponseModel[List[KLineData]])
async def get_kline(
    code: str,
    period: str = Query("daily", description="K 线周期"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    adjust: str = Query("qfq"),
    source: str = Query("auto", description="指定数据源"),
    source_priority: str = Query("", description="临时优先级列表"),
    source_exclude: str = Query("", description="排除的数据源"),
    fallback: bool = Query(True, description="是否允许故障转移"),
):
    """获取 K 线数据（支持多参数控制数据源）"""
    klines = await data_source_manager.get_kline(
        code=code,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
        period=period,
        source_type=None if source == "auto" else source,
        source_priority=source_priority if source_priority else None,
        source_exclude=source_exclude if source_exclude else None,
        fallback=fallback
    )
    return ResponseModel(data=klines)


@router.get("/{code}/realtime", response_model=ResponseModel[dict])
async def get_realtime_quote(
    code: str,
    source: str = Query("auto", description="指定数据源"),
    source_priority: str = Query("", description="临时优先级列表"),
    source_exclude: str = Query("", description="排除的数据源"),
):
    """获取实时行情（支持多参数控制数据源）"""
    quote = await data_source_manager.get_realtime_quote(
        code=code,
        source_type=None if source == "auto" else source,
        source_priority=source_priority if source_priority else None,
        source_exclude=source_exclude if source_exclude else None,
        fallback=True
    )
    
    if not quote:
        return ResponseModel(success=False, code="NOT_FOUND", message="未找到行情")
    
    return ResponseModel(data=quote)
```

---

## 三、使用示例

### 3.1 前端调用示例

```typescript
// frontend/src/services/stock.ts

export const stockApi = {
  /**
   * 获取股票列表
   * @param options 数据源控制选项
   */
  getStockList: (options?: {
    source?: 'auto' | 'efinance' | 'tushare' | 'akshare'
    sourcePriority?: string  // 如："efinance,tushare"
    sourceExclude?: string   // 如："tushare"
    fallback?: boolean
  }) => {
    return api.get('/stock/list', {
      params: {
        source: options?.source || 'auto',
        source_priority: options?.sourcePriority || '',
        source_exclude: options?.sourceExclude || '',
        fallback: options?.fallback ?? true,
      }
    })
  },
  
  /**
   * 获取 K 线数据
   */
  getKline: (code: string, options?: {
    period?: string
    startDate?: string
    endDate?: string
    adjust?: string
    source?: 'auto' | 'efinance' | 'tushare' | 'akshare'
    sourcePriority?: string
    sourceExclude?: string
  }) => {
    return api.get(`/stock/${code}/kline`, {
      params: {
        period: options?.period || 'daily',
        start_date: options?.startDate,
        end_date: options?.endDate,
        adjust: options?.adjust || 'qfq',
        source: options?.source || 'auto',
        source_priority: options?.sourcePriority || '',
        source_exclude: options?.sourceExclude || '',
      },
      timeout: 120000,
    })
  },
}

// 使用示例

// 1. 默认自动选择
const stocks1 = await stockApi.getStockList()

// 2. 临时指定优先级：优先 efinance，失败则 tushare
const stocks2 = await stockApi.getStockList({
  sourcePriority: 'efinance,tushare'
})

// 3. 排除 tushare（积分不足时）
const stocks3 = await stockApi.getStockList({
  sourcePriority: 'efinance,akshare',
  sourceExclude: 'tushare'
})

// 4. 强制使用 efinance，失败则报错
const stocks4 = await stockApi.getStockList({
  source: 'efinance',
  fallback: false
})

// 5. 获取 K 线，优先使用 akshare（历史数据更全）
const klines = await stockApi.getKline('600519', {
  period: 'daily',
  sourcePriority: 'akshare,efinance'
})
```

### 3.2 cURL 示例

```bash
# 1. 默认自动选择
curl http://localhost:8000/api/v1/stock/list

# 2. 临时指定优先级
curl "http://localhost:8000/api/v1/stock/list?source_priority=efinance,tushare,akshare"

# 3. 排除某些数据源
curl "http://localhost:8000/api/v1/stock/list?source_priority=efinance,akshare&source_exclude=tushare"

# 4. 强制使用特定数据源（不允许故障转移）
curl "http://localhost:8000/api/v1/stock/list?source=efinance&fallback=false"

# 5. 获取 K 线，优先使用 akshare
curl "http://localhost:8000/api/v1/stock/600519/kline?source_priority=akshare,efinance"
```

---

## 四、高级功能

### 4.1 智能推荐优先级

```python
# app/adapters/smart_router.py

class SmartDataSourceRouter:
    def get_recommended_priority(
        self,
        operation: str,
        time_of_day: Optional[str] = None
    ) -> List[str]:
        """
        根据操作类型和时间段推荐优先级
        
        Args:
            operation: 操作类型（kline/realtime/financial 等）
            time_of_day: 时间段（trading/off_trading/night）
        
        Returns:
            推荐的优先级列表
        """
        # 根据操作类型推荐
        if operation == "realtime":
            # 实时行情：优先 efinance（速度快）
            recommended = ["efinance", "tushare", "akshare"]
        elif operation == "kline":
            # K 线数据：优先 akshare（历史数据全）
            recommended = ["akshare", "efinance", "tushare"]
        elif operation == "financial":
            # 财务数据：优先 tushare（质量高）
            recommended = ["tushare", "efinance", "akshare"]
        else:
            # 默认优先级
            recommended = ["efinance", "tushare", "akshare"]
        
        # 根据时间段调整
        if time_of_day == "night":
            # 夜间：降低 tushare 优先级（可能维护）
            recommended = [s for s in recommended if s != "tushare"] + ["tushare"]
        
        return recommended


# API 路由
@router.get("/list/recommended", response_model=ResponseModel[dict])
async def get_stock_list_with_recommended_source():
    """使用推荐的数据源优先级获取股票列表"""
    router = SmartDataSourceRouter()
    
    # 获取推荐优先级
    recommended = router.get_recommended_priority(
        operation="get_stock_list",
        time_of_day="trading"
    )
    
    stocks = await data_source_manager.get_stock_list(
        source_priority=",".join(recommended)
    )
    
    return ResponseModel(
        data=stocks,
        message=f"使用推荐优先级：{recommended}"
    )
```

### 4.2 数据源性能统计

```python
# app/api/v1/endpoints/data_source.py

@router.get("/performance-stats", response_model=ResponseModel[dict])
async def get_performance_stats():
    """获取数据源性能统计（用于智能推荐）"""
    stats = {}
    
    for source_name in data_source_manager.get_available_sources():
        adapter = data_source_manager.get_adapter(source_name)
        
        if hasattr(adapter, 'get_stats'):
            adapter_stats = adapter.get_stats()
            
            stats[source_name] = {
                "total_requests": adapter_stats.get("total_requests", 0),
                "success_rate": adapter_stats.get("success_rate", 0),
                "avg_response_time": adapter_stats.get("avg_response_time", 0),
                "cache_hit_rate": adapter_stats.get("cache_hit_rate", 0),
            }
    
    # 计算推荐优先级
    router = SmartDataSourceRouter()
    recommended = router.get_recommended_priority("auto")
    
    return ResponseModel(
        data={
            "stats": stats,
            "recommended_priority": recommended,
            "recommendation_reason": "基于响应时间和成功率的综合评分"
        }
    )
```

---

## 五、前端 UI 组件

### 5.1 数据源优先级配置组件

```typescript
// frontend/src/components/DataSourcePriorityConfig.tsx

import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { dataSourceApi } from '../services/dataSource'

interface Props {
  onPriorityChange?: (priority: string) => void
}

export const DataSourcePriorityConfig: React.FC<Props> = ({ onPriorityChange }) => {
  const [priority, setPriority] = useState('efinance,tushare,akshare')
  const [exclude, setExclude] = useState('')
  
  const switchMutation = useMutation({
    mutationFn: (config: { priority: string; exclude: string }) =>
      dataSourceApi.switchSource(config.priority, config.exclude),
  })
  
  const handleApply = () => {
    switchMutation.mutate({ priority, exclude })
    onPriorityChange?.(priority)
  }
  
  return (
    <div className="data-source-config">
      <h3>数据源优先级配置</h3>
      
      <div className="form-group">
        <label>优先级列表（逗号分隔）：</label>
        <input
          type="text"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          placeholder="efinance,tushare,akshare"
        />
        <small>排在前面的数据源会优先使用</small>
      </div>
      
      <div className="form-group">
        <label>排除的数据源：</label>
        <input
          type="text"
          value={exclude}
          onChange={(e) => setExclude(e.target.value)}
          placeholder="tushare"
        />
        <small>这些数据源将不会被使用</small>
      </div>
      
      <button onClick={handleApply} disabled={switchMutation.isPending}>
        应用配置
      </button>
      
      {switchMutation.isSuccess && (
        <div className="success-message">配置已更新</div>
      )}
    </div>
  )
}
```

### 5.2 高级搜索组件

```typescript
// frontend/src/components/AdvancedStockSearch.tsx

import React, { useState } from 'react'

interface SearchOptions {
  keyword: string
  sourcePriority?: string
  sourceExclude?: string
}

export const AdvancedStockSearch: React.FC = () => {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [options, setOptions] = useState<SearchOptions>({
    keyword: '',
    sourcePriority: 'efinance,tushare',
    sourceExclude: '',
  })
  
  const handleSearch = async () => {
    const results = await stockApi.getStockList({
      sourcePriority: options.sourcePriority,
      sourceExclude: options.sourceExclude,
    })
    
    // 过滤结果
    const filtered = results.data.filter(stock =>
      stock.name.includes(options.keyword) ||
      stock.code.includes(options.keyword)
    )
    
    // 显示结果
  }
  
  return (
    <div className="advanced-search">
      <input
        type="text"
        placeholder="搜索股票..."
        value={options.keyword}
        onChange={(e) => setOptions({ ...options, keyword: e.target.value })}
      />
      
      <button onClick={() => setShowAdvanced(!showAdvanced)}>
        {showAdvanced ? '隐藏高级选项' : '高级选项'}
      </button>
      
      {showAdvanced && (
        <div className="advanced-options">
          <div className="form-group">
            <label>数据源优先级：</label>
            <select
              value={options.sourcePriority}
              onChange={(e) => setOptions({ ...options, sourcePriority: e.target.value })}
            >
              <option value="efinance,tushare,akshare">efinance → tushare → akshare</option>
              <option value="akshare,efinance,tushare">akshare → efinance → tushare</option>
              <option value="tushare,efinance,akshare">tushare → efinance → akshare</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>排除数据源：</label>
            <div>
              <label>
                <input
                  type="checkbox"
                  checked={options.sourceExclude?.includes('tushare')}
                  onChange={(e) => {
                    const exclude = e.target.checked
                      ? 'tushare'
                      : options.sourceExclude?.replace('tushare', '')
                    setOptions({ ...options, sourceExclude: exclude })
                  }}
                />
                排除 tushare（积分不足时）
              </label>
            </div>
          </div>
        </div>
      )}
      
      <button onClick={handleSearch}>搜索</button>
    </div>
  )
}
```

---

## 六、配置管理

### 6.1 环境变量

```bash
# .env

# 默认数据源优先级（逗号分隔）
DATA_SOURCE_PRIORITY=efinance,tushare,akshare,baostock

# 默认数据源
DEFAULT_DATA_SOURCE=auto

# 智能路由策略
ROUTING_STRATEGY=auto

# 是否允许故障转移
ALLOW_FALLBACK=true

# 数据源超时时间（秒）
SOURCE_TIMEOUT=10

# 健康检查间隔（秒）
HEALTH_CHECK_INTERVAL=60
```

### 6.2 用户偏好设置（前端）

```typescript
// frontend/src/store/slices/dataSourceSlice.ts

interface DataSourceState {
  // 用户自定义优先级
  userPriority: string | null
  
  // 排除的数据源
  excludedSources: string[]
  
  // 是否允许故障转移
  allowFallback: boolean
  
  // 当前使用的数据源
  currentSource: string | null
  
  // 数据源健康状态
  healthStatus: Record<string, DataSourceHealth>
}

const dataSourceSlice = createSlice({
  name: 'dataSource',
  initialState: {
    userPriority: null,
    excludedSources: [],
    allowFallback: true,
    currentSource: null,
    healthStatus: {},
  },
  reducers: {
    setUserPriority: (state, action: PayloadAction<string>) => {
      state.userPriority = action.payload
    },
    toggleExcludeSource: (state, action: PayloadAction<string>) => {
      const source = action.payload
      if (state.excludedSources.includes(source)) {
        state.excludedSources = state.excludedSources.filter(s => s !== source)
      } else {
        state.excludedSources.push(source)
      }
    },
    setAllowFallback: (state, action: PayloadAction<boolean>) => {
      state.allowFallback = action.payload
    },
  },
})
```

---

## 七、测试用例

### 7.1 单元测试

```python
# tests/test_source_priority.py

async def test_source_priority_parameter():
    """测试 source_priority 参数"""
    # 优先使用 efinance，失败则 tushare
    result = await data_source_manager.get_stock_info(
        code="600519",
        source_priority="efinance,tushare"
    )
    assert result is not None


async def test_source_exclude_parameter():
    """测试 source_exclude 参数"""
    # 排除 tushare
    result = await data_source_manager.get_stock_info(
        code="600519",
        source_exclude="tushare"
    )
    assert result is not None


async def test_source_force_no_fallback():
    """测试强制使用数据源且不允许故障转移"""
    # 强制使用不存在的源，且不允许故障转移
    with pytest.raises(Exception):
        await data_source_manager.get_stock_info(
            code="600519",
            source="nonexistent",
            fallback=False
        )
```

---

## 八、总结

### 8.1 参数优势

✅ **灵活性高** - 支持多种参数组合控制  
✅ **向后兼容** - 默认值不影响现有代码  
✅ **用户友好** - 简单的逗号分隔语法  
✅ **功能强大** - 支持优先级、排除、故障转移等  

### 8.2 使用场景

| 场景 | 参数组合 | 说明 |
|------|---------|------|
| 默认自动 | 不传参数 | 使用系统配置优先级 |
| 临时优先级 | `source_priority=efinance,tushare` | 临时调整优先级 |
| 排除数据源 | `source_exclude=tushare` | 排除特定数据源 |
| 强制使用 | `source=efinance&fallback=false` | 强制使用，失败报错 |
| 组合使用 | `source_priority=efinance,akshare&source_exclude=tushare` | 灵活组合 |

---

**文档版本**：v1.0  
**创建日期**：2026-03-18  
**维护者**：Quant 团队
