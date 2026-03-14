"""
Tushare 快速测试脚本
用于验证 Tushare 配置是否正确
"""

import tushare as ts
from dotenv import load_dotenv
import os
import sys

# 加载环境变量
load_dotenv()

def test_tushare():
    """测试 Tushare 基本功能"""
    
    print("=" * 60)
    print("Tushare 快速测试")
    print("=" * 60)
    print()
    
    # 1. 检查 Token
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        print("❌ 错误：未找到 TUSHARE_TOKEN 环境变量")
        print("   请在 .env 文件中配置 TUSHARE_TOKEN")
        return False
    
    print(f"✅ Token 已配置：{token[:20]}...")
    print()
    
    # 2. 初始化
    try:
        ts.set_token(token)
        pro = ts.pro_api()
        print(f"✅ Tushare 初始化成功")
        print(f"   版本：{ts.__version__}")
        print()
    except Exception as e:
        print(f"❌ 初始化失败：{e}")
        return False
    
    # 3. 测试基础接口
    tests = [
        ("交易日历", lambda: pro.trade_cal(
            exchange='', start_date='20240101', end_date='20240107', is_open='0'
        )),
        ("股票列表", lambda: pro.stock_basic(
            exchange='SSE', list_status='L', fields='ts_code,name'
        )),
        ("日线数据", lambda: pro.daily(
            ts_code='000001.SZ', start_date='20240102', end_date='20240105'
        )),
    ]
    
    success_count = 0
    for name, test_func in tests:
        try:
            print(f"📊 测试 {name}...", end=" ")
            df = test_func()
            if df is not None and len(df) > 0:
                print(f"✅ 成功 (获取到 {len(df)} 条数据)")
                success_count += 1
            else:
                print(f"⚠️  返回空数据")
        except Exception as e:
            print(f"❌ 失败：{str(e)[:50]}")
    
    print()
    print("=" * 60)
    print(f"测试结果：{success_count}/{len(tests)} 通过")
    print("=" * 60)
    
    if success_count == len(tests):
        print("\n✅ Tushare 配置正确，可以正常使用！")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查:")
        print("   1. Token 是否有效")
        print("   2. 是否有足够积分")
        print("   3. 网络连接是否正常")
        return False

if __name__ == '__main__':
    success = test_tushare()
    sys.exit(0 if success else 1)
