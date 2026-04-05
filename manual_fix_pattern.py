#!/usr/bin/env python3
"""
手动修复特定模式的缩进错误
"""

def manual_fix_pattern(file_path: str):
    """手动修复特定模式"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    fixed_count = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 查找 try: 行
        if line.strip() == 'try:':
            fixed_lines.append(line)
            i += 1
            
            # 查找 # 确保凭证有效（TLS 指纹伪装）
            if i < len(lines) and '# 确保凭证有效' in lines[i]:
                comment_line = lines[i]
                # 获取当前缩进
                indent = len(comment_line) - len(comment_line.lstrip())
                fixed_lines.append(comment_line)
                i += 1
                
                # 查找 await self._ensure_credentials()
                if i < len(lines) and 'await self._ensure_credentials()' in lines[i]:
                    code_line = lines[i]
                    code_indent = len(code_line) - len(code_line.lstrip())
                    
                    # 如果代码缩进小于注释缩进 + 4，需要修复
                    if code_indent < indent + 4:
                        fixed_lines.append(' ' * (indent + 4) + code_line.lstrip())
                        fixed_count += 1
                    else:
                        fixed_lines.append(code_line)
                    i += 1
                    
                    # 跳过空行
                    while i < len(lines) and lines[i].strip() == '':
                        fixed_lines.append(lines[i])
                        i += 1
                    
                    # 查找 # 限流
                    if i < len(lines) and '# 限流' in lines[i]:
                        limit_comment = lines[i]
                        limit_indent = len(limit_comment) - len(limit_comment.lstrip())
                        
                        if limit_indent < indent + 4:
                            fixed_lines.append(' ' * (indent + 4) + limit_comment.lstrip())
                        else:
                            fixed_lines.append(limit_comment)
                        i += 1
                        
                        # 查找 await self._rate_limit()
                        if i < len(lines) and 'await self._rate_limit()' in lines[i]:
                            rate_line = lines[i]
                            rate_indent = len(rate_line) - len(rate_line.lstrip())
                            
                            if rate_indent < indent + 4:
                                fixed_lines.append(' ' * (indent + 4) + rate_line.lstrip())
                                fixed_count += 1
                            else:
                                fixed_lines.append(rate_line)
                            i += 1
                            continue
            
            continue
        
        fixed_lines.append(line)
        i += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ 已修复 {fixed_count} 处缩进错误")

if __name__ == "__main__":
    manual_fix_pattern("backend/app/adapters/efinance_adapter.py")
