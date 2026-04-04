#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量为 EFinance API 添加智能重试 - 完整版本
"""

import re
from pathlib import Path

file_path = Path('app/adapters/efinance_adapter.py')
content = file_path.read_text(encoding='utf-8')

# 需要处理的 API 列表
TARGET_APIS = [
    'get_stock_info', 'get_stocks_base_info', 'get_deal_detail', 'get_history_bill',
    'get_market_index_kline', 'get_kline', 'get_multi_kline', 'get_weekly_kline',
    'get_monthly_kline', 'get_realtime_quote', 'get_latest_quote', 'get_sector_list',
    'get_chip_data', 'get_daily_billboard', 'get_belong_board', 'get_members',
    'get_today_bill', 'get_stock_bill_detail', 'get_market_moneyflow_dc',
    'get_top10_stock_holder_info', 'get_all_company_performance', 'get_all_report_dates',
    'get_market_realtime_quotes', 'get_financial_performance', 'get_historical_financial_performance',
    'get_fund_base_info', 'get_fund_codes', 'get_fund_invest_position', 'get_fund_quote_history',
    'get_fund_quote_history_multi', 'get_fund_realtime_increase_rate', 'get_fund_period_change',
    'get_fund_types_percentage'
]

modified_count = 0

for api_name in TARGET_APIS:
    # 匹配模式：找到 API 方法中的 try 块
    pattern = rf'(    async def {api_name}\(.*?\)(?:\s*->\s*.*?)?:\s*\n\s*""".*?""")(.*?)(        try:\n            if not EF_AVAILABLE:)'
    
    def add_fetch_sync(match):
        global modified_count
        docstring = match.group(1)
        between = match.group(2)
        
        # 检查是否已有 fetch_sync
        if 'def fetch_sync' in between:
            return match.group(0)
        
        # 找到 try 块之前的内容
        try_start = match.group(3)
        
        # 构建新的代码结构
        new_between = between.replace(try_start, '\n        def fetch_sync():\n' + try_start.replace('        try:\n', ''))
        
        # 在 try 块中添加智能重试
        new_try = '''        try:
            result = await self._retry_executor.execute(
                func=fetch_sync,
                context="''' + api_name + '''"
            )
'''
        
        modified_count += 1
        return docstring + new_between + new_try
    
    # 执行替换（单行模式）
    content = re.sub(pattern, add_fetch_sync, content, flags=re.DOTALL)

# 写回文件
file_path.write_text(content, encoding='utf-8')

print(f"✅ 已为 {modified_count} 个 API 添加智能重试机制")
print(f"📊 文件已更新：{file_path}")
