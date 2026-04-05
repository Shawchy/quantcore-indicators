#!/usr/bin/env python3
"""
批量添加剩余的类型注解
"""

import re

def add_remaining_type_hints(file_path: str):
    """添加剩余的类型注解"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义更多需要添加类型注解的方法
    type_hints = {
        # 记录方法
        r'def record_request_success\(self\):': 'def record_request_success(self) -> None:',
        r'def record_request_failure\(self\):': 'def record_request_failure(self) -> None:',
        
        # 代理方法
        r'async def setup_proxy\(self, proxy_url: Optional\[str\] = None\):': 'async def setup_proxy(self, proxy_url: Optional[str] = None) -> bool:',
        r'async def clear_proxy\(self\):': 'async def clear_proxy(self) -> None:',
        
        # 装饰器
        r'def rate_limit_decorator\(min_delay: float = 1\.0, max_delay: float = 2\.0, retries: int = 3\):': 'def rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3) -> Callable:',
        r'def async_rate_limit_decorator\(min_delay: float = 1\.0, max_delay: float = 2\.0, retries: int = 3\):': 'def async_rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3) -> Callable:',
        
        # 缓存方法
        r'def _get_cache_key\(self, api_name: str, \*\*kwargs\):': 'def _get_cache_key(self, api_name: str, **kwargs) -> str:',
        r'def _get_from_cache\(self, key: str, category: str = "default"\):': 'def _get_from_cache(self, key: str, category: str = "default") -> Optional[Any]:',
        r'def _set_to_cache\(self, key: str, data: Any, category: str = "default", ttl: int = 300\):': 'def _set_to_cache(self, key: str, data: Any, category: str = "default", ttl: int = 300) -> None:',
        
        # 降级方法
        r'async def _fallback_to_hybrid_client\(self\):': 'async def _fallback_to_hybrid_client(self) -> None:',
    }
    
    count = 0
    for pattern, replacement in type_hints.items():
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            count += 1
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已为 {count} 个方法添加类型注解")

if __name__ == "__main__":
    add_remaining_type_hints("backend/app/adapters/efinance_adapter.py")
    add_remaining_type_hints("backend/app/adapters/akshare_adapter.py")
