#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为 EFinance 适配器的所有 API 方法批量添加 TLS 指纹伪装和凭证注入
"""

import re
from pathlib import Path

# 读取文件
file_path = Path('app/adapters/efinance_adapter.py')
content = file_path.read_text(encoding='utf-8')

# 需要跳过的 API 方法（已有凭证注入）
SKIP_METHODS = ['get_stock_list']

# 匹配所有 async def get_xxx 方法
pattern = r'(    async def (get_\w+)\([^)]*\)(?:\s*->\s*[^:]+)?:\s*\n\s*"""([^"]*?)"""(\s*\n\s*try:|\s*\n\s*if\s+not\s+EF_AVAILABLE:|\s*\n\s*#|\s*\n\s*cache_key|\s*\n\s*await))'

matches = list(re.finditer(pattern, content, re.MULTILINE))

print(f"找到 {len(matches)} 个 API 方法")

modified_count = 0
skip_count = 0

# 从后向前处理，避免行号偏移
for match in reversed(matches):
    method_name = match.group(2)
    
    # 跳过已有凭证注入的方法
    if method_name in SKIP_METHODS:
        print(f"⏭️  跳过 {method_name} (已有凭证注入)")
        skip_count += 1
        continue
    
    # 检查方法是否已有 _ensure_credentials
    method_end = content.find('\n    async def ', match.end())
    if method_end == -1:
        method_end = len(content)
    
    method_content = content[match.start():method_end]
    
    if '_ensure_credentials' in method_content:
        print(f"⏭️  跳过 {method_name} (已有凭证注入)")
        skip_count += 1
        continue
    
    # 找到 docstring 结束位置
    docstring_end = match.end()
    
    # 查找 docstring 后的第一个非空行
    after_docstring = content[docstring_end:docstring_end+200]
    
    # 插入凭证注入和限流代码
    insert_code = '''
        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
'''
    
    # 在 docstring 后插入
    new_content = content[:docstring_end] + insert_code + content[docstring_end:]
    
    # 写回文件
    file_path.write_text(new_content, encoding='utf-8')
    content = new_content  # 更新内容供下一次迭代使用
    
    print(f"✅ 已为 {method_name} 添加 TLS 指纹伪装")
    modified_count += 1

print(f"\n部署完成！")
print(f"✅ 已修改：{modified_count} 个 API")
print(f"⏭️  已跳过：{skip_count} 个 API")
print(f"📊 总计：{modified_count + skip_count} 个 API")
