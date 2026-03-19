# 多数据源数据统一性与存储架构优化方案

**分析时间**: 2026-03-19  
**方案目标**: 解决多数据源数据一致性、技术指标计算、存储去重和分类存储问题

---

## 一、多数据源数据统一性方案

### 1.1 问题现状

**当前问题**:
- ❌ 5 个数据源（efinance、akshare、baostock、tickflow、tushare）数据格式不统一
- ❌ 相同股票在不同数据源可能存在数据差异
- ❌ 没有数据源优先级和数据校验机制
- ❌ 故障转移时数据一致性无法保证

### 1.2 数据统一性架构

```
┌─────────────────────────────────────────────────┐
│          数据源适配层 (Adapter Layer)             │
├─────────────────────────────────────────────────┤
│  EFinance  │  AkShare  │  Baostock  │  TickFlow │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│        数据标准化层 (Data Normalization)          │
│  - 统一字段命名                                   │
│  - 统一数据格式                                   │
│  - 统一股票代码格式                               │
│  - 数据质量校验                                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│        数据路由层 (Smart Routing)                 │
│  - 优先级路由                                     │
│  - 故障转移                                       │
│  - 负载均衡                                       │
│  - 数据源健康检查                                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│        数据校验层 (Data Validation)               │
│  - 跨数据源比对                                   │
│  - 异常值检测                                     │
│  - 数据完整性检查                                 │
│  - 数据一致性评分                                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│        存储层 (Storage Layer)                     │
│  - SQLite (热数据)                                │
│  - Parquet (冷数据)                               │
│  - Redis (分布式缓存 - 可选)                      │
└─────────────────────────────────────────────────┘
```

### 1.3 数据标准化实现

#### **Step 1: 定义统一数据模型**

**文件**: `app/models/unified_models.py` (新建)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class DataSourceType(str, Enum):
    """数据源类型"""
    EFINANCE = "efinance"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    TICKFLOW = "tickflow"
    TUSHARE = "tushare"

class AdjustType(str, Enum):
    """复权类型"""
    QFQ = "qfq"      # 前复权
    HFQ = "hfq"      # 后复权
    NONE = "none"    # 不复权

