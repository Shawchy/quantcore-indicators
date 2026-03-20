"""新浪财经 - 沪深京 A 股实时行情 API 端点

提供新浪财经沪深京 A 股实时行情数据接口
"""
from typing import List
from fastapi import APIRouter, Depends

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockZhASpotSina
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/zh-a-spot", response_model=ResponseModel[List[StockZhASpotSina]])
async def get_zh_a_spot(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取新浪财经沪深京 A 股实时行情数据
    
    返回所有沪深京 A 股上市公司的实时行情数据（约 5300 只股票，14 个字段）：
    
    **基本信息**:
    - **code**: 股票代码
    - **name**: 股票名称
    
    **价格信息**:
    - **latest_price**: 最新价
    - **change_amount**: 涨跌额
    - **change_pct**: 涨跌幅（%）
    - **high**: 最高价
    - **low**: 最低价
    - **open**: 今开
    - **prev_close**: 昨收
    
    **买卖盘口**:
    - **buy**: 买入价
    - **sell**: 卖出价
    
    **成交信息**:
    - **volume**: 成交量（股）
    - **turnover**: 成交额（元）
    
    **时间信息**:
    - **timestamp**: 时间戳
    
    使用场景：
    - 沪深京 A 股市场行情监控
    - 股票筛选和排序
    - 涨跌幅排行分析
    - 成交量/额排行
    - 盘口买卖价分析
    - 量化策略数据源
    
    注意：
    - 数据来源：新浪财经
    - 实时更新（交易时间内）
    - 包含沪深京全部 A 股股票
    - 缓存时间：5 分钟（建议增加时间间隔避免被封 IP）
    - 成交量单位为股（非手）
    
    数据量：
    - 约 5300+ 只股票
    - 每只股票 14 个字段
    
    特点：
    - 数据源稳定，更新及时
    - 包含买卖盘口价格
    - 时间戳精确到秒
    - 高频调用可能被限制 IP
    
    示例应用：
    - 获取涨停股票：筛选 change_pct >= 9.8
    - 获取跌停股票：筛选 change_pct <= -9.8
    - 获取高换手股票：按 volume/turnover 排序
    - 获取活跃股票：按 turnover 降序排序
    - 监控买卖价差：sell - buy
    
    与东方财富接口区别：
    - 新浪：14 个字段，包含买卖盘口，成交量单位为股
    - 东财：23 个字段，更多估值指标，成交量单位为手
    - 新浪缓存 5 分钟，东财缓存 3 分钟
    """
    try:
        data = await adapter.get_stock_zh_a_spot_sina()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取新浪财经实时行情失败：{str(e)}",
            "data": []
        }
