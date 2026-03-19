"""
统一数据模型和存储架构 - 测试示例

演示如何使用新实现的统一数据模型、存储路由、指标计算等功能
"""
import asyncio
from datetime import datetime
import pandas as pd


async def test_data_normalizer():
    """测试数据标准化转换器"""
    from app.utils.data_normalizer import DataNormalizer
    from app.models.unified_models import DataSourceType, AdjustType
    
    print("\n=== 测试数据标准化转换器 ===")
    
    # 测试代码标准化
    test_codes = ["600000", "600000.SH", "sh600000", "000001", "sz000001"]
    for code in test_codes:
        normalized = DataNormalizer.normalize_code(code)
        print(f"{code} -> {normalized}")
    
    # 测试市场类型判断
    test_codes = ["600000", "000001", "430001"]
    for code in test_codes:
        market = DataNormalizer.normalize_market(code)
        print(f"{code} -> {market.value}")
    
    # 测试 K 线数据标准化
    sample_data = {
        "股票代码": "600000",
        "日期": "2024-03-19",
        "开盘": 10.5,
        "最高": 10.8,
        "最低": 10.4,
        "收盘": 10.7,
        "成交量": 1000000,
        "成交额": 10700000,
        "换手率": 1.5
    }
    
    kline = DataNormalizer.normalize_kline(sample_data, DataSourceType.EFINANCE)
    print(f"\n标准化 K 线数据：{kline.code} {kline.date}")
    print(f"开盘：{kline.open}, 最高：{kline.high}, 最低：{kline.low}, 收盘：{kline.close}")


async def test_parquet_manager():
    """测试 Parquet 文件管理器"""
    from app.storage.parquet_manager import ParquetManager
    
    print("\n=== 测试 Parquet 文件管理器 ===")
    
    manager = ParquetManager()
    
    # 模拟 K 线数据
    sample_klines = [
        {
            "date": "2024-03-18",
            "open": 10.5,
            "high": 10.8,
            "low": 10.4,
            "close": 10.7,
            "volume": 1000000,
            "amount": 10700000
        },
        {
            "date": "2024-03-19",
            "open": 10.7,
            "high": 11.0,
            "low": 10.6,
            "close": 10.9,
            "volume": 1200000,
            "amount": 13080000
        }
    ]
    
    # 保存数据
    code = "600000"
    saved_count = manager.save_klines(code, sample_klines, adjust_type="qfq")
    print(f"保存 {code} K 线数据：{saved_count} 条")
    
    # 加载数据
    df = manager.load_klines(code, "2024-03-01", "2024-03-31", adjust_type="qfq")
    print(f"加载数据：{len(df)} 条")
    if not df.empty:
        print(df[["date", "open", "high", "low", "close"]].to_string())


async def test_cross_source_validator():
    """测试跨数据源校验器"""
    from app.utils.cross_source_validator import CrossSourceValidator
    from app.models.unified_models import UnifiedKLine, DataSourceType
    
    print("\n=== 测试跨数据源校验器 ===")
    
    validator = CrossSourceValidator(tolerance=0.01)
    
    # 模拟两个数据源的数据
    klines_efinance = [
        UnifiedKLine(
            code="600000",
            date="2024-03-19",
            open=10.5,
            high=10.8,
            low=10.4,
            close=10.7,
            volume=1000000,
            source=DataSourceType.EFINANCE
        )
    ]
    
    klines_akshare = [
        UnifiedKLine(
            code="600000",
            date="2024-03-19",
            open=10.5,
            high=10.8,
            low=10.4,
            close=10.71,  # 略有差异
            volume=1000000,
            source=DataSourceType.AKSHARE
        )
    ]
    
    klines_from_sources = {
        DataSourceType.EFINANCE: klines_efinance,
        DataSourceType.AKSHARE: klines_akshare
    }
    
    # 校验
    best_klines, report = validator.validate_multi_source(klines_from_sources)
    
    print(f"一致性比率：{report.consistency_rate*100:.2f}%")
    print(f"综合评分：{report.overall_score*100:.2f}")
    print(f"建议：{report.recommendations}")


async def test_indicators_manager():
    """测试技术指标管理器"""
    from app.services.indicators_manager import IndicatorsManager
    
    print("\n=== 测试技术指标管理器 ===")
    
    manager = IndicatorsManager(prefer_talib=False)  # 使用 pandas-ta
    
    # 创建模拟数据
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "open": 10 + pd.Series(range(100)).cumsum() / 100 + pd.Series(range(100)).apply(lambda x: x % 10) / 100,
        "high": 10.5 + pd.Series(range(100)).cumsum() / 100 + pd.Series(range(100)).apply(lambda x: x % 10) / 100,
        "low": 9.5 + pd.Series(range(100)).cumsum() / 100 + pd.Series(range(100)).apply(lambda x: x % 10) / 100,
        "close": 10 + pd.Series(range(100)).cumsum() / 100 + pd.Series(range(100)).apply(lambda x: x % 10) / 50,
        "volume": 1000000 + pd.Series(range(100)) * 10000
    })
    
    # 计算所有指标
    df_with_indicators = manager.calculate_all_indicators(df)
    
    print(f"计算指标完成，数据形状：{df_with_indicators.shape}")
    print(f"指标列：{[col for col in df_with_indicators.columns if 'ma' in col or 'macd' in col or 'rsi' in col]}")
    
    # 显示最新数据
    print("\n最新数据（包含指标）:")
    print(df_with_indicators.tail(1)[["date", "close", "ma5", "ma10", "macd", "rsi6"]])


async def test_storage_router():
    """测试存储路由器"""
    from app.storage.storage_router import StorageRouter
    
    print("\n=== 测试存储路由器 ===")
    
    router = StorageRouter(hot_threshold_days=90)
    
    # 模拟热数据（最近 30 天）
    hot_kline = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "open": 10.5,
        "high": 10.8,
        "low": 10.4,
        "close": 10.7,
        "volume": 1000000
    }
    
    # 模拟冷数据（100 天前）
    from datetime import timedelta
    cold_date = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
    cold_kline = {
        "date": cold_date,
        "open": 9.5,
        "high": 9.8,
        "low": 9.4,
        "close": 9.7,
        "volume": 800000
    }
    
    print(f"保存热数据：{hot_kline['date']}")
    await router.save_kline("600000", hot_kline)
    
    print(f"保存冷数据：{cold_kline['date']}")
    await router.save_kline("600000", cold_kline)
    
    print("存储路由器测试完成（实际存储需要数据库环境）")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("统一数据模型和存储架构 - 功能测试")
    print("=" * 60)
    
    try:
        await test_data_normalizer()
    except Exception as e:
        print(f"数据标准化测试失败：{e}")
    
    try:
        await test_parquet_manager()
    except Exception as e:
        print(f"Parquet 管理器测试失败：{e}")
    
    try:
        await test_cross_source_validator()
    except Exception as e:
        print(f"跨数据源校验测试失败：{e}")
    
    try:
        await test_indicators_manager()
    except Exception as e:
        print(f"指标管理器测试失败：{e}")
    
    try:
        await test_storage_router()
    except Exception as e:
        print(f"存储路由器测试失败：{e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
