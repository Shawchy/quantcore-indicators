import akshare as ak
import inspect

print('=== AKShare 板块相关方法 ===')
board_methods = [m for m in dir(ak) if 'board' in m.lower() or 'concept' in m.lower() or 'industry' in m.lower()]
for m in board_methods:
    print(f'  {m}')

print('\n=== AKShare 资金流向方法 ===')
fund_methods = [m for m in dir(ak) if 'fund' in m.lower() and 'flow' in m.lower()]
for m in fund_methods:
    print(f'  {m}')

print('\n=== 测试 board_industry_name_em ===')
try:
    df = ak.board_industry_name_em()
    print(f'成功: {len(df)} 条')
    print(df.columns.tolist())
except Exception as e:
    print(f'失败: {e}')

print('\n=== 测试 board_concept_name_em ===')
try:
    df = ak.board_concept_name_em()
    print(f'成功: {len(df)} 条')
except Exception as e:
    print(f'失败: {e}')

print('\n=== 测试 individual_fund_flow ===')
try:
    df = ak.individual_fund_flow(stock='000001', market='sz')
    print(f'成功: {len(df)} 条')
except Exception as e:
    print(f'失败: {e}')

print('\n=== 测试 stock_individual_fund_flow ===')
try:
    df = ak.stock_individual_fund_flow(stock='000001', market='sz')
    print(f'成功: {len(df)} 条')
except Exception as e:
    print(f'失败: {e}')
