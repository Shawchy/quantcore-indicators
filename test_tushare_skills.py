"""
Tushare Skills 配置验证脚本
"""
import tushare as ts
from pathlib import Path
from dotenv import load_dotenv
import os

print("=" * 70)
print("Tushare Skills 配置验证")
print("=" * 70)

# 1. 检查 Tushare 安装
print("\n1️⃣ 检查 Tushare 安装")
try:
    import tushare
    print(f"   ✅ Tushare 已安装")
    print(f"   版本：{tushare.__version__}")
except ImportError:
    print(f"   ❌ Tushare 未安装")
    print(f"   安装命令：pip install tushare -i https://pypi.tuna.tsinghua.edu.cn/simple")
    exit(1)

# 2. 加载 Token
print("\n2️⃣ 加载 Token")
# 首先尝试 backend/.env
env_file = Path(__file__).parent / "backend" / ".env"
if not env_file.exists():
    # 如果不存在，尝试当前目录
    env_file = Path(__file__).parent / ".env"
    
if env_file.exists():
    load_dotenv(env_file)
    token = os.getenv('TUSHARE_TOKEN')
    if token:
        print(f"   ✅ Token 已配置")
        print(f"   位置：{env_file}")
        print(f"   Token: {token[:10]}...{token[-5:]}")
    else:
        print(f"   ❌ Token 未配置")
        print(f"   请在 {env_file} 中添加：TUSHARE_TOKEN=your_token")
        exit(1)
else:
    print(f"   ❌ .env 文件不存在")
    print(f"   请检查：{env_file}")
    exit(1)

# 3. 测试连接
print("\n3️⃣ 测试 Tushare 连接")
try:
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 测试获取交易日历
    df = pro.trade_cal(exchange='', start_date='20240101', end_date='20240107')
    
    if not df.empty:
        print(f"   ✅ 连接成功")
        print(f"   获取到 {len(df)} 条交易日历数据")
    else:
        print(f"   ⚠️  连接成功但无数据")
        
except Exception as e:
    print(f"   ❌ 连接失败：{e}")
    print(f"\n   可能原因:")
    print(f"   1. Token 无效或已过期")
    print(f"   2. 积分不足（至少需要 120 分）")
    print(f"   3. 网络连接问题")
    print(f"\n   解决方案:")
    print(f"   1. 访问 https://tushare.pro/ 获取新 Token")
    print(f"   2. 完善个人信息获得 120 积分")
    print(f"   3. 检查网络连接")
    exit(1)

# 4. 测试积分查询
print("\n4️⃣ 查询积分状态")
try:
    user_info = pro.user()
    if not user_info.empty:
        points = user_info.iloc[0].get('points', 0)
        print(f"   ✅ 当前积分：{points} 分")
        
        if points < 120:
            print(f"   ⚠️  积分不足 120 分，部分功能不可用")
            print(f"   💡 建议：完善个人信息可获得 100 积分")
        elif points < 2000:
            print(f"   ✅ 积分充足，可使用基础功能")
            print(f"   💡 提示：距离周月线数据还差 {2000 - points} 分")
        else:
            print(f"   ✅ 积分充足，可使用高级功能")
    else:
        print(f"   ⚠️  无法查询积分信息")
except Exception as e:
    print(f"   ⚠️  无法查询积分：{e}")

# 5. 测试基础接口
print("\n5️⃣ 测试基础接口")

# 测试 1: 股票列表
print("   - 股票列表 (stock_basic)...", end=" ")
try:
    df = pro.stock_basic(exchange='', list_status='L', 
                         fields='ts_code,symbol,name', limit=10)
    if not df.empty:
        print(f"✅ ({len(df)} 只股票)")
    else:
        print(f"⚠️  (无数据)")
except Exception as e:
    print(f"❌ ({e})")

# 测试 2: 日线行情
print("   - 日线行情 (daily)...", end=" ")
try:
    df = pro.daily(ts_code='000001.SZ', start_date='20240301', end_date='20240312')
    if not df.empty:
        print(f"✅ ({len(df)} 条数据)")
    else:
        print(f"⚠️  (无数据)")
except Exception as e:
    print(f"❌ ({e})")

# 测试 3: 指数数据
print("   - 上证指数 (index_daily)...", end=" ")
try:
    df = pro.index_daily(ts_code='000001.SH', start_date='20240301', end_date='20240312')
    if not df.empty:
        print(f"✅ ({len(df)} 条数据)")
    else:
        print(f"⚠️  (无数据)")
except Exception as e:
    print(f"❌ ({e})")

# 测试 4: 分红送股
print("   - 分红送股 (dividend)...", end=" ")
try:
    df = pro.dividend(ts_code='000001.SZ', start_date='20200101', end_date='20241231')
    if not df.empty:
        print(f"✅ ({len(df)} 条记录)")
    else:
        print(f"⚠️  (无数据)")
except Exception as e:
    print(f"❌ ({e})")

print("\n" + "=" * 70)
print("✅ 验证完成")
print("=" * 70)

print("\n💡 提示:")
print("   - Tushare Skills 已配置完成")
print("   - 可以在 OpenClaw 中使用 Tushare 数据")
print("   - 查看完整文档：TUSHARE_SKILLS_SETUP.md")

print("\n🎯 下一步:")
print("   1. 在 OpenClaw 中安装 Skills:")
print("      clawhub install tushare-data")
print("   2. 或在对话框中输入:")
print("      请安装最新版 Tushare skills")
print("   3. 设置 Token:")
print("      请设置我的 Tushare Token：{token[:10]}...{token[-5:]}")

print("=" * 70)
