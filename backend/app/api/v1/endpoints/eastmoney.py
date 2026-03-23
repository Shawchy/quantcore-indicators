"""东方财富盘口异动和涨停板行情 API"""
from fastapi import APIRouter, Query
from typing import Optional, List
from app.models.schemas import ResponseModel
from app.models.unified_models import (
    StockChanges, StockBoardChange, StockZtPool, MarketChanges,
    StockZtPrevious, StockZtStrong, StockZtSubNew,
    StockComment, StockCommentDetailInstitution, StockCommentDetailScore,
    StockResearchReport, StockNotice, StockBalanceSheet, StockProfitSheet, StockCashFlowSheet,
    StockFinancialIndicator, StockInfoA, StockInfoSH, StockInfoSZ, StockInfoBJ,
    StockIndustryClfHistSW, StockIndustryPERatio, StockHoldNumCNInfo, StockPriceJS,
    StockAConestionLG, StockEBSLG, StockBuffettIndexLG,
    StockZhValuationBaidu, StockValueEM, StockZhVoteBaidu,
    StockAHighLowStatistics, StockABelowNetAssetStatistics,
    StockDzjySctj, StockDzjyMrmx,
    StockMarginRatioPa, StockMarginAccountInfo,
    StockMarginSse, StockMarginDetailSse, StockMarginSzse, StockMarginDetailSzse,
    StockMarginUnderlyingInfoSzse, StockProfitForecastEm,
    StockBoardIndustryNameEm, StockBoardIndustrySpotEm, StockBoardIndustryConsEm
)
from loguru import logger
from datetime import datetime

router = APIRouter()


@router.get("/changes", response_model=ResponseModel[List[StockChanges]])
async def get_stock_changes(
    symbol: str = Query("大笔买入", description="异动类型")
):
    """
    获取盘口异动数据
    
    Args:
        symbol: 异动类型，可选值：
            - 火箭发射
            - 快速反弹
            - 大笔买入
            - 封涨停板
            - 打开跌停板
            - 有大买盘
            - 竞价上涨
            - 高开 5 日线
            - 向上缺口
            - 60 日新高
            - 60 日大幅上涨
            - 加速下跌
            - 高台跳水
            - 大笔卖出
            - 封跌停板
            - 打开涨停板
            - 有大卖盘
            - 竞价下跌
            - 低开 5 日线
            - 向下缺口
            - 60 日新低
            - 60 日大幅下跌
    
    Returns:
        盘口异动数据列表
    
    Examples:
        - 获取大笔买入：/api/v1/eastmoney/changes?symbol=大笔买入
        - 获取火箭发射：/api/v1/eastmoney/changes?symbol=火箭发射
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        changes = await adapter.get_stock_changes(symbol=symbol)
        return ResponseModel(data=changes, message=f"获取成功，共{len(changes)}条")
    except Exception as e:
        logger.error(f"获取盘口异动数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-a-high-low-statistics", response_model=ResponseModel[List[StockAHighLowStatistics]])
async def get_stock_a_high_low_statistics(
    symbol: str = Query("all", description="市场：all=全部 A 股，sz50=上证 50，hs300=沪深 300，zz500=中证 500")
):
    """
    获取乐咕乐股 - 创新高/新低统计数据
    
    Args:
        symbol: 市场类型，可选值：
            - all: 全部 A 股
            - sz50: 上证 50
            - hs300: 沪深 300
            - zz500: 中证 500
    
    Returns:
        创新高/新低统计数据列表，包含：
        - 交易日
        - 相关指数收盘价
        - 20 日新高数量
        - 20 日新低数量
        - 60 日新高数量
        - 60 日新低数量
        - 120 日新高数量
        - 120 日新低数量
    
    Examples:
        - 获取全部 A 股统计：/api/v1/eastmoney/stock-a-high-low-statistics?symbol=all
        - 获取沪深 300 统计：/api/v1/eastmoney/stock-a-high-low-statistics?symbol=hs300
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        hl_data = await adapter.get_stock_a_high_low_statistics(symbol=symbol)
        return ResponseModel(data=hl_data, message=f"获取成功，共{len(hl_data)}条")
    except Exception as e:
        logger.error(f"获取创新高/新低统计数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-a-below-net-asset-statistics", response_model=ResponseModel[List[StockABelowNetAssetStatistics]])
async def get_stock_a_below_net_asset_statistics(
    symbol: str = Query("全部 A 股", description="市场：全部 A 股、沪深 300、上证 50、中证 500")
):
    """
    获取乐咕乐股 - 破净股统计数据
    
    Args:
        symbol: 市场类型，可选值：
            - 全部 A 股
            - 沪深 300
            - 上证 50
            - 中证 500
    
    Returns:
        破净股统计数据列表，包含：
        - 交易日
        - 破净股家数
        - 总公司数
        - 破净股比率
    
    Examples:
        - 获取全部 A 股统计：/api/v1/eastmoney/stock-a-below-net-asset-statistics?symbol=全部 A 股
        - 获取沪深 300 统计：/api/v1/eastmoney/stock-a-below-net-asset-statistics?symbol=沪深 300
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        bn_data = await adapter.get_stock_a_below_net_asset_statistics(symbol=symbol)
        return ResponseModel(data=bn_data, message=f"获取成功，共{len(bn_data)}条")
    except Exception as e:
        logger.error(f"获取破净股统计数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-dzjy-sctj", response_model=ResponseModel[List[StockDzjySctj]])
async def get_stock_dzjy_sctj():
    """
    获取东方财富网 - 大宗交易市场统计
    
    Returns:
        大宗交易市场统计数据列表，包含：
        - 序号
        - 交易日期
        - 上证指数
        - 上证指数涨跌幅（%）
        - 大宗交易成交总额（元）
        - 溢价成交总额（元）
        - 溢价成交总额占比（%）
        - 折价成交总额（元）
        - 折价成交总额占比（%）
    
    Examples:
        - 获取大宗交易市场统计：/api/v1/eastmoney/stock-dzjy-sctj
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sctj_data = await adapter.get_stock_dzjy_sctj()
        return ResponseModel(data=sctj_data, message=f"获取成功，共{len(sctj_data)}条")
    except Exception as e:
        logger.error(f"获取大宗交易市场统计数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-dzjy-mrmx", response_model=ResponseModel[List[StockDzjyMrmx]])
