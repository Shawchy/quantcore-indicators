#!/usr/bin/env python3
"""
修复合并的代码行
"""

import re

def fix_merged_lines(file_path: str):
    """修复合并的代码行"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复模式: logger.error(...)self.record_request_failure()
    pattern = r'logger\.error\(f"获取get_data失败：\{e\}"\)self\.record_request_failure\(\)'
    content = re.sub(pattern, 'self.record_request_failure()', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复文件: {file_path}")

if __name__ == "__main__":
    fix_merged_lines("backend/app/adapters/efinance_adapter.py")
