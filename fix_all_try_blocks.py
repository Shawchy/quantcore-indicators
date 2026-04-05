#!/usr/bin/env python3
"""
一次性修复所有 try: 块的缩进错误
"""

def fix_all_try_blocks(file_path: str):
    """修复所有 try: 块的缩进错误"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有匹配的模式
    # 从：
    #   try:
    #       # 确保凭证有效（TLS 指纹伪装）
    #   await self._ensure_credentials()
    #   
    #   # 限流
    #   await self._rate_limit()
    # 到：
    #   try:
    #       # 确保凭证有效（TLS 指纹伪装）
    #       await self._ensure_credentials()
    #       
    #       # 限流
    #       await self._rate_limit()
    
    import re
    
    # 查找所有 try: 后面跟着缩进的注释，但代码没有缩进的情况
    pattern = r'(try:)\n(        )(#[^\n]*\n)(        )(await self\._ensure_credentials\(\))\n(\n)(        )(#[^\n]*\n)(        )(await self\._rate_limit\(\))'
    
    count = 0
    while True:
        new_content = re.sub(
            pattern,
            r'\1\n\2\3\2    \5\n\6\2    \8\n\2    \10',
            content
        )
        if new_content == content:
            break
        content = new_content
        count += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复 {count} 处 try: 块缩进错误")

if __name__ == "__main__":
    fix_all_try_blocks("backend/app/adapters/efinance_adapter.py")