async def get_stock_dzjy_mrmx(
    symbol: str = Query("A 股", description="证券类型：A 股、B 股、基金、债券"),
    start_date: str = Query("", description="开始日期，格式：YYYYMMDD"),
    end_date: str = Query("", description="结束日期，格式：YYYYMMDD")
):
    """
    获取东方财富网 - 大宗交易每日明细
    
    Args:
        symbol: 证券类型，可选值：
            - A 股
            - B 股
            - 基金
            - 债券
        start_date: 开始日期，格式 YYYYMMDD
        end_date: 结束日期，格式 YYYYMMDD
    
    Returns:
        大宗交易每日明细数据列表，包含：
        - 序号
        - 交易日期
        - 证券代码
        - 证券简称
        - 涨跌幅（%）
        - 收盘价（元）
        - 成交价（元）
        - 折溢率（%）
        - 成交量（股）
        - 成交额（元）
        - 成交额/流通市值（%）
        - 买方营业部
        - 卖方营业部
    
    Examples:
        - 获取今日 A 股明细：/api/v1/eastmoney/stock-dzjy-mrmx?symbol=A 股
        - 获取指定日期范围：/api/v1/eastmoney/stock-dzjy-mrmx?symbol=A 股&start_date=20220104&end_date=20220104
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        mrmx_data = await adapter.get_stock_dzjy_mrmx(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return ResponseModel(data=mrmx_data, message=f"获取成功，共{len(mrmx_data)}条")
    except Exception as e:
        logger.error(f"获取大宗交易每日明细数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-margin-ratio-pa", response_model=ResponseModel[List[StockMarginRatioPa]])
async def get_stock_margin_ratio_pa(
    symbol: str = Query("深市", description="交易所：深市、沪市、北交所"),
    date: str = Query("", description="交易日期，格式：YYYYMMDD")
):
    """
    获取融资融券 - 标的证券名单及保证金比例
    
    Args:
        symbol: 交易所类型，可选值：
            - 深市
            - 沪市
            - 北交所
        date: 交易日期，格式 YYYYMMDD
    
    Returns:
        融资融券标的证券数据列表，包含：
        - 证券代码
        - 证券简称
        - 融资比例
        - 融券比例
    
    Examples:
        - 获取深市数据：/api/v1/eastmoney/stock-margin-ratio-pa?symbol=深市
        - 获取指定日期：/api/v1/eastmoney/stock-margin-ratio-pa?symbol=沪市&date=20260113
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        ratio_data = await adapter.get_stock_margin_ratio_pa(
            symbol=symbol,
            date=date
        )
        return ResponseModel(data=ratio_data, message=f"获取成功，共{len(ratio_data)}条")
    except Exception as e:
        logger.error(f"获取融资融券保证金比例数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-margin-account-info", response_model=ResponseModel[List[StockMarginAccountInfo]])
async def get_stock_margin_account_info():
    """
    获取东方财富网 - 融资融券账户统计
    
    Returns:
        融资融券账户统计数据列表，包含：
        - 日期
        - 融资余额（亿）
        - 融券余额（亿）
        - 融资买入额（亿）
        - 融券卖出额（亿）
        - 证券公司数量（家）
        - 营业部数量（家）
        - 个人投资者数量（万名）
        - 机构投资者数量（家）
        - 参与交易的投资者数量（万名）
        - 有融资融券负债的投资者数量（万名）
        - 担保物总价值（亿）
        - 平均维持担保比例（%）
    
    Examples:
        - 获取融资融券账户统计：/api/v1/eastmoney/stock-margin-account-info
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        info_data = await adapter.get_stock_margin_account_info()
        return ResponseModel(data=info_data, message=f"获取成功，共{len(info_data)}条")
    except Exception as e:
        logger.error(f"获取融资融券账户统计数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-zh-valuation-baidu/{symbol}", response_model=ResponseModel[List[StockZhValuationBaidu]])
async def get_stock_zh_valuation_baidu(
    symbol: str = Path(..., description="A 股代码，如：002044"),
    indicator: str = Query("总市值", description="估值指标：总市值、市盈率 (TTM)、市盈率 (静)、市净率、市现率"),
    period: str = Query("近一年", description="时间范围：近一年、近三年、近五年、近十年、全部")
):
    """
    获取百度股市通-A 股估值数据
    
    Args:
        symbol: A 股代码，如"002044"
        indicator: 估值指标类型，可选值：
            - 总市值
            - 市盈率 (TTM)
            - 市盈率 (静)
            - 市净率
            - 市现率
        period: 时间范围，可选值：
            - 近一年
            - 近三年
            - 近五年
            - 近十年
            - 全部
    
    Returns:
        估值数据列表，包含：
        - 日期
        - 估值指标值
    
    Examples:
        - 获取美年健康总市值（近一年）：/api/v1/eastmoney/stock-zh-valuation-baidu/002044?indicator=总市值&period=近一年
        - 获取市盈率（近三年）：/api/v1/eastmoney/stock-zh-valuation-baidu/002044?indicator=市盈率 (TTM)&period=近三年
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        valuation_data = await adapter.get_stock_zh_valuation_baidu(
            symbol=symbol, 
            indicator=indicator, 
            period=period
        )
        return ResponseModel(data=valuation_data, message=f"获取成功，共{len(valuation_data)}条")
    except Exception as e:
        logger.error(f"获取百度股市通估值数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-value-em/{symbol}", response_model=ResponseModel[List[StockValueEM]])
async def get_stock_value_em(symbol: str = Path(..., description="A 股代码，如：300766")):
    """
    获取东方财富网 - 个股估值数据
    
    Args:
        symbol: A 股代码，如"300766"
    
    Returns:
        个股估值数据列表，包含：
        - 数据日期
        - 当日收盘价（元）
        - 当日涨跌幅（%）
        - 总市值（元）
        - 流通市值（元）
        - 总股本（股）
        - 流通股本（股）
        - PE(TTM)
        - PE(静)
        - 市净率
        - PEG 值
        - 市现率
        - 市销率
    
    Examples:
        - 获取每日互动估值数据：/api/v1/eastmoney/stock-value-em/300766
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        value_data = await adapter.get_stock_value_em(symbol=symbol)
        return ResponseModel(data=value_data, message=f"获取成功，共{len(value_data)}条")
    except Exception as e:
        logger.error(f"获取东方财富个股估值数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-zh-vote-baidu/{symbol}", response_model=ResponseModel[List[StockZhVoteBaidu]])
async def get_stock_zh_vote_baidu(
    symbol: str = Path(..., description="A 股股票或指数代码，如：000001"),
    indicator: str = Query("股票", description="类型：指数、股票")
):
    """
    获取百度股市通 - 涨跌投票数据
    
    Args:
        symbol: A 股股票或指数代码，如"000001"
        indicator: 类型，可选值：
            - 指数
            - 股票
    
    Returns:
        涨跌投票数据列表，包含：
        - 周期（今日/本周/本月/今年）
        - 看涨票数
        - 看跌票数
        - 看涨比例（%）
        - 看跌比例（%）
    
    Examples:
        - 获取上证指数投票：/api/v1/eastmoney/stock-zh-vote-baidu/000001?indicator=指数
        - 获取个股投票：/api/v1/eastmoney/stock-zh-vote-baidu/002044?indicator=股票
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        vote_data = await adapter.get_stock_zh_vote_baidu(
            symbol=symbol, 
            indicator=indicator
        )
        return ResponseModel(data=vote_data, message=f"获取成功，共{len(vote_data)}条")
    except Exception as e:
        logger.error(f"获取百度股市通涨跌投票数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/cash-flow-sheet-report/{symbol}", response_model=ResponseModel[List[StockCashFlowSheet]])
