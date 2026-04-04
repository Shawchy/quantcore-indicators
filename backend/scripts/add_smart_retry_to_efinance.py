#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为 EFinance 适配器的所有 API 批量添加智能重试机制
"""

import re
from pathlib import Path

# 读取文件
file_path = Path('app/adapters/efinance_adapter.py')
content = file_path.read_text(encoding='utf-8')

# 智能重试代码模板
RETRY_TEMPLATE = '''        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="{context}"
            )
'''

# 匹配所有 try 块，替换为带智能重试的 try 块
# 模式：匹配 "try:" 后面跟着数据获取逻辑的部分
pattern = r'(        def fetch_sync\(\):.*?)(        try:\n            if not EF_AVAILABLE:)'

count = 0

def replace_try(match):
    global count
    fetch_func = match.group(1)
    context = "unknown"
    
    # 从上下文中提取方法名
    before_text = content[:match.start()]
    method_match = re.search(r'async def (get_\w+).*?def fetch_sync', before_text, re.DOTALL)
    if method_match:
        context = method_match.group(1)
    
    # 构建替换文本
    replacement = f'{fetch_func}        try:\n            result = await self._retry_executor.execute(\n                func=fetch_sync,\n                context="{context}"\n            )\n            if not EF_AVAILABLE:'
    
    count += 1
    return replacement

# 执行替换
new_content = re.sub(pattern, replace_try, content, flags=re.DOTALL)

# 写回文件
file_path.write_text(new_content, encoding='utf-8')

print(f"✅ 已为 {count} 个 API 添加智能重试机制")
print(f"📊 文件已更新：{file_path}")
