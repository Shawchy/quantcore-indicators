# 数据分类存储方案

## 📊 数据分类体系

### 一级分类（大类）

```
data/
├── stock/                    # 股票数据（一级分类）
│   ├── market/              # 市场数据
│   ├── financial/           # 财务数据
│   ├── technical/           # 技术数据
│   └── derivative/          # 衍生数据
│
├── fund/                     # 基金数据（一级分类）
│   ├── basic/               # 基础数据
│   ├── performance/         # 业绩数据
│   ├── portfolio/           # 持仓数据
│   └── derivative/          # 衍生数据
│
├── market/                   # 市场整体数据（一级分类）
│   ├── index/               # 指数数据
│   ├── sector/              # 板块数据
│   └── sentiment/           # 市场情绪
│
└── strategy/                 # 策略数据（一级分类）
    ├── backtest/            # 回测数据
    ├── live/                # 实盘数据
    └── analysis/            # 分析数据
```

---

## 🏢 股票数据分类（一级分类）

### 二级分类：市场数据

```
stock/market/
├── kline/                    # K 线数据
│   ├── daily/               # 日线
│   │   ├── {code}/
│   │   │   ├── {year}_{adjust}.parquet
│   │   │   └── metadata.json
│   │   └── _index.parquet
│   │
│   ├── weekly/              # 周线
│   │   ├── {code}/
│   │   │   └── {year}_{adjust}.parquet
│   │   └── _index.parquet
│   │
│   ├── monthly/             # 月线
│   │   ├── {code}/
│   │   │   └── {year}_{adjust}.parquet
│   │   └── _index.parquet
│   │
│   └── minute/              # 分钟线
│       ├── 1min/            # 1 分钟
│       ├── 5min/            # 5 分钟
│       ├── 15min/           # 15 分钟
│       ├── 30min/           # 30 分钟
│       └── 60min/           # 60 分钟
│
├── realtime/                 # 实时行情
│   ├── quote/               # 实时报价
│   │   └── {date}/
│   │       └── {code}.parquet
│   │
│   ├── tick/                # 逐笔成交
│   │   └── {date}/
│   │       └── {code}.parquet
│   │
│   └── orderbook/           # 盘口数据
│       └── {date}/
│           └── {code}.parquet
│
├── info/                     # 股票信息
│   ├── basic/               # 基本信息
│   │   └── stock_list.parquet
│   │
│   ├── industry/            # 行业分类
│   │   └── industry_classification.parquet
│   │
│   └── concept/             # 概念板块
│       └── concept_classification.parquet
│
└── moneyflow/                # 资金流向
    ├── individual/          # 个股资金流
    │   └── {date}/
    │       └── {code}.parquet
    │
    ├── market/              # 市场资金流
    │   └── {date}.parquet
    │
    └── sector/              # 板块资金流
        └── {date}.parquet
```

### 二级分类：财务数据

```
stock/financial/
├── balance_sheet/            # 资产负债表
│   ├── {code}/
│   │   └── {year}.parquet
│   └── _index.parquet
│
├── income_statement/         # 利润表
│   ├── {code}/
│   │   └── {year}.parquet
│   └── _index.parquet
│
├── cash_flow/                # 现金流量表
│   ├── {code}/
│   │   └── {year}.parquet
│   └── _index.parquet
│
├── indicators/               # 财务指标
│   ├── {code}/
│   │   └── {year}.parquet
│   └── _index.parquet
│
├── forecast/                 # 业绩预告
│   ├── {code}/
│   │   └── {year}.parquet
│   └── _index.parquet
│
└── report/                   # 财报原文
    ├── {code}/
    │   └── {year}_{quarter}.pdf
    └── _index.json
```

### 二级分类：技术数据

