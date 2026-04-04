#!/usr/bin/env python3
"""
修复 EFinance 适配器中的日志语法错误
这些错误是两行 logger 语句合并在一起导致的
"""

import re

def fix_log_syntax_errors(file_path: str):
    """修复日志语法错误"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复模式1: logger.error(...) logger.error(...)
    # 保留第二个更具体的错误日志
    pattern1 = r'logger\.error\(f"获取unknown失败：\{e\}"\)\s*logger\.error\(f"([^"]+)：\{e\}"\)'
    content = re.sub(pattern1, r'logger.error(f"\1：{e}")', content)
    
    # 修复模式2: logger.error(...)logger.warning(...)
    # 保留 warning 级别的日志
    pattern2 = r'logger\.error\(f"获取unknown失败：\{e\}"\)logger\.warning\(f"([^"]+)：\{e\}"\)'
    content = re.sub(pattern2, r'logger.warning(f"\1：{e}")', content)
    
    # 修复模式3: logger.error(...) logger.warning(...)
    pattern3 = r'logger\.error\(f"获取[^"]*失败：\{e\}"\)\s*logger\.warning\(f"([^"]+)：\{e\}"\)'
    content = re.sub(pattern3, r'logger.warning(f"\1：{e}")', content)
    
    # 修复模式4: logger.error(...) logger.error(...) - 保留第二个
    pattern4 = r'logger\.error\(f"获取[^"]*失败：\{e\}"\)\s*logger\.error\(f"([^"]+)：\{e\}"\)'
    content = re.sub(pattern4, r'logger.error(f"\1：{e}")', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已修复文件: {file_path}")

if __name__ == "__main__":
    fix_log_syntax_errors("backend/app/adapters/efinance_adapter.py")