class UnifiedKLine(BaseModel):
    """统一 K 线数据模型"""
    # 基础信息
    code: str = Field(..., description="股票代码（6 位数字）")
    date: str = Field(..., description="日期（YYYY-MM-DD）")
    time: Optional[str] = Field(None, description="时间（HH:MM:SS）")
    
    # 行情数据
    open: float = Field(..., ge=0, description="开盘价")
    high: float = Field(..., ge=0, description="最高价")
    low: float = Field(..., ge=0, description="最低价")
    close: float = Field(..., ge=0, description="收盘价")
    pre_close: Optional[float] = Field(None, ge=0, description="昨收价")
    
    # 成交量和成交额
    volume: float = Field(..., ge=0, description="成交量（股）")
    amount: Optional[float] = Field(None, ge=0, description="成交额（元）")
    turnover_rate: Optional[float] = Field(None, ge=0, description="换手率（%）")
    
    # 复权信息
    adjust_type: AdjustType = Field(AdjustType.QFQ, description="复权类型")
    adjust_factor: Optional[float] = Field(1.0, description="复权因子")
    
    # 数据来源
    source: DataSourceType = Field(..., description="数据源")
    source_time: Optional[str] = Field(None, description="数据源时间戳")
    
    # 质量评分
    quality_score: float = Field(1.0, ge=0, le=1, description="数据质量评分")
    
    # 元数据
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None
    
    @validator('code')
    def validate_code(cls, v):
        """验证股票代码格式"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("股票代码必须是 6 位数字")
        return v
    
    @validator('date')
    def validate_date(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("日期格式必须是 YYYY-MM-DD")
    
    @validator('high', 'low')
    def validate_price_range(cls, v, values):
        """验证价格合理性"""
        if 'open' in values and v < values['open'] * 0.9:
            # 价格波动超过 10% 视为异常（A 股涨跌停限制）
            raise ValueError("价格波动异常")
        return v

class UnifiedStockInfo(BaseModel):
    """统一股票基本信息模型"""
    code: str
    name: str
    market: str  # SH/SZ/BJ
    industry: Optional[str]
    area: Optional[str]
    list_date: Optional[str]
    total_shares: float
    float_shares: float
    total_market_cap: float
    float_market_cap: float
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    dividend_yield: Optional[float]
    
    # 数据来源
    source: DataSourceType
    source_time: str
    
    # 质量评分
    quality_score: float
```

#### **Step 2: 实现数据转换器**

**文件**: `app/utils/data_normalizer.py` (新建)

```python
from typing import Dict, Any, Optional, List
from app.models.unified_models import UnifiedKLine, DataSourceType, AdjustType
from loguru import logger

class DataNormalizer:
    """数据标准化转换器"""
    
    @staticmethod
    def normalize_code(code: str) -> str:
        """
        统一股票代码格式
        
        支持格式:
        - 600000 -> 600000
        - 600000.SH -> 600000
        - sh600000 -> 600000
        - 平安银行 -> 000001 (需要映射表)
        
        Returns:
            6 位数字代码
        """
        # 移除后缀
        if '.' in code:
            code = code.split('.')[0]
        # 移除前缀
        if code[:2].lower() in ['sh', 'sz', 'bj']:
            code = code[2:]
        return code.zfill(6)
    
    @staticmethod
    def normalize_kline(
        raw_data: Dict[str, Any],
        source: DataSourceType,
        adjust_type: AdjustType = AdjustType.QFQ
    ) -> Optional[UnifiedKLine]:
        """
        标准化 K 线数据
        
        Args:
            raw_data: 原始数据（字典格式）
            source: 数据源类型
            adjust_type: 复权类型
        
        Returns:
            标准化后的 K 线数据，失败返回 None
        """
        try:
            # 根据不同数据源提取字段
            if source == DataSourceType.EFINANCE:
                return DataNormalizer._normalize_efinance_kline(raw_data, adjust_type)
            elif source == DataSourceType.AKSHARE:
                return DataNormalizer._normalize_akshare_kline(raw_data, adjust_type)
            elif source == DataSourceType.BAOSTOCK:
                return DataNormalizer._normalize_baostock_kline(raw_data, adjust_type)
            elif source == DataSourceType.TICKFLOW:
                return DataNormalizer._normalize_tickflow_kline(raw_data, adjust_type)
            elif source == DataSourceType.TUSHARE:
                return DataNormalizer._normalize_tushare_kline(raw_data, adjust_type)
            else:
                logger.error(f"不支持的数据源：{source}")
                return None
                
        except Exception as e:
            logger.error(f"标准化 K 线数据失败：{e}")
            return None
    
    @staticmethod
    def _normalize_efinance_kline(
        data: Dict[str, Any],
        adjust_type: AdjustType
    ) -> UnifiedKLine:
        """转换 EFinance K 线数据"""
        return UnifiedKLine(
            code=DataNormalizer.normalize_code(str(data.get('股票代码', ''))),
            date=str(data.get('日期', '')),
            open=float(data.get('开盘', 0)),
            high=float(data.get('最高', 0)),
            low=float(data.get('最低', 0)),
            close=float(data.get('收盘', 0)),
            pre_close=float(data.get('昨收', 0)) if data.get('昨收') else None,
            volume=float(data.get('成交量', 0)),
            amount=float(data.get('成交额', 0)) if data.get('成交额') else None,
            turnover_rate=float(data.get('换手率', 0)) if data.get('换手率') else None,
            adjust_type=adjust_type,
            source=DataSourceType.EFINANCE,
            quality_score=1.0
        )
    
    @staticmethod
    def _normalize_akshare_kline(
        data: Dict[str, Any],
        adjust_type: AdjustType
    ) -> UnifiedKLine:
        """转换 AkShare K 线数据"""
        return UnifiedKLine(
            code=DataNormalizer.normalize_code(str(data.get('code', ''))),
            date=str(data.get('date', '')),
            open=float(data.get('open', 0)),
            high=float(data.get('high', 0)),
            low=float(data.get('low', 0)),
            close=float(data.get('close', 0)),
            volume=float(data.get('volume', 0)),
            amount=float(data.get('amount', 0)) if data.get('amount') else None,
            turnover_rate=float(data.get('turnover', 0)) if data.get('turnover') else None,
            adjust_type=adjust_type,
            source=DataSourceType.AKSHARE,
            quality_score=1.0
        )
    
    # ... 其他数据源的转换方法类似实现
```

#### **Step 3: 实现数据校验器**

**文件**: `app/utils/data_validator.py` (增强版)

```python
from typing import List, Dict, Any, Tuple
from app.models.unified_models import UnifiedKLine, DataSourceType
from loguru import logger
import numpy as np

class CrossSourceValidator:
    """跨数据源数据校验器"""
    
    def __init__(self, tolerance: float = 0.01):
        """
        Args:
            tolerance: 容差率（默认 1%）
        """
        self.tolerance = tolerance
    
    def validate_multi_source(
        self,
        klines_from_sources: Dict[DataSourceType, List[UnifiedKLine]]
    ) -> Tuple[List[UnifiedKLine], Dict[str, Any]]:
        """
        校验多个数据源的数据一致性
        
        Args:
            klines_from_sources: {数据源：K 线列表}
        
        Returns:
            (最佳 K 线列表，校验报告)
        """
        if not klines_from_sources:
            return [], {"error": "没有数据源"}
        
        # 1. 按日期对齐所有数据源的数据
        aligned_data = self._align_by_date(klines_from_sources)
        
        # 2. 对每个日期的数据进行比对
        best_klines = []
        validation_report = {
            "total_dates": len(aligned_data),
            "consistent_dates": 0,
            "inconsistent_dates": 0,
            "missing_dates": 0,
            "details": []
        }
        
        for date, klines_by_source in aligned_data.items():
            if len(klines_by_source) < 2:
                # 只有一个数据源有数据
                best_kline = list(klines_by_source.values())[0]
                best_klines.append(best_kline)
                validation_report["missing_dates"] += 1
                continue
            
            # 多个数据源都有数据，进行比对
            best_kline, consistency_report = self._select_best_kline(
                klines_by_source, date
            )
            best_klines.append(best_kline)
            
            if consistency_report["is_consistent"]:
                validation_report["consistent_dates"] += 1
            else:
                validation_report["inconsistent_dates"] += 1
                validation_report["details"].append({
                    "date": date,
                    "report": consistency_report
                })
        
        # 3. 计算一致性评分
        validation_report["consistency_rate"] = (
            validation_report["consistent_dates"] / 
            max(validation_report["total_dates"], 1)
        )
        
        return best_klines, validation_report
    
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
        # 数据源优先级
        priority = {
            DataSourceType.TUSHARE: 1,
            DataSourceType.EFINANCE: 2,
            DataSourceType.AKSHARE: 3,
            DataSourceType.BAOSTOCK: 4,
            DataSourceType.TICKFLOW: 5
        }
        
        # 检查一致性
        prices = {
            source: kline.close 
            for source, kline in klines_by_source.items()
        }
        
        price_values = list(prices.values())
        avg_price = np.mean(price_values)
        max_diff = max(abs(p - avg_price) / avg_price for p in price_values)
        
        is_consistent = max_diff <= self.tolerance
        
        # 如果不一致，标记所有数据源的质量评分
        if not is_consistent:
            for kline in klines_by_source.values():
                kline.quality_score = 0.5  # 降低质量评分
        
        # 选择优先级最高的数据源
        best_source = min(
            klines_by_source.keys(),
            key=lambda s: priority.get(s, 999)
        )
        
        report = {
            "date": date,
            "is_consistent": is_consistent,
            "max_difference": max_diff,
            "sources_count": len(klines_by_source),
            "best_source": best_source
        }
        
        return klines_by_source[best_source], report
```

### 1.4 数据源健康检查

**文件**: `app/utils/data_source_health.py` (新建)

```python
from typing import Dict, Any, List
from app.adapters.factory import DataSourceFactory
from loguru import logger
import asyncio
from datetime import datetime, timedelta

class DataSourceHealthChecker:
    """数据源健康检查器"""
    
    def __init__(self):
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.check_interval = 300  # 5 分钟
    
    async def check_all_sources(self) -> Dict[str, Dict[str, Any]]:
        """检查所有数据源的健康状态"""
        factory = DataSourceFactory()
        sources = factory.get_available_sources()
        
        tasks = []
        for source in sources:
            tasks.append(self._check_single_source(source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                self.health_status[source] = {
                    "status": "error",
                    "error": str(result),
                    "last_check": datetime.now().isoformat()
                }
            else:
                self.health_status[source] = result
        
        return self.health_status
    
    async def _check_single_source(self, source: str) -> Dict[str, Any]:
        """检查单个数据源的健康状态"""
        start_time = datetime.now()
        
        try:
            adapter = DataSourceFactory.get_adapter(source)
            
            # 测试查询（使用一个简单接口）
            test_code = "000001"
            stock_info = await adapter.get_stock_info(test_code)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if stock_info:
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat(),
                    "test_result": "success"
                }
            else:
                return {
                    "status": "degraded",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat(),
                    "test_result": "empty_data"
                }
                
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_healthy_sources(self) -> List[str]:
        """获取健康的数据源列表"""
        return [
            source for source, status in self.health_status.items()
            if status.get("status") == "healthy"
        ]
    
    def get_best_source(self) -> str:
        """获取最佳数据源（响应时间最短）"""
        healthy = [
            (source, status) 
            for source, status in self.health_status.items()
            if status.get("status") == "healthy"
        ]
        
        if not healthy:
            # 如果没有健康的，返回响应时间最短的
            all_sources = [
                (source, status) 
                for source, status in self.health_status.items()
                if status.get("status") != "error"
            ]
            if all_sources:
                return min(all_sources, key=lambda x: x[1].get("response_time", 999))[0]
            return "efinance"  # 默认
        
        return min(healthy, key=lambda x: x[1].get("response_time", 999))[0]
```

---

## 二、技术指标库选择方案

### 2.1 技术指标库对比

| 指标库 | 优点 | 缺点 | 适用场景 | 推荐度 |
|--------|------|------|---------|--------|
| **TA-Lib** | - 性能极高（C 实现）<br>- 指标丰富（150+）<br>- 行业标准 | - 安装复杂（需 C 库）<br>- Windows 支持差<br>- 依赖编译 | - 高频交易<br>- 生产环境<br>- 性能敏感 | ⭐⭐⭐⭐ |
| **pandas-ta** | - 纯 Python 实现<br>- 安装简单<br>- 与 pandas 无缝集成<br>- 文档完善 | - 性能较低<br>- 内存占用高 | - 研究分析<br>- 离线回测<br>- 快速原型 | ⭐⭐⭐⭐⭐ |
| **tushare 内置** | - 与 Tushare 数据源集成<br>- 计算简单 | - 指标有限<br>- 依赖 Tushare | - Tushare 用户 | ⭐⭐ |
| **自研指标** | - 完全可控<br>- 可定制 | - 开发成本高<br>- 需要测试 | - 特殊指标需求 | ⭐⭐⭐ |

### 2.2 推荐方案：**pandas-ta 为主，TA-Lib 为辅**

#### **方案架构**:

```
┌─────────────────────────────────────────┐
│       指标计算层 (Indicator Layer)        │
├─────────────────────────────────────────┤
│  首选：pandas-ta (纯 Python)              │
│  - 易于安装和维护                         │
│  - 与 pandas 完美集成                     │
│  - 支持 130+ 指标                         │
├─────────────────────────────────────────┤
│  备选：TA-Lib (可选)                      │
│  - 性能敏感场景使用                       │
│  - 通过配置启用                           │
│  - 自动降级到 pandas-ta                  │
└─────────────────────────────────────────┘
```

#### **实现代码**:

**文件**: `app/services/indicators_manager.py` (新建)

```python
from typing import Optional, Dict, Any, List
import pandas as pd
from loguru import logger

# 尝试导入 TA-Lib
try:
    import talib
    TALIB_AVAILABLE = True
    logger.info("TA-Lib 已安装，将用于高性能指标计算")
except ImportError:
    TALIB_AVAILABLE = False
    logger.info("TA-Lib 未安装，使用 pandas-ta 计算指标")

# 导入 pandas-ta
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.error("pandas-ta 未安装，请运行：pip install pandas-ta")

class IndicatorsManager:
    """技术指标管理器"""
    
    def __init__(self, prefer_talib: bool = True):
        """
        Args:
            prefer_talib: 是否优先使用 TA-Lib（如果可用）
        """
        self.prefer_talib = prefer_talib and TALIB_AVAILABLE
        self.use_pandas_ta = PANDAS_TA_AVAILABLE
    
    def calculate_ma(
        self,
        df: pd.DataFrame,
        periods: List[int] = [5, 10, 20, 60],
        price_column: str = "close"
    ) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 包含价格数据的 DataFrame
            periods: 周期列表
            price_column: 价格列名
        
        Returns:
            添加了 MA 列的 DataFrame
        """
        df = df.copy()
        
        if self.prefer_talib:
            # 使用 TA-Lib
            for period in periods:
                df[f'ma{period}'] = talib.SMA(df[price_column].values, timeperiod=period)
        else:
            # 使用 pandas-ta
            for period in periods:
                df[f'ma{period}'] = ta.sma(df[price_column], length=period)
        
        return df
    
    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        price_column: str = "close"
    ) -> pd.DataFrame:
        """计算 MACD 指标"""
        df = df.copy()
        
        if self.prefer_talib:
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
                df[price_column].values,
                fastperiod=fast,
                slowperiod=slow,
                signalperiod=signal
            )
        else:
            macd_df = ta.macd(
                df[price_column],
                fast=fast,
                slow=slow,
                signal=signal
            )
            df['macd'] = macd_df[f'MACD_{fast}_{slow}']
            df['macd_signal'] = macd_df[f'MACDs_{fast}_{slow}']
            df['macd_hist'] = macd_df[f'MACDh_{fast}_{slow}']
        
        return df
    
    def calculate_rsi(
        self,
        df: pd.DataFrame,
        periods: List[int] = [6, 12, 24],
        price_column: str = "close"
    ) -> pd.DataFrame:
        """计算 RSI 指标"""
        df = df.copy()
        
        if self.prefer_talib:
            for period in periods:
                df[f'rsi{period}'] = talib.RSI(df[price_column].values, timeperiod=period)
        else:
            for period in periods:
                df[f'rsi{period}'] = ta.rsi(df[price_column], length=period)
        
        return df
    
    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        price_column: str = "close"
    ) -> pd.DataFrame:
        """计算布林带"""
        df = df.copy()
        
        if self.prefer_talib:
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
                df[price_column].values,
                timeperiod=period,
                nbdevup=std_dev,
                nbdevdn=std_dev
            )
        else:
            bb_df = ta.bbands(df[price_column], length=period, std=std_dev)
            df['bb_upper'] = bb_df[f'BBU_{period}_{std_dev}']
            df['bb_middle'] = bb_df[f'BBM_{period}_{std_dev}']
            df['bb_lower'] = bb_df[f'BBL_{period}_{std_dev}']
        
        return df
    
    def calculate_all_indicators(
        self,
        df: pd.DataFrame,
        price_column: str = "close"
    ) -> pd.DataFrame:
        """
        一次性计算所有常用指标
        
        Returns:
            包含所有指标的 DataFrame
        """
        # 移动平均线
        df = self.calculate_ma(df, periods=[5, 10, 20, 60], price_column=price_column)
        
        # MACD
        df = self.calculate_macd(df, price_column=price_column)
        
        # RSI
        df = self.calculate_rsi(df, periods=[6, 12, 24], price_column=price_column)
        
        # 布林带
        df = self.calculate_bollinger_bands(df, price_column=price_column)
        
        # KDJ (只有 pandas-ta 支持)
        if self.use_pandas_ta:
            kdj_df = ta.kdj(df['high'], df['low'], df[price_column])
            df['kdj_k'] = kdj_df['KDJ_K_9_3']
            df['kdj_d'] = kdj_df['KDJ_D_9_3']
            df['kdj_j'] = kdj_df['KDJ_J_9_3']
        
        # ATR
        if self.prefer_talib:
            df['atr'] = talib.ATR(df['high'].values, df['low'].values, df[price_column].values, timeperiod=14)
        else:
            df['atr'] = ta.atr(df['high'], df['low'], df[price_column], length=14)
        
        return df