```
stock/technical/
├── indicators/               # 技术指标
│   ├── trend/               # 趋势指标
│   │   ├── ma/              # 移动平均
│   │   ├── macd/            # MACD
│   │   └── boll/            # 布林带
│   │
│   ├── momentum/            # 动量指标
│   │   ├── rsi/             # RSI
│   │   ├── kdj/             # KDJ
│   │   └── wr/              # 威廉指标
│   │
│   ├── volume/              # 成交量指标
│   │   ├── obv/             # OBV
│   │   └── vol/             # 成交量
│   │
│   └── volatility/          # 波动率指标
│       ├── atr/             # ATR
│       └── stddev/          # 标准差
│
├── chip/                     # 筹码数据
│   ├── distribution/        # 筹码分布
│   │   ├── {code}/
│   │   │   └── {year}.parquet
│   │   └── _index.parquet
│   │
│   ├── concentration/       # 筹码集中度
│   │   ├── {code}/
│   │   │   └── {year}.parquet
│   │   └── _index.parquet
│   │
│   └── shareholder/         # 股东人数
│       ├── {code}/
│       │   └── {year}.parquet
│       └── _index.parquet
│
└── pattern/                  # 形态识别
    ├── candlestick/         # K 线形态
    │   └── {date}.parquet
    │
    └── chart/               # 图表形态
        └── {date}.parquet
```

### 二级分类：衍生数据

```
stock/derivative/
├── factor/                   # 因子数据
│   ├── alpha/               # Alpha 因子
│   │   └── {date}.parquet
│   │
│   ├── beta/                # Beta 因子
│   │   └── {date}.parquet
│   │
│   └── risk/                # 风险因子
│       └── {date}.parquet
│
├── score/                    # 评分数据
│   ├── quality/             # 质量评分
│   │   └── {code}.parquet
│   │
│   ├── value/               # 价值评分
│   │   └── {code}.parquet
│   │
│   └── growth/              # 成长评分
│       └── {code}.parquet
│
└── prediction/               # 预测数据
    ├── price/               # 价格预测
    │   └── {date}.parquet
    │
    └── trend/               # 趋势预测
        └── {date}.parquet
```

---

## 💰 基金数据分类（一级分类）

### 二级分类：基础数据

```
fund/basic/
├── list/                     # 基金列表
│   ├── all_funds.parquet    # 全部基金
│   ├── stock_funds.parquet  # 股票型基金
│   ├── bond_funds.parquet   # 债券型基金
│   ├── mixed_funds.parquet  # 混合型基金
│   ├── index_funds.parquet  # 指数型基金
│   ├── qdii_funds.parquet   # QDII 基金
│   └── etf_funds.parquet    # ETF 基金
│
├── info/                     # 基金信息
│   ├── {fund_code}/
│   │   ├── basic_info.json
│   │   ├── manager.json
│   │   └── company.json
│   └── _index.parquet
│
├── classification/           # 基金分类
│   ├── by_type.parquet      # 按类型
│   ├── by_company.parquet   # 按公司
│   └── by_scale.parquet     # 按规模
│
└── dividend/                 # 分红数据
    ├── {fund_code}/
    │   └── dividend_history.parquet
    └── _index.parquet
```

### 二级分类：业绩数据

```
fund/performance/
├── nav/                      # 净值数据
│   ├── daily/               # 日净值
│   │   ├── {fund_code}/
│   │   │   └── {year}.parquet
│   │   └── _index.parquet
│   │
│   └── cumulative/          # 累计净值
│       ├── {fund_code}/
│       │   └── {year}.parquet
│       └── _index.parquet
│
├── return/                   # 收益数据
│   ├── daily/               # 日收益
│   │   └── {date}.parquet
│   │
│   ├── weekly/              # 周收益
│   │   └── {date}.parquet
│   │
│   ├── monthly/             # 月收益
│   │   └── {date}.parquet
│   │
│   ├── quarterly/           # 季收益
│   │   └── {date}.parquet
│   │
│   └── yearly/              # 年收益
│       └── {year}.parquet
│
├── ranking/                  # 排名数据
│   ├── by_type/             # 按类型排名
│   │   └── {date}.parquet
│   │
│   └── overall/             # 总排名
│       └── {date}.parquet
│
└── risk/                     # 风险指标
    ├── volatility/          # 波动率
    │   └── {fund_code}.parquet
    │
    ├── max_drawdown/        # 最大回撤
    │   └── {fund_code}.parquet
    │
    ├── sharpe/              # 夏普比率
    │   └── {fund_code}.parquet
    │
    └── sortino/             # 索提诺比率
        └── {fund_code}.parquet
```

