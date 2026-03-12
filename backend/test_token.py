"""
Tushare Token 验证脚本
用于快速测试 Token 是否有效
"""
import tushare as ts
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv 未安装，尝试从 .env 文件读取")

def test_tushare_token():
    """测试 Tushare Token 有效性"""
    print("=" * 60)
    print("Tushare Token 验证工具")
    print("=" * 60)
    
    # 获取 Token
    token = os.getenv('TUSHARE_TOKEN')
    points = os.getenv('TUSHARE_POINTS', '120')
    
    if not token:
        print("\n❌ 错误：未找到 TUSHARE_TOKEN 环境变量")
        print("\n解决方法:")
        print("1. 检查 backend/.env 文件是否存在")
        print("2. 确认 .env 文件中配置了 TUSHARE_TOKEN=your_token")
        print("3. 前往 https://tushare.pro/ 注册并获取 Token")
        return False
    
    # 显示 Token 信息（脱敏）
    token_preview = f"{token[:10]}...{token[-5:]}" if len(token) >= 15 else token
    print(f"\n📋 配置信息:")
    print(f"   Token: {token_preview}")
    print(f"   积分配置：{points} 分")
    
    try:
        # 设置 Token
        print("\n🔄 正在连接 Tushare...")
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 测试 1: 获取交易日历
        print("\n📅 测试 1: 获取交易日历数据...")
        df = pro.trade_cal(exchange='', start_date='20240101', end_date='20240107')
        
        if df.empty:
            print("❌ 失败：无法获取交易日历数据")
            print("   可能原因：Token 无效或积分不足")
            return False
        
        print(f"✅ 成功：获取到 {len(df)} 条交易日历数据")
        
        # 测试 2: 获取股票列表
        print("\n📊 测试 2: 获取股票列表...")
        try:
            df_stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
            if not df_stocks.empty:
                print(f"✅ 成功：获取到 {len(df_stocks)} 只股票信息")
            else:
                print("⚠️  警告：股票列表为空")
        except Exception as e:
            print(f"❌ 失败：{e}")
        
        # 测试 3: 查询用户积分（如果权限允许）
        print("\n💰 测试 3: 查询用户积分...")
        try:
            user_info = pro.user()
            if not user_info.empty:
                actual_points = user_info.iloc[0].get('points', 0)
                print(f"✅ 实际积分：{actual_points} 分")
                
                if actual_points < int(points):
                    print(f"⚠️  警告：配置积分 ({points}) 高于实际积分 ({actual_points})")
                    print(f"   建议：修改 .env 文件中 TUSHARE_POINTS={actual_points}")
                elif actual_points > int(points):
                    print(f"ℹ️  提示：实际积分 ({actual_points}) 高于配置积分 ({points})")
                    print(f"   建议：修改 .env 文件中 TUSHARE_POINTS={actual_points} 以解锁更多功能")
            else:
                print("⚠️  无法查询用户信息（可能是权限不足）")
        except Exception as e:
            print(f"⚠️  无法查询积分：{e}")
            print("   这不影响正常使用，只是无法查询积分信息")
        
        # 测试 4: 获取指数数据
        print("\n📈 测试 4: 获取上证指数数据...")
        try:
            df_index = pro.index_daily(ts_code='000001.SH', start_date='20240101', end_date='20240107')
            if not df_index.empty:
                print(f"✅ 成功：获取到 {len(df_index)} 条指数数据")
            else:
                print("⚠️  警告：指数数据为空")
        except Exception as e:
            print(f"❌ 失败：{e}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！Token 有效，可以正常使用")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 连接失败：{error_msg}")
        
        # 分析错误原因
        if "抱歉" in error_msg and "权限" in error_msg:
            print("\n🔍 问题分析:")
            print("   - Token 无效或已过期")
            print("   - 或者积分不足")
            print("\n💡 解决方法:")
            print("   1. 前往 https://tushare.pro/ 登录账号")
            print("   2. 在「个人主页」→「接口 TOKEN」获取新 Token")
            print("   3. 完善个人信息可获得 120 积分")
            print("   4. 更新 .env 文件中的 TUSHARE_TOKEN")
        elif "网络" in error_msg or "timeout" in error_msg.lower():
            print("\n🔍 问题分析:")
            print("   - 网络连接问题")
            print("\n💡 解决方法:")
            print("   1. 检查网络连接")
            print("   2. 稍后重试")
        else:
            print("\n🔍 可能原因:")
            print("   - Token 格式错误")
            print("   - Token 已失效")
            print("   - 账号被限制")
        
        print("\n" + "=" * 60)
        print("❌ Token 验证失败")
        print("=" * 60)
        
        return False

if __name__ == "__main__":
    success = test_tushare_token()
    sys.exit(0 if success else 1)
