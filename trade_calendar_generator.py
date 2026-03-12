"""
交易日历生成工具
当 Tushare 积分不足时，使用本地计算方式生成交易日历

方法：
1. 排除周末（周六、周日）
2. 排除中国法定节假日
3. 考虑调休情况
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json

# 中国法定节假日（2024 年）
# 来源：国务院办公厅关于 2024 年部分节假日安排的通知
CHINA_HOLIDAYS_2024 = {
    # 元旦：1 月 1 日放假，与周末连休
    '2024-01-01': '元旦',
    
    # 春节：2 月 10 日至 17 日放假调休，共 8 天
    '2024-02-10': '春节',
    '2024-02-11': '春节',
    '2024-02-12': '春节',
    '2024-02-13': '春节',
    '2024-02-14': '春节',
    '2024-02-15': '春节',
    '2024-02-16': '春节',
    '2024-02-17': '春节',
    
    # 清明节：4 月 4 日至 6 日放假调休，共 3 天
    '2024-04-04': '清明节',
    '2024-04-05': '清明节',
    '2024-04-06': '清明节',
    
    # 劳动节：5 月 1 日至 5 日放假调休，共 5 天
    '2024-05-01': '劳动节',
    '2024-05-02': '劳动节',
    '2024-05-03': '劳动节',
    '2024-05-04': '劳动节',
    '2024-05-05': '劳动节',
    
    # 端午节：6 月 10 日放假，与周末连休
    '2024-06-10': '端午节',
    
    # 中秋节：9 月 15 日至 17 日放假调休，共 3 天
    '2024-09-15': '中秋节',
    '2024-09-16': '中秋节',
    '2024-09-17': '中秋节',
    
    # 国庆节：10 月 1 日至 7 日放假调休，共 7 天
    '2024-10-01': '国庆节',
    '2024-10-02': '国庆节',
    '2024-10-03': '国庆节',
    '2024-10-04': '国庆节',
    '2024-10-05': '国庆节',
    '2024-10-06': '国庆节',
    '2024-10-07': '国庆节',
}

# 调休工作日（需要在周末上班）
CHINA_WORKDAY_ADJUSTMENTS_2024 = {
    # 2 月 4 日（周日）上班
    '2024-02-04': '春节调休',
    # 2 月 18 日（周日）上班
    '2024-02-18': '春节调休',
    # 4 月 7 日（周日）上班
    '2024-04-07': '清明调休',
    # 4 月 28 日（周日）上班
    '2024-04-28': '劳动节调休',
    # 5 月 11 日（周六）上班
    '2024-05-11': '劳动节调休',
    # 9 月 14 日（周六）上班
    '2024-09-14': '中秋调休',
    # 9 月 29 日（周日）上班
    '2024-09-29': '国庆调休',
    # 10 月 12 日（周六）上班
    '2024-10-12': '国庆调休',
}


def generate_trading_calendar(year: int = 2024, exchange: str = 'SSE'):
    """
    生成交易日历
    
    Args:
        year: 年份
        exchange: 交易所代码（SSE/SZSE 等）
    
    Returns:
        DataFrame: 交易日历数据
    """
    print(f"\n生成 {year} 年交易日历...")
    
    # 选择节假日数据
    if year == 2024:
        holidays = CHINA_HOLIDAYS_2024
        workday_adjustments = CHINA_WORKDAY_ADJUSTMENTS_2024
    else:
        # TODO: 添加其他年份的节假日数据
        print(f"⚠️  暂未配置 {year} 年的节假日数据，使用默认规则")
        holidays = {}
        workday_adjustments = {}
    
    # 生成全年日期
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31) if year != datetime.now().year else datetime.now()
    
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    # 生成交易日历
    calendar_data = []
    pre_trade_date = None
    
    for date in dates:
        date_str = date.strftime('%Y-%m-%d')
        cal_date = date.strftime('%Y%m%d')
        weekday = date.weekday()  # 0=周一，6=周日
        
        # 判断是否交易
        is_open = 1  # 默认交易
        
        # 检查是否是节假日
        if date_str in holidays:
            is_open = 0
            reason = holidays[date_str]
        # 检查是否是周末
        elif weekday >= 5:  # 周六或周日
            is_open = 0
            reason = '周末'
        else:
            reason = ''
        
        # 检查调休（周末需要上班/交易）
        if date_str in workday_adjustments:
            is_open = 1
            reason = workday_adjustments[date_str]
        
        # 更新上一个交易日
        if is_open == 1:
            current_pre_trade_date = pre_trade_date
            pre_trade_date = cal_date
        else:
            current_pre_trade_date = pre_trade_date
        
        # 添加到结果
        calendar_data.append({
            'exchange': exchange,
            'cal_date': cal_date,
            'is_open': is_open,
            'pretrade_date': current_pre_trade_date,
            'reason': reason
        })
    
    # 创建 DataFrame
    df = pd.DataFrame(calendar_data)
    
    # 统计
    total_days = len(df)
    open_days = len(df[df['is_open'] == 1])
    closed_days = len(df[df['is_open'] == 0])
    
    print(f"\n✅ 交易日历生成完成!")
    print(f"   总天数：{total_days} 天")
    print(f"   交易日：{open_days} 天")
    print(f"   休市日：{closed_days} 天")
    print(f"   交易日占比：{open_days/total_days*100:.1f}%")
    
    return df


def save_trading_calendar(df: pd.DataFrame, year: int = 2024):
    """保存交易日历到文件"""
    
    # 保存 CSV
    csv_file = Path(__file__).parent / f"trade_calendar_{year}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 CSV 已保存：{csv_file}")
    
    # 保存 JSON
    json_file = Path(__file__).parent / f"trade_calendar_{year}.json"
    df.to_json(json_file, orient='records', force_ascii=False, indent=2)
    print(f"💾 JSON 已保存：{json_file}")
    
    # 保存到后端数据目录
    backend_json = Path(__file__).parent / "backend" / "data" / f"trading_days_cache.json"
    df.to_json(backend_json, orient='records', force_ascii=False, indent=2)
    print(f"💾 后端缓存已保存：{backend_json}")


def load_trading_calendar(year: int = 2024):
    """加载交易日历"""
    json_file = Path(__file__).parent / f"trade_calendar_{year}.json"
    
    if json_file.exists():
        df = pd.read_json(json_file, orient='records')
        print(f"\n📖 已加载 {year} 年交易日历：{len(df)} 天")
        return df
    else:
        print(f"\n⚠️  {year} 年交易日历文件不存在")
        return None


def get_trading_days(start_date: str, end_date: str):
    """
    获取指定日期范围内的交易日
    
    Args:
        start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
        end_date: 结束日期
    
    Returns:
        list: 交易日列表
    """
    # 解析日期
    if len(start_date) == 8:
        start_date_str = start_date  # 保持 YYYYMMDD 格式
    elif '-' in start_date:
        start_date_str = start_date.replace('-', '')
    else:
        start_date_str = str(start_date)
    
    if len(end_date) == 8:
        end_date_str = end_date
    elif '-' in end_date:
        end_date_str = end_date.replace('-', '')
    else:
        end_date_str = str(end_date)
    
    # 确定年份
    year = int(start_date_str[:4])
    
    # 加载或生成日历
    df = load_trading_calendar(year)
    if df is None:
        df = generate_trading_calendar(year)
        save_trading_calendar(df, year)
    
    # 筛选日期范围（转换为整数比较）
    start_int = int(start_date_str)
    end_int = int(end_date_str)
    
    mask = (df['cal_date'] >= start_int) & \
           (df['cal_date'] <= end_int) & \
           (df['is_open'] == 1)
    
    trading_days = df[mask]['cal_date'].tolist()
    
    print(f"\n📅 {start_date_str} 到 {end_date_str} 的交易日：{len(trading_days)} 天")
    print(f"   日期：{', '.join([str(day) for day in trading_days])}")
    
    return trading_days


# 主函数
if __name__ == "__main__":
    print("=" * 70)
    print("交易日历生成工具")
    print("=" * 70)
    
    # 生成 2024 年交易日历
    df = generate_trading_calendar(2024, 'SSE')
    
    # 显示样例
    print(f"\n📊 数据样例:")
    print(df.head(20).to_string())
    
    # 保存文件
    save_trading_calendar(df, 2024)
    
    # 测试获取交易日
    print("\n" + "=" * 70)
    print("测试：获取 2024 年 3 月交易日")
    print("=" * 70)
    trading_days = get_trading_days('20240301', '20240331')
    
    print("\n" + "=" * 70)
    print("✅ 完成")
    print("=" * 70)
