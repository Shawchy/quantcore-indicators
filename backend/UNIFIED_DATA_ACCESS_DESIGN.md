# 统一数据源调用参数与数据清洗方案

## 📋 问题分析

### 当前 4 个数据源的参数差异

#### 1️⃣ K 线数据接口对比

| 数据源 | 方法签名 | 参数差异 | 数据字段差异 |
|--------|---------|---------|-------------|
| **EFinance** | `get_kline(code, start_date, end_date, klt, fqt, market_type, adjust)` | ✅ 支持周期 (klt)<br>✅ 支持复权 (fqt)<br>✅ 支持市场类型 | ✅ 字段最全<br>✅ 包含 turnover_rate |
| **AkShare** | `get_kline(code, start_date, end_date, adjust)` | ❌ 不支持周期<br>❌ 不支持市场类型<br>✅ 支持复权 | ⚠️ 字段较少<br>❌ 无 turnover_rate |
| **Baostock** | `get_kline(code, start_date, end_date, adjust)` | ❌ 不支持周期<br>❌ 不支持市场类型<br>✅ 支持复权 | ⚠️ 字段较少<br>❌ 无 turnover_rate |
| **TickFlow** | `get_kline(code, start_date, end_date, adjust, period)` | ✅ 支持周期 (period)<br>❌ 不支持市场类型<br>✅ 支持复权 | ✅ 字段较全<br>✅ 包含 turnover_rate |

#### 2️⃣ 主要问题

1. **参数不统一**
   - EFinance 使用 `klt` (101=日线)
   - TickFlow 使用 `period` ("daily")
   - AkShare/Baostock 不支持周期

2. **复权参数不统一**
   - EFinance 使用 `fqt` (1=前复权)
   - 其他使用 `adjust` ("qfq")

3. **数据字段不统一**
   - 有的有 `turnover_rate`
   - 有的有 `amount`
   - 日期格式不统一 (YYYYMMDD vs YYYY-MM-DD)

4. **错误处理不统一**
   - 有的返回空列表
   - 有的抛出异常
   - 有的返回 None

---

## 🎯 设计方案

### 方案概述

创建一个**统一的数据访问层 (Unified Data Access Layer)**，包含：

1. **统一参数规范** - 标准化的调用参数
2. **参数转换器** - 将统一参数转换为各数据源特定参数
3. **数据清洗器** - 清洗和标准化返回数据
4. **数据验证器** - 验证数据完整性和准确性

### 架构图

```
┌─────────────────────────────────────────────────┐
│          业务层 (Service Layer)                  │
│  stock_service.get_kline(code, start, end)      │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│      统一数据访问层 (Unified Access Layer)       │
│  ┌─────────────────────────────────────────┐   │
│  │  1. 统一参数对象 (UnifiedParams)         │   │
│  │  2. 参数转换器 (ParameterConverter)      │   │
│  │  3. 数据清洗器 (DataCleaner)             │   │
│  │  4. 数据验证器 (DataValidator)           │   │
│  └─────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│EFinance  │ │ AkShare  │ │Baostock  │ │TickFlow  │
│ Adapter  │ │ Adapter  │ │ Adapter  │ │ Adapter  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## 📊 详细实现

### 1️⃣ 统一参数对象

```python
# app/adapters/unified_params.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum

