import efinance as ef

print('Efinance 版本:', ef.__version__ if hasattr(ef, '__version__') else 'unknown')

print('\n=== ef.stock 可用方法 ===')
stock_methods = [m for m in dir(ef.stock) if not m.startswith('_')]
for m in stock_methods[:30]:
    print(f'  {m}')

print('\n=== 检查关键方法 ===')
methods = [
    'get_realtime_quotes',
    'get_quote_history',
    'get_base_info',
    'get_industry_board',
    'get_concept_board',
    'get_fund_flow'
]
for m in methods:
    print(f'{m}: {hasattr(ef.stock, m)}')
