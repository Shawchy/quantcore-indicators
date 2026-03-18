# efinance 接口前端应用方案

## 一、方案概述

本方案旨在将后端已优化的 efinance 数据接口完整应用到前端，提供实时、高效、稳定的金融数据展示。

### 1.1 目标

- ✅ 整合所有 efinance 接口到前端 API 服务层
- ✅ 完善前端 TypeScript 类型定义
- ✅ 优化数据加载性能和用户体验
- ✅ 提供统一的数据源切换机制
- ✅ 实现反风控策略的前端适配

### 1.2 优势

| 特性 | 说明 |
|------|------|
| **免费** | efinance 完全免费，无需注册或积分 |
| **实时** | 数据来源于东方财富，实时性强 |
| **全面** | 覆盖 A 股、基金、期货、债券等多种金融工具 |
| **稳定** | 反风控机制保障，降低被封 IP 风险 |
| **高效** | 本地缓存 + 并发请求，响应速度快 |

---

## 二、efinance 接口总览

### 2.1 已实现的接口列表

后端 `efinance_adapter.py` 已实现以下接口：

| 序号 | 接口名称 | 方法 | 用途 | 缓存时间 |
|------|---------|------|------|----------|
| 1 | `get_stock_list()` | GET | 获取全部 A 股股票列表 | 30 分钟 |
| 2 | `get_stock_info(code)` | GET | 获取单只股票基本信息 | 10 分钟 |
| 3 | `get_stock_info_batch(codes)` | GET | 批量获取股票信息 | 10 分钟 |
| 4 | `get_kline(code, period)` | GET | 获取 K 线（支持 8 种周期） | 5 分钟 |
| 5 | `get_weekly_kline(code)` | GET | 获取周 K 线 | 30 分钟 |
| 6 | `get_monthly_kline(code)` | GET | 获取月 K 线 | 30 分钟 |
| 7 | `get_realtime_quote(code)` | GET | 获取实时行情快照（38 字段） | 60 秒 |
| 8 | `get_latest_quote(codes)` | GET | 批量获取最新行情 | 60 秒 |
| 9 | `get_deal_detail(code)` | GET | 获取成交明细 | 5 分钟 |
| 10 | `get_history_bill(code)` | GET | 获取历史资金流向 | 5 分钟 |
| 11 | `get_stock_bill_detail(code)` | GET | 获取日内分钟级资金流向 | 60 秒 |
| 12 | `get_today_bill(trade_date)` | GET | 获取当日资金流向 | 5 分钟 |
| 13 | `get_sector_list(sector_type)` | GET | 获取板块列表 | 5 分钟 |
| 14 | `get_sector_components(sector_code)` | GET | 获取板块成分股 | 5 分钟 |
| 15 | `get_belong_board(code)` | GET | 获取股票所属板块 | 10 分钟 |
| 16 | `get_members(index_code)` | GET | 获取指数成分股 | 5 分钟 |
| 17 | `get_chip_data(code)` | GET | 获取筹码数据（股东人数） | 5 分钟 |
| 18 | `get_daily_billboard(start_date, end_date)` | GET | 获取龙虎榜数据 | 5 分钟 |
| 19 | `get_top10_stock_holder_info(code, top)` | GET | 获取前十大股东信息 | 10 分钟 |
| 20 | `get_market_realtime_quotes(market_types)` | GET | 获取市场/板块实时行情 | 60 秒 |
| 21 | `get_financial_performance(code, report_date)` | GET | 获取财务业绩（季报） | 10 分钟 |
| 22 | `get_all_report_dates()` | GET | 获取所有报告期日期 | 30 分钟 |
| 23 | `get_historical_financial_performance(code, limit)` | GET | 获取历史多个季度财报 | 10 分钟 |

### 2.2 K 线周期支持

| 周期代码 | 周期名称 | efinance 参数 | 用途 |
|---------|---------|--------------|------|
| `1m` | 1 分钟线 | 1 | 超短线交易 |
| `5m` | 5 分钟线 | 5 | 日内交易 |
| `15m` | 15 分钟线 | 15 | 短线交易 |
| `30m` | 30 分钟线 | 30 | 短线交易 |
| `60m` | 60 分钟线 | 60 | 中线交易 |
| `daily` | 日线 | 101 | 日线级别（默认） |
| `weekly` | 周线 | 102 | 周线级别 |
| `monthly` | 月线 | 103 | 月线级别 |

---

## 三、前端 API 服务层设计

### 3.1 API 服务层结构

```
frontend/src/services/
├── api.ts              # 基础 API 配置和拦截器
├── efinance.ts         # efinance 专用 API（新增）
├── stock.ts            # 股票相关 API（整合）
├── market.ts           # 市场行情 API（整合）
├── moneyflow.ts        # 资金流向 API（整合）
├── sector.ts           # 板块相关 API（整合）
└── index.ts            # 统一导出
```

### 3.2 efinance.ts API 服务（新增）

