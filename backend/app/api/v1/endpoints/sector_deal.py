"""股票行业成交与交易所概况 API 端点

提供深交所行业成交、上交所每日概况、个股信息查询等接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import SZSESectorSummary, SSEDealDaily, StockIndividualInfoEM, StockIndividualBasicInfoXQ
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/szse-sector-summary", response_model=ResponseModel[List[SZSESectorSummary]])
async def get_szse_sector_summary(
    symbol: str = Query(
        "当月",
        description="数据类型，choice of {'当月', '当年'}"
    ),
    date: str = Query(
        "",
        description="年月，格式 YYYYMM（如：202501）"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取深圳证券交易所股票行业成交数据
    
    返回数据字段：
    - **project_name**: 项目名称（行业类别）
    - **project_name_en**: 项目名称（英文）
    - **trading_days**: 交易天数
    - **turnover_amount**: 成交金额（人民币元）
    - **turnover_ratio**: 成交金额 - 占总计（%）
    - **turnover_shares**: 成交股数（股数）
    - **turnover_shares_ratio**: 成交股数 - 占总计（%）
    - **turnover_count**: 成交笔数（笔）
    - **turnover_count_ratio**: 成交笔数 - 占总计（%）
    
    行业类别包括：
    - 农林牧渔、采矿业、制造业、水电煤气
    - 建筑业、批发零售、运输仓储、住宿餐饮
    - 信息技术、金融业、房地产、商务服务
    - 科研服务、公共环保、居民服务、教育、卫生、文化传播、综合
    
    使用场景：
    - 分析各行业成交活跃度
    - 对比不同行业交易量
    - 追踪热点行业资金流向
    - 评估行业投资热度
    
    注意：
    - 日期格式：YYYYMM（如：202501）
    - 支持"当月"和"当年"两种统计类型
    """
    try:
        data = await adapter.get_szse_sector_summary(symbol, date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/sse-deal-daily", response_model=ResponseModel[List[SSEDealDaily]])
async def get_sse_deal_daily(
    date: str = Query(
        "",
        description="日期，格式 YYYYMMDD（如：20250221），仅支持 20211227 之后的数据"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取上海证券交易所每日概况数据
    
    返回数据项目：
    - **挂牌数**: 上市公司/股票数量
    - **市价总值**: 总市值（亿元）
    - **流通市值**: 流通市值（亿元）
    - **成交金额**: 成交金额（亿元）
    - **成交量**: 成交量（亿股）
    - **平均市盈率**: 市场平均市盈率
    - **换手率**: 换手率（%）
    - **流通换手率**: 流通股本换手率（%）
    
    分类统计：
    - **股票**: 总计
    - **主板 A**: 主板 A 股
    - **主板 B**: 主板 B 股
    - **科创板**: 科创板股票
    - **股票回购**: 回购股票
    
    使用场景：
    - 监控上交所每日交易概况
    - 分析市场整体活跃度
    - 追踪科创板发展情况
    - 评估市场估值水平
    
    注意：
    - 日期格式：YYYYMMDD（如：20250221）
    - 仅支持 2021 年 12 月 27 日之后的数据
    - 当前交易日数据需收盘后统计
    """
    try:
        if not date:
            from datetime import datetime
            date = datetime.now().strftime("%Y%m%d")
        
        data = await adapter.get_sse_deal_daily(date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/stock-info-em/{symbol}", response_model=ResponseModel[List[StockIndividualInfoEM]])
async def get_stock_info_em(
    symbol: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富个股信息
    
    返回数据项目：
    - **最新价**: 当前股票价格
    - **股票代码**: 6 位股票代码
    - **股票简称**: 股票名称
    - **总股本**: 总股本数量（股）
    - **流通股**: 流通股本数量（股）
    - **总市值**: 总市值（元）
    - **流通市值**: 流通市值（元）
    - **行业**: 所属行业
    - **上市时间**: 上市日期
    
    使用场景：
    - 快速获取个股基本信息
    - 查询股票市值和股本结构
    - 了解个股行业属性
    - 股票资料查询
    
    注意：
    - symbol: 股票代码（如：000001, 603777）
    - 数据来源：东方财富网
    - 实时更新（交易时间内）
    
    示例：
    - symbol="000001": 查询平安银行
    - symbol="603777": 查询来伊份
    """
    try:
        if not symbol:
            return {
                "code": 400,
                "message": "股票代码不能为空",
                "data": []
            }
        
        data = await adapter.get_stock_individual_info_em(symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/stock-info-xq/{symbol}", response_model=ResponseModel[List[StockIndividualBasicInfoXQ]])
async def get_stock_info_xq(
    symbol: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取雪球财经个股基本信息
    
    返回数据项目（38 个字段）：
    
    **公司基本信息**:
    - **org_name_cn**: 公司中文名称
    - **org_short_name_cn**: 公司中文简称
    - **org_name_en**: 公司英文名称
    - **org_short_name_en**: 公司英文简称
    - **pre_name_cn**: 曾用名
    
    **业务信息**:
    - **main_operation_business**: 主营业务
    - **operating_scope**: 经营范围
    - **affiliate_industry**: 所属行业
    
    **管理层信息**:
    - **legal_representative**: 法人代表
    - **general_manager**: 总经理
    - **secretary**: 董秘
    - **chairman**: 董事长
    - **executives_nums**: 管理层人数
    
    **联系信息**:
    - **telephone**: 联系电话
    - **postcode**: 邮政编码
    - **fax**: 传真
    - **email**: 电子邮箱
    - **org_website**: 公司网址
    - **reg_address_cn**: 注册地址
    - **office_address_cn**: 办公地址
    
    **资本信息**:
    - **reg_asset**: 注册资本（元）
    - **staff_num**: 员工人数
    - **established_date**: 成立日期（时间戳）
    - **listed_date**: 上市日期（时间戳）
    - **actual_controller**: 实际控制人
    - **classi_name**: 所有制性质
    
    **发行信息**:
    - **actual_issue_vol**: 实际发行量（股）
    - **issue_price**: 发行价格（元）
    - **actual_rc_net_amt**: 实际募集资金净额（元）
    - **pe_after_issuing**: 发行市盈率
    - **online_success_rate_of_issue**: 网上中签率（%）
    
    使用场景：
    - 详细的公司资料查询
    - 了解公司主营业务和经营范围
    - 查询公司联系方式和地址
    - 研究公司历史沿革（曾用名）
    - 分析公司股权结构（实际控制人）
    - 查询 IPO 发行信息
    
    注意：
    - symbol: 股票代码，需带市场标识（如：SH601127, SZ000001）
    - 数据来源：雪球财经
    - 相比东方财富，提供更详细的公司简介和发行信息
    
    示例：
    - symbol="SH601127": 查询赛力斯
    - symbol="SZ000001": 查询平安银行
    """
    try:
        if not symbol:
            return {
                "code": 400,
                "message": "股票代码不能为空",
                "data": []
            }
        
        data = await adapter.get_stock_individual_basic_info_xq(symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
