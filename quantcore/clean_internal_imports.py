"""
清理 Issue 1 修复后遗留的内部导入语句

这些导入语句在添加依赖注入后已不再需要。
"""

import re
from pathlib import Path


def clean_internal_imports():
    """清理函数内部的导入语句"""
    
    file_path = Path("backend/app/api/v1/endpoints/smart_realtime.py")
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    lines = content.split('\n')
    cleaned_lines = []
    
    in_function = False
    indent_level = 0
    skip_next_import = False
    
    # 需要移除的导入模式
    target_imports = [
        r'from app\.services\.smart_polling import smart_polling_service',
        r'from app\.services\.incremental_update import incremental_updater',
        r'from app\.utils\.anti_scraping_rules import anti_scraping_rules',
    ]
    
    for i, line in enumerate(lines):
        # 检测函数开始
        if line.strip().startswith('async def ') or line.strip().startswith('def '):
            in_function = True
            indent_level = len(line) - len(line.lstrip())
            cleaned_lines.append(line)
            continue
        
        # 检测装饰器（@router 等）
        if line.strip().startswith('@'):
            in_function = False
            cleaned_lines.append(line)
            continue
        
        # 如果在函数内部，检查是否是目标导入
        if in_function:
            # 检查当前行是否缩进级别高于函数定义
            current_indent = len(line) - len(line.lstrip())
            
            if current_indent > indent_level and line.strip():
                # 在函数内部且非空行
                is_target_import = any(
                    re.match(pattern, line.strip()) 
                    for pattern in target_imports
                )
                
                if is_target_import:
                    # 跳过这个导入
                    print(f"⚠️  跳过内部导入：{line.strip()}")
                    continue
        
        cleaned_lines.append(line)
    
    # 保存清理后的文件
    file_path.write_text('\n'.join(cleaned_lines), encoding='utf-8')
    print(f"✅ {file_path} 清理完成")
    return True


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir('..')  # 切换到 backend 目录的父级
    
    print("🧹 清理内部导入语句...")
    print()
    
    clean_internal_imports()
    
    print()
    print("✅ 清理完成！")