```typescript
// frontend/src/services/efinance.ts
import api from './api'
import type {
  StockBasicInfo,
  KLineData,
  RealtimeQuote,
  ShareholderInfo,
  CapitalFlowItem,
  SectorInfo,
  BoardInfo,
  IndexComponent,
  ChipData,
  BillboardEntry,
  FinancialPerformance,
} from '../types'

/**
 * efinance 数据源 API 服务
 * 
 * 特点：
 * - 完全免费，无需注册
 * - 数据来源于东方财富
 * - 支持反风控策略
 * - 本地缓存优化
 */
export const efinanceApi = {
  // ========== 股票基本信息 ==========
  
  /**
   * 获取全部 A 股股票列表
   * 缓存时间：30 分钟
   */
  getStockList: () =>
    api.get<StockBasicInfo[]>('/efinance/stock/list'),
  
  /**
   * 获取单只股票基本信息
   * 缓存时间：10 分钟
   */
  getStockInfo: (code: string) =>
    api.get<StockBasicInfo>(`/efinance/stock/${code}/info`),
  
  /**
   * 批量获取股票信息
   * 缓存时间：10 分钟
   */
  getStockInfoBatch: (codes: string[]) =>
    api.post<StockBasicInfo[]>('/efinance/stock/info/batch', { codes }),
  
  // ========== K 线数据 ==========
  
  /**
   * 获取 K 线数据（支持 8 种周期）
   * 缓存时间：5 分钟
   * 
   * @param code 股票代码
   * @param period K 线周期：1m/5m/15m/30m/60m/daily/weekly/monthly
   * @param startDate 开始日期 YYYY-MM-DD
   * @param endDate 结束日期 YYYY-MM-DD
   * @param adjust 复权类型：qfq/hfq/no
   */
  getKline: (
    code: string,
    params?: {
      period?: string
      startDate?: string
      endDate?: string
      adjust?: string
    }
  ) =>
    api.get<KLineData[]>(`/efinance/stock/${code}/kline`, {
      params: {
        period: params?.period || 'daily',
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq',
      },
      timeout: 120000, // 2 分钟超时
    }),
  
  /**
   * 获取周 K 线数据
   * 缓存时间：30 分钟
   */
  getWeeklyKline: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
      adjust?: string
    }
  ) =>
    api.get<KLineData[]>(`/efinance/stock/${code}/kline/weekly`, {
      params: {
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq',
      },
      timeout: 120000,
    }),
  
  /**
   * 获取月 K 线数据
   * 缓存时间：30 分钟
   */
  getMonthlyKline: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
      adjust?: string
    }
  ) =>
    api.get<KLineData[]>(`/efinance/stock/${code}/kline/monthly`, {
      params: {
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq',
      },
      timeout: 120000,
    }),
  
  // ========== 实时行情 ==========
  
  /**
   * 获取单只股票实时行情快照（38 个字段）
   * 缓存时间：60 秒
   */
  getRealtimeQuote: (code: string) =>
    api.get<RealtimeQuote>(`/efinance/stock/${code}/realtime`),
  
  /**
   * 批量获取最新行情
   * 缓存时间：60 秒
   */
  getLatestQuotes: (codes: string[]) =>
    api.post<RealtimeQuote[]>('/efinance/stock/quotes/batch', { codes }),
  
  /**
   * 获取市场/板块实时行情
   * 支持 21 个市场类型
   * 缓存时间：60 秒
   */
  getMarketQuotes: (params?: {
    marketTypes?: string[]
    fs?: string
    fields?: string[]
  }) =>
    api.get<RealtimeQuote[]>('/efinance/market/quotes', { params }),
  
  // ========== 资金流向 ==========
  
  /**
   * 获取单只股票日内分钟级资金流向
   * 缓存时间：60 秒
   */
  getStockBillDetail: (code: string) =>
    api.get<CapitalFlowItem[]>(`/efinance/stock/${code}/bill-detail`),
  
  /**
   * 获取历史资金流向
   * 缓存时间：5 分钟
   */
  getHistoryBill: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
    }
  ) =>
    api.get<CapitalFlowItem[]>(`/efinance/stock/${code}/bill-history`, { params }),
  
  /**
   * 获取当日资金流向
   * 缓存时间：5 分钟
   */
  getTodayBill: (tradeDate?: string) =>
    api.get<CapitalFlowItem[]>('/efinance/moneyflow/today', {
      params: { trade_date: tradeDate },
    }),
  
  /**
   * 获取成交明细
   * 缓存时间：5 分钟
   */
  getDealDetail: (code: string, maxCount?: number) =>
    api.get('/efinance/stock/deal-detail', {
      params: { code, max_count: maxCount },
    }),
  
  // ========== 板块相关 ==========
  
  /**
   * 获取板块列表
   * 缓存时间：5 分钟
   */
  getSectorList: (sectorType: string = 'industry') =>
    api.get<SectorInfo[]>('/efinance/sector/list', {
      params: { sector_type: sectorType },
    }),
  
  /**
   * 获取板块成分股
   * 缓存时间：5 分钟
   */
  getSectorComponents: (sectorCode: string) =>
    api.get<string[]>(`/efinance/sector/${sectorCode}/components`),
  
  /**
   * 获取股票所属板块
   * 缓存时间：10 分钟
   */
  getStockBoards: (code: string) =>
    api.get<BoardInfo[]>(`/efinance/stock/${code}/boards`),
  
  /**
   * 获取指数成分股
   * 缓存时间：5 分钟
   */
  getIndexComponents: (indexCode: string) =>
    api.get<IndexComponent[]>(`/efinance/index/${indexCode}/components`),
  
  // ========== 股东信息 ==========
  
  /**
   * 获取前十大股东信息
   * 支持获取前 1-10 大股东
   * 缓存时间：10 分钟
   * 
   * @param code 股票代码
   * @param top 获取前 top 个股东，默认 4
   */
  getTop10Shareholders: (code: string, top: number = 4) =>
    api.get<ShareholderInfo[]>(`/efinance/stock/${code}/shareholders`, {
      params: { top },
    }),
  
  // ========== 筹码数据 ==========
  
  /**
   * 获取筹码数据（股东人数）
   * 缓存时间：5 分钟
   */
  getChipData: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
    }
  ) =>
    api.get<ChipData[]>(`/efinance/stock/${code}/chip`, { params }),
  
  // ========== 龙虎榜 ==========
  
  /**
   * 获取龙虎榜数据
   * 缓存时间：5 分钟
   */
  getDailyBillboard: (params?: {
    startDate?: string
    endDate?: string
  }) =>
    api.get<BillboardEntry[]>('/efinance/billboard/daily', { params }),
  
  /**
   * 获取个股龙虎榜历史
   * 缓存时间：5 分钟
   */
  getStockBillboardHistory: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
    }
  ) =>
    api.get<BillboardEntry[]>(`/efinance/billboard/${code}`, { params }),
  
  // ========== 财务业绩 ==========
  
  /**
   * 获取财务业绩（季报）
   * 缓存时间：10 分钟
   */
  getFinancialPerformance: (
    code: string,
    params?: {
      reportDate?: string  // 报告期：2024-03-31
      reportType?: string  // 报告类型：quarterly
    }
  ) =>
    api.get<FinancialPerformance[]>(`/efinance/stock/${code}/financial`, { params }),
  
  /**
   * 获取所有可用报告期
   * 缓存时间：30 分钟
   */
  getAllReportDates: () =>
    api.get<{ date: string; name: string }[]>('/efinance/financial/report-dates'),
  
  /**
   * 获取历史多个季度财报
   * 缓存时间：10 分钟
   */
  getHistoricalFinancialPerformance: (
    code: string,
    limit: number = 10
  ) =>
    api.get<FinancialPerformance[]>(`/efinance/stock/${code}/financial/history`, {
      params: { limit },
    }),
  
  // ========== 数据源控制 ==========
  
  /**
   * 获取 efinance 状态
   */
  getStatus: () =>
    api.get('/efinance/status'),
  
  /**
   * 获取请求统计
   */
  getStats: () =>
    api.get('/efinance/stats'),
}

export default efinanceApi
```

