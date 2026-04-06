#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rust Extension Loading Diagnostic Script
"""

import os
import sys
import ctypes
import re

def check_pyd_file():
    """Check PYD file and its exports"""
    print("\n" + "=" * 60)
    print("1. Checking PYD File")
    print("=" * 60)
    
    pyd_path = "python/quantcore_indicators/quantcore_indicators.cp312-win_amd64.pyd"
    
    if not os.path.exists(pyd_path):
        print(f"[FAIL] PYD file not found: {pyd_path}")
        return False
    
    print(f"[OK] PYD file exists: {pyd_path}")
    print(f"     Size: {os.path.getsize(pyd_path)} bytes")
    
    try:
        lib = ctypes.CDLL(pyd_path)
        all_attrs = dir(lib)
        
        # Find PyInit functions
        pyinit_funcs = [attr for attr in all_attrs if 'PyInit' in attr]
        
        print(f"\n     Total exported attributes: {len(all_attrs)}")
        print(f"     PyInit functions found: {pyinit_funcs if pyinit_funcs else 'NONE'}")
        
        target_symbol = "PyInit_quantcore_indicators"
        if hasattr(lib, target_symbol):
            print(f"     [OK] Target symbol found: {target_symbol}")
            return True
        else:
            print(f"     [FAIL] Target symbol NOT found: {target_symbol}")
            
            # Show some public attributes for debugging
            public_attrs = [attr for attr in all_attrs if not attr.startswith('_')]
            if public_attrs:
                print(f"     Sample public attrs: {public_attrs[:10]}")
            
            return False
            
    except Exception as e:
        print(f"     [ERROR] Load failed: {e}")
        return False

def check_module_import():
    """Test module import"""
    print("\n" + "=" * 60)
    print("2. Testing Module Import")
    print("=" * 60)
    
    try:
        # Clear cache
        for key in list(sys.keys()):
            if 'quantcore' in key.lower():
                del sys[key]
        
        from quantcore_indicators import quantcore_indicators as rust_mod
        
        print("[OK] Rust submodule imported successfully!")
        print(f"     Module type: {type(rust_mod)}")
        funcs = [x for x in dir(rust_mod) if not x.startswith('_')]
        print(f"     Available functions: {funcs[:10]}")
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import failed:")
        print(f"       Error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def analyze_rust_code():
    """Analyze Rust code structure"""
    print("\n" + "=" * 60)
    print("3. Analyzing Rust Code Structure")
    print("=" * 60)
    
    lib_rs_path = "src/lib.rs"
    bindings_path = "src/pyo3_bindings.rs"
    
    issues = []
    
    if os.path.exists(lib_rs_path):
        with open(lib_rs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            has_extension_module = 'feature = "extension-module"' in content
            has_pub_mod = 'pub mod pyo3_bindings' in content
            has_pymodule_in_root = '#[pymodule]' in content
            
            print("  lib.rs analysis:")
            print(f"    - extension-module feature: {'OK' if has_extension_module else 'MISSING'}")
            print(f"    - pub mod pyo3_bindings: {'OK' if has_pub_mod else 'MISSING (private?)'}")
            print(f"    - #[pymodule] in root: {'YES' if has_pymodule_in_root else 'NO'}")
            
            if not has_pub_mod:
                issues.append("pyo3_bindings is private, should be pub mod")
                
    if os.path.exists(bindings_path):
        with open(bindings_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Extract pymodule function name
            pymodule_match = re.search(r'#\[pymodule\]\s*pub fn (\w+)', content)
            
            if pymodule_match:
                func_name = pymodule_match.group(1)
                is_pub = 'pub fn' in pymodule_match.group()
                
                print(f"\n  pyo3_bindings.rs analysis:")
                print(f"    - #[pymodule] function name: {func_name}")
                print(f"    - Is public: {'YES' if is_pub else 'NO'}")
                print(f"    - Matches .pyd filename: {'YES' if func_name == 'quantcore_indicators' else 'MISMATCH!'}")
                
                if func_name != 'quantcore_indicators':
                    issues.append(f"Function name '{func_name}' doesn't match expected 'quantcore_indicators'")
                    
                if not is_pub:
                    issues.append("pymodule function is not public")
    
    return issues

def main():
    """Main function"""
    print("=" * 60)
    print("Rust Extension Loading Diagnostic Report")
    print("=" * 60)
    
    results = []
    
    # Run checks
    results.append(("PYD File Check", check_pyd_file()))
    results.append(("Module Import Test", check_module_import()))
    
    # Analyze code
    issues = analyze_rust_code()
    
    # Summary
    print("\n" + "=" * 60)
    print("Diagnostic Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if issues:
        print(f"\nIdentified Issues ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    
    if passed < total or issues:
        print("\n[!] Issues found, further investigation needed")
        return 1
    else:
        print("\n[OK] All checks passed")
        return 0

if __name__ == "__main__":
    sys.exit(main())
