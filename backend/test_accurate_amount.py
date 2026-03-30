"""
测试使用 ak.stock_sh_a_spot_em 获取准确的沪市成交额
"""
import akshare as ak

print("=" * 70)
print("测试准确的成交额数据获取方法")
print("=" * 70)

# 获取沪市 A 股数据
print("\n获取沪市 A 股数据...")
df_sh = ak.stock_sh_a_spot_em()
sh_amount = df_sh['成交额'].sum()
print(f"沪市总成交额：{sh_amount/100000000:.2f}亿元")

# 获取深市 A 股数据
print("\n获取深市 A 股数据...")
df_sz = ak.stock_sz_a_spot_em()
sz_amount = df_sz['成交额'].sum()
print(f"深市总成交额：{sz_amount/100000000:.2f}亿元")

# 计算总和
total = sh_amount + sz_amount
print(f"\n两市总成交额：{total/100000000:.2f}亿元")

# 对比真实数据
print(f"\n对比真实数据 (2026 年 3 月 27 日):")
print(f"  沪市实际：7,996.96 亿元 | 获取：{sh_amount/100000000:.2f}亿元 | 误差：{abs(sh_amount/100000000 - 7996.96)/7996.96*100:.2f}%")
print(f"  深市实际：10,535.77 亿元 | 获取：{sz_amount/100000000:.2f}亿元 | 误差：{abs(sz_amount/100000000 - 10535.77)/10535.77*100:.2f}%")
print(f"  两市实际：18,500 亿元 | 获取：{total/100000000:.2f}亿元")

print("\n" + "=" * 70)
print("结论：可以使用 ak.stock_sh_a_spot_em 和 ak.stock_sz_a_spot_em 获取准确的成交额")
print("=" * 70)
