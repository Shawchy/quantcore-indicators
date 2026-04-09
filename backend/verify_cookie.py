"""
Cookie 验证工具

验证已获取的 Cookie 是否有效。
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger
import sys


async def verify_cookie_with_requests(cookie_file: Path) -> bool:
    """使用 requests 验证 Cookie"""
    try:
        # 加载 Cookie
        with open(cookie_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cookies = data.get('cookies', [])
        domain = data.get('domain', 'eastmoney.com')
        
        if not cookies:
            logger.error("❌ Cookie 文件为空")
            return False
        
        # 转换为 requests 格式
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']
        
        logger.info(f"✅ 加载了 {len(cookies)} 个 Cookie")
        
        # 显示关键 Cookie
        important_cookies = ['EM_HWhich', 'EM_sid', 'EM_uid', 'st']
        print("\n关键 Cookie:")
        for name in important_cookies:
            for cookie in cookies:
                if cookie['name'] == name:
                    value = cookie['value']
                    print(f"  - {name}: {value[:50]}{'...' if len(value) > 50 else ''}")
                    break
        
        # 发送测试请求
        logger.info("\n发送测试请求...")
        
        import requests
        
        test_url = f"https://www.{domain}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
        
        response = requests.get(test_url, headers=headers, cookies=cookie_dict, timeout=10)
        
        logger.info(f"响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Cookie 验证成功！")
            return True
        elif response.status_code == 403:
            logger.error("❌ Cookie 可能已过期或被封禁")
            return False
        else:
            logger.warning(f"⚠️  响应状态码：{response.status_code}")
            return response.status_code < 400
            
    except FileNotFoundError:
        logger.error(f"❌ Cookie 文件不存在：{cookie_file}")
        return False
    except Exception as e:
        logger.error(f"❌ 验证失败：{e}")
        return False


async def verify_cookie_with_curl_cffi(cookie_file: Path) -> bool:
    """使用 curl_cffi 验证 Cookie（更准确）"""
    try:
        from curl_cffi import requests
        
        # 加载 Cookie
        with open(cookie_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cookies = data.get('cookies', [])
        domain = data.get('domain', 'eastmoney.com')
        
        if not cookies:
            logger.error("❌ Cookie 文件为空")
            return False
        
        # 转换为 CookieJar
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']
        
        logger.info(f"✅ 加载了 {len(cookies)} 个 Cookie")
        
        # 发送测试请求
        logger.info("\n发送测试请求（使用 curl_cffi）...")
        
        test_url = f"https://www.{domain}"
        
        response = requests.get(
            test_url,
            impersonate='chrome120',
            cookies=cookie_dict,
            timeout=10
        )
        
        logger.info(f"响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Cookie 验证成功！")
            return True
        elif response.status_code == 403:
            logger.error("❌ Cookie 可能已过期或被封禁")
            return False
        else:
            logger.warning(f"⚠️  响应状态码：{response.status_code}")
            return response.status_code < 400
            
    except ImportError:
        logger.warning("⚠️  curl_cffi 未安装，跳过此验证")
        return None
    except Exception as e:
        logger.error(f"❌ 验证失败：{e}")
        return False


async def verify_all_cookies():
    """验证所有 Cookie 文件"""
    cookie_dir = Path("data/cookies")
    
    if not cookie_dir.exists():
        logger.error("❌ Cookie 目录不存在")
        return False
    
    cookie_files = list(cookie_dir.glob("*_manual.json")) + list(cookie_dir.glob("*_auto.json"))
    
    if not cookie_files:
        logger.warning("⚠️  未找到 Cookie 文件")
        print("\n提示:")
        print("1. 运行 cookie_helper.py 手动获取 Cookie")
        print("2. 或使用浏览器扩展导出 Cookie")
        return False
    
    logger.info(f"找到 {len(cookie_files)} 个 Cookie 文件")
    
    results = []
    for cookie_file in cookie_files:
        logger.info(f"\n验证：{cookie_file.name}")
        
        # 优先使用 curl_cffi 验证
        result = await verify_cookie_with_curl_cffi(cookie_file)
        
        # 如果 curl_cffi 不可用，使用 requests
        if result is None:
            result = await verify_cookie_with_requests(cookie_file)
        
        results.append((cookie_file.name, result))
    
    # 汇总结果
    print("\n" + "="*60)
    print("验证结果汇总")
    print("="*60)
    
    for name, result in results:
        status = "✅ 有效" if result else "❌ 无效"
        print(f"{status} - {name}")
    
    valid_count = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计：{valid_count}/{total} 个 Cookie 有效")
    
    return valid_count > 0


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔍 Cookie 验证工具")
    print("="*60)
    
    # 检查是否有指定的 Cookie 文件
    if len(sys.argv) > 1:
        cookie_file = Path(sys.argv[1])
        logger.info(f"验证指定文件：{cookie_file}")
        
        # 优先使用 curl_cffi
        result = await verify_cookie_with_curl_cffi(cookie_file)
        
        # 如果 curl_cffi 不可用，使用 requests
        if result is None:
            result = await verify_cookie_with_requests(cookie_file)
        
        success = result if result is not None else False
        
    else:
        # 验证所有 Cookie
        success = await verify_all_cookies()
    
    # 返回结果
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
