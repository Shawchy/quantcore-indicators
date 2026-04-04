#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为 EFinance 适配器的所有 except 块批量补充 logger.error
"""

import re
from pathlib import Path

file_path = Path('app/adapters/efinance_adapter.py')
content = file_path.read_text(encoding='utf-8')

# 匹配 except 块并添加 logger.error
# 模式：except Exception as e: 后面没有 logger.error
pattern = r'(    except Exception as e:)\s*(?!logger\.error)'

def add_logger_error(match):
    except_line = match.group(1)
    # 获取上下文中的 API 名称
    before_text = content[:match.start()]
    # 查找最近的 API 方法名
    method_match = re.search(r'async def (get_\w+)', before_text, re.DOTALL)
    context_name = method_match.group(1) if method_match else "unknown"
    
    # 添加 logger.error
    return f'{except_line}\n            logger.error(f"获取{context_name}失败：{{e}}")'

# 执行替换
new_content = re.sub(pattern, add_logger_error, content, flags=re.DOTALL)

# 统计修改次数
modified_count = len(re.findall(pattern, content))

# 写回文件
file_path.write_text(new_content, encoding='utf-8')

print(f"✅ 已为 {modified_count} 个 except 块添加 logger.error")
print(f"📊 文件已更新：{file_path}")
