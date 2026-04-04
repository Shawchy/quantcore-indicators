#!/usr/bin/env python3
"""
修复 EFinance 适配器中的日志语法错误 - 版本 2
处理更多变体
"""

import re

def fix_log_syntax_errors_v2(file_path: str):
    """修复日志语法错误"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复模式: logger.error(f"获取get_data失败：{e}") logger.error(f"...")
    # 保留第二个更具体的错误日志
    pattern1 = r'logger\.error\(f"获取get_data失败：\{e\}"\)\s*logger\.error\(f"([^"]+)\{e\}[^"]*"\)'
    content = re.sub(pattern1, r'logger.error(f"\1{e}")', content)
    
    # 修复模式: logger.error(f"获取get_data失败：{e}")logger.warning(f"...")
    pattern2 = r'logger\.error\(f"获取get_data失败：\{e\}"\)logger\.warning\(f"([^"]+)\{e\}[^"]*"\)'
    content = re.sub(pattern2, r'logger.warning(f"\1{e}")', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复文件: {file_path}")

if __name__ == "__main__":
    fix_log_syntax_errors_v2("backend/app/adapters/efinance_adapter.py")
