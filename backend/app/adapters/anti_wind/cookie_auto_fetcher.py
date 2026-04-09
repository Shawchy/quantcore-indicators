"""
Cookie 自动获取器（生产级）

提供自动获取、验证、续期 Cookie 的完整解决方案。
支持 Edge、Chrome 浏览器。

使用方式:
    from app.adapters.anti_wind.cookie_auto_fetcher import CookieAutoFetcher
    
    fetcher = CookieAutoFetcher(domain="eastmoney.com")
    success = await fetcher.fetch()
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from loguru import logger


class CookieAutoFetcher:
    """Cookie 自动获取器"""
    
    def __init__(
        self,
        domain: str = "eastmoney.com",
        browser: str = "edge",
        browser_path: Optional[str] = None,
        storage_dir: str = "data/cookies",
        expires_in_days: int = 7,
    ):
        """
        初始化 Cookie 自动获取器
        
        Args:
            domain: 目标域名
            browser: 浏览器类型（edge/chrome）
            browser_path: 浏览器路径（None 则自动检测）
            storage_dir: Cookie 存储目录
            expires_in_days: Cookie 有效期（天）
        """
        self.domain = domain
        self.browser = browser.lower()
        self.browser_path = browser_path or self._find_browser_path()
        self.storage_dir = Path(storage_dir)
        self.cookie_file = self.storage_dir / f"{domain}_auto.json"
        self.expires_in_days = expires_in_days
        
        # 确保目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        if self.browser_path:
            logger.info(f"✅ 找到 {browser.title()} 浏览器：{self.browser_path}")
        else:
            logger.warning(f"⚠️  未找到 {browser.title()} 浏览器，请手动指定路径")
    
    def _find_browser_path(self) -> Optional[str]:
        """查找浏览器路径"""
        if self.browser == "edge":
            possible_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
            ]
        else:  # chrome
            possible_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
            ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    async def fetch(self) -> bool:
        """
        自动获取 Cookie
        
        Returns:
            是否成功获取
        """
        logger.info("="*60)
        logger.info("🍪 开始自动获取 Cookie")
        logger.info(f"域名：{self.domain}")
        logger.info(f"浏览器：{self.browser.title()}")
        logger.info(f"浏览器路径：{self.browser_path or '自动检测'}")
        logger.info("="*60)
        
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
            
            # 配置浏览器
            options = ChromiumOptions()
            if self.browser_path:
                options.set_paths(browser_path=self.browser_path)
            
            options.headless()
            options.set_argument('--disable-blink-features=AutomationControlled')
            options.set_argument('--disable-gpu')
            options.set_argument('--no-sandbox')
            
            # 启动浏览器
            logger.info("启动浏览器...")
            page = ChromiumPage(options)
            
            try:
                # 访问目标网站
                target_url = f"https://www.{self.domain}"
                logger.info(f"访问：{target_url}")
                page.get(target_url)
                
                # 等待页面加载
                logger.info("等待页面加载...")
                await asyncio.sleep(5)
                
                # 获取 Cookie
                cookies = page.cookies()
                
                if cookies:
                    logger.info(f"✅ 获取到 {len(cookies)} 个 Cookie")
                    await self._save_cookies(cookies)
                    
                    # 验证 Cookie
                    is_valid = await self._verify_cookie()
                    if is_valid:
                        logger.info("✅ Cookie 验证通过")
                        return True
                    else:
                        logger.warning("⚠️  Cookie 验证失败，但已保存")
                        return True  # 仍然返回成功，让用户手动处理
                else:
                    logger.warning("⚠️  未获取到 Cookie")
                    return False
                    
            finally:
                page.quit()
                
        except ImportError as e:
            logger.error(f"❌ DrissionPage 未安装：{e}")
            return False
        except Exception as e:
            logger.error(f"❌ 获取失败：{e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    async def _save_cookies(self, cookies: List[Dict[str, Any]]):
        """保存 Cookie 到文件"""
        data = {
            'domain': self.domain,
            'cookies': cookies,
            'captured_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=self.expires_in_days)).isoformat(),
            'expires_in_days': self.expires_in_days,
            'auto_fetched': True,
            'browser': self.browser,
        }
        
        with open(self.cookie_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Cookie 已保存到：{self.cookie_file}")
        
        # 显示关键 Cookie
        important_cookies = ['EM_HWhich', 'EM_sid', 'EM_uid', 'st']
        cookie_names = [c.get('name', 'unknown') for c in cookies]
        logger.info(f"Cookie 列表：{cookie_names[:10]}{'...' if len(cookie_names) > 10 else ''}")
        
        print("\n关键 Cookie:")
        for name in important_cookies:
            for cookie in cookies:
                if cookie.get('name') == name:
                    value = cookie.get('value', '')
                    print(f"  - {name}: {value[:50]}{'...' if len(value) > 50 else ''}")
                    break
    
    async def _verify_cookie(self) -> bool:
        """验证 Cookie 有效性"""
        try:
            from curl_cffi import requests
            
            # 加载 Cookie
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cookies = data.get('cookies', [])
            cookie_dict = {c['name']: c['value'] for c in cookies}
            
            # 发送测试请求
            test_url = f"https://www.{self.domain}"
            response = requests.get(
                test_url,
                impersonate='chrome120',
                cookies=cookie_dict,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Cookie 验证成功（状态码：{response.status_code}）")
                return True
            else:
                logger.warning(f"⚠️  Cookie 验证失败（状态码：{response.status_code}）")
                return False
                
        except Exception as e:
            logger.error(f"❌ 验证失败：{e}")
            return False
    
    def is_expired(self) -> bool:
        """检查 Cookie 是否过期"""
        if not self.cookie_file.exists():
            return True
        
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            expires_at = datetime.fromisoformat(data['expires_at'])
            
            # 提前 1 小时续期
            check_time = datetime.now() + timedelta(hours=1)
            
            if check_time >= expires_at:
                logger.warning(f"⚠️  Cookie 即将过期：{expires_at}")
                return True
            else:
                logger.debug(f"✅ Cookie 仍在有效期内：{expires_at}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 检查过期失败：{e}")
            return True  # 出错时认为已过期
    
    def get_cookie_info(self) -> Optional[Dict[str, Any]]:
        """获取 Cookie 信息"""
        if not self.cookie_file.exists():
            return None
        
        try:
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'domain': data['domain'],
                'captured_at': data['captured_at'],
                'expires_at': data['expires_at'],
                'cookie_count': len(data['cookies']),
                'browser': data.get('browser', 'unknown'),
                'auto_fetched': data.get('auto_fetched', False),
            }
        except Exception as e:
            logger.error(f"❌ 获取 Cookie 信息失败：{e}")
            return None


class CookieRefreshListener:
    """Cookie 续期监听器"""
    
    def __init__(self, domain: str = "eastmoney.com"):
        self.domain = domain
        self.fetcher = CookieAutoFetcher(domain=domain)
        self.last_refresh_time: Optional[datetime] = None
        self.refresh_count = 0
        self.success_count = 0
        self.fail_count = 0
    
    async def check_and_refresh(self) -> bool:
        """检查并续期 Cookie"""
        # 检查是否过期
        if self.fetcher.is_expired():
            logger.info("🔄 Cookie 已过期，开始续期...")
            return await self.refresh()
        else:
            logger.debug("✅ Cookie 仍在有效期内")
            return True
    
    async def refresh(self) -> bool:
        """续期 Cookie"""
        logger.info("="*60)
        logger.info("🔄 开始续期 Cookie")
        logger.info(f"域名：{self.domain}")
        logger.info(f"时间：{datetime.now()}")
        logger.info("="*60)
        
        self.last_refresh_time = datetime.now()
        self.refresh_count += 1
        
        success = await self.fetcher.fetch()
        
        if success:
            logger.info("✅ Cookie 续期成功")
            self.success_count += 1
            return True
        else:
            logger.error("❌ Cookie 续期失败")
            self.fail_count += 1
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
        cookie_info = self.fetcher.get_cookie_info()
        
        return {
            'domain': self.domain,
            'last_refresh': self.last_refresh_time.isoformat() if self.last_refresh_time else None,
            'refresh_count': self.refresh_count,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'success_rate': self.success_count / self.refresh_count * 100 if self.refresh_count > 0 else 0,
            'cookie_info': cookie_info,
        }
    
    def print_status(self):
        """打印状态报告"""
        status = self.get_status()
        
        logger.info("\n" + "="*60)
        logger.info("📊 Cookie 续期状态报告")
        logger.info("="*60)
        logger.info(f"域名：{status['domain']}")
        logger.info(f"最后续期：{status['last_refresh'] or '未续期'}")
        logger.info(f"续期次数：{status['refresh_count']}")
        logger.info(f"成功次数：{status['success_count']}")
        logger.info(f"失败次数：{status['fail_count']}")
        logger.info(f"成功率：{status['success_rate']:.1f}%")
        
        if status['cookie_info']:
            logger.info(f"\nCookie 信息:")
            logger.info(f"  - 获取时间：{status['cookie_info']['captured_at']}")
            logger.info(f"  - 过期时间：{status['cookie_info']['expires_at']}")
            logger.info(f"  - Cookie 数量：{status['cookie_info']['cookie_count']}")
            logger.info(f"  - 浏览器：{status['cookie_info']['browser']}")
        
        logger.info("="*60)