### 3.3 TypeScript 类型定义（新增）

```typescript
// frontend/src/types/efinance.ts

/** 股票基本信息 */
export interface StockBasicInfo {
  code: string           // 股票代码
  name: string           // 股票名称
  market: string         // 市场：SH/SZ
  industry?: string      // 所属行业
  area?: string          // 所属地区
  list_date?: string     // 上市日期
  total_shares?: number  // 总股本（股）
  float_shares?: number  // 流通股本（股）
}

/** K 线数据 */
export interface KLineData {
  code: string           // 股票代码
  date: string           // 日期：YYYYMMDD
  open: number           // 开盘价
  high: number           // 最高价
  low: number            // 最低价
  close: number          // 收盘价
  volume: number         // 成交量
  amount?: number        // 成交额
  turnover_rate?: number // 换手率（%）
  pre_close?: number     // 昨收
}

/** 实时行情快照（38 字段） */
export interface RealtimeQuote {
  code: string                    // 股票代码
  name: string                    // 股票名称
  price: number                   // 最新价
  change: number                  // 涨跌额
  change_pct: number              // 涨跌幅（%）
  high: number                    // 最高价
  low: number                     // 最低价
  open: number                    // 今开
  prev_close: number              // 昨收
  avg_price?: number              // 均价
  volume: number                  // 成交量
  amount: number                  // 成交额
  turnover_rate: number           // 换手率（%）
  volume_ratio?: number           // 量比
  pe_ratio?: number               // 市盈率
  pb_ratio?: number               // 市净率
  total_market_cap?: number       // 总市值
  float_market_cap?: number       // 流通市值
  limit_up?: number               // 涨停价
  limit_down?: number             // 跌停价
  bid_prices?: number[]           // 买盘价格 [买 1-买 5]
  ask_prices?: number[]           // 卖盘价格 [卖 1-卖 5]
  bid_volumes?: number[]          // 买盘数量 [买 1-买 5]
  ask_volumes?: number[]          // 卖盘数量 [卖 1-卖 5]
  quote_time?: string             // 报价时间
}

/** 股东信息 */
export interface ShareholderInfo {
  code: string                    // 股票代码
  report_date: string             // 报告期/更新日期
  holder_code: string             // 股东代码
  holder_name: string             // 股东名称
  hold_amount?: number            // 持股数（股）
  hold_ratio?: number             // 持股比例（%）
  change?: string                 // 增减描述（不变/新进/数值）
  change_rate?: number            // 变动率（%）
}

/** 资金流向条目 */
export interface CapitalFlowItem {
  code: string                    // 股票代码
  name: string                    // 股票名称
  trade_date: string              // 交易日期
  close_price?: number            // 收盘价
  change_pct?: number             // 涨跌幅（%）
  main_net_amount?: number        // 主力净流入（元）
  main_net_amount_rate?: number   // 主力净流入率（%）
  buy_elg_amount?: number         // 超大单净流入（元）
  buy_lg_amount?: number          // 大单净流入（元）
  buy_md_amount?: number          // 中单净流入（元）
  buy_sm_amount?: number          // 小单净流入（元）
}

/** 板块信息 */
export interface SectorInfo {
  code: string                    // 板块代码
  name: string                    // 板块名称
  sector_type: string             // 板块类型：industry/concept
  change_pct?: number             // 涨跌幅（%）
  volume?: number                 // 成交量
  amount?: number                 // 成交额
}

/** 股票所属板块 */
export interface BoardInfo {
  code: string                    // 板块代码
  name: string                    // 板块名称
  board_type: string              // 板块类型：行业板块/概念板块/地域板块
  close_price?: number            // 板块收盘价
  change_pct?: number             // 板块涨跌幅（%）
}

/** 指数成分股 */
export interface IndexComponent {
  index_code: string              // 指数代码
  index_name: string              // 指数名称
  code: string                    // 股票代码
  name: string                    // 股票名称
  weight?: number                 // 权重（%）
  industry?: string               // 所属行业
}

/** 筹码数据 */
export interface ChipData {
  code: string                    // 股票代码
  date: string                    // 公告日期
  shareholder_count?: number      // 股东人数
  avg_shares_per_holder?: number  // 户均持股数
  control_degree?: number         // 集中度
  top10_holders_ratio?: number    // 前十大股东持股比例
}

/** 龙虎榜单条目 */
export interface BillboardEntry {
  code: string                    // 股票代码
  name: string                    // 股票名称
  trade_date: string              // 上榜日期
  close_price?: number            // 收盘价
  change_pct?: number             // 涨跌幅（%）
  turnover_amount?: number        // 成交额
  net_amount?: number             // 龙虎榜净买额
  buy_amount?: number             // 龙虎榜买入额
  sell_amount?: number            // 龙虎榜卖出额
  reason?: string                 // 上榜原因
}

/** 财务业绩（季报） */
export interface FinancialPerformance {
  code: string                    // 股票代码
  name: string                    // 股票简称
  report_date: string             // 公告日期
  revenue?: number                // 营业收入
  revenue_growth?: number         // 营业收入同比增长（%）
  revenue_qoq?: number            // 营业收入季度环比（%）
  net_profit?: number             // 净利润
  net_profit_growth?: number      // 净利润同比增长（%）
  net_profit_qoq?: number         // 净利润季度环比（%）
  eps?: number                    // 每股收益
  bvps?: number                   // 每股净资产
  roe?: number                    // 净资产收益率（%）
  gross_margin?: number           // 销售毛利率（%）
  cfps?: number                   // 每股经营现金流量
}

/** 市场实时行情 */
export interface MarketQuote {
  code: string                    // 股票代码
  name: string                    // 股票名称
  change_pct?: number             // 涨跌幅（%）
  price?: number                  // 最新价
  high?: number                   // 最高
  low?: number                    // 最低
  open?: number                   // 今开
  change?: number                 // 涨跌额
  turnover_rate?: number          // 换手率
  volume_ratio?: number           // 量比
  pe_ratio?: number               // 动态市盈率
  volume?: number                 // 成交量
  amount?: number                 // 成交额
  prev_close?: number             // 昨日收盘
  total_market_cap?: number       // 总市值
  float_market_cap?: number       // 流通市值
  market_type?: string            // 市场类型
}
```

