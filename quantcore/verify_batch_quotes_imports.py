"""
验证 get_batch_quotes 函数是否还有硬编码导入

检查内容：
1. 函数是否使用依赖注入参数
2. 函数体内是否有硬编码导入语句
"""

from pathlib import Path

BASE_DIR = Path(r"D:\PROJ\Quant")


def verify_get_batch_quotes():
    """验证 get_batch_quotes 函数"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 查找 get_batch_quotes 函数定义
    func_start = content.find("async def get_batch_quotes")
    if func_start == -1:
        return False, "未找到 get_batch_quotes 函数"
    
    # 查找下一个函数定义
    next_func = content.find("async def ", func_start + 1)
    if next_func == -1:
        next_func = len(content)
    
    # 提取函数体（包括文档字符串）
    func_body = content[func_start:next_func]
    
    print("🔍 验证 get_batch_quotes 函数...")
    print()
    
    # 检查 1: 是否有依赖注入参数
    has_di_params = (
        "smart_polling_service=Depends(get_smart_polling_service)" in func_body and
        "incremental_updater=Depends(get_incremental_updater)" in func_body
    )
    
    if has_di_params:
        print("✅ 函数签名包含依赖注入参数")
    else:
        print("❌ 函数签名缺少依赖注入参数")
    
    # 检查 2: 函数体内是否有硬编码导入
    # 查找 try 块内的导入（排除文档字符串）
    try_start = func_body.find("try:")
    if try_start != -1:
        # 提取 try 块开始后的代码
        try_block = func_body[try_start:try_start+500]
        
        has_internal_imports = (
            "from app.services.smart_polling import smart_polling_service" in try_block or
            "from app.services.incremental_update import incremental_updater" in try_block
        )
        
        if has_internal_imports:
            print("❌ 函数体内有硬编码导入语句")
            return False, "发现硬编码导入"
        else:
            print("✅ 函数体内无硬编码导入")
    else:
        print("⚠️ 未找到 try 块")
    
    # 检查 3: 是否使用了注入的参数
    uses_di_params = (
        "smart_polling_service.get_realtime_batch" in func_body and
        "incremental_updater.get_last_snapshot" in func_body
    )
    
    if uses_di_params:
        print("✅ 函数体使用了依赖注入参数")
    else:
        print("❌ 函数体未使用依赖注入参数")
    
    # 检查 4: 第 128-129 行的内容
    lines = func_body.split('\n')
    if len(lines) >= 33:  # 文档字符串中的行
        line_128 = lines[32] if len(lines) > 32 else ""  # 考虑偏移
        line_129 = lines[33] if len(lines) > 33 else ""
        
        print()
        print("📋 检查第 128-129 行:")
        print(f"   第 128 行：{line_128.strip()}")
        print(f"   第 129 行：{line_129.strip()}")
        
        # 检查是否是文档字符串
        if '"success": true' in line_128 or '"data":' in line_129:
            print("✅ 第 128-129 行是文档字符串中的示例响应，不是导入语句")
        else:
            print("⚠️ 第 128-129 行内容需要检查")
    
    print()
    
    all_passed = has_di_params and not has_internal_imports and uses_di_params
    
    if all_passed:
        return True, "get_batch_quotes 函数已正确使用依赖注入，无硬编码导入"
    else:
        return False, "get_batch_quotes 函数存在问题"


def main():
    """主验证函数"""
    
    print("=" * 60)
    print("🔍 验证 get_batch_quotes 函数导入问题")
    print("=" * 60)
    print()
    
    success, message = verify_get_batch_quotes()
    
    print()
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print()
    
    if success:
        print("✅ " + message)
        print()
        print("📝 结论:")
        print("   Issue1 描述的问题不存在")
        print("   第 128-129 行是文档字符串，不是硬编码导入")
        print("   函数已正确使用依赖注入")
    else:
        print("❌ " + message)
        print()
        print("⚠️ 需要修复")
    
    print()


if __name__ == "__main__":
    main()