async def get_cash_flow_sheet_report(symbol: str = Path(..., description="股票代码")):
    """获取现金流量表 - 按报告期"""
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_cash_flow_sheet_by_report(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取现金流量表（报告期）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/cash-flow-sheet-yearly/{symbol}", response_model=ResponseModel[List[StockCashFlowSheet]])
async def get_cash_flow_sheet_yearly(symbol: str = Path(..., description="股票代码")):
    """获取现金流量表 - 按年度"""
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_cash_flow_sheet_by_yearly(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取现金流量表（年度）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/cash-flow-sheet-quarterly/{symbol}", response_model=ResponseModel[List[StockCashFlowSheet]])
async def get_cash_flow_sheet_quarterly(symbol: str = Path(..., description="股票代码")):
    """获取现金流量表 - 按单季度"""
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_cash_flow_sheet_by_quarterly(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取现金流量表（单季度）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/financial-indicator/{symbol}", response_model=ResponseModel[List[StockFinancialIndicator]])
async def get_financial_indicator(
    symbol: str = Path(..., description="股票代码"),
    start_year: Optional[str] = Query(None, description="开始年份")
):
    """
    获取新浪财经财务指标
    
    Args:
        symbol: 股票代码，如"600004"
        start_year: 开始年份，如"2020"
    
    Returns:
        财务指标数据列表，包含 86 个字段：
        - 每股指标：摊薄每股收益、加权每股收益、每股净资产等
        - 盈利能力：总资产利润率、主营业务利润率、销售净利率等
        - 成长能力：主营业务收入增长率、净利润增长率等
        - 营运能力：应收账款周转率、存货周转率等
        - 偿债能力：流动比率、速动比率、资产负债率等
        - 现金流量：经营现金净流量对销售收入比率等
        - 资产明细：应收帐款、预付款、其它应收款等
    
    Examples:
        - 获取南方航空 2020 年财务指标：/api/v1/eastmoney/financial-indicator/600004?start_year=2020
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        indicators = await adapter.get_financial_analysis_indicator(symbol=symbol, start_year=start_year or "2020")
        return ResponseModel(data=indicators, message=f"获取成功，共{len(indicators)}条")
    except Exception as e:
        logger.error(f"获取新浪财经财务指标数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-info-a", response_model=ResponseModel[List[StockInfoA]])
async def get_stock_info_a():
    """
    获取沪深京 A 股股票列表
    
    Returns:
        沪深京 A 股股票代码和简称列表，包含：
        - 股票代码
        - 股票简称
    
    Examples:
        - 获取所有 A 股列表：/api/v1/eastmoney/stock-info-a
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        stocks = await adapter.get_stock_info_a_code_name()
        return ResponseModel(data=stocks, message=f"获取成功，共{len(stocks)}条")
    except Exception as e:
        logger.error(f"获取沪深京 A 股股票列表失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-info-sh/{symbol}", response_model=ResponseModel[List[StockInfoSH]])
async def get_stock_info_sh(symbol: str = Path(..., description="板块类型：主板 A 股、主板 B 股、科创板")):
    """
    获取上海证券交易所股票列表
    
    Args:
        symbol: 板块类型，可选值："主板 A 股"、"主板 B 股"、"科创板"
    
    Returns:
        上海证券交易所股票列表，包含：
        - 证券代码
        - 证券简称
        - 公司全称
        - 上市日期
    
    Examples:
        - 获取主板 A 股列表：/api/v1/eastmoney/stock-info-sh/主板 A 股
        - 获取科创板列表：/api/v1/eastmoney/stock-info-sh/科创板
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        stocks = await adapter.get_stock_info_sh_name_code(symbol=symbol)
        return ResponseModel(data=stocks, message=f"获取成功，共{len(stocks)}条")
    except Exception as e:
        logger.error(f"获取上海证券交易所股票列表失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-info-sz/{symbol}", response_model=ResponseModel[List[StockInfoSZ]])
async def get_stock_info_sz(symbol: str = Path(..., description="板块类型：A 股列表、B 股列表、CDR 列表、AB 股列表")):
    """
    获取深圳证券交易所股票列表
    
    Args:
        symbol: 板块类型，可选值："A 股列表"、"B 股列表"、"CDR 列表"、"AB 股列表"
    
    Returns:
        深圳证券交易所股票列表，包含：
        - 板块
        - A 股代码
        - A 股简称
        - A 股上市日期
        - A 股总股本
        - A 股流通股本
        - 所属行业
    
    Examples:
        - 获取 A 股列表：/api/v1/eastmoney/stock-info-sz/A 股列表
        - 获取创业板列表：/api/v1/eastmoney/stock-info-sz/创业板
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        stocks = await adapter.get_stock_info_sz_name_code(symbol=symbol)
        return ResponseModel(data=stocks, message=f"获取成功，共{len(stocks)}条")
    except Exception as e:
        logger.error(f"获取深圳证券交易所股票列表失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-info-bj", response_model=ResponseModel[List[StockInfoBJ]])
async def get_stock_info_bj():
    """
    获取北京证券交易所股票列表
    
    Returns:
        北京证券交易所股票列表，包含：
        - 证券代码
        - 证券简称
        - 总股本
        - 流通股本
        - 上市日期
        - 所属行业
        - 地区
        - 报告日期
    
    Examples:
        - 获取北交所股票列表：/api/v1/eastmoney/stock-info-bj
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        stocks = await adapter.get_stock_info_bj_name_code()
        return ResponseModel(data=stocks, message=f"获取成功，共{len(stocks)}条")
    except Exception as e:
        logger.error(f"获取北京证券交易所股票列表失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-industry-clf-hist-sw", response_model=ResponseModel[List[StockIndustryClfHistSW]])
async def get_stock_industry_clf_hist_sw():
    """
    获取申万行业分类变动历史
    
    Returns:
        申万行业分类变动历史数据，包含：
        - 股票代码
        - 计入日期
        - 申万行业代码
        - 更新日期
    
    Examples:
        - 获取申万行业分类历史：/api/v1/eastmoney/stock-industry-clf-hist-sw
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        industries = await adapter.get_stock_industry_clf_hist_sw()
        return ResponseModel(data=industries, message=f"获取成功，共{len(industries)}条")
    except Exception as e:
        logger.error(f"获取申万行业分类变动历史失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-industry-pe-ratio/{symbol}", response_model=ResponseModel[List[StockIndustryPERatio]])
async def get_stock_industry_pe_ratio(
    symbol: str = Path(..., description="行业分类类型：证监会行业分类、国证行业分类"),
    date: Optional[str] = Query(None, description="交易日，格式 YYYYMMDD")
):
    """
    获取行业市盈率
    
    Args:
        symbol: 行业分类类型，可选值："证监会行业分类"、"国证行业分类"
        date: 交易日，格式 YYYYMMDD，默认为最近日期
    
    Returns:
        行业市盈率数据列表，包含：
        - 变动日期
        - 行业分类
        - 行业层级
        - 行业编码
        - 行业名称
        - 公司数量
        - 纳入计算公司数量
        - 总市值 - 静态（亿元）
        - 净利润 - 静态（亿元）
        - 静态市盈率 - 加权平均
        - 静态市盈率 - 中位数
        - 静态市盈率 - 算术平均
    
    Examples:
        - 获取国证行业分类市盈率：/api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类
        - 获取指定日期数据：/api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类?date=20240617
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        pe_ratios = await adapter.get_stock_industry_pe_ratio_cninfo(symbol=symbol, date=date)
        return ResponseModel(data=pe_ratios, message=f"获取成功，共{len(pe_ratios)}条")
    except Exception as e:
        logger.error(f"获取行业市盈率数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-hold-num-cninfo", response_model=ResponseModel[List[StockHoldNumCNInfo]])
async def get_stock_hold_num_cninfo(
    date: str = Query(..., description="报告期，格式 YYYYMMDD，如：20210630")
):
    """
    获取股东人数及持股集中度
    
    Args:
        date: 报告期，格式 YYYYMMDD，可选值：XXXX0331、XXXX0630、XXXX0930、XXXX1231
              从 20170331 开始
    
    Returns:
        股东人数及持股集中度数据列表，包含：
        - 证券代码
        - 证券简称
        - 变动日期
        - 本期股东人数
        - 上期股东人数
        - 股东人数增幅（%）
        - 本期人均持股数量（万股）
        - 上期人均持股数量（万股）
        - 人均持股数量增幅（%）
    
    Examples:
        - 获取 2021 年中报股东人数：/api/v1/eastmoney/stock-hold-num-cninfo?date=20210630
        - 获取 2020 年报股东人数：/api/v1/eastmoney/stock-hold-num-cninfo?date=20201231
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        hold_nums = await adapter.get_stock_hold_num_cninfo(date=date)
        return ResponseModel(data=hold_nums, message=f"获取成功，共{len(hold_nums)}条")
    except Exception as e:
        logger.error(f"获取股东人数及持股集中度数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-price-js", response_model=ResponseModel[List[StockPriceJS]])
async def get_stock_price_js(
    symbol: str = Query("us", description="市场类型：us（美股）、hk（港股）")
):
    """
    获取美港目标价
    
    Args:
        symbol: 市场类型，可选值："us"（美股）、"hk"（港股），默认为"us"
    
    Returns:
        美港目标价数据列表，包含：
        - 日期
        - 个股名称
        - 评级
        - 先前目标价
        - 最新目标价
        - 机构名称
    
    Examples:
        - 获取美股目标价：/api/v1/eastmoney/stock-price-js?symbol=us
        - 获取港股目标价：/api/v1/eastmoney/stock-price-js?symbol=hk
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        price_targets = await adapter.get_stock_price_js(symbol=symbol)
        return ResponseModel(data=price_targets, message=f"获取成功，共{len(price_targets)}条")
    except Exception as e:
        logger.error(f"获取美港目标价数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/profit-sheet-report/{symbol}", response_model=ResponseModel[List[StockProfitSheet]])
async def get_profit_sheet_report(symbol: str = Path(..., description="股票代码")):
    """
    获取利润表 - 按报告期
    
    Args:
        symbol: 股票代码，如"SH600519"
    
    Returns:
        利润表数据列表（按报告期），包含：
        - 证券代码、股票代码、证券简称
        - 报告期、公告日期
        - 营业总收入、营业收入、营业成本
        - 营业利润、利润总额、净利润
        - 归母净利润、扣非净利润
        - 税金及附加、三费（销售、管理、财务）
        - 其他 180+ 财务指标字段
    
    Examples:
        - 获取贵州茅台利润表：/api/v1/eastmoney/profit-sheet-report/SH600519
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_profit_sheet_by_report(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取利润表（报告期）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/profit-sheet-yearly/{symbol}", response_model=ResponseModel[List[StockProfitSheet]])
async def get_profit_sheet_yearly(symbol: str = Path(..., description="股票代码")):
    """
    获取利润表 - 按年度
    
    Args:
        symbol: 股票代码，如"SH600519"
    
    Returns:
        利润表数据列表（按年度），包含：
        - 证券代码、股票代码、证券简称
        - 报告期、公告日期
        - 营业总收入、营业收入、营业成本
        - 营业利润、利润总额、净利润
        - 归母净利润、扣非净利润
        - 税金及附加、三费（销售、管理、财务）
        - 其他 180+ 财务指标字段
    
    Examples:
        - 获取贵州茅台年度利润表：/api/v1/eastmoney/profit-sheet-yearly/SH600519
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_profit_sheet_by_yearly(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取利润表（年度）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/profit-sheet-quarterly/{symbol}", response_model=ResponseModel[List[StockProfitSheet]])
async def get_profit_sheet_quarterly(symbol: str = Path(..., description="股票代码")):
    """
    获取利润表 - 按单季度
    
    Args:
        symbol: 股票代码，如"SH600519"
    
    Returns:
        利润表数据列表（按单季度），包含：
        - 证券代码、股票代码、证券简称
        - 报告期、公告日期
        - 营业总收入、营业收入、营业成本
        - 营业利润、利润总额、净利润
        - 归母净利润、扣非净利润
        - 税金及附加、三费（销售、管理、财务）
        - 其他 180+ 财务指标字段
    
    Examples:
        - 获取贵州茅台单季度利润表：/api/v1/eastmoney/profit-sheet-quarterly/SH600519
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_profit_sheet_by_quarterly(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取利润表（单季度）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/balance-sheet-report/{symbol}", response_model=ResponseModel[List[StockBalanceSheet]])
async def get_balance_sheet_report(symbol: str = Path(..., description="股票代码")):
    """
    获取资产负债表 - 按报告期
    
    Args:
        symbol: 股票代码，如"SH600519"
    
    Returns:
        资产负债表数据列表（按报告期），包含：
        - 证券代码、股票代码、证券简称
        - 报告期、公告日期
        - 资产总计、负债合计、所有者权益合计
        - 货币资金、应收账款、存货、固定资产
        - 短期借款、应付账款、长期借款
        - 未分配利润、实收资本等
        - 其他 300+ 财务指标字段
    
    Examples:
        - 获取贵州茅台资产负债表：/api/v1/eastmoney/balance-sheet-report/SH600519
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_balance_sheet_by_report(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取资产负债表（报告期）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/balance-sheet-yearly/{symbol}", response_model=ResponseModel[List[StockBalanceSheet]])
async def get_balance_sheet_yearly(symbol: str = Path(..., description="股票代码")):
    """
    获取资产负债表 - 按年度
    
    Args:
        symbol: 股票代码，如"SH600519"
    
    Returns:
        资产负债表数据列表（按年度），包含：
        - 证券代码、股票代码、证券简称
        - 报告期、公告日期
        - 资产总计、负债合计、所有者权益合计
        - 货币资金、应收账款、存货、固定资产
        - 短期借款、应付账款、长期借款
        - 未分配利润、实收资本等
        - 其他 300+ 财务指标字段
    
    Examples:
        - 获取贵州茅台年度资产负债表：/api/v1/eastmoney/balance-sheet-yearly/SH600519
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        sheets = await adapter.get_balance_sheet_by_yearly(symbol=symbol)
        return ResponseModel(data=sheets, message=f"获取成功，共{len(sheets)}条")
    except Exception as e:
        logger.error(f"获取资产负债表（年度）数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-comment", response_model=ResponseModel[List[StockComment]])
async def get_stock_comment():
    """
    获取千股千评数据
    
    Returns:
        千股千评数据列表，包含：
        - 序号、代码、名称
        - 最新价、涨跌幅
        - 换手率、市盈率
        - 主力成本、机构参与度
        - 综合得分、上升、目前排名
        - 关注指数、交易日
    
    Examples:
        - 获取千股千评：/api/v1/eastmoney/stock-comment
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        comments = await adapter.get_stock_comment()
        return ResponseModel(data=comments, message=f"获取成功，共{len(comments)}条")
    except Exception as e:
        logger.error(f"获取千股千评数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-comment-detail-institution/{symbol}", response_model=ResponseModel[List[StockCommentDetailInstitution]])
async def get_stock_comment_detail_institution(symbol: str = Path(..., description="股票代码")):
    """
    获取千股千评详情 - 主力控盘 - 机构参与度
    
    Args:
        symbol: 股票代码，如"600000"
    
    Returns:
        机构参与度历史数据列表，包含：
        - 交易日
        - 机构参与度（%）
    
    Examples:
        - 获取浦发银行机构参与度：/api/v1/eastmoney/stock-comment-detail-institution/600000
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        details = await adapter.get_stock_comment_detail_institution(symbol=symbol)
        return ResponseModel(data=details, message=f"获取成功，共{len(details)}条")
    except Exception as e:
        logger.error(f"获取个股机构参与度数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-comment-detail-score/{symbol}", response_model=ResponseModel[List[StockCommentDetailScore]])
async def get_stock_comment_detail_score(symbol: str = Path(..., description="股票代码")):
    """
    获取千股千评详情 - 综合评价 - 历史评分
    
    Args:
        symbol: 股票代码，如"600000"
    
    Returns:
        历史评分数据列表，包含：
        - 交易日
        - 评分
    
    Examples:
        - 获取浦发银行历史评分：/api/v1/eastmoney/stock-comment-detail-score/600000
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        details = await adapter.get_stock_comment_detail_score(symbol=symbol)
        return ResponseModel(data=details, message=f"获取成功，共{len(details)}条")
    except Exception as e:
        logger.error(f"获取个股历史评分数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-research-report/{symbol}", response_model=ResponseModel[List[StockResearchReport]])
async def get_stock_research_report(symbol: str = Path(..., description="股票代码")):
    """
    获取个股研报数据
    
    Args:
        symbol: 股票代码，如"000001"
    
    Returns:
        个股研报数据列表，包含：
        - 序号、股票代码、股票简称
        - 报告名称、东财评级、机构
        - 近一月个股研报数
        - 2024-2026 盈利预测（收益、市盈率）
        - 行业、日期、报告 PDF 链接
    
    Examples:
        - 获取平安银行研报：/api/v1/eastmoney/stock-research-report/000001
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    from fastapi import Path
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        reports = await adapter.get_stock_research_report(symbol=symbol)
        return ResponseModel(data=reports, message=f"获取成功，共{len(reports)}条")
    except Exception as e:
        logger.error(f"获取个股研报数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-notice-report", response_model=ResponseModel[List[StockNotice]])
async def get_stock_notice_report(
    symbol: str = Query("全部", description="公告类型"),
    date: Optional[str] = Query(None, description="日期，格式 YYYYMMDD")
):
    """
    获取沪深京 A 股公告
    
    Args:
        symbol: 公告类型，可选值：
            - 全部
            - 重大事项
            - 财务报告
            - 融资公告
            - 风险提示
            - 资产重组
            - 信息变更
            - 持股变动
        date: 日期，格式 YYYYMMDD，默认为今日
    
    Returns:
        公告数据列表，包含：
        - 代码、名称
        - 公告标题、公告类型
        - 公告日期、网址
    
    Examples:
        - 获取财务报告公告：/api/v1/eastmoney/stock-notice-report?symbol=财务报告
        - 获取指定日期公告：/api/v1/eastmoney/stock-notice-report?symbol=全部&date=20240613
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        notices = await adapter.get_stock_notice_report(symbol=symbol, date=date)
        return ResponseModel(data=notices, message=f"获取成功，共{len(notices)}条")
    except Exception as e:
        logger.error(f"获取公告数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/board-changes", response_model=ResponseModel[List[StockBoardChange]])
async def get_board_changes():
    """
    获取板块异动详情
    
    Returns:
        板块异动数据列表，包含：
        - 板块名称
        - 涨跌幅
        - 主力净流入
        - 板块异动总次数
        - 最频繁个股及类型
        - 异动类型列表
    
    Examples:
        - 获取板块异动：/api/v1/eastmoney/board-changes
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        changes = await adapter.get_board_changes()
        return ResponseModel(data=changes, message=f"获取成功，共{len(changes)}个板块")
    except Exception as e:
        logger.error(f"获取板块异动数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/zt-pool", response_model=ResponseModel[List[StockZtPool]])
async def get_zt_pool(
    date: Optional[str] = Query(None, description="日期，格式 YYYYMMDD，默认为今日")
):
    """
    获取涨停股池数据
    
    Args:
        date: 日期，格式 YYYYMMDD，默认为今日
    
    Returns:
        涨停股池数据列表，包含：
        - 股票代码、名称
        - 涨跌幅、最新价
        - 成交额、市值
        - 换手率、封板资金
        - 封板时间、炸板次数
        - 连板数、所属行业
    
    Examples:
        - 获取今日涨停：/api/v1/eastmoney/zt-pool
        - 获取指定日期：/api/v1/eastmoney/zt-pool?date=20241008
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        zt_stocks = await adapter.get_zt_pool(date=date)
        return ResponseModel(data=zt_stocks, message=f"获取成功，共{len(zt_stocks)}只涨停股")
    except Exception as e:
        logger.error(f"获取涨停股池数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/market-changes-summary", response_model=ResponseModel[MarketChanges])
async def get_market_changes_summary():
    """
    获取市场异动汇总
    
    Returns:
        市场异动汇总数据，包含各类型异动次数统计
    
    Examples:
        - 获取市场异动汇总：/api/v1/eastmoney/market-changes-summary
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        summary = await adapter.get_market_changes_summary()
        return ResponseModel(data=summary, message="获取成功")
    except Exception as e:
        logger.error(f"获取市场异动汇总失败：{e}")
        return ResponseModel(
            data=MarketChanges(
                timestamp=datetime.now().isoformat(),
                total_changes=0,
                rocket_launch=0,
                fast_rebound=0,
                big_buy=0,
                big_sell=0,
                limit_up=0,
                limit_down=0,
                high_dive=0
            ),
            message=f"获取失败：{e}"
        )
    finally:
        await adapter.close()


@router.get("/change-types", response_model=ResponseModel[List[dict]])
async def get_change_types():
    """
    获取所有异动类型列表
    
    Returns:
        异动类型列表
    
    Examples:
        - 获取异动类型：/api/v1/eastmoney/change-types
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    change_types = [
        {"key": "rocket", "name": "火箭发射"},
        {"key": "rebound", "name": "快速反弹"},
        {"key": "big_buy", "name": "大笔买入"},
        {"key": "limit_up", "name": "封涨停板"},
        {"key": "open_limit_down", "name": "打开跌停板"},
        {"key": "have_big_buy", "name": "有大买盘"},
        {"key": "call_auction_up", "name": "竞价上涨"},
        {"key": "high_open_5day", "name": "高开 5 日线"},
        {"key": "up_gap", "name": "向上缺口"},
        {"key": "new_60day_high", "name": "60 日新高"},
        {"key": "big_60day_up", "name": "60 日大幅上涨"},
        {"key": "accel_down", "name": "加速下跌"},
        {"key": "high_dive", "name": "高台跳水"},
        {"key": "big_sell", "name": "大笔卖出"},
        {"key": "limit_down", "name": "封跌停板"},
        {"key": "open_limit_up", "name": "打开涨停板"},
        {"key": "have_big_sell", "name": "有大卖盘"},
        {"key": "call_auction_down", "name": "竞价下跌"},
        {"key": "low_open_5day", "name": "低开 5 日线"},
        {"key": "down_gap", "name": "向下缺口"},
        {"key": "new_60day_low", "name": "60 日新低"},
        {"key": "big_60day_down", "name": "60 日大幅下跌"},
    ]
    
    return ResponseModel(data=change_types, message="获取成功")


@router.get("/zt-pool-previous", response_model=ResponseModel[List[StockZtPrevious]])
async def get_zt_pool_previous(
    date: Optional[str] = Query(None, description="日期，格式 YYYYMMDD，默认为昨日")
):
    """
    获取昨日涨停股池数据
    
    Args:
        date: 日期，格式 YYYYMMDD，默认为昨日
    
    Returns:
        昨日涨停股池数据列表，包含：
        - 股票代码、名称
        - 涨跌幅、最新价、涨停价
        - 成交额、市值
        - 换手率、涨速、振幅
        - 昨日封板时间、昨日连板数
        - 涨停统计、所属行业
    
    Examples:
        - 获取昨日涨停：/api/v1/eastmoney/zt-pool-previous
        - 获取指定日期：/api/v1/eastmoney/zt-pool-previous?date=20240415
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        zt_stocks = await adapter.get_zt_pool_previous(date=date)
        return ResponseModel(data=zt_stocks, message=f"获取成功，共{len(zt_stocks)}只股票")
    except Exception as e:
        logger.error(f"获取昨日涨停股池数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/zt-pool-strong", response_model=ResponseModel[List[StockZtStrong]])
async def get_zt_pool_strong(
    date: Optional[str] = Query(None, description="日期，格式 YYYYMMDD，默认为今日")
):
    """
    获取强势股池数据
    
    Args:
        date: 日期，格式 YYYYMMDD，默认为今日
    
    Returns:
        强势股池数据列表，包含：
        - 股票代码、名称
        - 涨跌幅、最新价、涨停价
        - 成交额、市值
        - 换手率、涨速
        - 是否新高、量比
        - 涨停统计、入选理由
        - 所属行业
    
    Examples:
        - 获取今日强势股：/api/v1/eastmoney/zt-pool-strong
        - 获取指定日期：/api/v1/eastmoney/zt-pool-strong?date=20241231
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        zt_stocks = await adapter.get_zt_pool_strong(date=date)
        return ResponseModel(data=zt_stocks, message=f"获取成功，共{len(zt_stocks)}只强势股")
    except Exception as e:
        logger.error(f"获取强势股池数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/zt-pool-sub-new", response_model=ResponseModel[List[StockZtSubNew]])
async def get_zt_pool_sub_new(
    date: Optional[str] = Query(None, description="日期，格式 YYYYMMDD，默认为今日")
):
    """
    获取次新股池数据
    
    Args:
        date: 日期，格式 YYYYMMDD，默认为今日
    
    Returns:
        次新股池数据列表，包含：
        - 股票代码、名称
        - 涨跌幅、最新价、涨停价
        - 成交额、市值
        - 转手率
        - 开板几日、开板日期
        - 上市日期
        - 是否新高、涨停统计
        - 所属行业
    
    Examples:
        - 获取今日次新股：/api/v1/eastmoney/zt-pool-sub-new
        - 获取指定日期：/api/v1/eastmoney/zt-pool-sub-new?date=20241231
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        zt_stocks = await adapter.get_zt_pool_sub_new(date=date)
        return ResponseModel(data=zt_stocks, message=f"获取成功，共{len(zt_stocks)}只次新股")
    except Exception as e:
        logger.error(f"获取次新股池数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-a-congestion-lg", response_model=ResponseModel[List[StockAConestionLG]])
async def get_stock_a_congestion_lg():
    """
    获取乐咕乐股 - 大盘拥挤度
    
    Returns:
        大盘拥挤度数据列表，包含：
        - 日期
        - 收盘价
        - 拥挤度
    
    Examples:
        - 获取大盘拥挤度：/api/v1/eastmoney/stock-a-congestion-lg
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        congestion_data = await adapter.get_stock_a_congestion_lg()
        return ResponseModel(data=congestion_data, message=f"获取成功，共{len(congestion_data)}条")
    except Exception as e:
        logger.error(f"获取大盘拥挤度数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-ebs-lg", response_model=ResponseModel[List[StockEBSLG]])
async def get_stock_ebs_lg():
    """
    获取乐咕乐股 - 股债利差
    
    Returns:
        股债利差数据列表，包含：
        - 日期
        - 沪深 300 指数
        - 股债利差
        - 股债利差均线
    
    Examples:
        - 获取股债利差：/api/v1/eastmoney/stock-ebs-lg
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        ebs_data = await adapter.get_stock_ebs_lg()
        return ResponseModel(data=ebs_data, message=f"获取成功，共{len(ebs_data)}条")
    except Exception as e:
        logger.error(f"获取股债利差数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-buffett-index-lg", response_model=ResponseModel[List[StockBuffettIndexLG]])
async def get_stock_buffett_index_lg():
    """
    获取乐咕乐股 - 巴菲特指标
    
    Returns:
        巴菲特指标数据列表，包含：
        - 日期
        - 收盘价
        - 总市值（亿元）
        - 上年度 GDP（亿元）
        - 近十年分位数
        - 总历史分位数
    
    Examples:
        - 获取巴菲特指标：/api/v1/eastmoney/stock-buffett-index-lg
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        buffett_data = await adapter.get_stock_buffett_index_lg()
        return ResponseModel(data=buffett_data, message=f"获取成功，共{len(buffett_data)}条")
    except Exception as e:
        logger.error(f"获取巴菲特指标数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-margin-sse", response_model=ResponseModel[List[StockMarginSse]])
async def get_stock_margin_sse(
    start_date: str = Query(..., description="开始日期，格式 YYYYMMDD"),
    end_date: str = Query(..., description="结束日期，格式 YYYYMMDD")
):
    """
    获取上海证券交易所 - 融资融券汇总数据
    
    Args:
        start_date: 开始日期，格式 YYYYMMDD，如"20010106"
        end_date: 结束日期，格式 YYYYMMDD，如"20210208"
    
    Returns:
        融资融券汇总数据列表，包含：
        - 信用交易日期
        - 融资余额（元）
        - 融资买入额（元）
        - 融券余量
        - 融券余量金额（元）
        - 融券卖出量
        - 融资融券余额（元）
    
    Examples:
        - 获取上交所融资融券汇总：/api/v1/eastmoney/stock-margin-sse?start_date=20010106&end_date=20210208
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        margin_data = await adapter.get_stock_margin_sse(
            start_date=start_date,
            end_date=end_date
        )
        return ResponseModel(data=margin_data, message=f"获取成功，共{len(margin_data)}条")
    except Exception as e:
        logger.error(f"获取上交所融资融券汇总数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-margin-detail-sse/{date}", response_model=ResponseModel[List[StockMarginDetailSse]])
async def get_stock_margin_detail_sse(date: str = Path(..., description="交易日期，格式 YYYYMMDD")):
    """
    获取上海证券交易所 - 融资融券明细数据
    
    Args:
        date: 交易日期，格式 YYYYMMDD，如"20230922"
    
    Returns:
        融资融券明细数据列表，包含：
        - 信用交易日期
        - 标的证券代码
        - 标的证券简称
        - 融资余额（元）
        - 融资买入额（元）
        - 融资偿还额（元）
        - 融券余量
        - 融券卖出量
        - 融券偿还量
    
    Examples:
        - 获取上交所融资融券明细：/api/v1/eastmoney/stock-margin-detail-sse/20230922
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        detail_data = await adapter.get_stock_margin_detail_sse(date=date)
        return ResponseModel(data=detail_data, message=f"获取成功，共{len(detail_data)}条")
    except Exception as e:
        logger.error(f"获取上交所融资融券明细数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-margin-szse/{date}", response_model=ResponseModel[List[StockMarginSzse]])
async def get_stock_margin_szse(date: str = Path(..., description="交易日期，格式 YYYYMMDD")):
    """
    获取深圳证券交易所 - 融资融券汇总数据
    
    Args:
        date: 交易日期，格式 YYYYMMDD，如"20240411"
    
    Returns:
        融资融券汇总数据列表，包含：
        - 融资买入额（亿元）
        - 融资余额（亿元）
        - 融券卖出量（亿股/亿份）
        - 融券余量（亿股/亿份）
        - 融券余额（亿元）
        - 融资融券余额（亿元）
    
    Examples:
        - 获取深交所融资融券汇总：/api/v1/eastmoney/stock-margin-szse/20240411
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        margin_data = await adapter.get_stock_margin_szse(date=date)
        return ResponseModel(data=margin_data, message=f"获取成功，共{len(margin_data)}条")
    except Exception as e:
        logger.error(f"获取深交所融资融券汇总数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-margin-detail-szse/{date}", response_model=ResponseModel[List[StockMarginDetailSzse]])
async def get_stock_margin_detail_szse(date: str = Path(..., description="交易日期，格式 YYYYMMDD")):
    """
    获取深圳证券交易所 - 融资融券明细数据
    
    Args:
        date: 交易日期，格式 YYYYMMDD，如"20230925"
    
    Returns:
        融资融券明细数据列表，包含：
        - 证券代码
        - 证券简称
        - 融资买入额（元）
        - 融资余额（元）
        - 融券卖出量（股/份）
        - 融券余量（股/份）
        - 融券余额（元）
        - 融资融券余额（元）
    
    Examples:
        - 获取深交所融资融券明细：/api/v1/eastmoney/stock-margin-detail-szse/20230925
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        detail_data = await adapter.get_stock_margin_detail_szse(date=date)
        return ResponseModel(data=detail_data, message=f"获取成功，共{len(detail_data)}条")
    except Exception as e:
        logger.error(f"获取深交所融资融券明细数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-margin-underlying-info-szse/{date}", response_model=ResponseModel[List[StockMarginUnderlyingInfoSzse]])
async def get_stock_margin_underlying_info_szse(date: str = Path(..., description="交易日期，格式 YYYYMMDD")):
    """
    获取深圳证券交易所 - 标的证券信息
    
    Args:
        date: 交易日期，格式 YYYYMMDD，如"20210727"
    
    Returns:
        标的证券信息数据列表，包含：
        - 证券代码
        - 证券简称
        - 融资标的（Y/N）
        - 融券标的（Y/N）
        - 当日可融资（Y/N）
        - 当日可融券（Y/N）
        - 融券卖出价格限制
        - 涨跌幅限制
    
    Examples:
        - 获取深交所标的证券信息：/api/v1/eastmoney/stock-margin-underlying-info-szse/20210727
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        info_data = await adapter.get_stock_margin_underlying_info_szse(date=date)
        return ResponseModel(data=info_data, message=f"获取成功，共{len(info_data)}条")
    except Exception as e:
        logger.error(f"获取深交所标的证券信息失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-profit-forecast-em", response_model=ResponseModel[List[StockProfitForecastEm]])
async def get_stock_profit_forecast_em(
    symbol: str = Query("", description="行业板块名称，默认为空（获取全部数据）")
):
    """
    获取东方财富网 - 盈利预测
    
    Args:
        symbol: 行业板块名称，默认为空（获取全部数据），如"船舶制造"
    
    Returns:
        盈利预测数据列表，包含：
        - 序号
        - 代码
        - 名称
        - 研报数
        - 机构投资评级 (近六个月)-买入
        - 机构投资评级 (近六个月)-增持
        - 机构投资评级 (近六个月)-中性
        - 机构投资评级 (近六个月)-减持
        - 机构投资评级 (近六个月)-卖出
        - 2022-2025 预测每股收益
    
    Examples:
        - 获取全部盈利预测：/api/v1/eastmoney/stock-profit-forecast-em
        - 获取特定行业：/api/v1/eastmoney/stock-profit-forecast-em?symbol=船舶制造
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        forecast_data = await adapter.get_stock_profit_forecast_em(symbol=symbol)
        return ResponseModel(data=forecast_data, message=f"获取成功，共{len(forecast_data)}条")
    except Exception as e:
        logger.error(f"获取东方财富盈利预测数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-board-industry-name-em", response_model=ResponseModel[List[StockBoardIndustryNameEm]])
async def get_stock_board_industry_name_em():
    """
    获取东方财富 - 行业板块
    
    Returns:
        行业板块数据列表，包含：
        - 排名
        - 板块名称
        - 板块代码
        - 最新价
        - 涨跌额
        - 涨跌幅（%）
        - 总市值
        - 换手率（%）
        - 上涨家数
        - 下跌家数
        - 领涨股票
        - 领涨股票涨跌幅（%）
    
    Examples:
        - 获取行业板块：/api/v1/eastmoney/stock-board-industry-name-em
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        board_data = await adapter.get_stock_board_industry_name_em()
        return ResponseModel(data=board_data, message=f"获取成功，共{len(board_data)}条")
    except Exception as e:
        logger.error(f"获取东方财富行业板块数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-board-industry-spot-em/{symbol}", response_model=ResponseModel[List[StockBoardIndustrySpotEm]])
async def get_stock_board_industry_spot_em(symbol: str = Path(..., description="板块名称，如'小金属'")):
    """
    获取东方财富 - 行业板块实时行情
    
    Args:
        symbol: 板块名称，如"小金属"
    
    Returns:
        行业板块实时行情数据列表，包含：
        - item: 项目（最新、最高、最低、开盘等）
        - value: 数值
    
    Examples:
        - 获取小金属板块实时行情：/api/v1/eastmoney/stock-board-industry-spot-em/小金属
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        spot_data = await adapter.get_stock_board_industry_spot_em(symbol=symbol)
        return ResponseModel(data=spot_data, message=f"获取成功，共{len(spot_data)}条")
    except Exception as e:
        logger.error(f"获取东方财富行业板块实时行情数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()


@router.get("/stock-board-industry-cons-em/{symbol}", response_model=ResponseModel[List[StockBoardIndustryConsEm]])
async def get_stock_board_industry_cons_em(symbol: str = Path(..., description="板块名称或板块代码，如'小金属'或'BK1027'")):
    """
    获取东方财富 - 行业板块成份股
    
    Args:
        symbol: 板块名称或板块代码，如"小金属"或"BK1027"
    
    Returns:
        行业板块成份股数据列表，包含：
        - 序号
        - 代码
        - 名称
        - 最新价
        - 涨跌幅（%）
        - 涨跌额
        - 成交量（手）
        - 成交额
        - 振幅（%）
        - 最高
        - 最低
        - 今开
        - 昨收
        - 换手率（%）
        - 市盈率 - 动态
        - 市净率
    
    Examples:
        - 获取小金属板块成份股：/api/v1/eastmoney/stock-board-industry-cons-em/小金属
        - 使用板块代码：/api/v1/eastmoney/stock-board-industry-cons-em/BK1027
    """
    from app.adapters.eastmoney_adapter import EastMoneyAdapter
    
    adapter = EastMoneyAdapter()
    await adapter.initialize()
    
    try:
        cons_data = await adapter.get_stock_board_industry_cons_em(symbol=symbol)
        return ResponseModel(data=cons_data, message=f"获取成功，共{len(cons_data)}条")
    except Exception as e:
        logger.error(f"获取东方财富行业板块成份股数据失败：{e}")
        return ResponseModel(data=[], message=f"获取失败：{e}")
    finally:
        await adapter.close()
