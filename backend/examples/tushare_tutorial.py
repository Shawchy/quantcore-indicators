"""
Tushare 使用教程
================

本教程将帮助您学习如何安装、配置和使用 Tushare 数据接口。

目录:
1. 安装 Tushare
2. 配置 Token
3. 基本使用示例
4. 常用接口示例
5. HTTP 协议方式
"""

# ============================================================================
# 1. 安装 Tushare
# ============================================================================

"""
方式 1: 使用 pip 安装 (推荐)
----------------------------
# 标准安装
pip install tushare

# 使用国内镜像源 (如果网络超时)
pip install tushare -i https://pypi.tuna.tsinghua.edu.cn/simple

方式 2: 从 PyPI 下载安装
-----------------------
访问 https://pypi.python.org/pypi/tushare/
下载后执行：python setup.py install

方式 3: 从 GitHub 安装
---------------------
git clone https://github.com/waditu/tushare.git
cd tushare
python setup.py install

升级 Tushare:
-------------
pip install tushare --upgrade

查看版本:
--------
import tushare
print(tushare.__version__)
"""

# ============================================================================
# 2. 配置 Token
# ============================================================================

import tushare as ts
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 方法 1: 使用 set_token (推荐)
# 只需要在第一次调用，token 会保存在本地
ts.set_token(os.getenv('TUSHARE_TOKEN', ''))

# 方法 2: 直接在 pro_api 中传入 token
# pro = ts.pro_api('your_token_here')

# 初始化 pro 接口
pro = ts.pro_api()

print("✅ Tushare 初始化成功!")
print(f"当前版本：{ts.__version__}")
print()

# ============================================================================
# 3. 基本使用示例
# ============================================================================

print("=" * 60)
print("基本使用示例")
print("=" * 60)
print()

# 示例 1: 获取交易日历
print("📅 示例 1: 获取交易日历")
print("-" * 60)
try:
    df = pro.trade_cal(
        exchange='',  # 交易所 SSE 上交所 SZSE 深交所
        start_date='20240101',
        end_date='20240131',
        fields='exchange,cal_date,is_open,pretrade_date',
        is_open='0'  # 0 表示休市，1 表示开市
    )
    print(f"获取到 {len(df)} 条交易日历数据")
    print(df.head())
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# 示例 2: 获取股票基本信息
print("📊 示例 2: 获取股票列表")
print("-" * 60)
try:
    df = pro.stock_basic(
        exchange='',  # 交易所 SSE SZSE BSE
        list_status='L',  # L 上市 D 退市 P 暂停
        fields='ts_code,symbol,name,area,industry,list_date'
    )
    print(f"获取到 {len(df)} 只股票信息")
    print(df.head())
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# 示例 3: 获取日线行情数据
print("📈 示例 3: 获取日线行情数据")
print("-" * 60)
try:
    df = pro.daily(
        ts_code='000001.SZ',  # 股票代码
        start_date='20240101',
        end_date='20240131',
        fields='ts_code,trade_date,open,high,low,close,vol,amount'
    )
    print(f"获取到 {len(df)} 条日线数据")
    print(df.head())
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# ============================================================================
# 4. 常用接口示例
# ============================================================================

print("=" * 60)
print("常用接口示例")
print("=" * 60)
print()

# 4.1 获取实时行情
print("⚡ 4.1 获取实时行情")
print("-" * 60)
try:
    df = pro.realtime(
        ts_code='000001.SZ',
        fields='ts_code,name,price,change,pct_chg,vol,amount'
    )
    print(df)
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# 4.2 获取复权因子
print("🔄 4.2 获取复权因子")
print("-" * 60)
try:
    df = pro.adj_factor(
        ts_code='000001.SZ',
        start_date='20240101',
        end_date='20240131'
    )
    print(f"获取到 {len(df)} 条复权因子数据")
    print(df.head())
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# 4.3 获取股票技术面指标
print("📐 4.3 获取技术指标")
print("-" * 60)
try:
    # MACD 指标
    df = pro.macd(
        ts_code='000001.SZ',
        start_date='20240101',
        end_date='20240131'
    )
    print("MACD 指标:")
    print(df.head())
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# 4.4 获取资金流向
print("💰 4.4 获取资金流向")
print("-" * 60)
try:
    df = pro.moneyflow(
        ts_code='000001.SZ',
        start_date='20240101',
        end_date='20240131'
    )
    print(f"获取到 {len(df)} 条资金流向数据")
    print(df.head())
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# 4.5 获取板块信息
print("🏢 4.5 获取板块信息")
print("-" * 60)
try:
    # 行业板块
    df = pro.index_classify(
        level='L1',  # L1 一级分类 L2 二级分类
        src='SW2021'  # 申万行业分类
    )
    print(f"获取到 {len(df)} 个行业板块")
    print(df.head())
    print()
except Exception as e:
    print(f"❌ 获取失败：{e}")
    print()

# ============================================================================
# 5. HTTP 协议方式
# ============================================================================

print("=" * 60)
print("HTTP 协议方式 (使用 curl)")
print("=" * 60)
print()

print("""
# 使用 curl 命令行工具示例:
curl -X POST -d '{
    "api_name": "trade_cal",
    "token": "your_token_here",
    "params": {
        "exchange":"",
        "start_date":"20240101",
        "end_date":"20240131",
        "is_open":"0"
    },
    "fields": "exchange,cal_date,is_open,pretrade_date"
}' http://api.tushare.pro

# 返回结果:
{
    "code": 0,
    "msg": null,
    "data": {
        "fields": ["exchange", "cal_date", "is_open", "pretrade_date"],
        "items": [
            ["SSE", "20240101", 0, "20231231"],
            ["SSE", "20240102", 1, "20231231"],
            ...
        ]
    }
}
""")

# ============================================================================
# 6. 注意事项
# ============================================================================

print("=" * 60)
print("注意事项")
print("=" * 60)
print("""
1. Token 安全:
   - 不要将 Token 提交到版本控制系统
   - 使用环境变量管理 Token
   - 定期更换 Token

2. 积分制度:
   - Tushare 采用积分制度，不同接口需要不同积分
   - 基础数据接口通常免费
   - 高级数据接口需要一定积分

3. 调用频率:
   - 注意 API 调用频率限制
   - 建议使用缓存机制
   - 避免频繁重复调用

4. 数据格式:
   - 日期格式：YYYYMMDD
   - 股票代码：000001.SZ (平安银行)
   - 返回数据：pandas DataFrame 格式

5. 错误处理:
   - code: 2002 表示权限问题
   - 网络超时请重试
   - 检查 Token 是否有效
""")

# ============================================================================
# 7. 常用股票代码示例
# ============================================================================

print("=" * 60)
print("常用股票代码示例")
print("=" * 60)
print("""
A 股市场:
- 000001.SZ - 平安银行 (深交所)
- 000002.SZ - 万科 A (深交所)
- 600000.SH - 浦发银行 (上交所)
- 600519.SH - 贵州茅台 (上交所)

指数:
- 000001.SH - 上证指数
- 399001.SZ - 深证成指
- 399006.SZ - 创业板指
""")

print("\n✅ 教程完成！")
print("\n💡 提示：运行此脚本前请确保:")
print("   1. 已安装 tushare: pip install tushare")
print("   2. 已配置 TUSHARE_TOKEN 环境变量")
print("   3. Token 有效且有足够积分")
