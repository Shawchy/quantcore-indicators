# 手动 Cookie 获取指南

## 为什么需要手动 Cookie？

**优势**：
- ✅ **零开销**：无需启动浏览器，启动时间从 3 秒降至 0.1 秒
- ✅ **高成功率**：真实用户登录，100% 绕过反爬
- ✅ **稳定性强**：不依赖浏览器自动化，无崩溃风险
- ✅ **维护简单**：只需每周更新一次

**适用场景**：
- ✅ 生产环境部署
- ✅ 高频数据请求
- ✅ 对启动时间敏感的场景

---

## 获取步骤

### 第一步：手动登录东方财富网

1. 打开 Chrome 浏览器（或 Edge）
2. 访问 **东方财富网**：https://www.eastmoney.com/
3. 如果需要，完成登录（部分数据无需登录）

**注意**：
- ✅ 目标网站是**东方财富网**（www.eastmoney.com）
- ❌ 不是天天基金网（fund.eastmoney.com，该网站不需要反爬）
- ✅ 东方财富网是综合财经门户，反爬策略主要针对该网站

### 第二步：打开开发者工具

1. 按 `F12` 打开开发者工具
2. 切换到 **Network（网络）** 标签页
3. 勾选 **Preserve log（保留日志）**

### 第三步：捕获请求

1. 刷新页面（`F5` 或 `Ctrl+R`）
2. 在 Network 标签页中找到任意请求（域名应包含 `eastmoney.com`）
3. 点击该请求

**正确示例**：
```
Request URL: https://www.eastmoney.com/
Request URL: https://data.eastmoney.com/...
Request URL: https://quote.eastmoney.com/...
```

**说明**：
- ✅ 东方财富网 Cookie 在整个 eastmoney.com 域名通用
- ✅ 获取的 Cookie 可以用于所有东方财富网子域名

### 第四步：复制 Cookie

1. 在右侧找到 **Request Headers（请求头）** 部分
2. 展开 **Cookie** 字段
3. 复制完整的 Cookie 字符串

示例：
```
Cookie: qgcookie=xxx; em_hq_fors=yyy; ASP.NET_SessionId=zzz; em-userid=aaa; em-username=bbb
```

### 第五步：解析 Cookie

将 Cookie 字符串解析为 JSON 格式。每个 Cookie 项的格式：

```json
{
  "name": "Cookie 名称",
  "value": "Cookie 值",
  "domain": ".eastmoney.com",
  "path": "/"
}
```

**常见 Cookie 字段说明**：

| Cookie 名称 | 说明 | 是否必须 |
|------------|------|---------|
| `qgcookie` | 全局 Cookie | ✅ 必须 |
| `em_hq_fors` | 行情 Cookie | ✅ 必须 |
| `ASP.NET_SessionId` | 会话 ID | ✅ 必须 |
| `em-userid` | 用户 ID | ⚠️ 可选（登录态） |
| `em-username` | 用户名 | ⚠️ 可选（登录态） |

---

## 配置文件格式

将解析后的 Cookie 保存到配置文件：

**文件路径**：`backend/data/cookies/eastmoney_com_manual.json`

**文件格式**：
```json
{
  "domain": "eastmoney.com",
  "cookies": [
    {
      "name": "qgcookie",
      "value": "从浏览器复制的值",
      "domain": ".eastmoney.com",
      "path": "/"
    },
    {
      "name": "em_hq_fors",
      "value": "从浏览器复制的值",
      "domain": ".eastmoney.com",
      "path": "/"
    },
    {
      "name": "ASP.NET_SessionId",
      "value": "从浏览器复制的值",
      "domain": ".eastmoney.com",
      "path": "/"
    }
  ],
  "captured_at": "2026-04-06T10:00:00",
  "expires_in_days": 7
}
```

**注意**：
- 文件名格式：`{域名}_manual.json`（域名中的 `.` 替换为 `_`）
- `captured_at`：ISO 8601 格式的时间戳
- `expires_in_days`：有效期（天），建议 7 天

---

## 快速解析工具

### 方法一：在线解析

访问：https://www.convertcsv.com/string-to-json.htm

1. 粘贴 Cookie 字符串
2. 选择解析方式
3. 导出 JSON

### 方法二：Python 脚本

使用提供的解析脚本：

```bash
python scripts/parse_cookie.py
```

**示例脚本**：

```python
# parse_cookie.py
import json
from datetime import datetime

def parse_cookie_string(cookie_str: str) -> list:
    """将 Cookie 字符串解析为标准格式"""
    cookies = []
    
    for item in cookie_str.split('; '):
        if '=' in item:
            name, value = item.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.eastmoney.com',
                'path': '/'
            })
    
    return cookies

# 使用示例
cookie_string = input("请输入 Cookie 字符串：")
cookies = parse_cookie_string(cookie_string)

# 生成配置文件
config = {
    'domain': 'eastmoney.com',
    'cookies': cookies,
    'captured_at': datetime.now().isoformat(),
    'expires_in_days': 7
}

# 保存到文件
with open('data/cookies/eastmoney_com_manual.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print("✅ Cookie 已保存到 data/cookies/eastmoney_com_manual.json")
```

