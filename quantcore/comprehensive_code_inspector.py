"""
全面代码检查工具

检查内容：
1. 所有 API 端点的依赖注入使用情况
2. 循环导入问题
3. 异常处理完整性
4. 服务模块存在性
5. 代码质量和最佳实践
"""

from pathlib import Path
import re
from typing import List, Dict, Tuple

BASE_DIR = Path(r"D:\PROJ\Quant")


class CodeInspector:
    """代码检查器"""
    
    def __init__(self):
        self.backend_dir = BASE_DIR / "backend"
        self.issues = []
        self.warnings = []
        self.success = []
    
    def check_all_endpoints(self):
        """检查所有 API 端点"""
        
        print("=" * 80)
        print("🔍 检查所有 API 端点")
        print("=" * 80)
        print()
        
        # 查找所有端点文件
        endpoints_dir = self.backend_dir / "app/api/v1/endpoints"
        
        if not endpoints_dir.exists():
            print(f"❌ 端点目录不存在：{endpoints_dir}")
            return
        
        endpoint_files = list(endpoints_dir.glob("*.py"))
        
        print(f"📂 发现 {len(endpoint_files)} 个端点文件:")
        for f in endpoint_files:
            print(f"   - {f.name}")
        print()
        
        # 检查每个文件
        for file_path in endpoint_files:
            self.check_endpoint_file(file_path)
    
    def check_endpoint_file(self, file_path: Path):
        """检查单个端点文件"""
        
        print(f"📄 检查文件：{file_path.name}")
        print("-" * 80)
        
        content = file_path.read_text(encoding='utf-8')
        
        # 1. 检查依赖注入函数定义
        self.check_dependency_injection_functions(content, file_path.name)
        
        # 2. 检查端点函数是否使用依赖注入
        self.check_endpoint_usage(content, file_path.name)
        
        # 3. 检查硬编码导入
        self.check_hardcoded_imports(content, file_path.name)
        
        # 4. 检查异常处理
        self.check_exception_handling(content, file_path.name)
        
        print()
    
    def check_dependency_injection_functions(self, content: str, filename: str):
        """检查依赖注入函数"""
        
        # 查找所有 get_* 函数（依赖注入函数）
        pattern = r'def (get_\w+)\(\):.*?Depends\('
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            print(f"  ✅ 发现 {len(matches)} 个依赖注入函数:")
            for match in matches:
                print(f"     - {match}")
            self.success.append(f"{filename}: {len(matches)} 个依赖注入函数")
        else:
            # 检查是否有 router 定义
            if "@router." in content:
                print(f"  ℹ️  未发现依赖注入函数（可能有端点定义）")
    
    def check_endpoint_usage(self, content: str, filename: str):
        """检查端点函数是否使用依赖注入"""
        
        # 查找所有 async def 函数
        endpoint_pattern = r'async def (\w+)\([^)]*Depends\([^)]+\)[^)]*\):'
        endpoints_with_di = re.findall(endpoint_pattern, content)
        
        if endpoints_with_di:
            print(f"  ✅ {len(endpoints_with_di)} 个端点使用依赖注入:")
            for endpoint in endpoints_with_di[:5]:  # 只显示前 5 个
                print(f"     - {endpoint}")
            if len(endpoints_with_di) > 5:
                print(f"     ... 还有 {len(endpoints_with_di) - 5} 个")
        
        # 查找有 Depends 但没有在参数中使用的情况
        all_async_funcs = re.findall(r'async def (\w+)\([^)]*\):', content)
        for func in all_async_funcs:
            func_start = content.find(f"async def {func}")
            if func_start == -1:
                continue
            
            next_func = content.find("async def ", func_start + 1)
            if next_func == -1:
                next_func = len(content)
            
            func_body = content[func_start:next_func]
            
            # 检查是否有 Depends 但在函数体内有硬编码导入
            if "Depends(" in func_body:
                if "from app.services." in func_body or "from app.utils." in func_body:
                    # 排除文档字符串
                    lines = func_body.split('\n')
                    in_try_block = False
                    for line in lines:
                        if 'try:' in line:
                            in_try_block = True
                        if in_try_block and ('from app.services.' in line or 'from app.utils.' in line):
                            if not line.strip().startswith('#'):  # 排除注释
                                print(f"  ⚠️  {func}: 可能存在硬编码导入")
                                self.warnings.append(f"{filename}/{func}: 依赖注入 + 硬编码导入并存")
    
    def check_hardcoded_imports(self, content: str, filename: str):
        """检查硬编码导入"""
        
        # 查找函数内部的导入（在 def 之后，缩进级别内）
        lines = content.split('\n')
        
        in_function = False
        function_name = ""
        function_indent = 0
        hardcoded_imports = []
        
        for i, line in enumerate(lines, 1):
            # 检测函数定义
            if line.strip().startswith('async def ') or line.strip().startswith('def '):
                in_function = True
                function_name = line.split('def ')[1].split('(')[0]
                function_indent = len(line) - len(line.lstrip())
                continue
            
            # 如果在函数内部
            if in_function and line.strip():
                current_indent = len(line) - len(line.lstrip())
                
                # 如果缩进级别回到或低于函数级别，退出函数
                if current_indent <= function_indent and not line.strip().startswith('#'):
                    in_function = False
                    continue
                
                # 检查是否是导入语句
                if (current_indent > function_indent and 
                    ('from app.services.' in line or 'from app.utils.' in line) and
                    line.strip().startswith('from')):
                    
                    # 排除文档字符串
                    if '"""' not in line and "'''" not in line:
                        hardcoded_imports.append((i, line.strip()))
        
        if hardcoded_imports:
            print(f"  ⚠️  发现 {len(hardcoded_imports)} 个函数内导入:")
            for line_num, import_line in hardcoded_imports[:5]:
                print(f"     L{line_num}: {import_line}")
            if len(hardcoded_imports) > 5:
                print(f"     ... 还有 {len(hardcoded_imports) - 5} 个")
            self.warnings.append(f"{filename}: {len(hardcoded_imports)} 个函数内导入")
        else:
            print(f"  ✅ 未发现函数内硬编码导入")
    
    def check_exception_handling(self, content: str, filename: str):
        """检查异常处理"""
        
        # 查找依赖注入函数
        di_func_pattern = r'def (get_\w+)\(\):'
        di_function_names = re.findall(di_func_pattern, content)
        
        for func_name in di_function_names:
            # 找到函数体
            func_start = content.find(f"def {func_name}")
            if func_start == -1:
                continue
            
            next_func = content.find("\ndef ", func_start + 1)
            if next_func == -1:
                next_func = len(content)
            
            func_body = content[func_start:next_func]
            
            has_try = 'try:' in func_body
            has_except_import = 'except ImportError' in func_body
            has_none_check = 'is None' in func_body
            has_http_exception = 'HTTPException' in func_body
            
            issues = []
            if not has_try:
                issues.append("缺少 try 块")
            if not has_except_import:
                issues.append("缺少 ImportError 捕获")
            if not has_none_check:
                issues.append("缺少 None 检查")
            if not has_http_exception:
                issues.append("缺少 HTTPException")
            
            if issues:
                print(f"  ⚠️  {func_name}: {', '.join(issues)}")
                self.warnings.append(f"{filename}/{func_name}: {'; '.join(issues)}")
            else:
                print(f"  ✅ {func_name}: 异常处理完善")
    
    def check_service_modules(self):
        """检查服务模块存在性"""
        
        print("=" * 80)
        print("🔍 检查服务模块")
        print("=" * 80)
        print()
        
        services_to_check = [
            ("app/services/smart_polling.py", "SmartPollingService"),
            ("app/services/incremental_update.py", "IncrementalUpdateService"),
            ("app/services/hybrid_realtime.py", "HybridRealtimeService"),
            ("app/utils/anti_scraping_rules.py", "AntiScrapingRules"),
        ]
        
        all_exist = True
        
        for module_path, class_name in services_to_check:
            file_path = self.backend_dir / module_path
            
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                if class_name in content:
                    print(f"  ✅ {module_path} - 存在且包含 {class_name}")
                    self.success.append(f"服务模块：{module_path}")
                else:
                    print(f"  ❌ {module_path} - 存在但不包含 {class_name}")
                    self.issues.append(f"服务模块：{module_path} 缺少 {class_name}")
                    all_exist = False
            else:
                print(f"  ❌ {module_path} - 不存在")
                self.issues.append(f"服务模块：{module_path} 不存在")
                all_exist = False
        
        print()
        
        if all_exist:
            print("  ✅ 所有服务模块都存在")
        else:
            print("  ⚠️  部分服务模块缺失")
    
    def check_circular_imports(self):
        """检查循环导入"""
        
        print("=" * 80)
        print("🔍 检查循环导入风险")
        print("=" * 80)
        print()
        
        # 检查端点文件中的导入模式
        endpoints_dir = self.backend_dir / "app/api/v1/endpoints"
        
        if not endpoints_dir.exists():
            return
        
        circular_risk = []
        
        for file_path in endpoints_dir.glob("*.py"):
            content = file_path.read_text(encoding='utf-8')
            
            # 检查是否在函数内部导入服务
            lines = content.split('\n')
            in_function = False
            
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('async def ') or line.strip().startswith('def '):
                    in_function = True
                elif line.strip().startswith('@') or (line.strip() and not line.strip().startswith(' ') and in_function):
                    in_function = False
                
                if in_function and 'from app.' in line and 'import' in line:
                    circular_risk.append((file_path.name, i, line.strip()))
        
        if circular_risk:
            print(f"  ⚠️  发现 {len(circular_risk)} 个潜在的循环导入风险:")
            for filename, line_num, import_line in circular_risk[:10]:
                print(f"     {filename}:L{line_num} - {import_line}")
            if len(circular_risk) > 10:
                print(f"     ... 还有 {len(circular_risk) - 10} 个")
            self.warnings.append(f"循环导入风险：{len(circular_risk)} 个")
        else:
            print(f"  ✅ 未发现循环导入风险")
    
    def generate_report(self):
        """生成检查报告"""
        
        print("=" * 80)
        print("📊 代码检查报告")
        print("=" * 80)
        print()
        
        print(f"✅ 成功项：{len(self.success)}")
        for item in self.success[:10]:
            print(f"   - {item}")
        if len(self.success) > 10:
            print(f"   ... 还有 {len(self.success) - 10} 个")
        print()
        
        print(f"⚠️  警告项：{len(self.warnings)}")
        for item in self.warnings[:10]:
            print(f"   - {item}")
        if len(self.warnings) > 10:
            print(f"   ... 还有 {len(self.warnings) - 10} 个")
        print()
        
        print(f"❌ 问题项：{len(self.issues)}")
        for item in self.issues:
            print(f"   - {item}")
        print()
        
        # 总体评价
        print("=" * 80)
        print("📈 总体评价")
        print("=" * 80)
        print()
        
        if len(self.issues) == 0 and len(self.warnings) == 0:
            print("  🎉 代码质量优秀，未发现问题！")
        elif len(self.issues) == 0:
            print(f"  ✅ 代码质量良好，有 {len(self.warnings)} 个警告需要注意")
        else:
            print(f"  ⚠️  发现 {len(self.issues)} 个问题，{len(self.warnings)} 个警告，建议修复")
        
        print()


def main():
    """主函数"""
    
    print()
    print("█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  全面代码检查工具".center(72) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    print()
    
    inspector = CodeInspector()
    
    # 1. 检查服务模块
    inspector.check_service_modules()
    print()
    
    # 2. 检查所有 API 端点
    inspector.check_all_endpoints()
    print()
    
    # 3. 检查循环导入
    inspector.check_circular_imports()
    print()
    
    # 4. 生成报告
    inspector.generate_report()


if __name__ == "__main__":
    main()
