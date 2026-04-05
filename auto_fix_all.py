#!/usr/bin/env python3
"""
自动修复 EFinance 中所有 try: 块的缩进错误
"""

import re

def auto_fix_all(file_path: str):
    """自动修复所有缩进错误"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # 检查是否是 try: 行
        if re.match(r'^\s*try:\s*$', line):
            # 获取 try: 的缩进级别
            try_indent = len(line) - len(line.lstrip())
            expected_indent = try_indent + 4  # try: 内部应该再缩进4个空格
            
            # 检查接下来的几行
            j = i + 1
            while j < len(lines) and j < i + 10:  # 检查接下来的10行
                next_line = lines[j]
                
                # 如果遇到下一个非空行且不是注释或代码，退出
                if next_line.strip() == '':
                    fixed_lines.append(next_line)
                    j += 1
                    continue
                
                # 检查是否是 # 确保凭证有效
                if '# 确保凭证有效' in next_line:
                    current_indent = len(next_line) - len(next_line.lstrip())
                    if current_indent < expected_indent:
                        # 需要修复缩进
                        fixed_lines.append(' ' * expected_indent + next_line.lstrip())
                        j += 1
                        
                        # 修复 await self._ensure_credentials()
                        if j < len(lines) and 'await self._ensure_credentials()' in lines[j]:
                            fixed_lines.append(' ' * expected_indent + lines[j].lstrip())
                            j += 1
                        
                        # 跳过空行
                        while j < len(lines) and lines[j].strip() == '':
                            fixed_lines.append(lines[j])
                            j += 1
                        
                        # 修复 # 限流
                        if j < len(lines) and '# 限流' in lines[j]:
                            fixed_lines.append(' ' * expected_indent + lines[j].lstrip())
                            j += 1
                        
                        # 修复 await self._rate_limit()
                        if j < len(lines) and 'await self._rate_limit()' in lines[j]:
                            fixed_lines.append(' ' * expected_indent + lines[j].lstrip())
                            j += 1
                        
                        i = j - 1
                        break
                else:
                    break
        
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ 已自动修复文件: {file_path}")

if __name__ == "__main__":
    auto_fix_all("backend/app/adapters/efinance_adapter.py")
