#!/usr/bin/env python3
"""
批量为 EFinance 方法添加返回类型注解
"""

import re

def add_type_hints(file_path: str):
    """批量添加类型注解"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义需要添加类型注解的方法映射
    type_hints = {
        # 反风控方法
        r'def _setup_request_headers\(self, rotate: bool = True\):': 'def _setup_request_headers(self, rotate: bool = True) -> None:',
        r'async def _rate_limit\(self\):': 'async def _rate_limit(self) -> None:',
        r'def _rate_limit_sync\(self\):': 'def _rate_limit_sync(self) -> None:',
        r'def record_request_success\(self\):': 'def record_request_success(self) -> None:',
        r'def record_request_failure\(self\):': 'def record_request_failure(self) -> None:',
        r'def enable_adaptive_delay\(self, enabled: bool = True\):': 'def enable_adaptive_delay(self, enabled: bool = True) -> None:',
        r'def reset_rate_limit_status\(self\):': 'def reset_rate_limit_status(self) -> None:',
        r'def set_custom_delay\(self, min_delay: float, max_delay: float\):': 'def set_custom_delay(self, min_delay: float, max_delay: float) -> None:',
        r'def _rotate_user_agent\(self\) -> str:': 'def _rotate_user_agent(self) -> str:',  # 已有
        r'def get_current_user_agent\(self\) -> str:': 'def get_current_user_agent(self) -> str:',  # 已有
        
        # 代理方法
        r'async def setup_proxy\(self, proxy_url: Optional\[str\] = None\):': 'async def setup_proxy(self, proxy_url: Optional[str] = None) -> bool:',
        r'async def clear_proxy\(self\):': 'async def clear_proxy(self) -> None:',
        
        # 装饰器
        r'def rate_limit_decorator\(min_delay: float = 1\.0, max_delay: float = 2\.0, retries: int = 3\):': 'def rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3) -> Callable:',
        r'def async_rate_limit_decorator\(min_delay: float = 1\.0, max_delay: float = 2\.0, retries: int = 3\):': 'def async_rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3) -> Callable:',
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
    add_type_hints("backend/app/adapters/efinance_adapter.py")
