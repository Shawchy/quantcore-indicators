#!/usr/bin/env python3
"""
全面修复 EFinance 适配器中的各种问题
"""

import re

def comprehensive_fix(file_path: str):
    """全面修复"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复 logger.error(...)logger.error(...) - 保留第二个
    content = re.sub(
        r'logger\.error\(f"获取get_data失败：\{e\}"\)\s*logger\.error\(f"([^"]+)\{e\}[^"]*"\)',
        r'logger.error(f"\1{e}")',
        content
    )
    
    # 2. 修复 logger.error(...)logger.warning(...) - 保留 warning
    content = re.sub(
        r'logger\.error\(f"获取get_data失败：\{e\}"\)\s*logger\.warning\(f"([^"]+)\{e\}[^"]*"\)',
        r'logger.warning(f"\1{e}")',
        content
    )
    
    # 3. 修复 logger.error(...)self.record_request_failure()
    content = re.sub(
        r'logger\.error\(f"获取get_data失败：\{e\}"\)\s*self\.record_request_failure\(\)',
        r'self.record_request_failure()',
        content
    )
    
    # 4. 修复 logger.error(...)if ...
    content = re.sub(
        r'logger\.error\(f"获取get_data失败：\{e\}"\)\s*if ',
        r'if ',
        content
    )
    
    # 5. 删除多余的 return []
    content = re.sub(
        r'result = await self\._retry_executor\.execute\(\s*func=fetch_sync,\s*context="[^"]+"\s*\)\s*\n\s*return \[\]',
        r'result = await self._retry_executor.execute(\n                func=fetch_sync,\n                context="get_stock_info"\n            )',
        content
    )
    
    # 6. 修复 try: 后面的缩进问题（简单版本）
    # 将 try:\n# 确保... 替换为 try:\n            # 确保...
    content = re.sub(
        r'(try:)\n\s*# 确保凭证有效',
        r'\1\n            # 确保凭证有效',
        content
    )
    
    content = re.sub(
        r'(try:)\n\s*await self\._ensure_credentials\(\)',
        r'\1\n            await self._ensure_credentials()',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复文件: {file_path}")

if __name__ == "__main__":
    comprehensive_fix("backend/app/adapters/efinance_adapter.py")
