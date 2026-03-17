# 自选股功能使用说明

## ✅ 功能状态

自选股功能已完善并测试通过！所有 API 均可正常使用。

---

## 🔐 认证说明

自选股 API 需要登录后才能使用，采用 **Bearer Token** 认证方式。

### 获取 Token

**接口**：`POST /api/v1/auth/login`

**请求**：
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer"
}
```

---

## 📋 API 列表

### 1. 添加股票到自选股

**接口**：`POST /api/v1/watchlist/add`

**请求**：
```bash
POST /api/v1/watchlist/add
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "code": "000001",
  "note": "平安银行"
}
```

**响应**：
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "data": {
    "code": "000001",
    "note": "平安银行",
    "message": "添加成功"
  }
}
```

---

### 2. 获取自选股列表

**接口**：`GET /api/v1/watchlist/list`

**请求**：
```bash
GET /api/v1/watchlist/list
Authorization: Bearer <your_token>
```

**响应**：
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "data": [
    {
      "code": "000001",
      "note": "平安银行",
      "created_at": "2026-03-16 22:37:03",
      "updated_at": "2026-03-16 22:37:03"
    },
    {
      "code": "002378",
      "note": null,
      "created_at": "2026-03-16 22:34:44",
      "updated_at": "2026-03-16 22:34:44"
    }
  ]
}
```

---

### 3. 删除自选股

**接口**：`DELETE /api/v1/watchlist/remove/{code}`

**请求**：
```bash
DELETE /api/v1/watchlist/remove/000001
Authorization: Bearer <your_token>
```

**响应**：
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "data": {
    "code": "000001",
    "message": "删除成功"
  }
}
```

---

### 4. 更新自选股备注

**接口**：`PUT /api/v1/watchlist/update/{code}`

**请求**：
```bash
PUT /api/v1/watchlist/update/000001
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "note": "更新后的备注 - 平安银行"
}
```

**响应**：
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "data": {
    "code": "000001",
    "note": "更新后的备注 - 平安银行",
    "message": "更新成功"
  }
}
```

---

### 5. 获取自选股行情

**接口**：`GET /api/v1/watchlist/quotes`

**请求**：
```bash
GET /api/v1/watchlist/quotes
Authorization: Bearer <your_token>
```

**响应**：
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "data": [
    {
      "code": "000001",
      "date": "20260316",
      "open": 10.93,
      "high": 10.97,
      "low": 10.88,
      "close": 10.92,
      "volume": 715603.01,
      "amount": 782089441.0,
      "note": "更新后的备注 - 平安银行"
    },
    {
      "code": "002378",
      "name": "",
      "price": 0.0,
      "change": 0.0,
      "change_pct": 0.0,
      "high": 37.12,
      "low": 35.17,
      "open": 35.68,
      "volume": 940352.54,
      "amount": 3397998550.0,
      "note": null
    }
  ]
}
```

---

## 💻 前端使用示例

### JavaScript / TypeScript

```javascript
// 1. 登录获取 token
async function login() {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: 'admin',
      password: 'admin123'
    })
  });
  
  const data = await response.json();
  return data.access_token;
}

// 2. 添加股票到自选股
async function addToWatchlist(code, note) {
  const token = await login();
  
  const response = await fetch('http://localhost:8000/api/v1/watchlist/add', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ code, note })
  });
  
  return await response.json();
}

// 3. 获取自选股列表
async function getWatchlist() {
  const token = await login();
  
  const response = await fetch('http://localhost:8000/api/v1/watchlist/list', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// 4. 获取自选股行情
async function getWatchlistQuotes() {
  const token = await login();
  
  const response = await fetch('http://localhost:8000/api/v1/watchlist/quotes', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// 使用示例
(async () => {
  // 添加股票
  await addToWatchlist('000001', '平安银行');
  
  // 获取列表
  const watchlist = await getWatchlist();
  console.log(watchlist);
  
  // 获取行情
  const quotes = await getWatchlistQuotes();
  console.log(quotes);
})();
```

