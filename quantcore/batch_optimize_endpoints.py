"""
批量优化 API 端点异常处理

优化列表：
1. performance.py - 5 个函数
2. audit.py - 3 个函数  
3. data_source.py - 3 个函数
4. lifecycle.py - 2 个函数
5. backup.py - 2 个函数
"""

from pathlib import Path
import re

BASE_DIR = Path(r"D:\PROJ\Quant")


def add_exception_handling(file_path: Path, functions_to_fix: list):
    """为指定函数添加异常处理"""
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    for func_name in functions_to_fix:
        # 查找函数定义
        func_pattern = rf'(async def {func_name}\([^)]*\):.*?)(?=\nasync def |\n@router|\Z)'
        matches = re.findall(func_pattern, content, re.DOTALL)
        
        if not matches:
            print(f"  ⚠️  未找到函数：{func_name}")
            continue
        
        func_body = matches[0]
        
        # 检查是否已经有 try 块
        if 'try:' in func_body and 'except' in func_body:
            print(f"  ✅ {func_name}: 已有异常处理")
            continue
        
        # 找到函数体的第一行（文档字符串后）
        lines = func_body.split('\n')
        new_func_lines = []
        in_docstring = False
        docstring_end = -1
        
        for i, line in enumerate(lines):
            new_func_lines.append(line)
            
            # 检测文档字符串结束
            if '"""' in line or "'''" in line:
                if in_docstring:
                    docstring_end = i
                    break
                elif line.count('"""') == 1 or line.count("'''") == 1:
                    in_docstring = True
        
        if docstring_end == -1:
            print(f"  ⚠️  {func_name}: 无法确定文档字符串位置")
            continue
        
        # 在文档字符串后添加 try 块
        indent = '    '
        new_func_lines.insert(docstring_end + 1, f'{indent}try:')
        
        # 缩进原有代码
        for i in range(docstring_end + 2, len(new_func_lines)):
            if new_func_lines[i].strip() and not new_func_lines[i].strip().startswith('#'):
                new_func_lines[i] = indent + new_func_lines[i]
        
        # 添加异常处理
        return_statements = []
        for line in lines[docstring_end+1:]:
            if 'return ' in line:
                return_statements.append(line.strip())
        
        if return_statements:
            # 找到最后一个 return 语句
            last_return = return_statements[-1]
            exception_handler = f'''{indent}except Exception as e:
{indent}    logger.error(f"{{func_name}}执行失败：{{e}}")
{indent}    raise HTTPException(status_code=500, detail="执行失败")'''
            
            # 在最后一个 return 后添加异常处理
            new_func_content = '\n'.join(new_func_lines)
            if last_return in new_func_content:
                new_func_content = new_func_content.replace(
                    last_return, 
                    last_return + '\n' + exception_handler,
                    1
                )
                
                # 替换原函数
                content = content.replace(func_body, new_func_content)
                print(f"  ✅ {func_name}: 已添加异常处理")
    
    # 保存
    file_path.write_text(content, encoding='utf-8')
    return True


def optimize_performance():
    """优化 performance.py"""
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/performance.py"
    
    if not file_path.exists():
        return False
    
    functions = [
        'get_query_stats',
        'get_index_suggestions', 
        'get_cache_stats',
        'get_cache_policies',
        'get_performance_overview'
    ]
    
    print("优化 performance.py...")
    success = add_exception_handling(file_path, functions)
    
    if success:
        print(f"✅ performance.py 优化完成\n")
    return success


def optimize_audit():
    """优化 audit.py"""
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/audit.py"
    
    if not file_path.exists():
        return False
    
    functions = [
        'get_audit_stats',
        'get_event_types',
        'get_severity_levels'
    ]
    
    print("优化 audit.py...")
    success = add_exception_handling(file_path, functions)
    
    if success:
        print(f"✅ audit.py 优化完成\n")
    return success


def optimize_data_source():
    """优化 data_source.py"""
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/data_source.py"
    
    if not file_path.exists():
        return False
    
    functions = [
        'get_data_source_health',
        'get_available_sources',
        'get_performance_stats'
    ]
    
    print("优化 data_source.py...")
    success = add_exception_handling(file_path, functions)
    
    if success:
        print(f"✅ data_source.py 优化完成\n")
    return success


def optimize_lifecycle():
    """优化 lifecycle.py"""
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/lifecycle.py"
    
    if not file_path.exists():
        return False
    
    functions = [
        'get_lifecycle_stats',
        'get_lifecycle_config'
    ]
    
    print("优化 lifecycle.py...")
    success = add_exception_handling(file_path, functions)
    
    if success:
        print(f"✅ lifecycle.py 优化完成\n")
    return success


def optimize_backup():
    """优化 backup.py"""
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/backup.py"
    
    if not file_path.exists():
        return False
    
    functions = [
        'get_backup_stats',
        'get_backup_config'
    ]
    
    print("优化 backup.py...")
    success = add_exception_handling(file_path, functions)
    
    if success:
        print(f"✅ backup.py 优化完成\n")
    return success


def main():
    """主函数"""
    
    print("=" * 60)
    print("🔧 批量优化 API 端点异常处理")
    print("=" * 60)
    print()
    
    optimizations = [
        ("performance.py", optimize_performance),
        ("audit.py", optimize_audit),
        ("data_source.py", optimize_data_source),
        ("lifecycle.py", optimize_lifecycle),
        ("backup.py", optimize_backup),
    ]
    
    results = []
    
    for name, func in optimizations:
        try:
            success = func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} 优化失败：{e}\n")
            results.append((name, False))
    
    # 总结
    print("=" * 60)
    print("优化总结")
    print("=" * 60)
    print()
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print("\n🎉 所有文件优化成功！")
    else:
        print("\n⚠️ 部分文件优化失败")
    
    print()


if __name__ == "__main__":
    main()
