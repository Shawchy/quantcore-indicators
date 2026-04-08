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
        super().__init__(config)
        self._client = None
        self._fingerprint_mode = self.config.get('tls_patch_mode', 'curl_cffi')
        self._impersonate = self.config.get('impersonate', 'chrome120')
    
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
                timeout=self.config.get('timeout', 30)
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
        
        # 确保已初始化
        if not self._client:
            await self.initialize()
        
        # 返回标准 headers，实际 TLS 配置在请求时处理
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