---

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """登录获取 token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]

def add_to_watchlist(code, note):
    """添加股票到自选股"""
    token = login()
    response = requests.post(
        f"{BASE_URL}/watchlist/add",
        json={"code": code, "note": note},
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def get_watchlist():
    """获取自选股列表"""
    token = login()
    response = requests.get(
        f"{BASE_URL}/watchlist/list",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def get_watchlist_quotes():
    """获取自选股行情"""
    token = login()
    response = requests.get(
        f"{BASE_URL}/watchlist/quotes",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 添加股票
    result = add_to_watchlist("000001", "平安银行")
    print(f"添加结果：{result}")
    
    # 获取列表
    watchlist = get_watchlist()
    print(f"自选股列表：{watchlist['data']}")
    
    # 获取行情
    quotes = get_watchlist_quotes()
    print(f"自选股行情：{quotes['data']}")
```

---

## 🧪 测试脚本

运行测试脚本验证所有功能：

```bash
python test_watchlist_api.py
```

**测试内容**：
1. ✅ 登录获取 Token
2. ✅ 添加股票到自选股
3. ✅ 获取自选股列表
4. ✅ 更新自选股备注
5. ✅ 获取自选股行情

---

## 📊 数据库表结构

**表名**：`watchlist`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| code | VARCHAR(10) | 股票代码（唯一） |
| note | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

## 🔧 后端实现

### 服务层

**文件**：`app/services/watchlist_service.py`

```python
class WatchlistService:
    async def get_watchlist(self) -> List[Dict[str, Any]]:
        """获取自选股列表"""
    
    async def add_to_watchlist(self, code: str, note: Optional[str] = None):
        """添加到自选股"""
    
    async def remove_from_watchlist(self, code: str):
        """从自选股删除"""
    
    async def update_watchlist_note(self, code: str, note: str):
        """更新自选股备注"""
    
    async def get_watchlist_quotes(self) -> List[Dict[str, Any]]:
        """获取自选股行情"""
```

### API 层

**文件**：`app/api/v1/endpoints/watchlist.py`

```python
@router.get("/list")
async def get_watchlist(current_user: CurrentUser = Depends):
    """获取自选股列表"""

@router.post("/add")
async def add_to_watchlist(
    code: str = Body(..., embed=True),
    note: str = Body(None, embed=True),
    current_user: CurrentUser = Depends
):
    """添加到自选股"""

@router.delete("/remove/{code}")
async def remove_from_watchlist(code: str, current_user: CurrentUser = Depends):
    """从自选股删除"""

@router.put("/update/{code}")
async def update_watchlist_note(
    code: str,
    note: str = Body(..., embed=True),
    current_user: CurrentUser = Depends
):
    """更新自选股备注"""

@router.get("/quotes")
async def get_watchlist_quotes(current_user: CurrentUser = Depends):
    """获取自选股行情"""
```

---

## ⚠️ 常见问题

### Q1: 401 错误 "未提供认证令牌"

**A**: 需要在请求头中添加 `Authorization: Bearer <token>`

**解决方案**：
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

### Q2: 添加股票失败

**A**: 检查：
1. 是否已登录获取 token
2. 股票代码格式是否正确（6 位数字）
3. 该股票是否已在自选股中（不能重复添加）

### Q3: 获取行情失败

**A**: 可能的原因：
1. 数据源不可用
2. 股票代码不存在
3. 网络问题

---

## 📚 相关文件

- **API 端点**：`app/api/v1/endpoints/watchlist.py`
- **服务层**：`app/services/watchlist_service.py`
- **数据库模型**：`app/storage/sqlite.py` (WatchlistDB 类)
- **测试脚本**：`test_watchlist_api.py`

---

## 🎯 功能特性

✅ **已实现功能**：
- 添加股票到自选股
- 删除自选股
- 更新自选股备注
- 获取自选股列表
- 获取自选股行情（实时）
- 用户认证保护
- 防止重复添加
- 数据持久化存储

🚀 **后续可扩展**：
- 批量添加/删除
- 分组管理
- 价格提醒
- 涨跌幅统计
- 导出功能

---

## 📝 更新日志

- **2026-03-16**: 完善自选股功能
  - ✅ 修复认证问题
  - ✅ 测试所有 API 端点
  - ✅ 创建使用文档
  - ✅ 创建测试脚本

---

**更新时间**：2026-03-16  
**测试状态**：✅ 全部通过  
**生产状态**：✅ 可用
