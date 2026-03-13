# 资金流向模块开发报告

## 📋 开发时间
2026 年 3 月 13 日 00:30

## ✅ 已完成的工作

### 1. ✅ 添加 Tushare moneyflow_mkt_dc 接口适配器方法

**文件**: `backend/app/adapters/tushare_adapter.py`

**新增方法**: `get_market_moneyflow_dc()`

**功能**:
- 获取大盘资金流向数据（东方财富数据源）
- 接口：moneyflow_mkt_dc
- 积分要求：120积分可试用，6000积分可正式调取
- 支持参数：
  - `trade_date`: 交易日期（YYYYMMDD格式）
  - `start_date`: 开始日期（YYYYMMDD格式）
  - `end_date`: 结束日期（YYYYMMDD格式）

**返回数据字段**:
- `trade_date`: 交易日期
- `close_sh`: 上证收盘价（点）
- `pct_change_sh`: 上证涨跌幅(%)
- `close_sz`: 深证收盘价（点）
- `pct_change_sz`: 深证涨跌幅(%)
- `net_amount`: 今日主力净流入净额（元）
- `net_amount_rate`: 今日主力净流入净占比%
- `buy_elg_amount`: 今日超大单净流入净额（元）
- `buy_elg_amount_rate`: 今日超大单净流入净占比%
- `buy_lg_amount`: 今日大单净流入净额（元）
- `buy_lg_amount_rate`: 今日大单净流入净占比%
- `buy_md_amount`: 今日中单净流入净额（元）
- `buy_md_amount_rate`: 今日中单净流入净占比%
- `buy_sm_amount`: 今日小单净流入净额（元）
- `buy_sm_amount_rate`: 今日小单净流入净占比%

**代码示例**:
```python
async def get_market_moneyflow_dc(
    self,
    trade_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取大盘资金流向数据（东方财富数据源）
    接口：moneyflow_mkt_dc
    积分：120积分可试用，6000积分可正式调取
    """
    try:
        # 检查适配器是否已初始化
        if not self._is_initialized or not self._pro:
            logger.error("Tushare 适配器未初始化")
            return []
        
        # 检查权限（120积分可试用，6000积分可正式调取）
        if self._points_manager:
            if not self._points_manager.check_and_log_permission("moneyflow_mkt_dc", "akshare"):
                logger.warning(f"Tushare 大盘资金流向需要 6000 积分，当前只有{self._points_manager.get_points()}分，使用备选数据源")
                return []
        
        # 调用 Tushare API
        df = await asyncio.to_thread(
            self._pro.moneyflow_mkt_dc,
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        
        # 处理数据...
        return result
    except Exception as e:
        logger.error(f"获取大盘资金流向数据失败：{e}")
        return []
```

---

## ⏳ 待完成的工作

### 2. 创建资金流向数据模型

**文件**: `backend/app/models/schemas.py`

**需要添加**:
```python
from pydantic import BaseModel
from typing import Optional

class MarketMoneyflowData(BaseModel):
    """大盘资金流向数据模型"""
    trade_date: str
    close_sh: Optional[float] = None
    pct_change_sh: Optional[float] = None
    close_sz: Optional[float] = None
    pct_change_sz: Optional[float] = None
    net_amount: Optional[float] = None
    net_amount_rate: Optional[float] = None
    buy_elg_amount: Optional[float] = None
    buy_elg_amount_rate: Optional[float] = None
    buy_lg_amount: Optional[float] = None
    buy_lg_amount_rate: Optional[float] = None
    buy_md_amount: Optional[float] = None
    buy_md_amount_rate: Optional[float] = None
    buy_sm_amount: Optional[float] = None
    buy_sm_amount_rate: Optional[float] = None
```

---

### 3. 创建资金流向服务层

**文件**: `backend/app/services/moneyflow_service.py`

**需要实现**:
```python
from app.adapters import data_source_manager
from app.models.schemas import MarketMoneyflowData
from typing import List, Optional

class MoneyflowService:
    async def get_market_moneyflow(
        self,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[MarketMoneyflowData]:
        """获取大盘资金流向数据"""
        data = await data_source_manager.get_market_moneyflow_dc(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        return [MarketMoneyflowData(**item) for item in data]
```