---

## 四、后端 API 路由设计

### 4.1 API 路由结构

```
backend/app/api/v1/endpoints/
├── efinance.py         # efinance 专用路由（新增）
├── stock.py            # 股票相关（整合）
├── market.py           # 市场行情（整合）
└── ...
```

### 4.2 efinance.py 路由（新增）

```python
"""
efinance 数据源 API 路由
提供完整的 efinance 接口封装
"""
from fastapi import APIRouter, Query, Path, HTTPException
from typing import List, Optional
from loguru import logger

from app.models.schemas import ResponseModel
from app.adapters.factory import data_source_manager

router = APIRouter(prefix="/efinance", tags=["efinance"])


# ========== 股票基本信息 ==========

@router.get("/stock/list", response_model=ResponseModel[List[dict]])
async def get_stock_list():
    """获取全部 A 股股票列表"""
    try:
        stocks = await data_source_manager.get_stock_list(source_type="efinance")
        return ResponseModel(data=[s.__dict__ for s in stocks])
    except Exception as e:
        logger.error(f"获取股票列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/info", response_model=ResponseModel[dict])
async def get_stock_info(code: str = Path(..., description="股票代码")):
    """获取单只股票基本信息"""
    try:
        stock = await data_source_manager.get_stock_info(
            code=code, source_type="efinance"
        )
        if not stock:
            return ResponseModel(success=False, code="NOT_FOUND", message="未找到股票")
        return ResponseModel(data=stock.__dict__)
    except Exception as e:
        logger.error(f"获取股票信息失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock/info/batch", response_model=ResponseModel[List[dict]])
async def get_stock_info_batch(codes: List[str]):
    """批量获取股票信息"""
    try:
        stocks = await data_source_manager.get_stock_info_batch(
            codes=codes, source_type="efinance"
        )
        return ResponseModel(data=[s.__dict__ for s in stocks])
    except Exception as e:
        logger.error(f"批量获取股票信息失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== K 线数据 ==========

@router.get("/stock/{code}/kline", response_model=ResponseModel[List[dict]])
async def get_kline(
    code: str = Path(..., description="股票代码"),
    period: str = Query("daily", description="K 线周期：1m/5m/15m/30m/60m/daily/weekly/monthly"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型：qfq/hfq/no"),
):
    """获取 K 线数据（支持 8 种周期）"""
    try:
        klines = await data_source_manager.get_kline(
            code=code,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
            period=period,
            source_type="efinance"
        )
        return ResponseModel(data=[k.__dict__ for k in klines])
    except Exception as e:
        logger.error(f"获取 K 线数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/kline/weekly", response_model=ResponseModel[List[dict]])
async def get_weekly_kline(
    code: str = Path(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    adjust: str = Query("qfq"),
):
    """获取周 K 线数据"""
    try:
        klines = await data_source_manager.get_weekly_kline(
            code=code, start_date=start_date, end_date=end_date, adjust=adjust,
            source_type="efinance"
        )
        return ResponseModel(data=[k.__dict__ for k in klines])
    except Exception as e:
        logger.error(f"获取周 K 线数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/kline/monthly", response_model=ResponseModel[List[dict]])
async def get_monthly_kline(
    code: str = Path(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    adjust: str = Query("qfq"),
):
    """获取月 K 线数据"""
    try:
        klines = await data_source_manager.get_monthly_kline(
            code=code, start_date=start_date, end_date=end_date, adjust=adjust,
            source_type="efinance"
        )
        return ResponseModel(data=[k.__dict__ for k in klines])
    except Exception as e:
        logger.error(f"获取月 K 线数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 实时行情 ==========

@router.get("/stock/{code}/realtime", response_model=ResponseModel[dict])
async def get_realtime_quote(code: str = Path(...)):
    """获取单只股票实时行情快照（38 个字段）"""
    try:
        quote = await data_source_manager.get_realtime_quote(
            code=code, source_type="efinance"
        )
        if not quote:
            return ResponseModel(success=False, code="NOT_FOUND", message="未找到行情")
        return ResponseModel(data=quote)
    except Exception as e:
        logger.error(f"获取实时行情失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock/quotes/batch", response_model=ResponseModel[List[dict]])
async def get_latest_quotes(codes: List[str]):
    """批量获取最新行情"""
    try:
        quotes = await data_source_manager.get_latest_quote(
            codes=codes, source_type="efinance"
        )
        if isinstance(quotes, dict):
            quotes = [quotes]
        return ResponseModel(data=quotes)
    except Exception as e:
        logger.error(f"批量获取行情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/quotes", response_model=ResponseModel[List[dict]])
async def get_market_quotes(
    market_types: Optional[str] = Query(None, description="市场类型列表，逗号分隔"),
    fs: Optional[str] = Query(None, description="高级筛选条件"),
    fields: Optional[str] = Query(None, description="自定义返回字段，逗号分隔"),
):
    """获取市场/板块实时行情（支持 21 个市场类型）"""
    try:
        market_types_list = market_types.split(",") if market_types else None
        fields_list = fields.split(",") if fields else None
        
        quotes = await data_source_manager.get_market_realtime_quotes(
            market_types=market_types_list,
            fs=fs,
            fields=fields_list,
            source_type="efinance"
        )
        return ResponseModel(data=[q.__dict__ for q in quotes])
    except Exception as e:
        logger.error(f"获取市场实时行情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 资金流向 ==========

@router.get("/stock/{code}/bill-detail", response_model=ResponseModel[List[dict]])
async def get_stock_bill_detail(code: str = Path(...)):
    """获取单只股票日内分钟级资金流向"""
    try:
        bill_detail = await data_source_manager.get_stock_bill_detail(
            code=code, source_type="efinance"
        )
        return ResponseModel(data=bill_detail)
    except Exception as e:
        logger.error(f"获取资金流向明细失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/bill-history", response_model=ResponseModel[List[dict]])
async def get_history_bill(
    code: str = Path(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """获取历史资金流向"""
    try:
        flows = await data_source_manager.get_history_bill(
            code=code,
            start_date=start_date,
            end_date=end_date,
            source_type="efinance"
        )
        return ResponseModel(data=[f.__dict__ for f in flows])
    except Exception as e:
        logger.error(f"获取历史资金流向失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/moneyflow/today", response_model=ResponseModel[List[dict]])
async def get_today_bill(trade_date: Optional[str] = Query(None)):
    """获取当日资金流向"""
    try:
        flows = await data_source_manager.get_today_bill(
            trade_date=trade_date, source_type="efinance"
        )
        return ResponseModel(data=[f.__dict__ for f in flows])
    except Exception as e:
        logger.error(f"获取当日资金流向失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/deal-detail", response_model=ResponseModel[List[dict]])
async def get_deal_detail(
    code: str = Query(...),
    max_count: int = Query(1000000, description="最大数据条数"),
):
    """获取成交明细"""
    try:
        deals = await data_source_manager.get_deal_detail(
            code=code, max_count=max_count, source_type="efinance"
        )
        return ResponseModel(data=deals)
    except Exception as e:
        logger.error(f"获取成交明细失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 板块相关 ==========

@router.get("/sector/list", response_model=ResponseModel[List[dict]])
async def get_sector_list(sector_type: str = Query("industry")):
    """获取板块列表"""
    try:
        sectors = await data_source_manager.get_sector_list(
            sector_type=sector_type, source_type="efinance"
        )
        return ResponseModel(data=[s.__dict__ for s in sectors])
    except Exception as e:
        logger.error(f"获取板块列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector/{sector_code}/components", response_model=ResponseModel[List[str]])
async def get_sector_components(sector_code: str = Path(...)):
    """获取板块成分股"""
    try:
        components = await data_source_manager.get_sector_components(
            sector_code=sector_code, source_type="efinance"
        )
        return ResponseModel(data=components)
    except Exception as e:
        logger.error(f"获取板块成分股失败 {sector_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/boards", response_model=ResponseModel[List[dict]])
async def get_stock_boards(code: str = Path(...)):
    """获取股票所属板块"""
    try:
        boards = await data_source_manager.get_belong_board(
            code=code, source_type="efinance"
        )
        return ResponseModel(data=[b.__dict__ for b in boards])
    except Exception as e:
        logger.error(f"获取股票所属板块失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/{index_code}/components", response_model=ResponseModel[List[dict]])
async def get_index_components(index_code: str = Path(...)):
    """获取指数成分股"""
    try:
        components = await data_source_manager.get_members(
            index_code=index_code, source_type="efinance"
        )
        return ResponseModel(data=[c.__dict__ for c in components])
    except Exception as e:
        logger.error(f"获取指数成分股失败 {index_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 股东信息 ==========

@router.get("/stock/{code}/shareholders", response_model=ResponseModel[List[dict]])
async def get_top10_shareholders(
    code: str = Path(...),
    top: int = Query(4, description="获取前 top 个股东，1-10", ge=1, le=10),
):
    """获取前十大股东信息"""
    try:
        shareholders = await data_source_manager.get_top10_stock_holder_info(
            code=code, top=top, source_type="efinance"
        )
        return ResponseModel(data=[s.__dict__ for s in shareholders])
    except Exception as e:
        logger.error(f"获取股东信息失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 筹码数据 ==========

@router.get("/stock/{code}/chip", response_model=ResponseModel[List[dict]])
async def get_chip_data(
    code: str = Path(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """获取筹码数据（股东人数）"""
    try:
        chip_data = await data_source_manager.get_chip_data(
            code=code,
            start_date=start_date,
            end_date=end_date,
            source_type="efinance"
        )
        return ResponseModel(data=[c.__dict__ for c in chip_data])
    except Exception as e:
        logger.error(f"获取筹码数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 龙虎榜 ==========

@router.get("/billboard/daily", response_model=ResponseModel[List[dict]])
async def get_daily_billboard(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """获取龙虎榜数据"""
    try:
        entries = await data_source_manager.get_daily_billboard(
            start_date=start_date,
            end_date=end_date,
            source_type="efinance"
        )
        return ResponseModel(data=[e.__dict__ for e in entries])
    except Exception as e:
        logger.error(f"获取龙虎榜数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/billboard/{code}", response_model=ResponseModel[List[dict]])
async def get_stock_billboard_history(
    code: str = Path(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """获取个股龙虎榜历史"""
    try:
        entries = await data_source_manager.get_daily_billboard(
            start_date=start_date,
            end_date=end_date,
            source_type="efinance"
        )
        # 筛选指定股票
        stock_entries = [e for e in entries if e.code == code]
        return ResponseModel(data=[e.__dict__ for e in stock_entries])
    except Exception as e:
        logger.error(f"获取龙虎榜历史失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 财务业绩 ==========

@router.get("/stock/{code}/financial", response_model=ResponseModel[List[dict]])
async def get_financial_performance(
    code: str = Path(...),
    report_date: Optional[str] = Query(None, description="报告期：2024-03-31"),
    report_type: str = Query("quarterly", description="报告类型"),
):
    """获取财务业绩（季报）"""
    try:
        performances = await data_source_manager.get_financial_performance(
            code=code,
            report_date=report_date,
            report_type=report_type,
            source_type="efinance"
        )
        return ResponseModel(data=[p.__dict__ for p in performances])
    except Exception as e:
        logger.error(f"获取财务业绩失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial/report-dates", response_model=ResponseModel[List[dict]])
async def get_all_report_dates():
    """获取所有可用报告期"""
    try:
        dates = await data_source_manager.get_all_report_dates(
            source_type="efinance"
        )
        return ResponseModel(data=dates)
    except Exception as e:
        logger.error(f"获取报告期日期失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/financial/history", response_model=ResponseModel[List[dict]])
async def get_historical_financial_performance(
    code: str = Path(...),
    limit: int = Query(10, description="获取最近 N 个季度", ge=1, le=20),
):
    """获取历史多个季度财报"""
    try:
        performances = await data_source_manager.get_historical_financial_performance(
            code=code,
            limit=limit,
            source_type="efinance"
        )
        return ResponseModel(data=[p.__dict__ for p in performances])
    except Exception as e:
        logger.error(f"获取历史财务业绩失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 数据源控制 ==========

@router.get("/status", response_model=ResponseModel[dict])
async def get_efinance_status():
    """获取 efinance 状态"""
    try:
        from app.adapters.efinance_adapter import EFinanceAdapter
        adapter = EFinanceAdapter()
        is_available = await adapter.initialize()
        return ResponseModel(data={
            "available": is_available,
            "source": "efinance",
            "version": "0.6.0"
        })
    except Exception as e:
        logger.error(f"获取 efinance 状态失败：{e}")
        return ResponseModel(success=False, code="ERROR", message=str(e))


@router.get("/stats", response_model=ResponseModel[dict])
async def get_efinance_stats():
    """获取请求统计信息"""
    try:
        from app.adapters.factory import data_source_manager
        stats = data_source_manager.get_stats("efinance")
        return ResponseModel(data=stats or {})
    except Exception as e:
        logger.error(f"获取统计信息失败：{e}")
        return ResponseModel(success=False, code="ERROR", message=str(e))
```

