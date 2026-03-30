"""
数据清洗与格式化验证脚本
检查数据处理器、验证器和标准化器的有效性
"""
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# 添加后端路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.data_processor import DataCleaner, PriceAdjuster, DataProcessor
from app.utils.data_validator import DataValidator
from app.utils.data_normalizer import DataNormalizer
from app.models.unified_models import DataSourceType, AdjustType
from loguru import logger

def test_data_cleaner():
    """测试数据清洗器"""
    print("=" * 80)
    print("测试数据清洗器 (DataCleaner)")
    print("=" * 80)
    
    cleaner = DataCleaner()
    
    # 创建测试数据
    test_data = {
        'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'open': [10.0, 10.5, None, 11.0, 11.5],  # 有缺失值
        'high': [10.8, 11.0, 11.2, 11.8, 12.0],
        'low': [9.5, 10.0, 10.2, 10.8, 11.0],
        'close': [10.5, 10.8, 11.0, 11.5, 11.8],
        'volume': [1000, 1200, 0, 1500, 1800],  # 有 0 值
    }
    
    df = pd.DataFrame(test_data)
    print("\n原始数据:")
    print(df)
    
    # 测试清洗
    cleaned_df = cleaner.clean_kline_data(df)
    print("\n清洗后的数据:")
    print(cleaned_df)
    
    # 测试验证
    validation = cleaner.validate_data(cleaned_df)
    print("\n数据验证结果:")
    print(f"  是否有效：{validation['is_valid']}")
    print(f"  错误：{validation['errors']}")
    print(f"  警告：{validation['warnings']}")
    print(f"  统计：{validation['stats']}")
    
    # 测试异常值检测
    test_outlier = {
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'open': [10.0, 10.5, 100.0],  # 异常值
        'high': [10.8, 11.0, 105.0],
        'low': [9.5, 10.0, 95.0],
        'close': [10.5, 10.8, 98.0],
        'volume': [1000, 1200, 1500],
    }
    df_outlier = pd.DataFrame(test_outlier)
    cleaned_outlier = cleaner.remove_outliers(df_outlier)
    print("\n异常值检测测试:")
    print(f"  原始数据：{len(df_outlier)} 条")
    print(f"  去除异常值后：{len(cleaned_outlier)} 条")
    
    print("\n✅ 数据清洗器测试完成\n")
    return True


def test_price_adjuster():
    """测试复权计算器"""
    print("=" * 80)
    print("测试复权计算器 (PriceAdjuster)")
    print("=" * 80)
    
    adjuster = PriceAdjuster()
    
    # 创建测试数据
    test_data = {
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'open': [10.0, 10.5, 11.0],
        'high': [10.8, 11.2, 11.8],
        'low': [9.5, 10.0, 10.5],
        'close': [10.5, 11.0, 11.5],
        'volume': [1000, 1200, 1500],
    }
    df = pd.DataFrame(test_data)
    
    # 创建复权因子
    adj_factor = pd.Series([1.0, 1.0, 0.5])  # 第 3 天分红，复权因子 0.5
    
    print("\n原始数据:")
    print(df)
    print("\n复权因子:")
    print(adj_factor.values)
    
    # 测试前复权
    qfq_df = adjuster.adjust_price(df.copy(), adj_factor, method='qfq')
    print("\n前复权 (qfq) 结果:")
    print(qfq_df)
    
    # 测试后复权
    hfq_df = adjuster.adjust_price(df.copy(), adj_factor, method='hfq')
    print("\n后复权 (hfq) 结果:")
    print(hfq_df)
    
    print("\n✅ 复权计算器测试完成\n")
    return True


def test_data_validator():
    """测试数据验证器"""
    print("=" * 80)
    print("测试数据验证器 (DataValidator)")
    print("=" * 80)
    
    validator = DataValidator()
    
    # 测试 K 线数据验证
    from app.adapters.base import KLineData
    
    valid_klines = [
        KLineData(code='000001', date='2024-01-01', open=10.0, high=10.8, low=9.5, close=10.5, volume=1000),
        KLineData(code='000001', date='2024-01-02', open=10.5, high=11.2, low=10.0, close=11.0, volume=1200),
    ]
    
    is_valid, errors = validator.validate_kline(valid_klines, '000001')
    print("\n有效数据验证:")
    print(f"  结果：{'✅ 有效' if is_valid else '❌ 无效'}")
    print(f"  错误：{errors}")
    
    # 测试无效数据
    invalid_klines = [
        KLineData(code='000001', date='2024-01-01', open=10.0, high=9.0, low=10.5, close=10.5, volume=1000),  # high < low
    ]
    
    is_valid, errors = validator.validate_kline(invalid_klines, '000001')
    print("\n无效数据验证:")
    print(f"  结果：{'✅ 有效' if is_valid else '❌ 无效'}")
    print(f"  错误：{errors}")
    
    # 测试 DataFrame 质量检查
    test_df = pd.DataFrame({
        'open': [10.0, 10.5, None],
        'high': [10.8, 11.2, 11.8],
        'low': [9.5, 10.0, 10.5],
        'close': [10.5, 11.0, 11.5],
        'volume': [1000, 1200, 1500],
    })
    
    quality_report = validator.check_data_quality(test_df, ['open', 'high', 'low', 'close', 'volume'])
    print("\nDataFrame 质量检查:")
    print(f"  总行数：{quality_report['total_rows']}")
    print(f"  缺失列：{quality_report['missing_columns']}")
    print(f"  空值统计：{quality_report['null_counts']}")
    print(f"  重复行：{quality_report['duplicate_rows']}")
    print(f"  质量评分：{quality_report['quality_score']:.2f}")
    
    print("\n✅ 数据验证器测试完成\n")
    return True


