"""东方财富 - 同行比较 API 端点

提供成长性和估值比较数据接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockZhGrowthComparisonEM, StockZhValuationComparisonEM, StockZhDupontComparisonEM, StockZhScaleComparisonEM
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/growth-comparison", response_model=ResponseModel[List[StockZhGrowthComparisonEM]])
async def get_growth_comparison(
    symbol: str = Query(..., description="股票代码（如 'SZ000895'）- 需要带市场前缀"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富成长性比较数据（同行比较）
    
    返回同行业公司的成长性比较数据（21 个字段）：
    
    **基本信息**:
    - **code**: 代码
    - **name**: 简称
    
    **基本每股收益增长率** (%):
    - **eps_growth_3y**: 3 年复合
    - **eps_growth_24a**: 24A（2024 年实际）
    - **eps_growth_ttm**: TTM（滚动 12 个月）
    - **eps_growth_25e**: 25E（2025 年预测）
    - **eps_growth_26e**: 26E（2026 年预测）
    - **eps_growth_27e**: 27E（2027 年预测）
    
    **营业收入增长率** (%):
    - **revenue_growth_3y**: 3 年复合
    - **revenue_growth_24a**: 24A
    - **revenue_growth_ttm**: TTM
    - **revenue_growth_25e**: 25E
    - **revenue_growth_26e**: 26E
    - **revenue_growth_27e**: 27E
    
    **净利润增长率** (%):
    - **net_profit_growth_3y**: 3 年复合
    - **net_profit_growth_24a**: 24A
    - **net_profit_growth_ttm**: TTM
    - **net_profit_growth_25e**: 25E
    - **net_profit_growth_26e**: 26E
    - **net_profit_growth_27e**: 27E
    
    **排名**:
    - **eps_growth_3y_rank**: 基本每股收益增长率 -3 年复合排名
    
    **使用场景**:
    - 同行业成长性对比
    - 行业增长趋势分析
    - 个股成长性定位
    - 投资价值评估
    - 行业研究报告
    
    **注意**:
    - 数据来源：东方财富网
    - 包含行业平均、行业中值
    - 缓存时间：1 小时
    - 股票代码需要带市场前缀（SZ/SH）
    
    **数据说明**:
    - **3 年复合**: 3 年复合增长率
    - **24A**: 2024 年实际数据
    - **TTM**: 滚动 12 个月数据
    - **25E/26E/27E**: 2025/2026/2027 年预测数据
    
    **示例应用**:
    
    1. **获取成长性比较数据**:
       ```
       GET /api/v1/stock-comparison/growth-comparison?symbol=SZ000895
       ```
    
    2. **分析行业成长性**:
       - 筛选 name='行业平均' 或 '行业中值' 的数据
       - 对比行业平均水平和个股表现
    
    3. **寻找高成长股**:
       - 按 eps_growth_3y 降序排序
       - 筛选增长率高于行业平均的股票
    
    4. **预测未来增长**:
       - 分析 25E/26E/27E 预测数据
       - 判断行业增长趋势
    """
    try:
        data = await adapter.get_stock_zh_growth_comparison_em(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取成长性比较数据失败：{str(e)}",
            "data": []
        }


