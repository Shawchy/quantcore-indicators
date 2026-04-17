"""
Alpha工厂使用示例

展示如何使用完整的Alpha工厂系统进行因子生产、组合优化和风险管理
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import date, timedelta


async def example_basic_usage():
    """基础使用示例"""
    print("=" * 60)
    print("Alpha工厂基础使用示例")
    print("=" * 60)
    
    from quantcore.alpha import AlphaFactory
    
    # 1. 初始化工厂
    factory = AlphaFactory()
    await factory.initialize()
    
    # 2. 查看工厂状态
    status = factory.get_status()
    print(f"\n工厂状态: {status['initialized']}")
    print(f"可用优化器: {status['available_optimizers']}")
    print(f"可用爬虫: {status['available_crawlers']}")
    
    # 3. 准备测试数据
    symbols = ['000001.SZ', '600036.SH', '300750.SZ']
    
    np.random.seed(42)
    dates = pd.date_range(end=date.today(), periods=252, freq='B')
    
    returns = pd.DataFrame(
        np.random.randn(252, len(symbols)) * 0.02,
        index=dates,
        columns=symbols
    )
    
    print(f"\n测试数据: {returns.shape}")
    
    # 4. 生产因子
    print("\n正在生产因子...")
    factor_result = await factory.produce_factors(symbols)
    
    print(f"生产因子数: {factor_result.summary['factors_count']}")
    print(f"因子列表: {factor_result.summary['factors_produced'][:5]}...")
    if factor_result.errors:
        print(f"错误: {factor_result.errors[:2]}")
    
    return factory, returns


async def example_portfolio_optimization():
    """组合优化示例"""
    print("\n" + "=" * 60)
    print("组合优化示例")
    print("=" * 60)
    
    from quantcore.alpha import AlphaFactory
    
    factory = AlphaFactory()
    
    # 准备收益率数据
    symbols = ['000001.SZ', '600036.SH', '300750.SZ', '601318.SH', '000858.SZ']
    
    np.random.seed(42)
    dates = pd.date_range(end=date.today(), periods=252, freq='B')
    returns = pd.DataFrame(
        np.random.randn(252, len(symbols)) * 0.02 + 0.0005,
        index=dates,
        columns=symbols
    )
    
    # 均值-方差优化
    print("\n1. 均值-方差优化 (Mean-Variance)...")
    result_mv = await factory.optimize_portfolio(
        returns,
        method='mean_variance',
        risk_aversion=1.0
    )
    
    print(f"预期收益: {result_mv.expected_return:.4f}")
    print(f"预期风险: {result_mv.expected_risk:.4f}")
    print(f"夏普比率: {result_mv.sharpe_ratio:.4f}")
    print(f"\n权重分配:")
    for asset, weight in result_mv.weights.items():
        if abs(weight) > 0.01:
            print(f"  {asset}: {weight:.4f}")
    
    # 风险平价优化
    print("\n2. 风险平价优化 (Risk Parity)...")
    result_rp = await factory.optimize_portfolio(
        returns,
        method='risk_parity'
    )
    
    print(f"预期收益: {result_rp.expected_return:.4f}")
    print(f"预期风险: {result_rp.expected_risk:.4f}")
    print(f"夏普比率: {result_rp.sharpe_ratio:.4f}")
    
    # 最大分散化优化
    print("\n3. 最大分散化优化 (Max Diversification)...")
    result_md = await factory.optimize_portfolio(
        returns,
        method='max_diversification'
    )
    
    print(f"预期收益: {result_md.expected_return:.4f}")
    print(f"预期风险: {result_md.expected_risk:.4f}")
    print(f"夏普比率: {result_md.sharpe_ratio:.4f}")


async def example_alternative_data():
    """另类数据采集示例"""
    print("\n" + "=" * 60)
    print("另类数据采集示例")
    print("=" * 60)
    
    from quantcore.alpha.alternative.raw import (
        FundFlowCrawler,
        SentimentCrawler,
        ESGCrawler
    )
    
    symbols = ['000001.SZ', '600036.SH', '300750.SZ']
    
    # 资金流向数据
    print("\n1. 资金流向因子...")
    fund_crawler = FundFlowCrawler()
    fund_factors = await fund_crawler.calculate_fund_flow_factors(symbols)
    
    for symbol, factors in list(fund_factors.items())[:2]:
        print(f"\n{symbol}:")
        print(f"  主力净流入比例: {factors.get('main_net_inflow_ratio', 0):.4f}")
        print(f"  大单占比: {factors.get('large_order_ratio', 0):.4f}")
    
    # 舆情情感数据
    print("\n2. 舆情情感因子...")
    sentiment_crawler = SentimentCrawler()
    sentiment_factors = await sentiment_crawler.calculate_sentiment_factors(symbols)
    
    for symbol, factors in list(sentiment_factors.items())[:2]:
        print(f"\n{symbol}:")
        print(f"  综合情感得分: {factors.get('sentiment_composite', 0):.4f}")
        print(f"  新闻关注度: {factors.get('news_attention', 0):.4f}")
    
    # ESG数据
    print("\n3. ESG因子...")
    esg_crawler = ESGCrawler()
    esg_factors = await esg_crawler.calculate_esg_factors(symbols)
    
    for symbol, factors in list(esg_factors.items())[:2]:
        print(f"\n{symbol}:")
        print(f"  ESG总分: {factors.get('esg_total_score', 0):.4f}")
        print(f"  环境评分: {factors.get('esg_environment_score', 0):.4f}")
        print(f"  社会评分: {factors.get('esg_social_score', 0):.4f}")
        print(f"  治理评分: {factors.get('esg_governance_score', 0):.4f}")


async def example_risk_model():
    """风险模型示例"""
    print("\n" + "=" * 60)
    print("Barra风险模型示例")
    print("=" * 60)
    
    from quantcore.alpha import BarraRiskModel
    
    # 初始化风险模型
    risk_model = BarraRiskModel(model_type="barra_cne5")
    await risk_model.initialize()
    
    print(f"\n风险模型类型: {risk_model.model_type}")
    print(f"风格因子数量: {len(risk_model.style_factors)}")
    print(f"行业因子数量: {len(risk_model.industry_factors)}")
    
    # 模拟持仓分析
    positions = {
        '000001.SZ': 0.25,
        '600036.SH': 0.30,
        '300750.SZ': 0.20,
        '601318.SH': 0.15,
        '000858.SZ': 0.10
    }
    
    print("\n模拟持仓:")
    for asset, weight in positions.items():
        print(f"  {asset}: {weight:.2%}")
    
    # 风险分析（需要实际因子暴露数据）
    try:
        risk_analysis = await risk_model.analyze_portfolio(positions)
        
        print("\n风险分析结果:")
        if 'total_risk' in risk_analysis:
            print(f"  总风险: {risk_analysis['total_risk']:.4f}")
        if 'factor_risks' in risk_analysis:
            print(f"  因子风险贡献:")
            for factor, risk in list(risk_analysis['factor_risks'].items())[:5]:
                print(f"    {factor}: {risk:.4f}")
                
    except Exception as e:
        print(f"风险分析需要完整因子数据: {e}")


async def example_transaction_cost():
    """交易成本模型示例"""
    print("\n" + "=" * 60)
    print("交易成本模型示例")
    print("=" * 60)
    
    from quantcore.alpha.optimizer.transaction_cost import (
        TransactionCostModel,
        TradeCostConfig
    )
    
    # 配置交易成本
    config = TradeCostConfig(
        commission_rate=0.0003,  # 万三佣金
        stamp_tax_rate=0.001,   # 千一印花税
        slippage_rate=0.001,    # 千一滑点
    )
    
    cost_model = TransactionCostModel(config=config)
    
    # 计算交易成本
    trades = [
        {'symbol': '000001.SZ', 'direction': 'buy', 
         'quantity': 10000, 'price': 15.5, 'market_cap': 200e8},
        {'symbol': '600036.SH', 'direction': 'sell',
         'quantity': 5000, 'price': 45.0, 'market_cap': 500e8},
    ]
    
    print("\n交易成本明细:")
    for trade in trades:
        cost = cost_model.calculate_trade_cost(
            symbol=trade['symbol'],
            direction=trade['direction'],
            quantity=trade['quantity'],
            price=trade['price'],
            market_cap=trade['market_cap']
        )
        
        print(f"\n{trade['symbol']} ({trade['direction']}):")
        print(f"  交易金额: {trade['quantity'] * trade['price']:,.0f} 元")
        print(f"  佣金: {cost.commission:.2f} 元")
        print(f"  印花税: {cost.stamp_tax:.2f} 元")
        print(f"  滑点: {cost.slippage:.2f} 元")
        print(f"  市场冲击: {cost.market_impact:.2f} 元")
        print(f"  总成本: {cost.total_cost:.2f} 元 ({cost.cost_ratio:.4%})")


async def example_full_pipeline():
    """完整流水线示例"""
    print("\n" + "=" * 60)
    print("完整流水线示例")
    print("=" * 60)
    
    from quantcore.alpha import AlphaFactory
    
    # 初始化工厂
    factory = AlphaFactory()
    
    # 准备数据
    symbols = ['000001.SZ', '600036.SH', '300750.SZ']
    
    np.random.seed(42)
    dates = pd.date_range(end=date.today(), periods=252, freq='B')
    returns = pd.DataFrame(
        np.random.randn(252, len(symbols)) * 0.02 + 0.0005,
        index=dates,
        columns=symbols
    )
    
    print("\n运行完整流水线...")
    print(f"股票数量: {len(symbols)}")
    print(f"数据长度: {len(returns)} 个交易日")
    
    # 运行完整流水线
    result = await factory.run_full_pipeline(
        symbols=symbols,
        returns=returns,
        optimization_method='mean_variance'
    )
    
    print(f"\n流水线状态: {result['status']}")
    print(f"执行时间: {result.get('duration_seconds', 0):.2f} 秒")
    
    if 'factor_production' in result:
        fp = result['factor_production']
        print(f"\n因子生产:")
        print(f"  生产因子数: {fp['factors_count']}")
        print(f"  错误数: {fp['errors_count']}")
    
    if 'portfolio_optimization' in result:
        po = result['portfolio_optimization']
        print(f"\n组合优化:")
        print(f"  预期收益: {po['expected_return']:.4f}")
        print(f"  预期风险: {po['expected_risk']:.4f}")
        print(f"  夏普比率: {po['sharpe_ratio']:.4f}")
        print(f"  使用优化器: {po['optimizer']}")


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  QuantCore Alpha 工厂 - 使用示例".center(52) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60 + "\n")
    
    try:
        # 示例1: 基础使用
        await example_basic_usage()
        
        # 示例2: 组合优化
        await example_portfolio_optimization()
        
        # 示例3: 另类数据
        await example_alternative_data()
        
        # 示例4: 风险模型
        await example_risk_model()
        
        # 示例5: 交易成本
        await example_transaction_cost()
        
        # 示例6: 完整流水线
        await example_full_pipeline()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