### 二级分类：持仓数据

```
fund/portfolio/
├── stock_position/           # 股票持仓
│   ├── {fund_code}/
│   │   ├── {year}_{quarter}.parquet
│   │   └── metadata.json
│   └── _index.parquet
│
├── bond_position/            # 债券持仓
│   ├── {fund_code}/
│   │   ├── {year}_{quarter}.parquet
│   │   └── metadata.json
│   └── _index.parquet
│
├── industry_allocation/      # 行业配置
│   ├── {fund_code}/
│   │   ├── {year}_{quarter}.parquet
│   │   └── metadata.json
│   └── _index.parquet
│
├── top_holdings/             # 十大重仓
│   ├── {fund_code}/
│   │   ├── {year}_{quarter}.parquet
│   │   └── metadata.json
│   └── _index.parquet
│
└── change/                   # 持仓变动
    ├── {fund_code}/
    │   └── {year}.parquet
    └── _index.parquet
```

### 二级分类：衍生数据

```
fund/derivative/
├── factor/                   # 因子分析
│   ├── style/               # 风格因子
│   │   └── {fund_code}.parquet
│   │
│   ├── industry/            # 行业因子
│   │   └── {fund_code}.parquet
│   │
│   └── size/                # 规模因子
│       └── {fund_code}.parquet
│
├── score/                    # 基金评分
│   ├── performance/         # 业绩评分
│   │   └── {fund_code}.parquet
│   │
│   ├── risk/                # 风险评分
│   │   └── {fund_code}.parquet
│   │
│   └── overall/             # 综合评分
│       └── {fund_code}.parquet
│
└── prediction/               # 预测数据
    ├── nav/                 # 净值预测
    │   └── {date}.parquet
    │
    └── ranking/             # 排名预测
        └── {date}.parquet
```

---

## 📈 市场数据分类（一级分类）

### 二级分类：指数数据

```
market/index/
├── kline/                    # 指数 K 线
│   ├── daily/               # 日线
│   │   ├── {index_code}/
│   │   │   └── {year}.parquet
│   │   └── _index.parquet
│   │
│   ├── weekly/              # 周线
│   │   └── {index_code}/
│   │       └── {year}.parquet
│   │
│   └── monthly/             # 月线
│       └── {index_code}/
│           └── {year}.parquet
│
├── components/               # 成分股
│   ├── {index_code}/
│   │   ├── {date}.parquet
│   │   └── metadata.json
│   └── _index.parquet
│
└── weight/                   # 权重数据
    ├── {index_code}/
    │   ├── {date}.parquet
    │   └── metadata.json
    └── _index.parquet
```

### 二级分类：板块数据

```
market/sector/
├── industry/                 # 行业板块
│   ├── list.parquet         # 板块列表
│   ├── kline/               # 板块 K 线
│   │   └── {sector_code}/
│   │       └── {year}.parquet
│   └── components/          # 成分股
│       └── {sector_code}.parquet
│
├── concept/                  # 概念板块
│   ├── list.parquet         # 板块列表
│   ├── kline/               # 板块 K 线
│   │   └── {concept_code}/
│   │       └── {year}.parquet
│   └── components/          # 成分股
│       └── {concept_code}.parquet
│
└── region/                   # 地域板块
    ├── list.parquet         # 板块列表
    └── components/          # 成分股
        └── {region_code}.parquet
```

### 二级分类：市场情绪

