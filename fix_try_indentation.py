#!/usr/bin/env python3
"""
修复 try: 块中的缩进问题
处理模式：
  try:
      # 注释（正确缩进）
  await self.xxx()  （错误：应该缩进但没有）
"""

import re

def fix_try_indentation(file_path: str):
    """修复 try 块缩进"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 模式1: 注释正确缩进，但代码没有
    # 查找：try:\n            # 确保...\n        await
    pattern1 = r'(try:\s*\n\s+)(# 确保凭证有效[^\n]*\n)(\s*)await self\._ensure_credentials\(\)'
    replacement1 = r'\1\2\1await self._ensure_credentials()'
    content = re.sub(pattern1, replacement1, content)
    
    # 模式2: 空行后的 # 限流
    pattern2 = r'(try:\s*\n\s+# 确保[^\n]*\n\s+await self\._ensure_credentials\(\)\s*\n)(\s*\n)(\s*)# 限流'
    replacement2 = r'\1\2\1# 限流'
    content = re.sub(pattern2, replacement2, content)
    
    # 模式3: # 限流后的 await self._rate_limit()
    pattern3 = r'(try:\s*\n\s+# 确保[^\n]*\n\s+await self\._ensure_credentials\(\)[^\n]*\n\s*\n\s+# 限流[^\n]*\n)(\s*)await self\._rate_limit\(\)'
    replacement3 = r'\1\2await self._rate_limit()'
    # 注意：这里假设已经有一定缩进，只是可能不对
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复文件: {file_path}")

if __name__ == "__main__":
    fix_try_indentation("backend/app/adapters/efinance_adapter.py")
