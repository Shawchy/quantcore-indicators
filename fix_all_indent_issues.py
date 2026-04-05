#!/usr/bin/env python3
"""
修复所有缩进问题
包括：
1. 缩进不足（await 没有正确缩进）
2. 缩进过度（await 缩进过多）
"""

def fix_all_indent_issues(file_path: str):
    """修复所有缩进问题"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
    
    fixed_lines = []
    i = 0
    fixed_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 查找 try: 行
        if line.strip() == 'try:':
            fixed_lines.append(line)
            i += 1
            
            # 获取 try: 的缩进
            try_indent = len(line) - len(line.lstrip())
            expected_indent = try_indent + 4
            
            # 查找接下来的4行（注释、代码、空行、注释、代码）
            pattern_lines = []
            for j in range(5):
                if i + j < len(lines):
                    pattern_lines.append(lines[i + j])
            
            # 检查是否符合模式
            if len(pattern_lines) >= 4:
                # 第1行：# 确保凭证有效
                if '# 确保凭证有效' in pattern_lines[0]:
                    comment1_indent = len(pattern_lines[0]) - len(pattern_lines[0].lstrip())
                    
                    # 第2行：await self._ensure_credentials()
                    if 'await self._ensure_credentials()' in pattern_lines[1]:
                        code1_indent = len(pattern_lines[1]) - len(pattern_lines[1].lstrip())
                        
                        # 修复第2行
                        if code1_indent != expected_indent:
                            lines[i + 1] = ' ' * expected_indent + pattern_lines[1].lstrip()
                            fixed_count += 1
                    
                    # 第3行：空行或 # 限流
                    idx = 2
                    if pattern_lines[2].strip() == '':
                        idx = 3
                    
                    if idx < len(pattern_lines) and '# 限流' in pattern_lines[idx]:
                        comment2_indent = len(pattern_lines[idx]) - len(pattern_lines[idx].lstrip())
                        
                        # 修复注释行
                        if comment2_indent != expected_indent:
                            lines[i + idx] = ' ' * expected_indent + pattern_lines[idx].lstrip()
                        
                        # 下一行：await self._rate_limit()
                        if i + idx + 1 < len(lines) and 'await self._rate_limit()' in lines[i + idx + 1]:
                            code2_indent = len(lines[i + idx + 1]) - len(lines[i + idx + 1].lstrip())
                            
                            # 修复
                            if code2_indent != expected_indent:
                                lines[i + idx + 1] = ' ' * expected_indent + lines[i + idx + 1].lstrip()
                                fixed_count += 1
            
            # 添加已处理的行
            for j in range(i, min(i + 10, len(lines))):
                fixed_lines.append(lines[j])
            i += 10
            continue
        
        fixed_lines.append(line)
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"✅ 已修复 {fixed_count} 处缩进问题")

if __name__ == "__main__":
    fix_all_indent_issues("backend/app/adapters/efinance_adapter.py")
