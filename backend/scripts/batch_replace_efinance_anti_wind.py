"""
批量替换 EFinanceAdapter 中的老反风控调用

将以下模式：
    result = await self._retry_executor.execute(func=xxx, context="yyy")

替换为：
    result = await self._execute_with_anti_wind(request_func=xxx, context="yyy")
"""

import re
from pathlib import Path

def replace_anti_wind_patterns(file_path: str):
    """批量替换老的反风控模式"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计替换数量
    replacements = {
        'await self._retry_executor.execute': 0,
    }
    
    # 替换 await self._retry_executor.execute 调用
    # 这个比较复杂，需要保留 func 和 context 参数
    pattern = r'await self\._retry_executor\.execute\(\s*func=(\w+),\s*context="([^"]+)"[^\)]*\)'
    
    def replace_retry(match):
        func_name = match.group(1)
        context = match.group(2)
        return f'await self._execute_with_anti_wind(\n                request_func={func_name},\n                context="{context}"\n            )'
    
    matches = re.findall(pattern, content)
    replacements['await self._retry_executor.execute'] = len(matches)
    content = re.sub(pattern, replace_retry, content)
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return replacements


if __name__ == "__main__":
    file_path = Path(__file__).parent.parent / "app" / "adapters" / "efinance_adapter.py"
    
    print(f"开始批量替换：{file_path}")
    replacements = replace_anti_wind_patterns(str(file_path))
    
    print("\n替换完成！统计：")
    for pattern, count in replacements.items():
        print(f"  - {pattern}: {count} 处")
    
    total = sum(replacements.values())
    print(f"\n总计替换：{total} 处")
    print("\n✅ 批量替换完成！请运行测试验证。")
