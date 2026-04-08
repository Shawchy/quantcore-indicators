"""
批量替换 AkShareAdapter 中的老反风控调用

将以下模式：
    await self._ensure_credentials()
    await self._rate_limit()
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
        'await self._ensure_credentials()': 0,
        'await self._rate_limit()': 0,
        'await self._retry_executor.execute': 0,
    }
    
    # 1. 删除所有 await self._ensure_credentials() 和紧随的注释
    pattern1 = r'\s*#[^\n]*确保凭证有效[^\n]*\n\s*await self\._ensure_credentials\(\)'
    matches1 = re.findall(pattern1, content)
    replacements['await self._ensure_credentials()'] = len(matches1)
    content = re.sub(pattern1, '', content)
    
    # 2. 删除所有 await self._rate_limit() 和紧随的注释
    pattern2 = r'\s*#[^\n]*限流[^\n]*\n\s*await self\._rate_limit\(\)'
    matches2 = re.findall(pattern2, content)
    replacements['await self._rate_limit()'] = len(matches2)
    content = re.sub(pattern2, '', content)
    
    # 3. 替换 await self._retry_executor.execute 调用
    # 这个比较复杂，需要保留 func 和 context 参数
    pattern3 = r'await self\._retry_executor\.execute\(\s*func=(\w+),\s*context="([^"]+)"[^\)]*\)'
    
    def replace_retry(match):
        func_name = match.group(1)
        context = match.group(2)
        return f'await self._execute_with_anti_wind(\n                request_func={func_name},\n                context="{context}"\n            )'
    
    matches3 = re.findall(pattern3, content)
    replacements['await self._retry_executor.execute'] = len(matches3)
    content = re.sub(pattern3, replace_retry, content)
    
    # 4. 删除老的反风控方法（可选，这里先不删除，保持向后兼容）
    # _ensure_credentials, _rate_limit, _rotate_user_agent, _detect_rate_limit 等
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return replacements


if __name__ == "__main__":
    # 直接在当前目录查找 akshare_adapter.py
    file_path = Path(__file__).parent.parent / "app" / "adapters" / "akshare_adapter.py"
    
    print(f"开始批量替换：{file_path}")
    replacements = replace_anti_wind_patterns(str(file_path))
    
    print("\n替换完成！统计：")
    for pattern, count in replacements.items():
        print(f"  - {pattern}: {count} 处")
    
    total = sum(replacements.values())
    print(f"\n总计替换：{total} 处")
    print("\n✅ 批量替换完成！请运行测试验证。")