### 方法三：使用内置工具（推荐）

```bash
# 运行内置工具
python scripts/save_manual_cookie.py
```

交互式输入 Cookie，自动生成配置文件。

---

## 验证 Cookie 有效性

### 方法一：查看日志

启动后端服务，查看日志：

```bash
python -m uvicorn app.main:app --reload
```

**预期输出**：
```
INFO - ✅ Level 0: 加载手动 Cookie 成功：eastmoney.com (过期时间：7 天)
INFO - 🚀 使用手动 Cookie 模式（零开销，推荐）
```

### 方法二：测试 API

```python
from app.adapters.factory import data_source_manager

# 获取板块列表
sectors = await data_source_manager.get_sector_list('industry')
print(f"板块数量：{len(sectors)}")
```

如果成功返回数据，说明 Cookie 有效。

### 方法三：检查状态

```python
from app.adapters.credential_injector import get_global_injector

injector = await get_global_injector()
status = injector.get_status()
print(status)
```

---

## Cookie 续期

### 自动检测过期

系统会自动检测 Cookie 过期：

- 过期前 1 小时：日志提醒
- 过期后：自动删除配置文件，降级到自动获取模式

### 手动续期

1. 重复上述获取步骤
2. 覆盖原有配置文件
3. 重启后端服务

### 自动续期（未来功能）

```python
# 启动 Cookie 监听器
from app.adapters.credential_injector import CookieMonitor

monitor = CookieMonitor(injector)
await monitor.start_monitoring(check_interval_minutes=60)
```

---

## 故障排查

### 问题 1：Cookie 加载失败

**症状**：
```
ERROR - 加载手动 Cookie 失败：...
```

**解决**：
1. 检查文件路径是否正确
2. 检查 JSON 格式是否正确
3. 检查文件名格式：`eastmoney_com_manual.json`

### 问题 2：Cookie 立即过期

**症状**：
```
WARNING - ⚠️  手动 Cookie 已过期：eastmoney.com，请重新获取
```

**解决**：
1. 检查 `captured_at` 时间是否正确
2. 检查 `expires_in_days` 是否合理（建议 7 天）
3. 重新获取 Cookie

### 问题 3：Cookie 无效

**症状**：
- API 返回 403 错误
- 提示"未登录"或"会话无效"

**解决**：
1. Cookie 可能已失效，重新获取
2. 检查是否缺少必要字段（qgcookie、em_hq_fors）
3. 尝试登录东方财富网后重新获取

---

## 最佳实践

### 1. 定期更新

- **频率**：每周一次
- **提醒**：设置日历提醒
- **自动化**：未来支持自动续期

### 2. 备份 Cookie

```bash
# 备份当前 Cookie
cp data/cookies/eastmoney_com_manual.json data/cookies/eastmoney_com_manual.json.backup
```

### 3. 多环境同步

**开发环境** → **生产环境**：

```bash
# 安全传输
scp data/cookies/eastmoney_com_manual.json user@server:/path/to/data/cookies/
```

**注意**：Cookie 包含敏感信息，请使用安全传输方式。

### 4. 监控成功率

```python
# 定期检查 API 成功率
success_rate = monitor_api_success_rate()
if success_rate < 90%:
    # 提醒更新 Cookie
    send_alert("Cookie 可能失效，请检查")
```

---

## 安全注意事项

### 1. 不要泄露 Cookie

- ❌ 不要提交到 Git
- ❌ 不要分享到公开论坛
- ❌ 不要发送给他人

### 2. 使用 .gitignore

确保 `.gitignore` 包含：

```gitignore
# Cookie 文件
data/cookies/*_manual.json
data/cookies/*.json
```

### 3. 生产环境安全

- ✅ 使用文件权限限制访问
- ✅ 加密存储敏感 Cookie
- ✅ 定期轮换 Cookie

---

## 常见问题

### Q1: Cookie 有效期多久？

A: 通常 7-30 天，具体取决于东方财富网的策略。建议每周更新一次。

### Q2: 需要登录才能获取 Cookie 吗？

A: 部分数据无需登录。但建议登录后获取，以获得完整权限。

### Q3: 多个域名需要分别获取吗？

A: 是的。每个域名（如 `eastmoney.com`、`fund.eastmoney.com`）需要分别获取。

### Q4: 可以自动化获取吗？

A: 可以，但不推荐。自动化获取可能被反爬机制检测，手动获取更可靠。

### Q5: Cookie 失效了怎么办？

A: 系统会自动降级到 Playwright 或 curl_cffi 模式，不影响使用。

---

## 相关文档

- [反爬策略优化方案 2026](./ANTI_WIND_OPTIMIZATION_2026.md)
- [凭证注入状态报告](./CREDENTIAL_INJECTION_STATUS.md)
- [反风控策略完整实施](./ANTI_WIND_STRATEGY_COMPLETE.md)

---

**最后更新**: 2026-04-06  
**维护者**: Quant Platform Team
