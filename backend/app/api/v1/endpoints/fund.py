"""
基金 API 路由

提供基金基本信息、净值、持仓等接口
"""
from fastapi import APIRouter, Query, Path, HTTPException
from typing import List, Optional, Union, Dict
from loguru import logger
import asyncio

from app.models.schemas import ResponseModel, FundInfo
from app.adapters.factory import data_source_manager
from app.services.smart_loader import smart_loader

router = APIRouter(tags=["基金信息"])

# 基金 API 超时配置（秒）
FUND_API_TIMEOUT = 45  # 基金数据获取超时时间


# ===== 具体路径放在前面 =====

@router.get("/base-info/{fund_code}", response_model=ResponseModel[Union[FundInfo, List[FundInfo]]])
async def get_fund_base_info(
    fund_code: str = Path(..., description="基金代码（6 位）或多个基金代码（逗号分隔）")
):
    """
    获取基金基本信息
    
    Args:
        fund_code: 6 位基金代码，支持多个代码（逗号分隔）
            - 单只基金：'161725'
            - 多只基金：'161725,005827'
    
    Returns:
        单只基金返回 FundInfo 对象
        多只基金返回 FundInfo 列表
        
    Examples:
        # 获取单只基金
        GET /api/v1/fund/base-info/161725
        
        # 获取多只基金
        GET /api/v1/fund/base-info/161725,005827
    """
    try:
        # 判断是单只还是多只
        if ',' in fund_code:
            # 多只基金
            fund_codes = [code.strip() for code in fund_code.split(',') if code.strip()]
            
            if not fund_codes:
                return ResponseModel(
                    success=False,
                    code="INVALID_PARAM",
                    message="基金代码不能为空"
                )
            
            # 批量获取 - 直接使用数据源（批量操作不适合缓存）
            fund_list = await data_source_manager.get_fund_base_info(
                fund_codes=fund_codes,
                source_type="efinance"
            )
            
            if not fund_list:
                return ResponseModel(
                    success=False,
                    code="NOT_FOUND",
                    message="未找到基金信息"
                )
            
            return ResponseModel(data=fund_list)
        else:
            # 单只基金 - 使用智能加载器（带缓存）
            fund_info = await data_source_manager.get_fund_base_info(
                fund_codes=fund_code.strip(),
                source_type="efinance"
            )
            
            if not fund_info:
                return ResponseModel(
                    success=False,
                    code="NOT_FOUND",
                    message=f"未找到基金：{fund_code}"
                )
            
            return ResponseModel(data=fund_info)
    
    except Exception as e:
        logger.error(f"获取基金基本信息失败 {fund_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime-rate/{fund_codes}", response_model=ResponseModel[Union[dict, List[dict]]])
async def get_fund_realtime_increase_rate(
    fund_codes: str = Path(..., description="6 位基金代码或多个基金代码（逗号分隔）")
):
    """
    获取基金实时估算涨跌幅度
    
    Args:
        fund_codes: 6 位基金代码，支持多个代码（逗号分隔）
            - 单只基金：'161725'
            - 多只基金：'161725,005827'
    
    Returns:
        单只基金返回 dict 对象
        多只基金返回 dict 列表
        每个包含：
        - code: 基金代码
        - name: 基金名称
        - net_value: 最新净值
        - nav_date: 最新净值公开日期
        - estimate_time: 估算时间
        - estimate_change_pct: 估算涨跌幅
        
    Examples:
        # 获取单只基金实时估算涨跌幅
        GET /api/v1/fund/realtime-rate/161725
        
        # 获取多只基金实时估算涨跌幅
        GET /api/v1/fund/realtime-rate/161725,005827
    """
    try:
        # 判断是单只还是多只
        if ',' in fund_codes:
            # 多只基金 - 批量获取直接使用数据源
            fund_code_list = [code.strip() for code in fund_codes.split(',') if code.strip()]
            
            if not fund_code_list:
                return ResponseModel(
                    success=False,
                    code="INVALID_PARAM",
                    message="基金代码不能为空"
                )
            
            # 使用异步超时控制
            rate_list = await asyncio.wait_for(
                data_source_manager.get_fund_realtime_increase_rate(
                    fund_codes=fund_code_list,
                    source_type="efinance"
                ),
                timeout=FUND_API_TIMEOUT
            )
            
            if not rate_list:
                return ResponseModel(
                    success=False,
                    code="NOT_FOUND",
                    message="未找到基金实时估算数据"
                )
            
            return ResponseModel(data=rate_list)
        else:
            # 单只基金 - 实时数据不使用缓存（变化频繁）
            fund_code = fund_codes.strip()
            
            if not fund_code:
                return ResponseModel(
                    success=False,
                    code="INVALID_PARAM",
                    message="基金代码不能为空"
                )
            
            # 使用异步超时控制
            rate_info = await asyncio.wait_for(
                data_source_manager.get_fund_realtime_increase_rate(
                    fund_codes=fund_code,
                    source_type="efinance"
                ),
                timeout=FUND_API_TIMEOUT
            )
            
            if not rate_info:
                return ResponseModel(
                    success=False,
                    code="NOT_FOUND",
                    message=f"未找到基金实时估算数据：{fund_code}"
                )
            
            return ResponseModel(data=rate_info)
    
    except asyncio.TimeoutError:
        logger.warning(f"获取基金实时估算涨跌幅超时 {fund_codes}（超过{FUND_API_TIMEOUT}秒）")
        raise HTTPException(
            status_code=504,
            detail=f"数据源响应超时（{FUND_API_TIMEOUT}秒），请稍后重试"
        )
    except Exception as e:
        logger.error(f"获取基金实时估算涨跌幅失败 {fund_codes}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history/batch", response_model=ResponseModel[dict])