```
market/sentiment/
├── fear_greed_index/         # 恐慌贪婪指数
│   └── {date}.parquet
│
├── breadth/                  # 市场广度
│   ├── advance_decline/     # 涨跌比
│   │   └── {date}.parquet
│   │
│   └── new_high_low/        # 新高新低
│       └── {date}.parquet
│
├── margin/                   # 融资融券
│   ├── balance/             # 融资余额
│   │   └── {date}.parquet
│   │
│   └── buying/              # 融资买入
│       └── {date}.parquet
│
└── liquidity/                # 流动性
    ├── turnover/            # 换手率
    │   └── {date}.parquet
    │
    └── volume/              # 成交量
        └── {date}.parquet
```

---

## 🎯 策略数据分类（一级分类）

### 二级分类：回测数据

```
strategy/backtest/
├── result/                   # 回测结果
│   ├── {strategy_id}/
│   │   ├── summary.json     # 回测摘要
│   │   ├── trades.parquet   # 交易记录
│   │   ├── equity.parquet   # 资金曲线
│   │   └── metrics.json     # 性能指标
│   └── _index.parquet
│
├── optimization/             # 参数优化
│   ├── {strategy_id}/
│   │   ├── params.parquet   # 参数组合
│   │   └── results.parquet  # 优化结果
│   └── _index.parquet
│
└── comparison/               # 策略对比
    ├── {date}.parquet       # 对比结果
    └── ranking.parquet      # 排名
```

### 二级分类：实盘数据

```
strategy/live/
├── orders/                   # 订单数据
│   ├── pending/             # 待成交
│   │   └── {date}.parquet
│   │
│   ├── filled/              # 已成交
│   │   └── {date}.parquet
│   │
│   └── cancelled/           # 已取消
│       └── {date}.parquet
│
├── positions/                # 持仓数据
│   ├── current.parquet      # 当前持仓
│   └── history/
│       └── {date}.parquet
│
├── equity/                   # 资金数据
│   ├── daily.parquet        # 每日资金
│   └── realtime.parquet     # 实时资金
│
└── risk/                     # 风控数据
    ├── exposure.parquet     # 风险敞口
    └── limit.parquet        # 风险限制
```

### 二级分类：分析数据

```
strategy/analysis/
├── performance/              # 业绩分析
│   ├── returns.parquet      # 收益分析
│   ├── risk.parquet         # 风险分析
│   └── attribution.parquet  # 归因分析
│
├── signal/                   # 信号分析
│   ├── entry.parquet        # 入场信号
│   ├── exit.parquet         # 出场信号
│   └── quality.parquet      # 信号质量
│
└── report/                   # 分析报告
    ├── daily/               # 日报
    │   └── {date}.html
    │
    ├── weekly/              # 周报
    │   └── {date}.html
    │
    └── monthly/             # 月报
        └── {date}.html
```

---

## 🗂️ 元数据管理

### 全局索引文件

每个二级分类目录下都有 `_index.parquet` 文件，记录该分类下所有文件的元数据：

```python
# _index.parquet 结构
{
    "file_path": "stock/market/kline/daily/000001/2024_qfq.parquet",
    "code": "000001",
    "year": 2024,
    "adjust_type": "qfq",
    "record_count": 244,
    "file_size_mb": 0.5,
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-12-31 23:59:59",
    "checksum": "abc123...",
    "quality_score": 0.98
}
```

### 元数据文件

每个股票/基金目录下都有 `metadata.json` 文件：

```json
{
    "code": "000001",
    "name": "平安银行",
    "market": "SZ",
    "industry": "银行",
    "sector": "金融",
    "list_date": "1991-04-03",
    "data_coverage": {
        "kline": {
            "start_date": "1991-04-03",
            "end_date": "2024-12-31",
            "completeness": 0.99
        },
        "financial": {
            "start_date": "2000-03-31",
            "end_date": "2024-09-30",
            "completeness": 0.95
        }
    },
    "last_updated": "2024-12-31 23:59:59"
}
```

---

## 🚀 实施步骤

### 步骤 1: 创建目录结构

