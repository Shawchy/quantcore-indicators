# 统一数据适配器 API 参考

**版本:** 1.0  
**更新日期:** 2026-03-19

---

## 📚 目录

1. [快速开始](#快速开始)
2. [核心类](#核心类)
3. [使用示例](#使用示例)
4. [配置选项](#配置选项)

---

## 🚀 快速开始

### 安装依赖
```bash
pip install pandas pandas-ta sqlalchemy pydantic efinance baostock
```

### 基本用法
```python
from app.adapters.unified_adapter import EFinanceUnifiedAdapter

adapter = EFinanceUnifiedAdapter()
await adapter.initialize()

klines = await adapter.get_unified_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-03-31"
)
```

---

## 🏗️ 核心类

### UnifiedDataAdapter

统一数据适配器基类（抽象类）

#### 属性
- `source_type: DataSourceType` - 数据源类型

#### 方法

##### `get_unified_kline()`
获取统一格式 K 线数据

```python
async def get_unified_kline(
    code: str,
    start_date: str,
    end_date: str,
    adjust_type: str = "qfq",
    save_to_storage: bool = True,
    calculate_indicators: bool = False
) -> List[UnifiedKLine]
```

**参数:**
- `code` - 股票代码（如 "600000"）
- `start_date` - 开始日期（"YYYY-MM-DD"）
- `end_date` - 结束日期（"YYYY-MM-DD"）
- `adjust_type` - 复权类型（"qfq"前复权，"hfq"后复权，"qfq"不复权）
- `save_to_storage` - 是否保存到存储（默认 True）
- `calculate_indicators` - 是否计算技术指标（默认 False）

**返回:**
- `List[UnifiedKLine]` - 统一格式 K 线数据列表

**示例:**
```python
klines = await adapter.get_unified_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-03-31",
    calculate_indicators=True
)
```

##### `get_unified_kline_batch()`
批量获取 K 线数据

```python
async def get_unified_kline_batch(
    codes: List[str],
    start_date: str,
    end_date: str,
    adjust_type: str = "qfq",
    save_to_storage: bool = True,
    max_concurrent: int = 3
) -> Dict[str, List[UnifiedKLine]]
```

**参数:**
- `codes` - 股票代码列表（如 ["600000", "000001"]）
- `start_date` - 开始日期
- `end_date` - 结束日期
- `adjust_type` - 复权类型
- `save_to_storage` - 是否保存到存储
- `max_concurrent` - 最大并发数（默认 3）

**返回:**
- `Dict[str, List[UnifiedKLine]]` - 字典：{code: [KLineData]}

**示例:**
```python
results = await adapter.get_unified_kline_batch(
    codes=["600000", "000001", "300750"],
    start_date="2024-01-01",
    end_date="2024-03-31",
    max_concurrent=2
)
```

##### `validate_across_sources()`
跨数据源一致性校验

```python
async def validate_across_sources(
    code: str,
    date: str,
    other_adapter: 'UnifiedDataAdapter'
) -> Dict[str, Any]
```

**参数:**
- `code` - 股票代码
- `date` - 校验日期
- `other_adapter` - 另一个数据源适配器

**返回:**
- `Dict[str, Any]` - 校验结果（包含一致性比率、评分等）

**示例:**
```python
ef_adapter = EFinanceUnifiedAdapter()
ak_adapter = AkShareUnifiedAdapter()

result = await ef_adapter.validate_across_sources(
    code="600000",
    date="2024-03-19",
    other_adapter=ak_adapter
)

print(f"一致性：{result['consistency_ratio']:.2%}")
```

##### `check_health()`
检查数据源健康状态

```python
async def check_health() -> Dict[str, Any]
```

**返回:**
- `Dict[str, Any]` - 健康状态（status, latency, error_rate 等）

**示例:**
```python
health = await adapter.check_health()
print(f"状态：{health.get('status')}")
```

---

### UnifiedKLine

统一 K 线数据模型

#### 字段
- `code: str` - 股票代码
- `date: str` - 日期
- `open: float` - 开盘价
- `high: float` - 最高价
- `low: float` - 最低价
- `close: float` - 收盘价
- `pre_close: Optional[float]` - 昨收价
- `volume: float` - 成交量
- `amount: Optional[float]` - 成交额
- `turnover_rate: Optional[float]` - 换手率
- `adjust_type: AdjustType` - 复权类型
- `source: DataSourceType` - 数据源
- `quality_score: float` - 质量评分

**示例:**
```python
kline = UnifiedKLine(
    code="600000",
    date="2024-03-19",
    open=10.5,
    high=10.8,
    low=10.4,
    close=10.7,
    volume=5000000,
    amount=52500000,
    turnover_rate=2.5
)
```

---

### DataSourceFactory

数据源工厂类

#### 方法

##### `get_unified_adapter()`
获取统一适配器

```python
@classmethod
def get_unified_adapter(cls, source_type: Optional[str] = None) -> UnifiedDataAdapter
```

**参数:**
- `source_type` - 数据源类型（"efinance", "akshare", "baostock", "tickflow"）

**返回:**
- `UnifiedDataAdapter` - 统一适配器实例

**示例:**
```python
await DataSourceFactory.initialize()
adapter = DataSourceFactory.get_unified_adapter("efinance")
```

##### `get_adapter()`
获取普通适配器（向后兼容）

```python
@classmethod
def get_adapter(cls, source_type: Optional[str] = None) -> BaseDataAdapter
```

**示例:**
```python
adapter = DataSourceFactory.get_adapter("efinance")
```

---

## 📖 使用示例

### 示例 1: 基本 K 线获取

```python
from app.adapters.unified_adapter import EFinanceUnifiedAdapter

adapter = EFinanceUnifiedAdapter()
await adapter.initialize()

klines = await adapter.get_unified_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-03-31"
)

for kline in klines:
    print(f"{kline.date}: 开{kline.open} 收{kline.close}")
```

### 示例 2: 带技术指标

```python
klines = await adapter.get_unified_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-03-31",
    calculate_indicators=True
)

# 指标数据已附加到 kline 对象
# 可通过 DataFrame 访问
df = adapter._klines_to_dataframe(klines)
print(df.columns)  # 包含 ma5, ma10, macd 等指标列
```

### 示例 3: 批量处理

```python
codes = ["600000", "000001", "300750"]
results = await adapter.get_unified_kline_batch(
    codes=codes,
    start_date="2024-01-01",
    end_date="2024-03-31",
    max_concurrent=2
)

for code, klines in results.items():
    print(f"{code}: {len(klines)} 条")
```

### 示例 4: 跨数据源校验

```python
from app.adapters.unified_adapter import EFinanceUnifiedAdapter, AkShareUnifiedAdapter

ef_adapter = EFinanceUnifiedAdapter()
ak_adapter = AkShareUnifiedAdapter()

result = await ef_adapter.validate_across_sources(
    code="600000",
    date="2024-03-19",
    other_adapter=ak_adapter
)

print(f"一致性：{result['consistency_ratio']:.2%}")
print(f"评分：{result['score']:.2f}")
print(f"建议：{result['recommendations']}")
```

### 示例 5: 使用工厂

```python
from app.adapters.factory import DataSourceFactory

# 初始化
await DataSourceFactory.initialize()

# 获取统一适配器
adapter = DataSourceFactory.get_unified_adapter("efinance")

# 或使用普通适配器
normal_adapter = DataSourceFactory.get_adapter("efinance")
```

---

## ⚙️ 配置选项

### 存储配置

```python
STORAGE_CONFIG = {
    "hot_threshold_days": 90,  # 热数据阈值（天）
    "parquet_base_dir": "./data/parquet",  # Parquet 基础目录
    "cache_ttl": {
        "realtime": 60,    # 实时数据缓存 TTL
        "kline": 300,      # K 线数据缓存 TTL
        "indicators": 300, # 指标数据缓存 TTL
    }
}
```

### 指标配置

```python
INDICATORS_CONFIG = {
    "prefer_talib": True,   # 优先使用 TA-Lib
    "use_pandas_ta": True,  # 使用 pandas-ta
}
```

### 数据源配置

```python
DATA_SOURCE_CONFIG = {
    "health_check_interval": 300,  # 健康检查间隔（秒）
    "consistency_tolerance": 0.01, # 一致性容差率（1%）
    "priority": ["efinance", "akshare", "baostock", "tickflow", "tushare"],
}
```

---

## 🔧 高级功能

### 自定义存储路由

```python
from app.storage.storage_router import StorageRouter

router = StorageRouter(hot_threshold_days=60)  # 自定义 60 天阈值

await router.save_kline(
    code="600000",
    kline_data=kline_dict,
    adjust_type="qfq"
)
```

### 自定义指标计算

```python
from app.services.indicators_manager import IndicatorsManager

manager = IndicatorsManager(prefer_talib=False)

# 计算单一指标
df = manager.calculate_ma(df, periods=[5, 10, 20])
df = manager.calculate_macd(df)

# 计算所有指标
df = manager.calculate_all_indicators(df)
```

### 数据版本管理

```python
from app.storage.data_versioning import DataVersionManager

version_mgr = DataVersionManager()

# 记录版本
await version_mgr.record_change(
    code="600000",
    change_type="update",
    description="更新 K 线数据"
)

# 查询历史
history = await version_mgr.get_history("600000")
```

---

## ❓ 常见问题

### Q: 如何切换数据源？
A: 使用 `DataSourceFactory.get_unified_adapter(source_type)`

### Q: 指标计算需要多少数据？
A: 建议至少 30 条，MACD 等指标需要更多数据

### Q: 如何禁用自动存储？
A: 设置 `save_to_storage=False`

### Q: 并发数设置多少合适？
A: 默认 3，可根据网络和数据源负载调整（建议 1-5）

---

## 📞 支持

- **文档:** `/backend/API_REFERENCE.md`
- **测试:** `/backend/test_unified_integration.py`
- **示例:** `/backend/integration_example.py`

---

**文档版本:** 1.0  
**最后更新:** 2026-03-19
