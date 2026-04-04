#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 EFinance 适配器中缺少凭证注入的 API
"""

import re
from pathlib import Path

# 读取文件
file_path = Path('app/adapters/efinance_adapter.py')
content = file_path.read_text(encoding='utf-8')

# 需要修复的 API 列表（行号）
MISSING_APIS = [
    1088,  # get_kline
    1275,  # get_multi_kline
    1407,  # get_weekly_kline
    1451,  # get_monthly_kline
    1494,  # get_realtime_quote (已有文档但无代码)
    1912,  # get_daily_billboard (已有文档但无代码)
    2209,  # get_stock_bill_detail (已有文档但无代码)
    2366,  # get_market_moneyflow_dc
    2467,  # get_top10_stock_holder_info (已有文档但无代码)
    2766,  # get_market_realtime_quotes (已有文档但无代码)
    2970,  # get_financial_performance
    3175,  # get_fund_base_info
    3287,  # get_fund_codes
    3369,  # get_fund_invest_position
    3462,  # get_fund_quote_history
    3539,  # get_fund_quote_history_multi
    3632,  # get_fund_realtime_increase_rate
    3774,  # get_fund_period_change
    3874,  # get_fund_types_percentage
]

# 凭证注入代码模板
INJECT_CODE = """        # 确保凭证有效（TLS 指纹伪装）
        await self._ensure_credentials()
        
        # 限流
        await self._rate_limit()
        
"""

fixed_count = 0

# 从后向前处理，避免行号偏移
for line_num in reversed(MISSING_APIS):
    lines = content.split('\n')
    
    # 找到目标行
    if line_num <= len(lines):
        target_line = lines[line_num - 1]
        
        # 检查是否是 async def get_ 开头
        if 'async def get_' in target_line:
            # 找到 docstring 结束位置（"""）
            docstring_end = -1
            quote_count = 0
            for i in range(line_num - 1, min(line_num + 30, len(lines))):
                line = lines[i]
                quote_count += line.count('"""')
                if quote_count >= 2:
                    docstring_end = i + 1
                    break
            
            if docstring_end > 0:
                # 检查是否已有 _ensure_credentials
                context = '\n'.join(lines[line_num-1:docstring_end+5])
                if '_ensure_credentials' not in context:
                    # 插入凭证注入代码
                    lines.insert(docstring_end, INJECT_CODE.rstrip())
                    content = '\n'.join(lines)
                    fixed_count += 1
                    print(f"✅ 已修复行 {line_num}: {target_line.strip()}")
                else:
                    print(f"⏭️  跳过行 {line_num}: 已有凭证注入")
            else:
                print(f"❌ 未找到 docstring 结束：行 {line_num}")

# 写回文件
file_path.write_text(content, encoding='utf-8')

print(f"\n修复完成！")
print(f"✅ 已修复：{fixed_count} 个 API")
print(f"📊 总计检查：{len(MISSING_APIS)} 个 API")
