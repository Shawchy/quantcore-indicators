#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 EFinance 适配器中智能重试的代码结构问题
"""

import re
from pathlib import Path

file_path = Path('app/adapters/efinance_adapter.py')
content = file_path.read_text(encoding='utf-8')

# 修复模式 1: 修复 try 块缩进问题
# 查找：try:\n        # 确保凭证有效
# 替换为：# 确保凭证有效...然后 def fetch_sync

fix_count = 0

# 修复 get_chip_data
pattern1 = r'(    async def get_chip_data\(.*?\) -> List\[ChipData\]:\s*"""获取筹码数据""")\s*try:\s*(# 确保凭证有效.*?await self._rate_limit\(\)\s*)'
replacement1 = r'\1\n        \2\n        def fetch_sync():'
content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
fix_count += 1

# 修复 get_all_company_performance
pattern2 = r'(    async def get_all_company_performance.*?List\[CompanyPerformance\]:.*?""")\s*try:\s*(# 确保凭证有效.*?await self._rate_limit\(\)\s*)'
replacement2 = r'\1\n        \2\n        def fetch_sync():'
content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
fix_count += 1

# 写回文件
file_path.write_text(content, encoding='utf-8')

print(f"✅ 已修复 {fix_count} 个 API 的代码结构")
print(f"📊 文件已更新：{file_path}")