---

## 五、前端组件集成方案

### 5.1 需要新增/修改的组件

| 组件名称 | 路径 | 状态 | 说明 |
|---------|------|------|------|
| `EfinanceQuote.tsx` | `components/` | 新增 | efinance 实时行情展示 |
| `EfinanceKLine.tsx` | `components/` | 新增 | efinance K 线图（多周期） |
| `ShareholderTable.tsx` | `components/` | 新增 | 前十大股东表格 |
| `MoneyflowChart.tsx` | `components/` | 新增 | 资金流向图表 |
| `SectorPerformance.tsx` | `components/` | 新增 | 板块行情展示 |
| `StockDetail.tsx` | `pages/` | 修改 | 整合 efinance 数据 |
| `MarketQuotes.tsx` | `pages/` | 修改 | 整合市场行情 |

### 5.2 StockDetail.tsx 修改示例

```typescript
// frontend/src/pages/StockDetail.tsx
import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { efinanceApi } from '../services/efinance'
import type { RealtimeQuote, KLineData, ShareholderInfo } from '../types'

export const StockDetail: React.FC = () => {
  const { code } = useParams<{ code: string }>()
  const [quote, setQuote] = useState<RealtimeQuote | null>(null)
  const [klines, setKlines] = useState<KLineData[]>([])
  const [shareholders, setShareholders] = useState<ShareholderInfo[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    if (!code) return
    
    const fetchData = async () => {
      try {
        setLoading(true)
        // 并发获取数据
        const [quoteData, klineData, shareholderData] = await Promise.all([
          efinanceApi.getRealtimeQuote(code),
          efinanceApi.getKline(code, { period: 'daily' }),
          efinanceApi.getTop10Shareholders(code, 4),
        ])
        
        setQuote(quoteData.data)
        setKlines(klineData.data)
        setShareholders(shareholderData.data)
      } catch (error) {
        console.error('获取股票数据失败:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [code])
  
  if (loading) {
    return <div>加载中...</div>
  }
  
  return (
    <div>
      {/* 实时行情 */}
      {quote && (
        <RealtimeQuoteCard quote={quote} />
      )}
      
      {/* K 线图 */}
      <KLineChart klines={klines} />
      
      {/* 前十大股东 */}
      <ShareholderTable shareholders={shareholders} />
    </div>
  )
}
```

