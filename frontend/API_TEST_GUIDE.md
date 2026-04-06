# API 调用测试指南

## 问题诊断

**当前错误**: "所有 API 请求失败"

**可能原因**:
1. 后端服务未启动
2. API 端点路径错误
3. 认证问题（需要登录）
4. 网络问题

---

## 测试步骤

### 1. 检查后端服务是否启动

```bash
cd m:\Project\Quant\backend
# 查看是否有运行的 uvicorn 进程
# 或者重新启动
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**预期日志**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     交易日历服务初始化完成
```

---

### 2. 直接测试 API 端点

使用浏览器或 Postman 测试：

#### 测试有效日期 API
```
GET http://localhost:8000/api/v1/screener/effective-date
```

**预期响应**:
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "success",
  "data": {
    "effective_date": "20260406",
    "is_today": true,
    "is_market_open": true,
    "latest_trading_day": "20260406",
    "previous_trading_day": "20260403",
    "current_time": "14:30:00"
  }
}
```

#### 测试交易日列表 API
```
GET http://localhost:8000/api/v1/screener/trading-days?limit=20
```

**预期响应**:
```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "success",
  "data": [
    {
      "date": "20260406",
      "display": "4 月 6 日",
      "is_today": true,
      "is_latest": true,
      "is_selected": true
    },
    ...
  ]
}
```

---

### 3. 检查前端配置

查看 `.env` 文件：

```bash
cd m:\Project\Quant\frontend
cat .env
```

**预期内容**:
```
VITE_API_BASE_URL=/api/v1
```

如果使用代理，检查 `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

---

### 4. 检查浏览器控制台

打开浏览器开发者工具（F12），查看：

1. **Console** 标签：查看 JavaScript 错误
2. **Network** 标签：查看 API 请求状态

**常见错误**:
- `404 Not Found`: API 路径错误
- `401 Unauthorized`: 需要登录
- `500 Internal Server Error`: 后端错误
- `ERR_CONNECTION_REFUSED`: 后端未启动

---

### 5. 检查认证

如果 API 需要认证，查看是否已登录：

```typescript
// 在浏览器控制台运行
console.log(localStorage.getItem('auth_token'))
```

如果返回 `null`，需要先登录。

---

## 修复内容

### 已修复的代码问题

**修复前**（错误）:
```typescript
const results = await Promise.all([
  screenerApi.getEffectiveDate(),
  screenerApi.getTradingDays(20),
  new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error('请求超时')), API_TIMEOUT)
  )
]).catch((error) => {
  return [null, null]
})
```

**问题**:
- `Promise.all` 包含 3 个 Promise
- `.catch()` 返回 `[null, null]`，但实际会返回 3 个值
- 解构赋值失败

**修复后**（正确）:
```typescript
const results = await Promise.race([
  Promise.all([
    screenerApi.getEffectiveDate(),
    screenerApi.getTradingDays(20)
  ]),
  new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error('请求超时')), API_TIMEOUT)
  )
])
```

**修复说明**:
- 使用 `Promise.race` 实现超时
- 内部使用 `Promise.all` 并行请求两个 API
- 返回正确的数组结构 `[EffectiveDateInfo, TradingDay[]]`

---

## 验证方法

### 启动后端
```bash
cd m:\Project\Quant\backend
python -m uvicorn app.main:app --reload
```

### 启动前端
```bash
cd m:\Project\Quant\frontend
npm run dev
```

### 预期行为
1. ✅ 前端成功加载
2. ✅ 日期选择器正常显示
3. ✅ 显示最近 20 个交易日
4. ✅ 无 JavaScript 错误
5. ✅ Network 标签显示 API 请求成功（状态码 200）

---

## 故障排查

### 问题 1: API 返回 404

**解决**:
- 检查后端路由配置
- 确认 API 路径：`/api/v1/screener/effective-date`
- 查看后端日志

### 问题 2: API 返回 401

**解决**:
- 先登录获取 Token
- 检查前端是否正确携带 Authorization header

### 问题 3: API 返回 500

**解决**:
- 查看后端日志
- 检查数据库连接
- 检查交易日历服务是否正常

### 问题 4: Connection Refused

**解决**:
- 确认后端已启动
- 检查端口是否正确（默认 8000）
- 检查防火墙设置

---

## 相关文件

- **前端组件**: `frontend/src/components/SmartDateSelector.tsx`
- **API 服务**: `frontend/src/services/api.ts`
- **后端路由**: `backend/app/api/v1/endpoints/screener.py`
- **后端服务**: `backend/app/services/trading_calendar.py`

---

**最后更新**: 2026-04-06  
**修复状态**: ✅ 已完成  
**测试状态**: ⏳ 待验证