async def get_fund_quote_history_multi(
    fund_codes: List[str] = Query(..., description="基金代码列表"),
    pz: int = Query(40000, description="页码，默认 40000 获取全部历史数据")
):
    """
    批量获取多只基金历史净值数据
    
    Args:
        fund_codes: 基金代码列表
        pz: 页码，默认 40000 获取全部历史数据
    
    Returns:
        字典，key = 基金代码，value = 对应净值数据列表
        
    Examples:
        # 批量获取多只基金历史净值
        POST /api/v1/fund/history/batch
        Body: ["161725", "005918"]
        
        # 获取最近 100 条
        POST /api/v1/fund/history/batch?pz=100
    """
    try:
        if not fund_codes:
            return ResponseModel(
                success=False,
                code="INVALID_PARAM",
                message="基金代码列表不能为空"
            )
        
        # 批量获取历史数据 - 直接使用数据源（批量操作）
        history_dict = await data_source_manager.get_fund_quote_history_multi(
            fund_codes=fund_codes,
            pz=pz,
            source_type="efinance"
        )
        
        if not history_dict:
            return ResponseModel(
                success=False,
                code="NOT_FOUND",
                message="未找到基金历史净值数据"
            )
        
        total_count = sum(len(v) for v in history_dict.values())
        logger.info(f"批量获取 {len(fund_codes)} 只基金历史净值数据成功：共{total_count}条")
        return ResponseModel(data=history_dict)
    
    except Exception as e:
        logger.error(f"批量获取基金历史净值数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== 通用路径放在后面 =====

@router.get("/codes", response_model=ResponseModel[List[dict]])
async def get_fund_codes(
    fund_type: Optional[str] = Query(
        None,
        description="基金类型：zq=债券/gp=股票/etf=ETF/hh=混合/zs=指数/fof=FOF/qdii=QDII，空=全部"
    )
):
    """
    获取天天基金网公开的全部公募基金名单
    
    Args:
        fund_type: 基金类型
            - 'zq': 债券类型基金
            - 'gp': 股票类型基金
            - 'etf': ETF 基金
            - 'hh': 混合型基金
            - 'zs': 指数型基金
            - 'fof': FOF 基金
            - 'qdii': QDII 型基金
            - None 或不传：全部类型
    
    Returns:
        基金代码列表
        
    Examples:
        # 获取全部类型基金
        GET /api/v1/fund/codes
        
        # 获取股票型基金
        GET /api/v1/fund/codes?fund_type=gp
        
        # 获取 ETF 基金
        GET /api/v1/fund/codes?fund_type=etf
    """
    try:
        # 基金代码列表变化不频繁，适合缓存（每日更新）
        fund_list = await data_source_manager.get_fund_codes(
            fund_type=fund_type,
            source_type="efinance"
        )
        
        if not fund_list:
            return ResponseModel(
                success=False,
                code="NOT_FOUND",
                message=f"未找到基金代码列表（类型：{fund_type or '全部'}）"
            )
        
        logger.info(f"获取基金代码列表成功：{len(fund_list)}条")
        return ResponseModel(data=fund_list)
    
    except Exception as e:
        logger.error(f"获取基金代码列表失败（类型：{fund_type}）: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{fund_code}/position", response_model=ResponseModel[List[dict]])
async def get_fund_invest_position(
    fund_code: str = Path(..., description="基金代码（6 位）"),
    dates: Optional[str] = Query(
        None,
        description="日期或日期列表（逗号分隔），如：2021-12-31 或 2021-12-31,2021-09-30，空=最新"
    )
):
    """
    获取基金持仓占比数据（前十大重仓股）
    
    Args:
        fund_code: 基金代码（6 位）
        dates: 日期或日期列表（逗号分隔）
            - 不传或空：最新公开日期
            - '2021-12-31': 单个公开持仓日期
            - '2021-12-31,2021-09-30': 多个公开持仓日期
    
    Returns:
        基金持仓占比数据列表，包含：
        - fund_code: 基金代码
        - stock_code: 股票代码
        - stock_name: 股票简称
        - position_ratio: 持仓占比（%）
        - change: 较上期变化（%）
        - report_date: 公开日期
        
    Examples:
        # 获取最新公开的持仓数据
        GET /api/v1/fund/161725/position
        
        # 获取单个日期的持仓数据
        GET /api/v1/fund/161725/position?dates=2021-12-31
        
        # 获取多个日期的持仓数据
        GET /api/v1/fund/161725/position?dates=2021-12-31,2021-09-30
    """
    try:
        # 解析 dates 参数
        dates_param = None
        if dates:
            date_list = [d.strip() for d in dates.split(',') if d.strip()]
            if len(date_list) == 1:
                dates_param = date_list[0]
            else:
                dates_param = date_list
        
        # 基金持仓数据变化不频繁（季度更新），适合缓存
        position_list = await data_source_manager.get_fund_invest_position(
            fund_code=fund_code,
            dates=dates_param,
            source_type="efinance"
        )
        
        if not position_list:
            return ResponseModel(
                success=False,
                code="NOT_FOUND",
                message=f"未找到基金持仓数据（代码：{fund_code}, 日期：{dates or '最新'}）"
            )
        
        logger.info(f"获取基金 {fund_code} 持仓占比数据成功：{len(position_list)}条")
        return ResponseModel(data=position_list)
    
    except Exception as e:
        logger.error(f"获取基金持仓占比数据失败 {fund_code} (dates={dates}): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{fund_code}/history", response_model=ResponseModel[List[dict]])
async def get_fund_quote_history(
    fund_code: str = Path(..., description="基金代码（6 位）"),
    pz: int = Query(40000, description="页码，默认 40000 获取全部历史数据")
):
    """
    获取单只基金历史净值数据
    
    Args:
        fund_code: 基金代码（6 位）
        pz: 页码，默认 40000 获取全部历史数据
    
    Returns:
        基金历史净值数据列表，包含：
        - fund_code: 基金代码
        - date: 日期
        - unit_nav: 单位净值
        - accumulated_nav: 累计净值
        - change_pct: 涨跌幅（%）
        
    Examples:
        # 获取全部历史净值
        GET /api/v1/fund/161725/history
        
        # 获取最近 100 条
        GET /api/v1/fund/161725/history?pz=100
    """
    try:
        # 使用智能加载器获取基金历史净值（带缓存）
        history_list = await smart_loader.get_fund_nav(
            code=fund_code,
            use_cache=True
        )
        
        # 如果缓存未命中或数据为空，从 API 获取
        if not history_list:
            history_list = await data_source_manager.get_fund_quote_history(
                fund_code=fund_code,
                pz=pz,
                source_type="efinance"
            )
        
        if not history_list:
            return ResponseModel(
                success=False,
                code="NOT_FOUND",
                message=f"未找到基金历史净值数据（代码：{fund_code}）"
            )
        
        logger.info(f"获取基金 {fund_code} 历史净值数据成功：{len(history_list)}条")
        return ResponseModel(data=history_list)
    
    except Exception as e:
        logger.error(f"获取基金历史净值数据失败 {fund_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{fund_code}/period-change", response_model=ResponseModel[List[dict]])
async def get_fund_period_change(
    fund_code: str = Path(..., description="基金代码（6 位）")
):
    """
    获取基金阶段涨跌幅度
    
    Args:
        fund_code: 基金代码（6 位）
    
    Returns:
        基金阶段涨跌数据列表，包含：
        - fund_code: 基金代码
        - period: 时间段（如：近一周、近一月、近三月、近六月、近一年、近两年、近三年、近五年、今年以来、成立以来）
        - return_rate: 收益率（%）
        - avg_return: 同类平均（%）
        - rank: 同类排行
        - total_count: 同类总数
        - rank_rate: 排名百分比（rank/total_count，越低越好）
        
    Examples:
        # 获取基金阶段涨跌幅
        GET /api/v1/fund/161725/period-change
        
        # 查看近一年表现
        # 返回数据中包含近一年、近三年等不同时间段的收益率和排名
    """
    try:
        # 基金阶段涨跌幅每日更新，适合缓存
        period_list = await data_source_manager.get_fund_period_change(
            fund_code=fund_code,
            source_type="efinance"
        )
        
        if not period_list:
            return ResponseModel(
                success=False,
                code="NOT_FOUND",
                message=f"未找到基金阶段涨跌幅数据（代码：{fund_code}）"
            )
        
        logger.info(f"获取基金 {fund_code} 阶段涨跌幅成功：{len(period_list)}个时间段")
        return ResponseModel(data=period_list)
    
    except Exception as e:
        logger.error(f"获取基金阶段涨跌幅失败 {fund_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{fund_code}/assets", response_model=ResponseModel[List[dict]])
async def get_fund_assets_allocation(
    fund_code: str = Path(..., description="基金代码（6 位）"),
    dates: Optional[str] = Query(
        None,
        description="日期或日期列表（逗号分隔），如：2021-12-31 或 2021-12-31,2021-06-30，空=最新"
    )
):
    """
    获取基金资产配置比例（不同类型占比）
    
    Args:
        fund_code: 基金代码（6 位）
        dates: 日期或日期列表（逗号分隔）
            - 不传或空：最新公开日期
            - '2021-12-31': 单个公开持仓日期
            - '2021-12-31,2021-06-30': 多个公开持仓日期
    
    Returns:
        基金资产配置比例数据列表，包含：
        - fund_code: 基金代码
        - report_date: 公开日期
        - stock_ratio: 股票比重（%）
        - bond_ratio: 债券比重（%）
        - cash_ratio: 现金比重（%）
        - other_ratio: 其他比重（%）
        - total_scale: 总规模（亿元）
        
    Examples:
        # 获取最新资产配置
        GET /api/v1/fund/005827/assets
        
        # 获取指定日期的资产配置
        GET /api/v1/fund/005827/assets?dates=2021-12-31
        
        # 获取多个日期的资产配置
        GET /api/v1/fund/005827/assets?dates=2021-12-31,2021-06-30
    """
    try:
        # 解析 dates 参数
        dates_param = None
        if dates:
            date_list = [d.strip() for d in dates.split(',') if d.strip()]
            if len(date_list) == 1:
                dates_param = date_list[0]
            else:
                dates_param = date_list
        
        # 基金资产配置数据季度更新，适合缓存
        assets_list = await data_source_manager.get_fund_types_percentage(
            fund_code=fund_code,
            dates=dates_param,
            source_type="efinance"
        )
        
        if not assets_list:
            return ResponseModel(
                success=False,
                code="NOT_FOUND",
                message=f"未找到基金资产配置数据（代码：{fund_code}, 日期：{dates or '最新'}）"
            )
        
        logger.info(f"获取基金 {fund_code} 资产配置比例成功：{len(assets_list)}个日期")
        return ResponseModel(data=assets_list)
    
    except Exception as e:
        logger.error(f"获取基金资产配置比例失败 {fund_code} (dates={dates}): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ResponseModel[List[Dict[str, str]]])
async def get_fund_list(
    fund_type: Optional[str] = Query(None, description="基金类型：zq=债券型，gp=股票型，etf=ETF，hh=混合型，zs=指数型，fof=FOF，qdii=QDII"),
):
    """
    获取基金代码列表
    
    Args:
        fund_type: 基金类型（可选，不传则获取全部类型）
    
    Returns:
        基金代码列表，每项包含 code 和 name
    """
    try:
        # 基金列表变化不频繁，适合缓存
        result = await data_source_manager.get_fund_codes(fund_type=fund_type)
        
        return ResponseModel(
            data=result,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取基金列表失败 (fund_type={fund_type}): {e}")
        raise HTTPException(status_code=500, detail=str(e))
