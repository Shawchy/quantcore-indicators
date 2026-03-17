# 自选股 API 快速参考

## 🔐 认证

所有自选股 API 需要 Bearer Token 认证。

**获取 Token**：
```bash
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "admin123"
}
```

**使用 Token**：
```bash
Authorization: Bearer <your_token>
```

---

## 📋 API 端点

### 添加股票
```bash
POST /api/v1/watchlist/add
{
  "code": "000001",
  "note": "平安银行"
}
```

### 获取列表
```bash
GET /api/v1/watchlist/list
```

### 删除股票
```bash
DELETE /api/v1/watchlist/remove/{code}
```

### 更新备注
```bash
PUT /api/v1/watchlist/update/{code}
{
  "note": "新备注"
}
```

### 获取行情
```bash
GET /api/v1/watchlist/quotes
```

---

## 💻 代码示例

### JavaScript
```javascript
const token = await login();

// 添加股票
await fetch('/api/v1/watchlist/add', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ code: '000001', note: '平安银行' })
});

// 获取列表
const list = await fetch('/api/v1/watchlist/list', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 获取行情
const quotes = await fetch('/api/v1/watchlist/quotes', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### Python
```python
token = login()

# 添加股票
requests.post(
    '/api/v1/watchlist/add',
    json={'code': '000001', 'note': '平安银行'},
    headers={'Authorization': f'Bearer {token}'}
)

# 获取列表
requests.get('/api/v1/watchlist/list',
    headers={'Authorization': f'Bearer {token}'}
)

# 获取行情
requests.get('/api/v1/watchlist/quotes',
    headers={'Authorization': f'Bearer {token}'}
)
```

---

## 🧪 测试

```bash
python test_watchlist_api.py
```

---

## 📊 响应格式

**成功**：
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "data": {...}
}
```

**失败**：
```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "错误信息"
}
```

---

## 📁 相关文件

- 完整文档：[WATCHLIST_API_GUIDE.md](WATCHLIST_API_GUIDE.md)
- 测试脚本：[test_watchlist_api.py](test_watchlist_api.py)

---

**最后更新**：2026-03-16
