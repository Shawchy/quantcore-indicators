"""
quantcore-indicators 安装验证脚本

运行：python verify_install.py
"""
import sys
import os

# 添加 Python 包装器路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

def check_module():
    print("="*60)
    print("quantcore-indicators 安装验证")
    print("="*60)
    print()

    # 1. 检查模块导入
    print("[1/4] 检查模块导入...")
    try:
        import quantcore_indicators
        print("  ✅ 模块导入成功")
    except ImportError as e:
        print(f"  ❌ 模块导入失败: {e}")
        return False
    print()

    # 2. 检查 Rust 扩展状态
    print("[2/4] 检查 Rust 扩展...")
    if quantcore_indicators._RUST_AVAILABLE:
        print("  ✅ Rust 扩展已加载 (高性能模式)")
    else:
        print("  ⚠️ Rust 扩展未加载，将使用 Python fallback")
        print("  提示：运行 build_and_install.bat 编译 Rust 扩展")
    print()

    # 3. 检查可用指标
    print("[3/4] 检查可用指标...")
    indicators = quantcore_indicators.__all__
    print(f"  共 {len(indicators)} 个指标：")
    for ind in indicators:
        print(f"    - {ind}")
    print()

    # 4. 快速功能测试
    print("[4/4] 快速功能测试...")
    try:
        import numpy as np
        
        # 测试数据
        prices = [float(i) for i in range(1, 101)]
        
        # 测试 MA
        ma_result = quantcore_indicators.ma(prices, 20)
        print(f"  ✅ MA(20): 返回 {len(ma_result)} 个值")
        
        # 测试 EMA
        ema_result = quantcore_indicators.ema(prices, 12)
        print(f"  ✅ EMA(12): 返回 {len(ema_result)} 个值")
        
        # 测试 MACD
        macd_result = quantcore_indicators.macd(prices, 12, 26, 9)
        print(f"  ✅ MACD: 返回 {len(macd_result['macd'])} 个值")
        
        # 测试 RSI
        rsi_result = quantcore_indicators.rsi(prices, 14)
        print(f"  ✅ RSI(14): 返回 {len(rsi_result)} 个值")
        
        print()
        print("  所有指标测试通过!")
        
    except Exception as e:
        print(f"  ❌ 功能测试失败: {e}")
        return False
    
    print()
    print("="*60)
    print("✅ 验证完成！quantcore-indicators 可以正常使用")
    print("="*60)
    return True

if __name__ == "__main__":
    success = check_module()
    sys.exit(0 if success else 1)