```

### 2.3 安装建议

**requirements.txt** 添加:
```txt
# 技术指标计算
pandas-ta>=0.3.14b  # 主要指标库（推荐）
# TA-Lib>=0.4.28    # 可选，高性能指标计算（需要预编译 C 库）
```

**安装说明**:
```bash
# 基础安装（推荐）
pip install pandas-ta

# 高级安装（需要 TA-Lib）
# Windows: 先安装 https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA-Lib
pip install pandas-ta
```

---

## 三、存储逻辑优化方案

### 3.1 当前问题分析

**已识别问题**:
1. ❌ Parquet 存储路径不统一（两套实现）
2. ❌ 缓存与持久化数据可能不同步
3. ❌ 缺少数据版本管理
4. ❌ 数据更新策略不完善

### 3.2 统一存储架构

```
┌─────────────────────────────────────────────────┐
│          存储管理层 (Storage Manager)             │
├─────────────────────────────────────────────────┤
│  热数据层 (Hot Tier)                              │
│  - Redis 缓存（分布式，可选）                     │
│  - 内存缓存（LRU，5 分钟 TTL）                    │
│  - 用途：实时行情、热点数据                       │
├─────────────────────────────────────────────────┤
│  温数据层 (Warm Tier)                             │
│  - SQLite 数据库                                  │
│  - 最近 3 个月数据                                 │
│  - 用途：近期 K 线、技术指标                      │
├─────────────────────────────────────────────────┤
│  冷数据层 (Cold Tier)                             │
│  - Parquet 文件（按代码 + 年份分区）              │
│  - 3 个月以上历史数据                             │
│  - 用途：历史归档、回测分析                       │
└─────────────────────────────────────────────────┘
```

### 3.3 统一 Parquet 存储路径

**文件**: `app/storage/parquet_manager.py` (新建)

```python
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