---

## 六、性能优化策略

### 6.1 前端优化

```typescript
// 1. 请求并发
const fetchData = async () => {
  const [quote, klines, shareholders] = await Promise.all([
    efinanceApi.getRealtimeQuote(code),
    efinanceApi.getKline(code),
    efinanceApi.getTop10Shareholders(code),
  ])
}

// 2. 请求缓存（React Query）
import { useQuery } from '@tanstack/react-query'

const useStockQuote = (code: string) => {
  return useQuery({
    queryKey: ['efinance', 'quote', code],
    queryFn: () => efinanceApi.getRealtimeQuote(code),
    staleTime: 60 * 1000, // 1 分钟内不重复请求
    refetchInterval: 30 * 1000, // 30 秒自动刷新
  })
}

// 3. 虚拟滚动（大数据列表）
import { useVirtualizer } from '@tanstack/react-virtual'

const VirtualTable = ({ data }) => {
  const parentRef = useRef()
  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 35,
  })
  
  return (
    <div ref={parentRef} style={{ height: 400, overflow: 'auto' }}>
      {virtualizer.getVirtualItems().map(virtualRow => (
        <div key={virtualRow.key}>{data[virtualRow.index].name}</div>
      ))}
    </div>
  )
}
```

### 6.2 后端优化

