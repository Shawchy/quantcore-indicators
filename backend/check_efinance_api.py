import efinance as ef
import inspect

print('=== 检查 get_realtime_quotes 签名 ===')
sig = inspect.signature(ef.stock.get_realtime_quotes)
print(f'签名: {sig}')
print(f'参数: {list(sig.parameters.keys())}')

print('\n=== 检查 get_quote_history 签名 ===')
sig = inspect.signature(ef.stock.get_quote_history)
print(f'签名: {sig}')
print(f'参数: {list(sig.parameters.keys())}')

print('\n=== 测试 get_realtime_quotes ===')
try:
    df = ef.stock.get_realtime_quotes()
    print(f'成功: {len(df)} 条')
    print(df.columns.tolist())
except Exception as e:
    print(f'失败: {e}')

print('\n=== 测试 get_quote_history ===')
try:
    df = ef.stock.get_quote_history('000001')
    print(f'成功: {len(df)} 条')
    print(df.columns.tolist())
except Exception as e:
    print(f'失败: {e}')

print('\n=== 测试 get_base_info ===')
try:
    info = ef.stock.get_base_info('000001')
    print(f'成功: {type(info)}')
    if isinstance(info, dict):
        for k, v in list(info.items())[:5]:
            print(f'  {k}: {v}')
except Exception as e:
    print(f'失败: {e}')

print('\n=== 检查是否有板块相关方法 ===')
board_methods = [m for m in dir(ef) if 'board' in m.lower() or 'concept' in m.lower() or 'industry' in m.lower()]
print(f'板块相关方法: {board_methods}')

print('\n=== 检查 ef 模块顶层 ===')
ef_top = [m for m in dir(ef) if not m.startswith('_')]
print(f'ef 顶层: {ef_top}')
