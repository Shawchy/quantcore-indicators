"""
Cookie 获取助手

提供手动获取 Cookie 的详细指南和验证工具。
"""

import json
from pathlib import Path
from datetime import datetime
import sys


def print_cookie_guide():
    """打印 Cookie 获取指南"""
    guide = """
╔══════════════════════════════════════════════════════════════╗
║                    Cookie 获取指南                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  方法 1: 使用浏览器开发者工具（推荐）                         ║
║  ────────────────────────────────────────────────────────    ║
║                                                              ║
║  1. 打开浏览器（Chrome/Edge/Firefox）                         ║
║  2. 访问：https://www.eastmoney.com                          ║
║  3. 按 F12 打开开发者工具                                     ║
║  4. 切换到 "Network" (网络) 标签                             ║
║  5. 刷新页面（F5）                                            ║
║  6. 点击任意请求                                              ║
║  7. 在 "Request Headers" (请求头) 中找到 "Cookie"             ║
║  8. 复制 Cookie 值                                            ║
║                                                              ║
║  方法 2: 使用浏览器扩展                                       ║
║  ────────────────────────────────────────────────────────    ║
║                                                              ║
║  1. 安装 Cookie 编辑扩展（如 "EditThisCookie"）               ║
║  2. 访问：https://www.eastmoney.com                          ║
║  3. 点击扩展图标                                              ║
║  4. 点击 "导出" -> "JSON"                                    ║
║  5. 复制 JSON 内容                                            ║
║                                                              ║
║  方法 3: 使用浏览器控制台                                     ║
║  ────────────────────────────────────────────────────────    ║
║                                                              ║
║  1. 访问：https://www.eastmoney.com                          ║
║  2. 按 F12 打开控制台                                         ║
║  3. 输入：document.cookie                                     ║
║  4. 复制输出的 Cookie 字符串                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(guide)


def validate_cookie(cookie_str: str) -> bool:
    """验证 Cookie 格式"""
    # 简单验证
    if not cookie_str or len(cookie_str) < 10:
        return False
    
    # 检查是否包含关键 Cookie
    important_keys = ['EM_', 'st', 'sid', 'uid']
    has_important = any(key in cookie_str for key in important_keys)
    
    return has_important


def save_cookie_manual(cookie_data, domain: str = "eastmoney.com"):
    """手动保存 Cookie"""
    cookie_file = Path("data/cookies") / f"{domain}_manual.json"
    
    # 确保目录存在
    cookie_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 准备数据
    data = {
        'domain': domain,
        'cookies': cookie_data,
        'captured_at': datetime.now().isoformat(),
        'expires_in_days': 7,
        'auto_fetched': False,
        'manual': True,
    }
    
    # 保存
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Cookie 已保存到：{cookie_file}")


def parse_cookie_string(cookie_str: str) -> list:
    """解析 Cookie 字符串为列表格式"""
    cookies = []
    
    # 分割 Cookie
    pairs = cookie_str.split('; ')
    
    for pair in pairs:
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': 'eastmoney.com',
                'path': '/',
            })
    
    return cookies


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🍪 Cookie 获取助手")
    print("="*60)
    
    # 打印指南
    print_cookie_guide()
    
    # 交互式获取
    print("\n请选择获取方式:")
    print("1. 粘贴 Cookie 字符串（从浏览器控制台）")
    print("2. 粘贴 Cookie JSON（从浏览器扩展）")
    print("3. 退出")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    if choice == '1':
        print("\n请粘贴 Cookie 字符串:")
        cookie_str = input("> ").strip()
        
        if validate_cookie(cookie_str):
            # 解析并保存
            cookies = parse_cookie_string(cookie_str)
            save_cookie_manual(cookies)
            
            print(f"\n✅ 成功保存 {len(cookies)} 个 Cookie")
            
            # 显示关键 Cookie
            important_cookies = ['EM_HWhich', 'EM_sid', 'EM_uid', 'st']
            print("\n关键 Cookie:")
            for name in important_cookies:
                for cookie in cookies:
                    if cookie['name'] == name:
                        value = cookie['value']
                        print(f"  - {name}: {value[:50]}{'...' if len(value) > 50 else ''}")
                        break
        else:
            print("\n❌ Cookie 格式不正确或缺少关键信息")
    
    elif choice == '2':
        print("\n请粘贴 Cookie JSON:")
        try:
            cookie_json = input("> ").strip()
            cookies = json.loads(cookie_json)
            
            if isinstance(cookies, list) and len(cookies) > 0:
                save_cookie_manual(cookies)
                print(f"\n✅ 成功保存 {len(cookies)} 个 Cookie")
            else:
                print("\n❌ Cookie JSON 格式不正确")
        except json.JSONDecodeError:
            print("\n❌ JSON 格式错误")
    
    elif choice == '3':
        print("\n👋 再见")
        sys.exit(0)
    else:
        print("\n❌ 无效选项")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Cookie 获取完成！")
    print("="*60)
    print("\n下一步:")
    print("1. 运行测试脚本验证 Cookie 是否有效")
    print("2. 反风控策略会自动使用保存的 Cookie")
    print("3. Cookie 有效期通常为 7 天，过期后请重新获取")
    print("\n" + "="*60)


if __name__ == "__main__":
    # 确保 data/cookies 目录存在
    Path("data/cookies").mkdir(parents=True, exist_ok=True)
    
    main()