```python
# 1. 并发请求
async def get_stock_data(code: str):
    quote, klines, shareholders = await asyncio.gather(
        adapter.get_realtime_quote(code),
        adapter.get_kline(code),
        adapter.get_top10_stock_holder_info(code),
    )

# 2. 缓存策略
_cache_ttl = {
    'kline': 300,        # 5 分钟
    'quote': 60,         # 1 分钟
    'stock_info': 600,   # 10 分钟
}

# 3. 反风控
await adapter._rate_limit()  # 频率控制
adapter.record_request_success()  # 成功统计
```

---

## 七、数据源切换机制

### 7.1 前端数据源控制

```typescript
// frontend/src/store/slices/dataSourceSlice.ts
interface DataSourceState {
  currentSource: 'efinance' | 'tushare' | 'akshare'
  sources: {
    efinance: { enabled: boolean; priority: number }
    tushare: { enabled: boolean; priority: number }
    akshare: { enabled: boolean; priority: number }
  }
}

// 自动故障转移
const fetchWithFailover = async (apiCalls: Array<() => Promise<any>>) => {
  for (const call of apiCalls) {
    try {
      return await call()
    } catch (error) {
      console.warn('数据源失败，尝试下一个:', error)
    }
  }
  throw new Error('所有数据源均失败')
}
```