---

### 4. 创建资金流向 API 端点

**文件**: `backend/app/api/v1/endpoints/moneyflow.py`

**需要实现**:
```python
from fastapi import APIRouter, Query
from app.models.schemas import ResponseModel
from app.api.deps import CurrentUser
from app.services.moneyflow_service import MoneyflowService

router = APIRouter()
moneyflow_service = MoneyflowService()

@router.get("/market", response_model=ResponseModel[list])
async def get_market_moneyflow(
    current_user: CurrentUser,
    trade_date: Optional[str] = Query(None, description="交易日期 YYYYMMDD"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
):
    """获取大盘资金流向数据"""
    data = await moneyflow_service.get_market_moneyflow(
        trade_date=trade_date,
        start_date=start_date,
        end_date=end_date
    )
    return ResponseModel(data=[item.dict() for item in data])
```

---

### 5. 创建前端资金流向组件

**文件**: `frontend/src/components/MarketMoneyflowCard.tsx`

**需要实现**:
- 显示大盘资金流向数据
- 使用 ECharts 绘制资金流向图表
- 显示主力净流入、超大单、大单、中单、小单净流入

---

### 6. 集成资金流向到首页概览

**文件**: `frontend/src/pages/Dashboard.tsx`

**需要修改**:
- 添加资金流向卡片到首页
- 调用资金流向 API
- 显示实时资金流向数据

---

## 📊 API 端点设计

### GET /api/v1/moneyflow/market

**描述**: 获取大盘资金流向数据

**参数**:
- `trade_date`: 交易日期（YYYYMMDD格式，可选）
- `start_date`: 开始日期（YYYYMMDD格式，可选）
- `end_date`: 结束日期（YYYYMMDD格式，可选）

**响应**:
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "获取成功",
  "data": [
    {
      "trade_date": "20240930",
      "close_sh": 3336.50,
      "pct_change_sh": 8.06,
      "close_sz": 10529.76,
      "pct_change_sz": 10.67,
      "net_amount": -35700113408.00,
      "net_amount_rate": -2.15,
      "buy_elg_amount": -6500884480.00,
      "buy_elg_amount_rate": -0.39,
      "buy_lg_amount": -29199228928.00,
      "buy_lg_amount_rate": -1.76,
      "buy_md_amount": 12345678901.00,
      "buy_md_amount_rate": 0.74,
      "buy_sm_amount": 23456789012.00,
      "buy_sm_amount_rate": 1.41
    }
  ]
}
```

---

## 🎯 娡块功能

### 后端功能
1. ✅ Tushare API 适配器方法
2. ⏳ 数据模型定义
3. ⏳ 服务层实现
4. ⏳ API 端点实现

### 前端功能
1. ⏳ 资金流向卡片组件
2. ⏳ 首页集成
3. ⏳ API 调用
4. ⏳ 数据展示

---

## 📝 后续步骤

1. **创建数据模型**: 在 `schemas.py` 中添加 `MarketMoneyflowData` 模型
2. **创建服务层**: 实现 `MoneyflowService` 类
3. **创建 API 端点**: 实现 `/api/v1/moneyflow/market` 端点
4. **创建前端组件**: 实现 `MarketMoneyflowCard` 组件
5. **集成到首页**: 在 Dashboard 页面添加资金流向卡片

---

## ✅ 总结

**已完成**: 1/6 (17%)

**主要工作**:
- ✅ 添加了 Tushare moneyflow_mkt_dc 接口适配器方法
- ✅ 支持日期范围查询
- ✅ 支持积分权限检查
- ✅ 完整的数据字段映射

**下一步**: 继续实现数据模型、服务层、API 端点和前端组件

---

**开发完成时间**: 2026-03-13 00:30  
**开发者**: AI Assistant  
**状态**: ✅ 适配器方法已完成，继续开发中
