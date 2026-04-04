#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为 EFinance 适配器的所有 API 批量添加 TLS 指纹伪装文档说明
"""

import re
from pathlib import Path

file_path = Path('app/adapters/efinance_adapter.py')
content = file_path.read_text(encoding='utf-8')

# 需要处理的 API 列表
TARGET_APIS = [
    'get_stock_list', 'get_stock_info', 'get_stocks_base_info', 'get_deal_detail',
    'get_history_bill', 'get_market_index_kline', 'get_kline', 'get_multi_kline',
    'get_weekly_kline', 'get_monthly_kline', 'get_realtime_quote', 'get_latest_quote',
    'get_sector_list', 'get_chip_data', 'get_daily_billboard', 'get_belong_board',
    'get_members', 'get_today_bill', 'get_stock_bill_detail', 'get_market_moneyflow_dc',
    'get_top10_stock_holder_info', 'get_all_company_performance', 'get_all_report_dates',
    'get_market_realtime_quotes', 'get_financial_performance', 'get_historical_financial_performance',
    'get_fund_base_info', 'get_fund_codes', 'get_fund_invest_position', 'get_fund_quote_history',
    'get_fund_quote_history_multi', 'get_fund_realtime_increase_rate', 'get_fund_period_change',
    'get_fund_types_percentage', 'get_board_industry_name_em', 'get_board_industry_cons_em'
]

modified_count = 0

for api_name in TARGET_APIS:
    # 匹配模式：找到 API 方法的 docstring
    # 模式 1: """获取 xxx""" -> """获取 xxx（带 TLS 指纹伪装 + 凭证注入）"""
    pattern1 = rf'(    async def {api_name}\(.*?\)(?:\s*->\s*.*?)?:\s*\n\s*""")([^""]*?)(""")'
    
    def add_tls_doc(match):
        global modified_count
        prefix = match.group(1)
        doc_content = match.group(2)
        suffix = match.group(3)
        
        # 检查是否已有 TLS 说明
        if 'TLS' in doc_content or '凭证' in doc_content:
            return match.group(0)
        
        # 添加 TLS 说明
        new_doc = doc_content
        if not new_doc.strip().endswith('）'):
            if new_doc.strip():
                new_doc = new_doc.rstrip() + '（带 TLS 指纹伪装 + 凭证注入）\n'
            else:
                new_doc = '（带 TLS 指纹伪装 + 凭证注入）\n'
        
        modified_count += 1
        return f'{prefix}{new_doc}{suffix}'
    
    # 执行替换
    content = re.sub(pattern1, add_tls_doc, content, flags=re.DOTALL)

# 写回文件
file_path.write_text(content, encoding='utf-8')

print(f"✅ 已为 {modified_count} 个 API 添加 TLS 指纹伪装文档说明")
print(f"📊 文件已更新：{file_path}")