def test_data_normalizer():
    """测试数据标准化器"""
    print("=" * 80)
    print("测试数据标准化器 (DataNormalizer)")
    print("=" * 80)
    
    normalizer = DataNormalizer()
    
    # 测试股票代码格式化
    test_codes = ['600000', '600000.SH', 'sh600000', '000001', '000001.SZ', 'sz000001']
    print("\n股票代码格式化测试:")
    for code in test_codes:
        normalized = normalizer.normalize_code(code)
        print(f"  {code:15} -> {normalized}")
    
    # 测试市场类型判断
    print("\n市场类型判断:")
    for code in ['600000', '000001', '430000']:
        market = normalizer.normalize_market(code)
        print(f"  {code:10} -> {market.value}")
    
    # 测试 K 线数据标准化 (EFinance 格式)
    efinance_data = {
        '股票代码': '600000',
        '日期': '20240101',
        '开盘': 10.0,
        '最高': 10.8,
        '最低': 9.5,
        '收盘': 10.5,
        '成交量': 1000,
        '成交额': 10000000,
        '换手率': 1.5,
        '昨收': 10.2,
    }
    
    normalized_kline = normalizer.normalize_kline(efinance_data, DataSourceType.EFINANCE, AdjustType.QFQ)
    print("\nEFinance K 线数据标准化:")
    print(f"  代码：{normalized_kline.code}")
    print(f"  日期：{normalized_kline.date}")
    print(f"  开盘：{normalized_kline.open}")
    print(f"  收盘：{normalized_kline.close}")
    print(f"  数据源：{normalized_kline.source}")
    print(f"  复权类型：{normalized_kline.adjust_type}")
    
    # 测试验证
    is_valid = normalizer.validate_kline(normalized_kline)
    print(f"  验证结果：{'✅ 有效' if is_valid else '❌ 无效'}")
    
    print("\n✅ 数据标准化器测试完成\n")
    return True


def test_data_processor():
    """测试完整数据处理流程"""
    print("=" * 80)
    print("测试完整数据处理流程 (DataProcessor)")
    print("=" * 80)
    
    processor = DataProcessor()
    
    # 创建测试数据
    test_data = {
        'date': pd.date_range('2024-01-01', periods=10, freq='D'),
        'open': [10.0 + i * 0.5 for i in range(10)],
        'high': [10.8 + i * 0.5 for i in range(10)],
        'low': [9.5 + i * 0.5 for i in range(10)],
        'close': [10.5 + i * 0.5 for i in range(10)],
        'volume': [1000 + i * 100 for i in range(10)],
    }
    df = pd.DataFrame(test_data)
    
    print("\n原始数据:")
    print(df.head())
    
    # 处理数据
    processed_df = processor.process_kline(df, clean=True, validate=True, fill_missing=False)
    print("\n处理后的数据:")
    print(processed_df.head())
    
    # 计算收益率
    returns_df = processor.calculate_returns(processed_df)
    print("\n收益率计算:")
    print(returns_df[['date', 'close', 'return', 'log_return']].head())
    
    # 计算波动率
    volatility_df = processor.calculate_volatility(returns_df, window=5)
    print("\n波动率计算:")
    print(volatility_df[['date', 'close', 'return', 'volatility']].head())
    
    print("\n✅ 完整数据处理流程测试完成\n")
    return True


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("数据清洗与格式化验证报告")
    print("=" * 80)
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    results = {
        '数据清洗器': test_data_cleaner(),
        '复权计算器': test_price_adjuster(),
        '数据验证器': test_data_validator(),
        '数据标准化器': test_data_normalizer(),
        '完整处理流程': test_data_processor(),
    }
    
    print("=" * 80)
    print("测试结果总结")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有测试通过！数据清洗和格式化功能正常。")
    else:
        print("❌ 部分测试失败，请检查相关模块。")
    print("=" * 80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
