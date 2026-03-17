"""简单测试 efinance get_realtime_quotes"""
import efinance as ef

print("测试 efinance get_realtime_quotes API...")

# 测试 1: 默认（沪深京 A 股）
print("\n1. 默认获取沪深京 A 股...")
try:
    df = ef.stock.get_realtime_quotes()
    print(f"成功！获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(f"示例：{df.iloc[0]['股票代码']} {df.iloc[0]['股票名称']} 最新价={df.iloc[0]['最新价']} 涨跌幅={df.iloc[0]['涨跌幅']}")
except Exception as e:
    print(f"失败：{e}")

# 测试 2: 创业板
print("\n2. 获取创业板...")
try:
    df = ef.stock.get_realtime_quotes('创业板')
    print(f"成功！获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(f"示例：{df.iloc[0]['股票代码']} {df.iloc[0]['股票名称']} 最新价={df.iloc[0]['最新价']} 涨跌幅={df.iloc[0]['涨跌幅']}")
except Exception as e:
    print(f"失败：{e}")

# 测试 3: ETF
print("\n3. 获取 ETF...")
try:
    df = ef.stock.get_realtime_quotes('ETF')
    print(f"成功！获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(f"示例：{df.iloc[0]['股票代码']} {df.iloc[0]['股票名称']} 最新价={df.iloc[0]['最新价']} 涨跌幅={df.iloc[0]['涨跌幅']}")
except Exception as e:
    print(f"失败：{e}")

# 测试 4: 多个市场
print("\n4. 获取多个市场（创业板，科创板）...")
try:
    df = ef.stock.get_realtime_quotes(['创业板', '科创板'])
    print(f"成功！获取到 {len(df)} 条数据")
    if len(df) > 0:
        print(f"示例：{df.iloc[0]['股票代码']} {df.iloc[0]['股票名称']} 最新价={df.iloc[0]['最新价']} 涨跌幅={df.iloc[0]['涨跌幅']}")
except Exception as e:
    print(f"失败：{e}")

print("\n测试完成！")