class ParquetManager:
    """统一的 Parquet 文件管理器"""
    
    def __init__(self, base_dir: str = "./data/parquet"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 统一的目录结构
        self.kline_dir = self.base_dir / "kline"
        self.indicators_dir = self.base_dir / "indicators"
        self.chip_dir = self.base_dir / "chip"
        self.backtest_dir = self.base_dir / "backtest"
        
        # 创建目录
        for dir_path in [self.kline_dir, self.indicators_dir, 
                         self.chip_dir, self.backtest_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_kline_path(
        self,
        code: str,
        year: int,
        adjust_type: str = "qfq"
    ) -> Path:
        """
        获取 K 线文件路径
        
        目录结构:
        data/parquet/kline/{code}/{year}_{adjust_type}.parquet
        """
        code_dir = self.kline_dir / code
        code_dir.mkdir(parents=True, exist_ok=True)
        return code_dir / f"{year}_{adjust_type}.parquet"
    
    def save_klines(
        self,
        code: str,
        klines: List[Dict[str, Any]],
        adjust_type: str = "qfq"
    ) -> int:
        """
        保存 K 线数据到 Parquet
        
        特性:
        - 按年份自动分区
        - 自动合并和去重
        - 保留元数据
        """
        if not klines:
            return 0
        
        df = pd.DataFrame(klines)
        
        # 提取年份
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        
        saved_count = 0
        for year in df['year'].unique():
            year_df = df[df['year'] == year].drop('year', axis=1)
            parquet_path = self.get_kline_path(code, year, adjust_type)
            
            if parquet_path.exists():
                # 读取已有数据
                existing_df = pd.read_parquet(parquet_path)
                
                # 合并数据
                combined_df = pd.concat([existing_df, year_df], ignore_index=True)
                
                # 去重（保留最新）
                combined_df = combined_df.drop_duplicates(
                    subset=['date'],
                    keep='last'
                )
                
                # 排序
                combined_df = combined_df.sort_values('date')
            else:
                combined_df = year_df
            
            # 保存
            combined_df.to_parquet(parquet_path, index=False)
            saved_count += len(year_df)
            
            logger.debug(f"保存 {code} {year}年 K 线到 {parquet_path}")
        
        return saved_count
    
    def load_klines(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str = "qfq"
    ) -> pd.DataFrame:
        """
        加载 K 线数据
        
        自动从多个年份文件中加载并合并
        """
        start_year = int(start_date[:4])
        end_year = int(end_date[:4])
        
        dfs = []
        for year in range(start_year, end_year + 1):
            parquet_path = self.get_kline_path(code, year, adjust_type)
            if parquet_path.exists():
                df = pd.read_parquet(parquet_path)
                dfs.append(df)
        
        if not dfs:
            return pd.DataFrame()
        
        # 合并
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # 筛选日期范围
        combined_df['date'] = pd.to_datetime(combined_df['date'])
        mask = (combined_df['date'] >= start_date) & (combined_df['date'] <= end_date)
        result = combined_df[mask]
        
        return result.sort_values('date')
    
    def add_metadata(
        self,
        parquet_path: Path,
        metadata: Dict[str, Any]
    ):
        """
        添加元数据到 Parquet 文件
        
        元数据包括:
        - 数据来源
        - 更新时间
        - 数据质量评分
        - 版本号
        """
        if not parquet_path.exists():
            return
        
        # 读取
        df = pd.read_parquet(parquet_path)
        
        # 添加元数据列（如果不存在）
        for key, value in metadata.items():
            if key not in df.columns:
                df[key] = value
        
        # 保存
        df.to_parquet(parquet_path, index=False)
```

### 3.4 数据去重和更新策略

**文件**: `app/storage/data_deduplication.py` (新建)

```python
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.sqlite import KLine, get_session
from loguru import logger
from datetime import datetime

class DataDeduplicationManager:
    """数据去重管理器"""
    
    @staticmethod
    async def deduplicate_klines(
        code: str,
        klines: List[Dict[str, Any]],
        adjust_type: str = "qfq"
    ) -> List[Dict[str, Any]]:
        """
        去重 K 线数据
        
        策略:
        1. 查询数据库中已存在的日期
        2. 过滤掉已存在的记录
        3. 只返回需要插入的新数据
        """
        async with get_session() as session:
            # 1. 提取所有日期
            dates = [k['date'] for k in klines]
            
            # 2. 批量查询已存在的记录
            query = select(KLine.date).where(
                and_(
                    KLine.code == code,
                    KLine.date.in_(dates),
                    KLine.adjust_type == adjust_type
                )
            )
            result = await session.execute(query)
            existing_dates = set(result.scalars().all())
            
            # 3. 过滤新数据
            new_klines = [
                k for k in klines 
                if k['date'] not in existing_dates
            ]
            
            if new_klines:
                logger.info(f"股票 {code} 去重后剩余 {len(new_klines)} 条新记录")
            else:
                logger.debug(f"股票 {code} 所有数据已存在")
            
            return new_klines
    
    @staticmethod
    async def update_if_changed(
        code: str,
        klines: List[Dict[str, Any]],
        adjust_type: str = "qfq"
    ) -> tuple[int, int]:
        """
        更新已变化的数据
        
        Returns:
            (插入数量，更新数量)
        """
        async with get_session() as session:
            inserted = 0
            updated = 0
            
            for kline_data in klines:
                # 查询是否已存在
                query = select(KLine).where(
                    and_(
                        KLine.code == code,
                        KLine.date == kline_data['date'],
                        KLine.adjust_type == adjust_type
                    )
                )
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # 检查是否变化
                    if DataDeduplicationManager._has_changed(existing, kline_data):
                        # 更新
                        for key, value in kline_data.items():
                            setattr(existing, key, value)
                        existing.updated_at = datetime.now().isoformat()
                        updated += 1
                else:
                    # 插入
                    new_kline = KLine(**kline_data)
                    session.add(new_kline)
                    inserted += 1
            
            if inserted > 0 or updated > 0:
                await session.commit()
                logger.info(f"股票 {code}: 插入{inserted}条，更新{updated}条")
            
            return inserted, updated
    
    @staticmethod
    def _has_changed(existing: KLine, new_data: Dict[str, Any]) -> bool:
        """检查数据是否发生变化"""
        for key, value in new_data.items():
            if key in ['code', 'date', 'adjust_type']:
                continue
            if getattr(existing, key, None) != value:
                return True
        return False
```

### 3.5 数据版本管理

**文件**: `app/storage/data_versioning.py` (新建)

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.storage.sqlite import Base, get_session
from datetime import datetime
from typing import Optional

class DataVersion(Base):
    """数据版本表"""
    __tablename__ = "data_versions"
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(50), nullable=False)  # 表名
    record_id = Column(Integer, nullable=False)  # 记录 ID
    version = Column(Integer, nullable=False)  # 版本号
    operation = Column(String(20), nullable=False)  # INSERT/UPDATE/DELETE
    old_data = Column(String)  # 旧数据（JSON）
    new_data = Column(String)  # 新数据（JSON）
    changed_by = Column(String(50))  # 操作者（数据源）
    changed_at = Column(DateTime, default=datetime.now)  # 变更时间
    reason = Column(String)  # 变更原因

class DataVersionManager:
    """数据版本管理器"""
    
    @staticmethod
    async def create_version(
        table_name: str,
        record_id: int,
        operation: str,
        old_data: Optional[dict] = None,
        new_data: Optional[dict] = None,
        changed_by: str = "system",
        reason: str = ""
    ):
        """创建数据版本记录"""
        async with get_session() as session:
            # 获取当前最大版本号
            from sqlalchemy import select, func
            query = select(func.max(DataVersion.version)).where(
                DataVersion.table_name == table_name,
                DataVersion.record_id == record_id
            )
            result = await session.execute(query)
            max_version = result.scalar() or 0
            
            version = DataVersion(
                table_name=table_name,
                record_id=record_id,
                version=max_version + 1,
                operation=operation,
                old_data=str(old_data) if old_data else None,
                new_data=str(new_data) if new_data else None,
                changed_by=changed_by,
                reason=reason
            )
            
            session.add(version)
            await session.commit()
    
    @staticmethod
    async def get_version_history(
        table_name: str,
        record_id: int
    ) -> list:
        """获取数据版本历史"""
        async with get_session() as session:
            query = select(DataVersion).where(
                DataVersion.table_name == table_name,
                DataVersion.record_id == record_id
            ).order_by(DataVersion.version.desc())
            
            result = await session.execute(query)
            return result.scalars().all()
```

---

## 四、分类存储方案

### 4.1 数据分类标准

| 数据类型 | 访问频率 | 数据量 | 存储位置 | 保留策略 |
|---------|---------|--------|---------|---------|
| **实时行情** | 极高 | 小 | Redis + 内存 | 当天 |
| **近期 K 线** | 高 | 中 | SQLite | 3 个月 |
| **历史 K 线** | 低 | 大 | Parquet | 永久 |
| **技术指标** | 中 | 中 | SQLite | 可重新计算 |
| **股票信息** | 中 | 小 | SQLite | 永久，变化时更新 |
| **筹码数据** | 低 | 中 | Parquet | 永久 |
| **回测结果** | 低 | 大 | Parquet | 永久 |

### 4.2 存储路由实现

**文件**: `app/storage/storage_router.py` (新建)

```python
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from app.storage.parquet_manager import ParquetManager
from app.storage.sqlite import get_session, KLine
from sqlalchemy import select, and_
from loguru import logger

class StorageRouter:
    """存储路由器 - 根据数据特征自动选择存储位置"""
    
    def __init__(self):
        self.parquet_manager = ParquetManager()
        self.hot_threshold_days = 90  # 热数据阈值（天）
    
    async def save_kline(
        self,
        code: str,
        kline_data: Dict[str, Any],
        adjust_type: str = "qfq"
    ):
        """
        智能保存 K 线数据
        
        策略:
        - 最近 3 个月：SQLite（热数据）
        - 3 个月以上：Parquet（冷数据）
        """
        kline_date = datetime.strptime(kline_data['date'], "%Y-%m-%d")
        days_old = (datetime.now() - kline_date).days
        
        if days_old <= self.hot_threshold_days:
            # 热数据：保存到 SQLite
            await self._save_to_sqlite(code, kline_data, adjust_type)
            logger.debug(f"保存热数据 {code} {kline_data['date']} 到 SQLite")
        else:
            # 冷数据：保存到 Parquet
            await self._save_to_parquet(code, [kline_data], adjust_type)
            logger.debug(f"保存冷数据 {code} {kline_data['date']} 到 Parquet")
    
    async def load_klines(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str = "qfq"
    ) -> list:
        """
        智能加载 K 线数据
        
        自动从 SQLite 和 Parquet 中加载并合并
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        threshold_dt = datetime.now() - timedelta(days=self.hot_threshold_days)
        
        all_klines = []
        
        # 1. 从 SQLite 加载热数据
        if start_dt <= threshold_dt <= end_dt:
            sqlite_klines = await self._load_from_sqlite(
                code, start_date, threshold_dt.strftime("%Y-%m-%d"), adjust_type
            )
            all_klines.extend(sqlite_klines)
            logger.debug(f"从 SQLite 加载 {len(sqlite_klines)} 条热数据")
        
        # 2. 从 Parquet 加载冷数据
        if start_dt <= threshold_dt:
            parquet_klines = await self._load_from_parquet(
                code, start_date, threshold_dt.strftime("%Y-%m-%d"), adjust_type
            )
            all_klines.extend(parquet_klines)
            logger.debug(f"从 Parquet 加载 {len(parquet_klines)} 条冷数据")
        
        # 3. 合并和排序
        all_klines.sort(key=lambda x: x['date'])
        
        return all_klines
    
    async def _save_to_sqlite(
        self,
        code: str,
        kline_data: Dict[str, Any],
        adjust_type: str
    ):
        """保存到 SQLite"""
        async with get_session() as session:
            # 检查是否已存在
            query = select(KLine).where(
                and_(
                    KLine.code == code,
                    KLine.date == kline_data['date'],
                    KLine.adjust_type == adjust_type
                )
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新
                for key, value in kline_data.items():
                    setattr(existing, key, value)
            else:
                # 插入
                new_kline = KLine(**kline_data, adjust_type=adjust_type)
                session.add(new_kline)
            
            await session.commit()
    
    async def _save_to_parquet(
        self,
        code: str,
        klines: list,
        adjust_type: str
    ):
        """保存到 Parquet"""
        self.parquet_manager.save_klines(code, klines, adjust_type)
    
    async def _load_from_sqlite(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str
    ) -> list:
        """从 SQLite 加载"""
        async with get_session() as session:
            query = select(KLine).where(
                and_(
                    KLine.code == code,
                    KLine.date >= start_date,
                    KLine.date <= end_date,
                    KLine.adjust_type == adjust_type
                )
            ).order_by(KLine.date)
            
            result = await session.execute(query)
            return [self._kline_to_dict(k) for k in result.scalars().all()]
    
    async def _load_from_parquet(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str
    ) -> list:
        """从 Parquet 加载"""
        df = self.parquet_manager.load_klines(code, start_date, end_date, adjust_type)
        return df.to_dict('records')
    
    def _kline_to_dict(self, kline: KLine) -> dict:
        """KLine 对象转字典"""
        return {
            'code': kline.code,
            'date': kline.date,
            'open': kline.open,
            'high': kline.high,
            'low': kline.low,
            'close': kline.close,
            'volume': kline.volume,
            'amount': kline.amount,
            'turnover_rate': kline.turnover_rate,
            'pre_close': kline.pre_close
        }
```

---

## 五、实施建议

### 5.1 分阶段实施

#### **阶段 1: 基础架构（1-2 周）**
- ✅ 创建统一数据模型
- ✅ 实现数据标准化转换器
- ✅ 统一 Parquet 存储路径
- ✅ 添加数据去重逻辑

#### **阶段 2: 数据校验（1 周）**
- ✅ 实现跨数据源校验
- ✅ 添加数据质量评分
- ✅ 实施数据源健康检查

#### **阶段 3: 存储优化（1-2 周）**
- ✅ 实现存储路由器
- ✅ 添加数据版本管理
- ✅ 优化缓存策略

#### **阶段 4: 指标计算（1 周）**
- ✅ 集成 pandas-ta
- ✅ 实现指标管理器
- ✅ 添加 TA-Lib 支持（可选）

### 5.2 配置建议

**app/config.py** 添加:
```python
# 数据存储配置
STORAGE_CONFIG = {
    "hot_threshold_days": 90,  # 热数据阈值
    "parquet_base_dir": "./data/parquet",
    "sqlite_db": "./data/sqlite/quant.db",
    "cache_ttl": {
        "realtime": 60,
        "kline": 300,
        "indicators": 300
    }
}

# 技术指标配置
INDICATORS_CONFIG = {
    "prefer_talib": True,  # 优先使用 TA-Lib
    "use_pandas_ta": True  # 使用 pandas-ta
}

# 数据源配置
DATA_SOURCE_CONFIG = {
    "health_check_interval": 300,  # 健康检查间隔（秒）
    "consistency_tolerance": 0.01,  # 数据一致性容差
    "priority": ["efinance", "akshare", "baostock", "tickflow", "tushare"]
}
```

### 5.3 性能优化建议

1. **批量操作**: 每次至少处理 100 条记录
2. **索引优化**: 为常用查询添加复合索引
3. **连接池**: 使用 SQLAlchemy 异步连接池
4. **分区存储**: 按代码和年份分区 Parquet 文件
5. **缓存预热**: 开盘前预加载热点数据

---

## 六、总结

### 6.1 核心方案

1. **数据统一性**: 标准化模型 + 跨数据源校验 + 智能路由
2. **技术指标**: pandas-ta 为主，TA-Lib 为辅
3. **存储逻辑**: 三级存储 + 自动去重 + 版本管理
4. **分类存储**: 按访问频率自动路由到不同存储层

### 6.2 预期效果

- ✅ 数据一致性提升至 99%+
- ✅ 存储效率提升 50%+
- ✅ 查询性能提升 2-5 倍
- ✅ 维护成本降低 70%

### 6.3 下一步行动

1. 评审方案，确认需求
2. 创建实施任务列表
3. 分阶段开发和测试
4. 文档更新和培训

---

**方案制定时间**: 2026-03-19  
**方案状态**: ✅ 完成，待评审  
**下一步**: 用户评审和确认