class KlinePeriod(str, Enum):
    """K 线周期枚举"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    MINUTE_60 = "60m"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class AdjustType(str, Enum):
    """复权类型"""
    NONE = "none"      # 不复权
    FORWARD = "forward"  # 前复权
    BACKWARD = "backward"  # 后复权

class MarketType(str, Enum):
    """市场类型"""
    A_SHARE = "a_share"
    HK_SHARE = "hk_share"
    US_SHARE = "us_share"
    CN_FUND = "cn_fund"
    CN_BOND = "cn_bond"

@dataclass
class UnifiedKlineParams:
    """统一 K 线查询参数"""
    code: str                          # 股票代码
    start_date: Optional[str] = None   # 开始日期 (YYYY-MM-DD)
    end_date: Optional[str] = None     # 结束日期 (YYYY-MM-DD)
    period: KlinePeriod = KlinePeriod.DAILY  # 周期
    adjust: AdjustType = AdjustType.FORWARD  # 复权
    market_type: MarketType = MarketType.A_SHARE  # 市场类型
    include_fields: Optional[list] = None  # 包含的字段（None=全部）
    exclude_fields: Optional[list] = None  # 排除的字段
    limit: Optional[int] = None        # 最大返回条数
    timeout: int = 30                  # 超时时间（秒）
    retry_count: int = 3              # 重试次数
    use_cache: bool = True            # 是否使用缓存
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'period': self.period.value,
            'adjust': self.adjust.value,
            'market_type': self.market_type.value,
            'include_fields': self.include_fields,
            'exclude_fields': self.exclude_fields,
            'limit': self.limit,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'use_cache': self.use_cache
        }
```

### 2️⃣ 参数转换器

```python
# app/adapters/parameter_converter.py
from typing import Dict, Any
from .unified_params import UnifiedKlineParams, KlinePeriod, AdjustType

class ParameterConverter:
    """参数转换器 - 将统一参数转换为各数据源特定参数"""
    
    @staticmethod
    def to_efinance_params(unified: UnifiedKlineParams) -> Dict[str, Any]:
        """转换为 EFinance 参数"""
        # 周期转换
        klt_map = {
            KlinePeriod.MINUTE_1: 1,
            KlinePeriod.MINUTE_5: 5,
            KlinePeriod.MINUTE_15: 15,
            KlinePeriod.MINUTE_30: 30,
            KlinePeriod.MINUTE_60: 60,
            KlinePeriod.DAILY: 101,
            KlinePeriod.WEEKLY: 102,
            KlinePeriod.MONTHLY: 103,
        }
        
        # 复权转换
        fqt_map = {
            AdjustType.NONE: 0,
            AdjustType.FORWARD: 1,
            AdjustType.BACKWARD: 2,
        }
        
        # 市场类型转换
        market_map = {
            MarketType.A_SHARE: None,  # EFinance 默认 A 股
            MarketType.HK_SHARE: 'Hongkong',
            MarketType.US_SHARE: 'US_stock',
        }
        
        return {
            'code': unified.code,
            'start_date': unified.start_date,
            'end_date': unified.end_date,
            'klt': klt_map.get(unified.period, 101),
            'fqt': fqt_map.get(unified.adjust, 1),
            'market_type': market_map.get(unified.market_type),
            'timeout': unified.timeout,
            'retry_count': unified.retry_count,
        }
    
    @staticmethod
    def to_akshare_params(unified: UnifiedKlineParams) -> Dict[str, Any]:
        """转换为 AkShare 参数"""
        # AkShare 不支持周期，需要特殊处理
        if unified.period not in [KlinePeriod.DAILY, None]:
            raise ValueError(f"AkShare 不支持 {unified.period} 周期")
        
        # 复权转换
        adjust_map = {
            AdjustType.NONE: "",
            AdjustType.FORWARD: "qfq",
            AdjustType.BACKWARD: "hfq",
        }
        
        return {
            'code': unified.code,
            'start_date': unified.start_date,
            'end_date': unified.end_date,
            'adjust': adjust_map.get(unified.adjust, "qfq"),
            'timeout': unified.timeout,
            'retry_count': unified.retry_count,
        }
    
    @staticmethod
    def to_baostock_params(unified: UnifiedKlineParams) -> Dict[str, Any]:
        """转换为 Baostock 参数"""
        # Baostock 不支持周期
        if unified.period not in [KlinePeriod.DAILY, None]:
            raise ValueError(f"Baostock 不支持 {unified.period} 周期")
        
        # 复权转换
        adjust_map = {
            AdjustType.NONE: "0",
            AdjustType.FORWARD: "1",
            AdjustType.BACKWARD: "2",
        }
        
        return {
            'code': unified.code,
            'start_date': unified.start_date,
            'end_date': unified.end_date,
            'adjust': adjust_map.get(unified.adjust, "1"),
            'timeout': unified.timeout,
            'retry_count': unified.retry_count,
        }
    
    @staticmethod
    def to_tickflow_params(unified: UnifiedKlineParams) -> Dict[str, Any]:
        """转换为 TickFlow 参数"""
        # 周期转换
        period_map = {
            KlinePeriod.MINUTE_1: '1m',
            KlinePeriod.MINUTE_5: '5m',
            KlinePeriod.DAILY: 'daily',
            KlinePeriod.WEEKLY: 'weekly',
            KlinePeriod.MONTHLY: 'monthly',
        }
        
        return {
            'code': unified.code,
            'start_date': unified.start_date,
            'end_date': unified.end_date,
            'period': period_map.get(unified.period, 'daily'),
            'adjust': unified.adjust.value,
            'timeout': unified.timeout,
            'retry_count': unified.retry_count,
        }
```

### 3️⃣ 数据清洗器

```python
# app/adapters/data_cleaner.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from .unified_params import UnifiedKlineParams
from app.adapters.base import KLineData

class DataCleaner:
    """数据清洗器 - 清洗和标准化各数据源返回的数据"""
    
    # 标准字段列表
    STANDARD_FIELDS = [
        'code', 'date', 'open', 'high', 'low', 'close',
        'volume', 'amount', 'turnover_rate', 'pre_close'
    ]
    
    @staticmethod
    def clean_date(date_str: str) -> str:
        """清洗日期格式，统一为 YYYY-MM-DD"""
        if not date_str:
            return ""
        
        # 去除空格和特殊字符
        date_str = str(date_str).strip()
        
        # 尝试多种格式
        formats = [
            '%Y%m%d',      # 20260327
            '%Y-%m-%d',    # 2026-03-27
            '%Y/%m/%d',    # 2026/03/27
            '%Y%m%d%H%M%S', # 20260327150000
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # 如果都无法解析，返回原值
        return date_str
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            value = value.strip().replace(',', '')
            if value == '' or value == '-' or value.lower() == 'nan':
                return default
            try:
                return float(value)
            except ValueError:
                return default
        return default
    
    @staticmethod
    def clean_kline_data(
        raw_data: List[Dict[str, Any]],
        params: UnifiedKlineParams,
        source_type: str
    ) -> List[KLineData]:
        """清洗 K 线数据"""
        cleaned = []
        
        for row in raw_data:
            try:
                # 标准化字段
                kline = KLineData(
                    code=str(row.get('code', params.code)),
                    date=DataCleaner.clean_date(row.get('date', '')),
                    open=DataCleaner.safe_float(row.get('open', 0)),
                    high=DataCleaner.safe_float(row.get('high', 0)),
                    low=DataCleaner.safe_float(row.get('low', 0)),
                    close=DataCleaner.safe_float(row.get('close', 0)),
                    volume=DataCleaner.safe_float(row.get('volume', 0)),
                    amount=DataCleaner.safe_float(row.get('amount'), None),
                    turnover_rate=DataCleaner.safe_float(row.get('turnover_rate'), None),
                    pre_close=DataCleaner.safe_float(row.get('pre_close'), None)
                )
                
                # 字段过滤
                if params.include_fields:
                    # 只保留指定字段
                    filtered = {k: v for k, v in kline.__dict__.items() 
                               if k in params.include_fields}
                    kline = KLineData(**filtered)
                
                elif params.exclude_fields:
                    # 排除指定字段
                    filtered = {k: v for k, v in kline.__dict__.items() 
                               if k not in params.exclude_fields}
                    kline = KLineData(**filtered)
                
                cleaned.append(kline)
                
            except Exception as e:
                logger.warning(f"清洗 K 线数据失败：{row}, 错误：{e}")
                continue
        
        # 按日期排序
        cleaned.sort(key=lambda x: x.date)
        
        # 应用 limit
        if params.limit and len(cleaned) > params.limit:
            cleaned = cleaned[-params.limit:]
        
        return cleaned
    
    @staticmethod
    def validate_kline_data(klines: List[KLineData]) -> tuple[bool, List[str]]:
        """验证 K 线数据质量"""
        errors = []
        
        if not klines:
            errors.append("数据为空")
            return False, errors
        
        # 检查必要字段
        required_fields = ['code', 'date', 'open', 'high', 'low', 'close', 'volume']
        for i, kline in enumerate(klines[:10]):  # 只检查前 10 条
            for field in required_fields:
                value = getattr(kline, field, None)
                if value is None or value == '':
                    errors.append(f"第{i}条数据缺少必要字段：{field}")
        
        # 检查价格合理性
        for i, kline in enumerate(klines[:100]):
            if kline.high < kline.low:
                errors.append(f"第{i}条数据最高价 < 最低价")
            if kline.close < 0:
                errors.append(f"第{i}条数据收盘价为负")
        
        # 检查日期连续性（日线数据）
        if len(klines) > 1:
            dates = [k.date for k in klines]
            if len(dates) != len(set(dates)):
                errors.append("存在重复日期")
        
        is_valid = len(errors) == 0
        return is_valid, errors
```

### 4️⃣ 统一数据访问层

```python
# app/adapters/unified_adapter.py
from typing import List, Dict, Any, Optional, Type
from loguru import logger
from .unified_params import UnifiedKlineParams, AdjustType
from .parameter_converter import ParameterConverter
from .data_cleaner import DataCleaner
from .base import KLineData, DataSourceType
from .factory import DataSourceFactory

class UnifiedDataAdapter:
    """统一数据访问适配器"""
    
    def __init__(self, default_source: DataSourceType = DataSourceType.EFINANCE):
        self.default_source = default_source
        self.factory = DataSourceFactory()
        self.converter = ParameterConverter()
        self.cleaner = DataCleaner()
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily",
        adjust: str = "forward",
        market_type: str = "a_share",
        limit: Optional[int] = None,
        source_type: Optional[DataSourceType] = None,
        use_cache: bool = True
    ) -> List[KLineData]:
        """
        统一 K 线数据获取接口
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: 周期 (1m/5m/15m/30m/60m/daily/weekly/monthly)
            adjust: 复权 (none/forward/backward)
            market_type: 市场类型 (a_share/hk_share/us_share)
            limit: 最大返回条数
            source_type: 数据源类型（None=自动选择）
            use_cache: 是否使用缓存
        
        Returns:
            标准化的 K 线数据列表
        """
        # 创建统一参数对象
        params = UnifiedKlineParams(
            code=code,
            start_date=start_date,
            end_date=end_date,
            period=period,
            adjust=adjust,
            market_type=market_type,
            limit=limit,
            use_cache=use_cache
        )
        
        # 选择数据源
        if source_type is None:
            source_type = self._select_best_source(params)
        
        logger.info(f"获取 K 线数据：{code}, 数据源：{source_type.value}")
        
        try:
            # 获取适配器
            adapter = self.factory.get_adapter(source_type)
            
            # 转换参数
            if source_type == DataSourceType.EFINANCE:
                adapter_params = self.converter.to_efinance_params(params)
                raw_data = await adapter.get_kline(**adapter_params)
            elif source_type == DataSourceType.AKSHARE:
                adapter_params = self.converter.to_akshare_params(params)
                raw_data = await adapter.get_kline(**adapter_params)
            elif source_type == DataSourceType.BAOSTOCK:
                adapter_params = self.converter.to_baostock_params(params)
                raw_data = await adapter.get_kline(**adapter_params)
            elif source_type == DataSourceType.TICKFLOW:
                adapter_params = self.converter.to_tickflow_params(params)
                raw_data = await adapter.get_kline(**adapter_params)
            else:
                raise ValueError(f"不支持的数据源：{source_type}")
            
            # 数据清洗
            cleaned_data = self.cleaner.clean_kline_data(
                raw_data=[k.__dict__ for k in raw_data],
                params=params,
                source_type=source_type.value
            )
            
            # 数据验证
            is_valid, errors = self.cleaner.validate_kline_data(cleaned_data)
            if not is_valid:
                logger.warning(f"K 线数据验证失败：{errors}")
            
            logger.info(f"获取 K 线数据成功：{len(cleaned_data)}条")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"获取 K 线数据失败：{e}")
            
            # 自动故障转移
            if source_type != self.default_source:
                logger.info(f"尝试故障转移到 {self.default_source.value}")
                return await self.get_kline(
                    code=code,
                    start_date=start_date,
                    end_date=end_date,
                    period=period,
                    adjust=adjust,
                    source_type=self.default_source
                )
            
            return []
    
    def _select_best_source(self, params: UnifiedKlineParams) -> DataSourceType:
        """根据参数自动选择最优数据源"""
        
        # 1. 根据周期选择
        if params.period not in ['daily', None]:
            # 非日线周期，优先 TickFlow 或 EFinance
            return DataSourceType.TICKFLOW
        
        # 2. 根据市场类型选择
        if params.market_type == 'hk_share':
            return DataSourceType.TICKFLOW
        elif params.market_type == 'us_share':
            return DataSourceType.TICKFLOW
        
        # 3. 默认使用 EFinance
        return self.default_source
```

### 5️⃣ 使用示例

```python
# 使用示例
from app.adapters.unified_adapter import UnifiedDataAdapter
from app.adapters.base import DataSourceType

# 初始化统一适配器
unified = UnifiedDataAdapter()

# 示例 1: 获取日线数据（前复权）
klines = await unified.get_kline(
    code="600519",
    start_date="2023-01-01",
    end_date="2026-03-27",
    period="daily",
    adjust="forward"
)

# 示例 2: 获取 5 分钟 K 线
klines_5m = await unified.get_kline(
    code="600519",
    start_date="2026-03-20",
    end_date="2026-03-27",
    period="5m",
    adjust="none"
)

# 示例 3: 获取港股数据
hk_klines = await unified.get_kline(
    code="00700",
    start_date="2023-01-01",
    end_date="2026-03-27",
    period="daily",
    adjust="forward",
    market_type="hk_share",
    source_type=DataSourceType.TICKFLOW
)

# 示例 4: 获取周线数据（后复权）
weekly = await unified.get_kline(
    code="600519",
    start_date="2020-01-01",
    end_date="2026-03-27",
    period="weekly",
    adjust="backward",
    limit=100  # 只返回最近 100 条
)

# 示例 5: 指定数据源
ef_klines = await unified.get_kline(
    code="600519",
    start_date="2023-01-01",
    end_date="2026-03-27",
    source_type=DataSourceType.EFINANCE
)
```

---

## 📊 数据清洗规则

### 日期格式统一

| 原始格式 | 目标格式 | 示例 |
|---------|---------|------|
| YYYYMMDD | YYYY-MM-DD | 20260327 → 2026-03-27 |
| YYYY/MM/DD | YYYY-MM-DD | 2026/03/27 → 2026-03-27 |
| YYYY-MM-DD HH:MM:SS | YYYY-MM-DD | 2026-03-27 15:00:00 → 2026-03-27 |

### 数值字段清洗

| 字段 | 清洗规则 | 默认值 |
|------|---------|--------|
| open/high/low/close | 转为 float，处理 NaN | 0.0 |
| volume | 转为 float，去除逗号 | 0.0 |
| amount | 转为 float，允许 None | None |
| turnover_rate | 转为 float，允许 None | None |

### 字段映射

| 标准字段 | EFinance | AkShare | Baostock | TickFlow |
|---------|----------|---------|----------|----------|
| code | 股票代码 | 股票代码 | 证券代码 | code |
| date | 时间 | 日期 | 日期 | date |
| open | 开盘 | 开盘 | 开盘价 | open |
| high | 最高 | 最高 | 最高价 | high |
| low | 最低 | 最低 | 最低价 | low |
| close | 收盘 | 收盘 | 收盘价 | close |
| volume | 成交量 | 成交量 | 成交量 | volume |
| amount | 成交额 | 成交额 | 成交额 | amount |
| turnover_rate | 换手率 | - | - | turnoverRate |

---

## 🎯 优势

### 1. 调用参数统一

**修复前**:
```python
# 不同数据源需要记住不同参数
efinance.get_kline(code, klt=101, fqt=1)
akshare.get_kline(code, adjust="qfq")
tickflow.get_kline(code, period="daily")
```

**修复后**:
```python
# 统一参数，自动适配
unified.get_kline(code, period="daily", adjust="forward")
```

### 2. 数据格式统一

**修复前**:
```python
# 不同数据源返回不同格式
efinance: date="20260327"
akshare: date="2026-03-27"
tickflow: date="2026-03-27 15:00:00"
```

**修复后**:
```python
# 统一返回 YYYY-MM-DD 格式
all: date="2026-03-27"
```

### 3. 自动故障转移

```python
# 主数据源失败时自动切换
klines = await unified.get_kline(code="600519")
# EFinance 失败 → 自动尝试 AkShare → 自动尝试 Baostock
```

### 4. 数据质量验证

```python
# 自动验证数据完整性
is_valid, errors = cleaner.validate_kline_data(klines)
if not is_valid:
    logger.warning(f"数据质量问题：{errors}")
```

---

## 📝 实施步骤

### Phase 1: 基础框架 (1-2 天)

1. ✅ 创建 `unified_params.py` - 统一参数对象
2. ✅ 创建 `parameter_converter.py` - 参数转换器
3. ✅ 创建 `data_cleaner.py` - 数据清洗器
4. ✅ 创建 `unified_adapter.py` - 统一适配器

### Phase 2: 数据源适配 (2-3 天)

1. ✅ 修改 EFinance 适配器 - 支持新参数
2. ✅ 修改 AkShare 适配器 - 支持新参数
3. ✅ 修改 Baostock 适配器 - 支持新参数
4. ✅ 修改 TickFlow 适配器 - 支持新参数

### Phase 3: 测试验证 (1-2 天)

1. ✅ 单元测试 - 参数转换
2. ✅ 单元测试 - 数据清洗
3. ✅ 集成测试 - 跨数据源调用
4. ✅ 性能测试 - 响应时间

### Phase 4: 迁移上线 (1 天)

1. ✅ 更新 Service 层调用
2. ✅ 更新 API 接口
3. ✅ 监控日志
4. ✅ 回滚方案

---

## 🔮 未来扩展

### 1. 支持更多数据源

```python
class DataSourceType(str, Enum):
    YAHOO_FINANCE = "yahoo"
    POLYDATA = "polydata"
    RICEQUANT = "ricequant"
```

### 2. 智能数据源选择

```python
# 基于历史性能自动选择最优数据源
async def select_best_source(code: str, period: str) -> DataSourceType:
    # 分析过去 7 天各数据源的响应时间、成功率
    # 返回最优数据源
    pass
```

### 3. 数据预加载

```python
# 预加载热门股票数据到缓存
await unified.preload_cache(
    codes=['600519', '000001', '300750'],
    period='daily',
    days=30
)
```

---

**设计日期**: 2026-03-27  
**实施难度**: ⭐⭐⭐⭐ (中等偏上)  
**预计工期**: 5-8 天  
**维护成本**: ⭐⭐⭐ (中等)
