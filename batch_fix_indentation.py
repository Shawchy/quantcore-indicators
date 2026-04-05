#!/usr/bin/env python3
"""
批量修复 EFinance 中的缩进错误
模式：
  try:
      # 注释（正确缩进）
  await self.xxx()  （错误：未缩进）
"""

import re

def batch_fix_indentation(file_path: str):
    """批量修复缩进错误"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并修复所有 try: 块中的缩进问题
    # 模式：try:\n(8个空格)# 确保...\n(8个空格)await\n\n(8个空格)# 限流\n(8个空格)await
    # 应该改为：try:\n(12个空格)# 确保...\n(12个空格)await\n\n(12个空格)# 限流\n(12个空格)await
    
    # 修复模式1: try: 后面跟着正确缩进的注释，但代码没有缩进
    pattern = r'(try:)\n(        )(#[^\n]*\n)(        )(await self\._ensure_credentials\(\))\n(\n)(        )(#[^\n]*\n)(        )(await self\._rate_limit\(\))'
    
    def replace_match(m):
        return f"{m.group(1)}\n{m.group(2)}    {m.group(3)}{m.group(2)}    {m.group(5)}\n{m.group(6)}{m.group(2)}    {m.group(8)}{m.group(2)}    {m.group(10)}"
    
    content = re.sub(pattern, replace_match, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已批量修复文件: {file_path}")

if __name__ == "__main__":
    batch_fix_indentation("backend/app/adapters/efinance_adapter.py")
