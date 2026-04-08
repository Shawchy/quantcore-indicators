"""
清理 EFinanceAdapter 中的老反风控方法调用

删除所有：
- await self._ensure_credentials()
- await self._rate_limit()
以及相关的注释行
"""

import re
from pathlib import Path

def clean_old_methods(file_path: str):
    """清理老的反风控方法调用"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计清理数量
    cleaned = {
        '_ensure_credentials': 0,
        '_rate_limit': 0,
    }
    
    # 1. 删除所有 await self._ensure_credentials() 和前面的注释行
    pattern1 = r'#[^\n]*确保凭证有效[^\n]*\n\s*await self\._ensure_credentials\(\)\n'
    matches1 = re.findall(pattern1, content)
    cleaned['_ensure_credentials'] = len(matches1)
    content = re.sub(pattern1, '', content)
    
    # 2. 删除所有 await self._rate_limit() 和前面的注释行
    pattern2 = r'#[^\n]*限流 [^\n]*\n\s*await self\._rate_limit\(\)\n'
    matches2 = re.findall(pattern2, content)
    cleaned['_rate_limit'] = len(matches2)
    content = re.sub(pattern2, '', content)
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return cleaned


if __name__ == "__main__":
    file_path = Path(__file__).parent.parent / "app" / "adapters" / "efinance_adapter.py"
    
    print(f"开始清理：{file_path}")
    cleaned = clean_old_methods(str(file_path))
    
    print("\n清理完成！统计：")
    for method, count in cleaned.items():
        print(f"  - {method}: {count} 处")
    
    total = sum(cleaned.values())
    print(f"\n总计清理：{total} 处")
    print("\n✅ 清理完成！请运行测试验证。")