---

## 八、测试计划

### 8.1 单元测试

```typescript
// frontend/src/services/__tests__/efinance.test.ts
import { efinanceApi } from '../efinance'

describe('efinanceApi', () => {
  it('should fetch realtime quote', async () => {
    const response = await efinanceApi.getRealtimeQuote('600519')
    expect(response.data).toHaveProperty('price')
    expect(response.data).toHaveProperty('change_pct')
  })
  
  it('should fetch kline data', async () => {
    const response = await efinanceApi.getKline('600519', { period: 'daily' })
    expect(response.data).toBeInstanceOf(Array)
    expect(response.data[0]).toHaveProperty('date')
    expect(response.data[0]).toHaveProperty('close')
  })
})
```

### 8.2 集成测试

```python
# backend/tests/test_efinance_api.py
async def test_get_realtime_quote(client):
    response = await client.get("/efinance/stock/600519/realtime")
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'price' in data['data']
```

---

## 九、部署方案

### 9.1 环境变量配置

```bash
# frontend/.env
VITE_API_BASE_URL=/api/v1
VITE_DEFAULT_DATA_SOURCE=efinance
VITE_ENABLE_DATA_SOURCE_SWITCH=true
```

### 9.2 Docker 配置

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - EFANCE_ENABLED=true
      - TUSHARE_ENABLED=false
    ports:
      - "8000:8000"
  
  frontend:
    build: ./frontend
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    ports:
      - "3000:80"
```

---

## 十、总结

### 10.1 实施步骤

1. **第一阶段**：后端 API 路由开发（2 天）
   - 创建 `efinance.py` 路由文件
   - 实现所有接口端点
   - 编写单元测试

2. **第二阶段**：前端 API 服务层（2 天）
   - 创建 `efinance.ts` 服务文件
   - 完善 TypeScript 类型定义
   - 编写集成测试

3. **第三阶段**：前端组件开发（3 天）
   - 新增专用组件
   - 修改现有页面
   - UI/UX 优化

4. **第四阶段**：测试与优化（2 天）
   - 性能测试
   - 压力测试
   - 用户体验优化

### 10.2 预期效果

- ✅ **数据完整性**：覆盖 23 个核心接口
- ✅ **响应速度**：平均响应时间 < 500ms
- ✅ **稳定性**：99.9% 可用性
- ✅ **用户体验**：流畅的数据展示和交互

### 10.3 风险控制

- **反风控策略**：频率控制、请求头伪装、缓存机制
- **故障转移**：多数据源自动切换
- **错误处理**：完善的错误提示和重试机制
- **监控告警**：实时监控 API 健康状态

---

**文档版本**：v1.0  
**创建日期**：2026-03-18  
**最后更新**：2026-03-18  
**维护者**：Quant 团队
