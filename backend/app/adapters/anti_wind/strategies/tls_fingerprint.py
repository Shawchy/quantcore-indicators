"""
TLS 指纹伪装策略

模拟真实浏览器的 TLS 握手特征，绕过服务器指纹识别。
"""

from typing import Any, Dict, Optional
from loguru import logger
from .base import BaseStrategy


class TLSFingerprintStrategy(BaseStrategy):
    """TLS 指纹伪装策略"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 配置分离：只提取需要的配置
        super().__init__(config)
        self._client = None
        self._fingerprint_mode = config.get('tls_patch_mode', 'curl_cffi')
        self._impersonate = config.get('impersonate', 'chrome120')
        self._timeout = config.get('timeout', 30)
    
    async def initialize(self):
        """初始化 TLS 客户端"""
        if self._client:
            return
        
        try:
            # 导入 curl_cffi
            from curl_cffi import requests
            
            # 创建会话
            self._client = requests.Session(
                impersonate=self._impersonate,
                timeout=self._timeout
            )
            
            logger.info(f"✅ TLS 指纹客户端初始化成功（{self._fingerprint_mode}, {self._impersonate}）")
            
        except ImportError:
            logger.warning("⚠️  curl_cffi 未安装，TLS 指纹伪装不可用")
            self.disable()
        except Exception as e:
            logger.error(f"TLS 指纹客户端初始化失败：{e}")
            self.disable()
    
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """请求前配置 TLS 指纹"""
        if not self.enabled:
            return headers
        
        # Facade 已确保初始化，这里直接返回
        return headers
    
    async def after_request(self, response: Any) -> Any:
        """请求后处理"""
        return response
    
    def get_client(self):
        """获取 TLS 客户端"""
        return self._client
    
    def switch_fingerprint(self, impersonate: str):
        """切换 TLS 指纹"""
        self._impersonate = impersonate
        self._client = None  # 重置客户端
        logger.info(f"TLS 指纹已切换：{impersonate}")