```bash
# 创建一级分类目录
mkdir -p data/stock data/fund data/market data/strategy

# 创建股票二级分类
mkdir -p data/stock/{market,financial,technical,derivative}
mkdir -p data/stock/market/{kline,realtime,info,moneyflow}
mkdir -p data/stock/financial/{balance_sheet,income_statement,cash_flow,indicators,forecast,report}
mkdir -p data/stock/technical/{indicators,chip,pattern}
mkdir -p data/stock/derivative/{factor,score,prediction}

# 创建基金二级分类
mkdir -p data/fund/{basic,performance,portfolio,derivative}
mkdir -p data/fund/basic/{list,info,classification,dividend}
mkdir -p data/fund/performance/{nav,return,ranking,risk}
mkdir -p data/fund/portfolio/{stock_position,bond_position,industry_allocation,top_holdings,change}
mkdir -p data/fund/derivative/{factor,score,prediction}

# 创建市场二级分类
mkdir -p data/market/{index,sector,sentiment}
mkdir -p data/market/index/{kline,components,weight}
mkdir -p data/market/sector/{industry,concept,region}
mkdir -p data/market/sentiment/{fear_greed_index,breadth,margin,liquidity}

# 创建策略二级分类
mkdir -p data/strategy/{backtest,live,analysis}
mkdir -p data/strategy/backtest/{result,optimization,comparison}
mkdir -p data/strategy/live/{orders,positions,equity,risk}
mkdir -p data/strategy/analysis/{performance,signal,report}
```

### 步骤 2: 数据迁移脚本

```python
# backend/app/storage/migration/migrate_to_classified_structure.py
from pathlib import Path
import shutil
from loguru import logger

class DataMigration:
    """数据迁移工具"""
    
    def __init__(self):
        self.old_parquet_dir = Path("./data/parquet")
        self.new_data_dir = Path("./data")
    
    async def migrate_all(self):
        """迁移所有数据"""
        # 1. 迁移股票 K 线数据
        await self.migrate_stock_kline()
        
        # 2. 迁移基金数据
        await self.migrate_fund_data()
        
        # 3. 迁移市场数据
        await self.migrate_market_data()
        
        logger.info("数据迁移完成")
    
    async def migrate_stock_kline(self):
        """迁移股票 K 线数据"""
        old_kline_dir = self.old_parquet_dir / "kline"
        
        for code_dir in old_kline_dir.iterdir():
            if not code_dir.is_dir():
                continue
            
            code = code_dir.name
            
            for parquet_file in code_dir.glob("*.parquet"):
                # 解析文件名: 2024_qfq.parquet
                parts = parquet_file.stem.split("_")
                year = parts[0]
                adjust = parts[1] if len(parts) > 1 else "qfq"
                
                # 新路径
                new_path = (
                    self.new_data_dir / 
                    "stock" / "market" / "kline" / "daily" / 
                    code / f"{year}_{adjust}.parquet"
                )
                
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(parquet_file, new_path)
                
                logger.info(f"迁移: {parquet_file} -> {new_path}")
    
    async def migrate_fund_data(self):
        """迁移基金数据"""
        # 根据实际基金数据位置迁移
        pass
    
    async def migrate_market_data(self):
        """迁移市场数据"""
        # 迁移指数、板块等数据
        pass
```

---

## 📊 分类统计

### 数据分类统计

| 一级分类 | 二级分类数 | 三级分类数 | 数据类型 |
|---------|-----------|-----------|---------|
| **股票** | 4 | 20+ | K 线、财务、技术、衍生 |
| **基金** | 4 | 15+ | 基础、业绩、持仓、衍生 |
| **市场** | 3 | 10+ | 指数、板块、情绪 |
| **策略** | 3 | 10+ | 回测、实盘、分析 |
| **总计** | **14** | **55+** | - |

---

## 🎯 总结

本数据分类存储方案具备：

1. ✅ **清晰的层次结构** - 一级、二级、三级分类
2. ✅ **易于扩展** - 新增数据类型只需添加目录
3. ✅ **便于查询** - 按分类快速定位数据
4. ✅ **统一管理** - 元数据和索引文件
5. ✅ **自动化迁移** - 提供迁移脚本

实施后，数据存储将具备**企业级数据仓库**的管理能力！

---

**最后更新**: 2026-03-28  
**维护者**: 架构团队
