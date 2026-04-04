#!/usr/bin/env python3
"""
TLS 指纹伪装批量部署脚本
为所有剩余的 AkShare API 添加 await self._ensure_credentials()
"""

import re

def add_tls_fingerprint_to_file(filepath):
    """为文件中的所有 API 添加 TLS 指纹伪装"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义需要修改的 API 模式
    patterns = [
        # 模式 1: 简单的 await self._rate_limit()
        (r'(async def get_\w+\([^)]*\) -> [^:]+:\n\s+"""[^"]+""")\n(\s+)await self\._rate_limit\(\)',
         r'\1\n\2# 确保凭证有效（TLS 指纹伪装）\n\2await self._ensure_credentials()\n\2\n\2# 限流\n\2await self._rate_limit()'),
    ]
    
    # 应用所有模式
    modified = False
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            modified = True
            print(f"✓ 应用模式：{pattern[:50]}... (修改 {count} 处)")
    
    # 保存修改后的文件
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✓ 文件已更新：{filepath}")
    else:
        print(f"\n✗ 没有需要修改的内容")
    
    return modified

if __name__ == '__main__':
    filepath = 'app/adapters/akshare_adapter.py'
    add_tls_fingerprint_to_file(filepath)
