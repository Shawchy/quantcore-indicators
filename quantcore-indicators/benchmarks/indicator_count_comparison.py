"""
pandas-ta 支持的指标种类清单
"""

# pandas-ta 完整指标列表 (130+ 个)
PANDAS_TA_INDICATORS = {
    # 重叠指标 (Overlap) - 绘制在价格图表上
    "Overlap": [
        "SMA", "EMA", "WMA", "DEMA", "TEMA", "TRIMA", "KAMA", "MAMA", "T3",
        "VWAP", "VWMA", "MACD", "ADX", "AROOON", "AROOONOSC", "BOLLINGERBANDS",
        "DONCHIANKELNER", "ICHIMOKU", "SUPERTREND", "PSAR", "ZL_EMA", "HMA",
        "JMA", "FIR_EMA", "SSMA", "SWMA", "VIDYA", "TMA", "ALMA", "SINWMA",
        "MIDPRICE", "MIDPOINT", "SAR", "BBANDS",
    ],
    # 动量指标 (Momentum)
    "Momentum": [
        "RSI", "STOCH", "STOCHRSI", "MACD", "AO", "APO", "BOP", "CCI",
        "CMO", "COPPOCK", "ER", "ERI", "FISHER", "INERTIA", "KDJ",
        "MOM", "PO", "ROC", "RSX", "RSI", "SLOPE", "TRIX", "TSI",
        "UO", "WILLR", "STC", "BRAR", "CR", "DM", "PPO", "PVO",
        "QQE", "RVI", "SFX", "TRIX", "TR", "TTF",
    ],
    # 成交量指标 (Volume)
    "Volume": [
        "OBV", "AD", "ADOSC", "CMF", "EFIV", "EOM", "KVO", "MFI",
        "NVI", "PVI", "PVT", "VP", "VWAP", "VWMA", "WVAD",
    ],
    # 波动率指标 (Volatility)
    "Volatility": [
        "ATR", "TRUE_RANGE", "UI", "MAS", "NATR", "PDIST", "RVI",
        "THERMO", "CHEN_VOL", "GC_VOL", "HIST_VOL", "IMPLIED_VOL",
        "MEAN_ABS_DEV", "STDEV", "VAR", "Z_SCORE",
    ],
    # 周期指标 (Cycle)
    "Cycle": [
        "HT_DCPERIOD", "HT_DCPHASE", "HT_PHASOR", "HT_SINE", "HT_TRENDMODE",
    ],
    # 统计指标 (Statistics)
    "Statistics": [
        "ENTROPY", "KURTOSIS", "SKEW", "STDDEV", "VAR", "ZSCORE",
        "MAD", "MEDIAN", "PERCENTILE", "QUANTILE", "TOS_STDEV",
    ],
    # 蜡烛图模式 (Candle Patterns)
    "Candle": [
        "CDL_DOJI", "CDL_INSIDE", "CDL_PATTERN",
    ],
}

# 自研 quantcore-indicators 指标
QUANTCORE_INDICATORS = [
    "MA",           # 简单移动平均
    "EMA",          # 指数移动平均
    "WMA",          # 加权移动平均
    "MACD",         # 指数平滑异同移动平均
    "RSI",          # 相对强弱指数
    "BollingerBands", # 布林带
    "ATR",          # 平均真实波动范围
    "CCI",          # 顺势指标
    "KDJ",          # 随机指标 (KDJ)
    "OBV",          # 能量潮
    "WilliamsR",    # 威廉指标
    "ADX",          # 平均趋向指数
    "Stochastic",   # 随机指标
    "VWAP",         # 成交量加权平均价
]

def print_comparison():
    print("="*100)
    print("pandas-ta vs quantcore-indicators (Rust) 指标种类对比")
    print("="*100)
    print()
    
    # pandas-ta 统计
    total_pandas = sum(len(v) for v in PANDAS_TA_INDICATORS.values())
    print(f"pandas-ta 指标总数: {total_pandas}+")
    print()
    
    for cat, indicators in PANDAS_TA_INDICATORS.items():
        print(f"  {cat} ({len(indicators)}):")
        print(f"    {', '.join(indicators[:10])}")
        if len(indicators) > 10:
            print(f"    ... +{len(indicators) - 10} more")
        print()
    
    print("-"*100)
    print(f"\n自研 quantcore-indicators 指标总数: {len(QUANTCORE_INDICATORS)}")
    print(f"指标列表:")
    for ind in QUANTCORE_INDICATORS:
        print(f"  ✅ {ind}")
    
    print("\n" + "-"*100)
    print("\n📊 对比总结:")
    print(f"  pandas-ta: {total_pandas}+ 指标 (覆盖全市场)")
    print(f"  quantcore: {len(QUANTCORE_INDICATORS)} 指标 (聚焦核心高频指标)")
    print(f"  覆盖率: {len(QUANTCORE_INDICATORS) / total_pandas * 100:.1f}%")
    
    print("\n💡 说明:")
    print("  quantcore-indicators 专注核心指标，追求极致性能")
    print("  稀有指标（如 Ichimoku、Fibonacci、Candle Pattern）使用 pandas-ta fallback")
    print("  通过 indicators_manager.py 智能选择，两者互补")

if __name__ == "__main__":
    print_comparison()