@router.get("/valuation-comparison", response_model=ResponseModel[List[StockZhValuationComparisonEM]])
async def get_valuation_comparison(
    symbol: str = Query(..., description="股票代码（如 'SZ000895'）- 需要带市场前缀"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富估值比较数据（同行比较）
    
    返回同行业公司的估值比较数据（20 个字段）：
    
    **基本信息**:
    - **rank**: 排名
    - **code**: 代码
    - **name**: 简称
    
    **PEG 指标**:
    - **peg**: PEG（市盈率相对盈利增长比率）
    
    **市盈率 (PE)**:
    - **pe_24a**: 24A（2024 年实际）
    - **pe_ttm**: TTM（滚动 12 个月）
    - **pe_25e**: 25E（2025 年预测）
    - **pe_26e**: 26E（2026 年预测）
    - **pe_27e**: 27E（2027 年预测）
    
    **市销率 (PS)**:
    - **ps_24a**: 24A
    - **ps_ttm**: TTM
    - **ps_25e**: 25E
    - **ps_26e**: 26E
    - **ps_27e**: 27E
    
    **市净率 (PB)**:
    - **pb_24a**: 24A
    - **pb_mrq**: MRQ（最新季度）
    
    **市现率 (PCF)**:
    - **pcf1_24a**: 市现率 1-24A
    - **pcf1_ttm**: 市现率 1-TTM
    - **pcf2_24a**: 市现率 2-24A
    - **pcf2_ttm**: 市现率 2-TTM
    
    **企业价值倍数**:
    - **ev_ebitda_24a**: EV/EBITDA-24A
    
    **使用场景**:
    - 同行业估值对比
    - 低估股票筛选
    - 估值水平分析
    - 投资价值评估
    - 行业研究报告
    
    **注意**:
    - 数据来源：东方财富网
    - 包含行业平均、行业中值
    - 缓存时间：1 小时
    - 股票代码需要带市场前缀（SZ/SH）
    
    **估值指标说明**:
    - **PEG**: 市盈率/净利润增长率，<1 表示低估
    - **PE**: 市盈率，股价/每股收益
    - **PS**: 市销率，市值/营业收入
    - **PB**: 市净率，股价/每股净资产
    - **PCF**: 市现率，股价/现金流
    - **EV/EBITDA**: 企业价值/息税折旧摊销前利润
    
    **示例应用**:
    
    1. **获取估值比较数据**:
       ```
       GET /api/v1/stock-comparison/valuation-comparison?symbol=SZ000895
       ```
    
    2. **寻找低估股票**:
       - 按 pe_ttm 升序排序
       - 筛选 PE 低于行业平均的股票
    
    3. **PEG 选股**:
       - 筛选 peg < 1 的股票
       - 寻找成长性被低估的标的
    
    4. **估值横向对比**:
       - 对比 PE、PB、PS 等多个指标
       - 综合评估估值水平
    
    5. **分析行业估值**:
       - 查看行业平均、行业中值的估值水平
       - 判断行业整体估值高低
    """
    try:
        data = await adapter.get_stock_zh_valuation_comparison_em(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取估值比较数据失败：{str(e)}",
            "data": []
        }


@router.get("/dupont-comparison", response_model=ResponseModel[List[StockZhDupontComparisonEM]])
async def get_dupont_comparison(
    symbol: str = Query(..., description="股票代码（如 'SZ000895'）- 需要带市场前缀"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富杜邦分析比较数据（同行比较）
    
    返回同行业公司的杜邦分析比较数据（19 个字段）：
    
    **基本信息**:
    - **code**: 代码
    - **name**: 简称
    
    **ROE**(净资产收益率，%):
    - **roe_3y_avg**: 3 年平均
    - **roe_22a**: 22A（2022 年实际）
    - **roe_23a**: 23A（2023 年实际）
    - **roe_24a**: 24A（2024 年实际）
    
    **净利率** (%):
    - **net_profit_margin_3y_avg**: 3 年平均
    - **net_profit_margin_22a**: 22A
    - **net_profit_margin_23a**: 23A
    - **net_profit_margin_24a**: 24A
    
    **总资产周转率**:
    - **asset_turnover_3y_avg**: 3 年平均
    - **asset_turnover_22a**: 22A
    - **asset_turnover_23a**: 23A
    - **asset_turnover_24a**: 24A
    
    **权益乘数** (财务杠杆):
    - **equity_multiplier_3y_avg**: 3 年平均
    - **equity_multiplier_22a**: 22A
    - **equity_multiplier_23a**: 23A
    - **equity_multiplier_24a**: 24A
    
    **排名**:
    - **roe_3y_avg_rank**: ROE-3 年平均排名
    
    **杜邦分析核心公式**:
    ```
    ROE = 净利率 × 总资产周转率 × 权益乘数
    ```
    
    **使用场景**:
    - 同行业 ROE 对比
    - 盈利能力分析
    - 运营效率分析
    - 财务杠杆分析
    - 投资价值评估
    
    **注意**:
    - 数据来源：东方财富网
    - 包含行业平均、行业中值
    - 缓存时间：1 小时
    - 股票代码需要带市场前缀（SZ/SH）
    
    **示例应用**:
    
    1. **获取杜邦分析数据**:
       ```
       GET /api/v1/stock-comparison/dupont-comparison?symbol=SZ000895
       ```
    
    2. **ROE 对比分析**:
       - 对比个股与行业平均的 ROE
       - 分析 ROE 的稳定性（3 年平均 vs 单年）
    
    3. **杜邦分析三因素**:
       - 净利率：反映盈利能力
       - 总资产周转率：反映运营效率
       - 权益乘数：反映财务杠杆
    
    4. **寻找高 ROE 股票**:
       - 按 roe_3y_avg 降序排序
       - 分析高 ROE 的驱动因素
    """
    try:
        data = await adapter.get_stock_zh_dupont_comparison_em(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取杜邦分析比较数据失败：{str(e)}",
            "data": []
        }


@router.get("/scale-comparison", response_model=ResponseModel[List[StockZhScaleComparisonEM]])
async def get_scale_comparison(
    symbol: str = Query(..., description="股票代码（如 'SZ000895'）- 需要带市场前缀"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富公司规模比较数据（同行比较）
    
    返回同行业公司的规模比较数据（10 个字段）：
    
    **基本信息**:
    - **code**: 代码
    - **name**: 简称
    
    **市值指标** (元):
    - **total_market_cap**: 总市值
    - **total_market_cap_rank**: 总市值排名
    - **float_market_cap**: 流通市值
    - **float_market_cap_rank**: 流通市值排名
    
    **营收和利润指标** (元):
    - **revenue**: 营业收入
    - **revenue_rank**: 营业收入排名
    - **net_profit**: 净利润
    - **net_profit_rank**: 净利润排名
    
    **使用场景**:
    - 同行业规模对比
    - 行业地位分析
    - 龙头企业识别
    - 投资标的筛选
    - 行业研究报告
    
    **注意**:
    - 数据来源：东方财富网
    - 包含行业平均、行业中值
    - 缓存时间：1 小时
    - 股票代码需要带市场前缀（SZ/SH）
    
    **示例应用**:
    
    1. **获取公司规模数据**:
       ```
       GET /api/v1/stock-comparison/scale-comparison?symbol=SZ000895
       ```
    
    2. **行业龙头识别**:
       - 按 total_market_cap 降序排序
       - 按 revenue 降序排序
       - 识别市值和营收领先的企業
    
    3. **规模与估值对比**:
       - 结合估值比较数据
       - 分析大市值公司的估值水平
    
    4. **行业集中度分析**:
       - 计算前几名企业的市场份额
       - 分析行业竞争格局
    """
    try:
        data = await adapter.get_stock_zh_scale_comparison_em(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取公司规模比较数据失败：{str(e)}",
            "data": []
        }
