# 快速获取 Cookie - 天天基金网

## 🎯 目标网站

**东方财富网**：https://www.eastmoney.com/

✅ **说明**：
- 东方财富网是综合财经门户（需要反爬策略）
- 天天基金网（fund.eastmoney.com）不需要反爬
- 获取的 Cookie 在整个 eastmoney.com 域名通用

---

## 📝 3 分钟快速获取 Cookie

### 步骤 1：访问网站（30 秒）

1. 打开 Chrome 或 Edge 浏览器
2. 访问：**https://www.eastmoney.com/**
3. 看到东方财富网首页即正确

**验证是否正确**：
- ✅ 页面标题包含"东方财富网"
- ✅ 网址是 `www.eastmoney.com`
- ✅ 页面显示股票、财经新闻等信息

---

### 步骤 2：打开开发者工具（30 秒）

1. 按键盘 `F12`（或右键 → 检查）
2. 点击 **Network**（网络）标签
3. 勾选 **Preserve log**（保留日志）

---

### 步骤 3：刷新页面并复制 Cookie（1 分钟）

1. 按 `F5` 刷新页面
2. 在 Network 标签中找到任意请求
3. 点击该请求
4. 在右侧找到 **Request Headers**（请求头）
5. 找到 **Cookie** 字段
6. 复制完整的 Cookie 字符串

**正确的请求 URL 示例**：
```
https://www.eastmoney.com/
https://data.eastmoney.com/...
https://quote.eastmoney.com/...
```

**说明**：
- ✅ 所有 eastmoney.com 域名的 Cookie 都是通用的
- ✅ 获取的 Cookie 可以用于东方财富网所有子域名

---

### 步骤 4：保存 Cookie（1 分钟）

1. 打开文件：`backend/data/cookies/eastmoney_com_manual.json`
2. 如果没有该文件，复制示例文件：
   ```bash
   cp data/cookies/eastmoney_com_manual.json.example data/cookies/eastmoney_com_manual.json
   ```
3. 编辑文件，将 Cookie 值填入

**Cookie 字符串格式示例**：
```
qgcookie=xxx; em_hq_fors=yyy; ASP.NET_SessionId=zzz; em-userid=aaa; em-username=bbb
```

**JSON 格式示例**：
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
    }
  ],
  "captured_at": "2026-04-06T10:00:00",
  "expires_in_days": 7
}
```

---

## ✅ 验证是否成功

### 方法 1：查看启动日志

```bash
python -m uvicorn app.main:app --reload
```

**成功日志**：
```
INFO - ✅ Level 0: 加载手动 Cookie 成功：eastmoney.com (过期时间：7 天)
INFO - 🚀 使用手动 Cookie 模式（零开销，推荐）
```

### 方法 2：测试 API

```python
from app.adapters.factory import data_source_manager

# 获取板块列表
sectors = await data_source_manager.get_sector_list('industry')
print(f"✅ 板块数量：{len(sectors)}")
```

---

## ⚠️ 常见问题

### Q1: Cookie 文件应该放在哪里？

**A**: `backend/data/cookies/eastmoney_com_manual.json`

完整路径示例：
```
m:\Project\Quant\backend\data\cookies\eastmoney_com_manual.json
```

### Q2: Cookie 有效期多久？

**A**: 通常 7-30 天。建议每周更新一次。

### Q3: 需要登录吗？

**A**: 部分数据无需登录。但建议登录后获取完整权限。

### Q4: 如何判断 Cookie 已过期？

**A**: 系统会自动检测并提示：
```
WARNING - ⚠️  手动 Cookie 已过期：eastmoney.com，请重新获取
```

### Q5: Cookie 失效了怎么办？

**A**: 
1. 系统会自动降级到 Playwright 或 curl_cffi 模式
2. 重新获取 Cookie 并更新文件

---

## 📸 截图示意

### 正确的网站
```
网址：https://www.eastmoney.com/
标题：东方财富网：财经门户，提供专业的财经、股票、行情、证券...
```

### Network 标签页
```
[✓] Preserve log
Name: GetFundNewsList
Method: GET
Status: 200
```

### Request Headers
```
Cookie: qgcookie=xxx; em_hq_fors=yyy; ASP.NET_SessionId=zzz
        ↑ 复制这里的内容
```

---

## 🔗 相关文档

- [完整 Cookie 获取指南](./MANUAL_COOKIE_GUIDE.md)
- [反爬策略优化报告](./ANTI_WIND_OPTIMIZATION_REPORT_2026.md)

---

**最后更新**: 2026-04-06  
**维护者**: Quant Platform Team
