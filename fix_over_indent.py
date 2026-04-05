#!/usr/bin/env python3
"""
修复过度缩进的问题
模式：
  try:
      # 注释
          await self.xxx()  （错误：缩进过多）
"""

def fix_over_indent(file_path: str):
    """修复过度缩进"""
    
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
            
            # 查找注释行
            if i < len(lines) and '#' in lines[i] and '确保凭证有效' in lines[i]:
                comment_line = lines[i]
                comment_indent = len(comment_line) - len(comment_line.lstrip())
                fixed_lines.append(comment_line)
                i += 1
                
                # 查找 await self._ensure_credentials()
                if i < len(lines) and 'await self._ensure_credentials()' in lines[i]:
                    code_line = lines[i]
                    code_indent = len(code_line) - len(code_line.lstrip())
                    
                    # 如果代码缩进大于注释缩进 + 4，需要修复
                    if code_indent > comment_indent + 4:
                        fixed_lines.append(' ' * (comment_indent + 4) + code_line.lstrip())
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
                        limit_line = lines[i]
                        limit_indent = len(limit_line) - len(limit_line.lstrip())
                        
                        if limit_indent > comment_indent + 4:
                            fixed_lines.append(' ' * (comment_indent + 4) + limit_line.lstrip())
                        else:
                            fixed_lines.append(limit_line)
                        i += 1
                        
                        # 查找 await self._rate_limit()
                        if i < len(lines) and 'await self._rate_limit()' in lines[i]:
                            rate_line = lines[i]
                            rate_indent = len(rate_line) - len(rate_line.lstrip())
                            
                            if rate_indent > comment_indent + 4:
                                fixed_lines.append(' ' * (comment_indent + 4) + rate_line.lstrip())
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
    
    print(f"✅ 已修复 {fixed_count} 处过度缩进错误")

if __name__ == "__main__":
    fix_over_indent("backend/app/adapters/efinance_adapter.py")
