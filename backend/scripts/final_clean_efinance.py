"""
最终清理 EFinanceAdapter 中的老反风控方法
"""

import re
from pathlib import Path

def clean_all_old_methods(file_path: str):
    """清理所有老的反风控方法调用"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计清理数量
    cleaned = {
        '_ensure_credentials': 0,
        '_rate_limit': 0,
    }
    
    # 1. 删除所有 await self._ensure_credentials() 和前面的注释行（各种格式）
    patterns1 = [
        r'#[^\n]*确保凭证有效 [^\n]*\n\s*await self\._ensure_credentials\(\)\n',
        r'#[^\n]*TLS 指纹伪装 [^\n]*\n\s*await self\._ensure_credentials\(\)\n',
        r'\s*await self\._ensure_credentials\(\)\n',  # 没有注释的
    ]
    
    for pattern in patterns1:
        matches = re.findall(pattern, content)
        cleaned['_ensure_credentials'] += len(matches)
        content = re.sub(pattern, '', content)
    
    # 2. 删除所有 await self._rate_limit() 和前面的注释行（各种格式）
    patterns2 = [
        r'#[^\n]*限流 [^\n]*\n\s*await self\._rate_limit\(\)\n',
        r'#[^\n]*频率控制 [^\n]*\n\s*await self\._rate_limit\(\)\n',
        r'#[^\n]*请求频率控制 [^\n]*\n\s*await self\._rate_limit\(\)\n',
        r'\s*await self\._rate_limit\(\)\n',  # 没有注释的
    ]
    
    for pattern in patterns2:
        matches = re.findall(pattern, content)
        cleaned['_rate_limit'] += len(matches)
        content = re.sub(pattern, '', content)
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return cleaned


if __name__ == "__main__":
    file_path = Path(__file__).parent.parent / "app" / "adapters" / "efinance_adapter.py"
    
    print(f"开始清理：{file_path}")
    cleaned = clean_all_old_methods(str(file_path))
    
    print("\n清理完成！统计：")
    for method, count in cleaned.items():
        print(f"  - {method}: {count} 处")
    
    total = sum(cleaned.values())
    print(f"\n总计清理：{total} 处")
    print("\n✅ 清理完成！请运行测试验证。")
