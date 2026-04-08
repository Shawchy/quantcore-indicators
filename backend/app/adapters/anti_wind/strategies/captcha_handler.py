"""
验证码处理策略

检测页面中的验证码，支持多种验证码类型，提供人工处理等待机制。
"""

from typing import Optional, Dict, Any, List
from loguru import logger
from .base import BaseStrategy
import asyncio
import time


class CaptchaHandlerStrategy(BaseStrategy):
    """验证码处理策略
    
    功能：
    1. 检测页面中的验证码（基于关键词和元素）
    2. 支持多种验证码类型（滑块、图形、极验等）
    3. 提供人工处理等待机制
    4. 验证码超时自动重试
    
    配置参数：
    - timeout: 等待人工处理的超时时间（秒，默认 60）
    - check_interval: 检查验证码是否消失的间隔（秒，默认 1）
    - auto_retry: 验证码超时后是否自动重试（默认 True）
    """
    
    # 验证码关键词列表
    CAPTCHA_KEYWORDS = [
        'captcha', '验证码', '滑动验证', '图形验证',
        'geetest', '极验', 'vaptcha', '网易易盾',
        'aliyun', '阿里云验证', '腾讯验证码',
        '请完成安全验证', '安全检查', '人机验证',
        'slider', 'slide-verify', 'nc_1_wrapper'
    ]
    
    # 验证码 CSS 选择器
    CAPTCHA_SELECTORS = [
        '.geetest_slider', '.geetest_panel',
        '#nc_1_wrapper', '.nc_wrapper',
        '.captcha', '#captcha',
        '.verify-wrap', '.slide-verify',
        '#captcha_modal', '.captcha-modal',
        '.yidun_bg', '.yidun'
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        self._timeout = self.config.get('timeout', 60)
        self._check_interval = self.config.get('check_interval', 1)
        self._auto_retry = self.config.get('auto_retry', True)
        
        self._captcha_detected = False
        self._captcha_type: Optional[str] = None
        self._captcha_selector: Optional[str] = None
        
        logger.info(f"验证码处理策略已初始化 (timeout={self._timeout}s)")
    
    async def detect_captcha(self, page: Any) -> Dict[str, Any]:
        """检测页面中是否有验证码
        
        Args:
            page: Playwright page 对象
        
        Returns:
            检测结果字典：
            - detected: 是否检测到验证码
            - type: 验证码类型（geetest, slider, image, unknown）
            - selector: 验证码元素的选择器
            - message: 检测信息
        """
        if not self.is_enabled():
            return {'detected': False}
        
        result = {
            'detected': False,
            'type': None,
            'selector': None,
            'message': None
        }
        
        try:
            # 方法 1：检测页面内容中的关键词
            content = await page.content()
            page_text = await page.evaluate('() => document.body.innerText')
            
            for keyword in self.CAPTCHA_KEYWORDS:
                if keyword.lower() in content.lower() or keyword in page_text:
                    result['detected'] = True
                    result['message'] = f"检测到验证码指示器：{keyword}"
                    
                    # 判断验证码类型
                    if 'geetest' in content.lower() or '极验' in page_text:
                        result['type'] = 'geetest'
                    elif 'slider' in content.lower() or '滑动' in page_text:
                        result['type'] = 'slider'
                    elif '图形验证' in page_text:
                        result['type'] = 'image'
                    else:
                        result['type'] = 'unknown'
                    
                    logger.debug(f"验证码检测：{result['message']}")
                    break
            
            # 方法 2：检测验证码元素
            if not result['detected']:
                for selector in self.CAPTCHA_SELECTORS:
                    element = await page.query_selector(selector)
                    if element:
                        result['detected'] = True
                        result['type'] = 'slider'
                        result['selector'] = selector
                        result['message'] = f"检测到验证码元素：{selector}"
                        logger.debug(f"验证码检测：{result['message']}")
                        break
            
            # 保存检测结果
            if result['detected']:
                self._captcha_detected = True
                self._captcha_type = result['type']
                self._captcha_selector = result['selector']
            
        except Exception as e:
            logger.error(f"验证码检测失败：{e}")
            result['message'] = f"检测失败：{e}"
        
        return result
    
    async def wait_for_manual_solve(self, page: Any) -> bool:
        """等待人工处理验证码
        
        Args:
            page: Playwright page 对象
        
        Returns:
            bool: 是否成功通过验证码
        """
        if not self.is_enabled():
            return True
        
        if not self._captcha_detected:
            return True
        
        logger.info(f"检测到验证码 ({self._captcha_type})，等待人工处理... (超时：{self._timeout}秒)")
        
        start_time = time.time()
        
        while time.time() - start_time < self._timeout:
            try:
                # 检查验证码是否还存在
                if self._captcha_selector:
                    element = await page.query_selector(self._captcha_selector)
                    if not element:
                        logger.info("验证码已通过（元素消失）")
                        self._captcha_detected = False
                        return True
                else:
                    # 重新检测
                    result = await self.detect_captcha(page)
                    if not result['detected']:
                        logger.info("验证码已通过（检测不到）")
                        self._captcha_detected = False
                        return True
                
                await asyncio.sleep(self._check_interval)
                
            except Exception as e:
                logger.error(f"检查验证码状态失败：{e}")
                await asyncio.sleep(self._check_interval)
        
        logger.warning(f"验证码处理超时 ({self._timeout}秒)")
        return False
    
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """请求前执行（验证码策略不需要）"""
        # 验证码策略在请求后检测页面
        return headers
    
    async def after_request(self, response: Any) -> Any:
        """请求后执行（检查响应中是否有验证码信息）"""
        if not self.is_enabled():
            return response
        
        # 检查响应中是否包含验证码相关信息
        if isinstance(response, dict):
            content = response.get('content', '')
            if content:
                for keyword in self.CAPTCHA_KEYWORDS:
                    if keyword.lower() in content.lower():
                        logger.warning(f"响应中检测到验证码关键词：{keyword}")
                        self._captcha_detected = True
                        self._captcha_type = 'unknown'
                        break
        
        return response
    
    async def check_and_handle(self, page: Any) -> bool:
        """检查并处理验证码（一站式方法）
        
        Args:
            page: Playwright page 对象
        
        Returns:
            bool: 是否成功通过验证码（或没有验证码）
        """
        if not self.is_enabled():
            return True
        
        # 检测验证码
        result = await self.detect_captcha(page)
        
        if result['detected']:
            logger.warning(f"发现验证码：{result['type']} - {result['message']}")
            # 等待人工处理
            return await self.wait_for_manual_solve(page)
        
        return True
    
    def reset(self):
        """重置验证码状态"""
        self._captcha_detected = False
        self._captcha_type = None
        self._captcha_selector = None
        logger.debug("验证码状态已重置")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前验证码状态"""
        return {
            'enabled': self.is_enabled(),
            'captcha_detected': self._captcha_detected,
            'captcha_type': self._captcha_type,
            'captcha_selector': self._captcha_selector,
            'timeout': self._timeout,
        }
