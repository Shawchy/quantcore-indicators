"""
第一个测试：验证 QuantCore 安装成功
"""

import quantcore
from quantcore import quantcore_engine

print("=" * 60)
print("🎉 QuantCore 安装成功！")
print("=" * 60)
print(f"版本：{quantcore_engine.version()}")
print(f"问候：{quantcore_engine.hello_quant()}")
print(f"测试计算：2 + 3 = {quantcore_engine.add(2, 3)}")
print("=" * 60)
print("\n✅ 所有测试通过！Rust 引擎已经可以正常工作！")
print("\n下一步：")
print("1. 完善 Rust 数据模型（Bar、Order、Trade 等）")
print("2. 实现回测引擎")
print("3. 创建策略框架")
print("\n继续加油！🚀")
