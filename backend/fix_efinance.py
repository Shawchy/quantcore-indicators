import re
import sys

# 读取文件
with open('app/adapters/efinance_adapter.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复模式：孤立的 except 块前面缺少 try 和函数定义
# 我们需要找到所有孤立的 except 并添加对应的 try 和函数定义

lines = content.split('\n')
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # 检查是否是孤立的 except 行
    if re.match(r'^\s+except \(ValueError, TypeError\):', line):
        # 检查前一行是否已经是 try
        prev_line = fixed_lines[-1] if fixed_lines else ''
        if not prev_line.strip().startswith('try:'):
            # 需要添加 try 和函数定义
            # 获取缩进
            indent = len(line) - len(line.lstrip())
            func_indent = indent - 4
            
            # 查找更早的行来确定上下文
            context_found = False
            for j in range(len(fixed_lines) - 1, max(0, len(fixed_lines) - 20), -1):
                if 'def ' in fixed_lines[j] or 'for ' in fixed_lines[j] or 'if ' in fixed_lines[j]:
                    context_found = True
                    break
            
            # 添加缺失的 try 块（假设这是在一个循环内）
            if context_found:
                # 插入 try 和 return 语句
                fixed_lines.append(' ' * func_indent + 'def safe_convert(value, default=0.0):')
                fixed_lines.append(' ' * func_indent + '    try:')
                # 下一行应该是 return 语句
                if i + 1 < len(lines) and 'return' in lines[i + 1]:
                    fixed_lines.append(lines[i + 1])  # return 语句
                    i += 1
                fixed_lines.append(line)  # except 行
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)
    
    i += 1

# 写回文件
with open('app/adapters/efinance_adapter.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("修复完成")
