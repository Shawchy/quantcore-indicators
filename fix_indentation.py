#!/usr/bin/env python3
"""
修复 EFinance 适配器中的缩进错误
主要修复 try: 后面代码块没有正确缩进的问题
"""

import re

def fix_indentation_issues(file_path: str):
    """修复缩进错误"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # 检查是否是 try: 行（在行尾或单独一行）
        if re.match(r'^\s*try:\s*$', line) or re.match(r'"""\s*\ntry:\s*$', line):
            # 检查下一行是否没有正确缩进
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # 如果下一行是 # 确保凭证有效 或 # 限流，但没有正确缩进
                if re.match(r'^\s*# 确保凭证有效', next_line) or re.match(r'^\s*# 限流', next_line):
                    # 检查缩进是否正确（应该是 12 个空格，即 3 级缩进）
                    if not next_line.startswith('            '):
                        # 修复缩进
                        fixed_lines.append('            # 确保凭证有效（TLS 指纹伪装）\n')
                        i += 2
                        # 修复 await self._ensure_credentials()
                        if i < len(lines):
                            fixed_lines.append('            await self._ensure_credentials()\n')
                            i += 1
                        # 修复空行
                        if i < len(lines) and lines[i].strip() == '':
                            fixed_lines.append('\n')
                            i += 1
                        # 修复 # 限流
                        if i < len(lines) and '# 限流' in lines[i]:
                            fixed_lines.append('            # 限流\n')
                            i += 1
                        # 修复 await self._rate_limit()
                        if i < len(lines) and '_rate_limit()' in lines[i]:
                            fixed_lines.append('            await self._rate_limit()\n')
                            i += 1
                        continue
        
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ 已修复文件: {file_path}")

if __name__ == "__main__":
    fix_indentation_issues("backend/app/adapters/efinance_adapter.py")
