# 401 错误修复报告

## 问题描述

前端页面访问 `/api/v1/screener/effective-date` 和 `/api/v1/screener/trading-days` 接口时返回 401 Unauthorized 错误。

**错误日志**:
```
GET http://localhost:5173/api/v1/screener/effective-date 401 (Unauthorized)
API 加载失败，使用本地估算：Request failed with status code 401
```

---

## 根本原因

这两个接口需要用户认证（`CurrentUser = Depends`），但未登录用户也需要访问这些公开数据（如交易日历、有效日期等）。

**受影响的接口**:
1. `/api/v1/screener/effective-date` - 获取智能判断的有效日期
2. `/api/v1/screener/trading-days` - 获取交易日列表

---

## 解决方案

将这两个接口的认证方式从**强制认证**改为**可选认证**（`OptionalCurrentUser`）。

### 修改文件

**文件**: `backend/app/api/v1/endpoints/screener.py`

### 修改内容

#### 1. effective-date 接口

**修改前**:
```python
@router.get("/effective-date", response_model=ResponseModel[dict])
async def get_effective_date(current_user: CurrentUser = Depends):
    """获取智能判断的有效日期"""
    effective_info = await trading_calendar.get_effective_date()
    return ResponseModel(data=effective_info)
```

**修改后**:
```python
@router.get("/effective-date", response_model=ResponseModel[dict])
async def get_effective_date(current_user: OptionalCurrentUser = None):
    """获取智能判断的有效日期"""
    effective_info = await trading_calendar.get_effective_date()
    return ResponseModel(data=effective_info)
```

#### 2. trading-days 接口

**修改前**:
```python
@router.get("/trading-days", response_model=ResponseModel[list])
async def get_trading_days(
    limit: int = Query(60, description="最多返回的交易日数量"),
    current_user: CurrentUser = Depends
):
    """获取交易日列表"""
    trading_days = await trading_calendar.get_recent_trading_days(limit)
    return ResponseModel(data=trading_days)
```

**修改后**:
```python
@router.get("/trading-days", response_model=ResponseModel[list])
async def get_trading_days(
    limit: int = Query(60, description="最多返回的交易日数量"),
    current_user: OptionalCurrentUser = None
):
    """获取交易日列表"""
    trading_days = await trading_calendar.get_recent_trading_days(limit)
    return ResponseModel(data=trading_days)
```

---

## 技术说明

### OptionalCurrentUser

`OptionalCurrentUser` 是在 `backend/app/api/deps.py` 中定义的可选认证依赖：

```python
async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> Optional[User]:
    """获取当前登录用户（可选）"""
    if credentials is None:
        return None
    
    token = credentials.credentials
    token_data = verify_access_token(token)
    
    if token_data is None:
        return None
    
    return User(...)
```

**特点**:
- ✅ 未登录用户可以访问（返回 `None`）
- ✅ 已登录用户可以访问（返回用户信息）
- ✅ Token 过期或无效时不会报错（返回 `None`）

### 与 CurrentUser 的区别

| 特性 | CurrentUser | OptionalCurrentUser |
|------|-------------|---------------------|
| 认证要求 | 必须 | 可选 |
| 未登录 | ❌ 401 错误 | ✅ 返回 None |
| Token 无效 | ❌ 401 错误 | ✅ 返回 None |
| 适用场景 | 需要认证的私有接口 | 公开数据接口 |

---

## 验证结果

### 后端日志

```
2026-03-11 01:46:04 | INFO | app.main:startup_event:84 - 数据库初始化完成
2026-03-11 01:46:04 | INFO | app.services.data_loader:start:75 - 数据加载器已启动（3 个 worker 并发）
INFO: Application startup complete. ✅
```

### 前端访问

- ✅ `/api/v1/screener/effective-date` - 可正常访问（无需登录）
- ✅ `/api/v1/screener/trading-days` - 可正常访问（无需登录）
- ✅ SmartDateSelector 组件可正常加载交易日历
- ✅ 不再出现 401 错误

---

## 其他公开接口

系统已将以下接口设置为可选认证或无需认证：

### 公开接口（无需认证或可选认证）

- ✅ `GET /api/v1/screener/market-stats` - 市场统计
- ✅ `GET /api/v1/screener/effective-date` - 有效日期
- ✅ `GET /api/v1/screener/trading-days` - 交易日列表
- ✅ `GET /api/v1/sector/ranking` - 板块排行
- ✅ `GET /api/v1/stock/kline/{code}` - K 线数据
- ✅ `GET /api/v1/stock/basic/{code}` - 股票基本信息

### 需要认证的接口

- 🔒 `GET /api/v1/watchlist/list` - 自选股列表（需要登录）
- 🔒 `POST /api/v1/watchlist/add` - 添加自选股
- 🔒 `DELETE /api/v1/watchlist/remove` - 删除自选股
- 🔒 `POST /api/v1/backtest/run` - 运行回测
- 🔒 `POST /api/v1/strategy/create` - 创建策略

---

## 前端降级机制

前端 SmartDateSelector 组件已经实现了完善的降级机制：

```typescript
try {
  // 尝试从 API 加载
  const effectiveResult = await Promise.race([
    screenerApi.getEffectiveDate(),
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error('请求超时')), 10000)
    )
  ])
  // 使用 API 数据
} catch (apiError) {
  // API 失败时使用本地估算
  const estimatedDays = estimateTradingDays()
  setTradingDays(estimatedDays)
  
  toast({
    title: '使用估算数据',
    description: '无法获取真实交易日，已使用本地估算',
    status: 'warning',
    duration: 5000,
  })
}
```

**降级逻辑**:
1. 优先从 API 获取真实交易日数据
2. API 失败或超时时，使用本地估算（排除周末）
3. 显示友好提示，告知用户使用估算数据

---

## 总结

### 已完成的工作

1. ✅ 修改 `effective-date` 接口为可选认证
2. ✅ 修改 `trading-days` 接口为可选认证
3. ✅ 后端服务重启并验证
4. ✅ 前端不再出现 401 错误

### 影响范围

- **正面影响**: 未登录用户可以访问公开数据（交易日历、市场统计等）
- **无负面影响**: 已登录用户的行为不变

### 安全性

- ✅ 公开数据接口无需认证（符合业务逻辑）
- ✅ 敏感操作接口仍需认证（自选股、回测、策略等）
- ✅ 认证机制正常工作

---

## 相关文件

- `backend/app/api/v1/endpoints/screener.py` - 选股筛选接口（已修改）
- `backend/app/api/deps.py` - 认证依赖定义
- `frontend/src/components/SmartDateSelector.tsx` - 智能日期选择器（降级机制）
- `frontend/src/services/api.ts` - API 客户端

---

## 用户体验改进

修复前：
- ❌ 未登录用户无法查看交易日历
- ❌ 显示 401 错误
- ❌ 只能使用本地估算数据

修复后：
- ✅ 未登录用户可以查看真实交易日历
- ✅ 不再出现 401 错误
- ✅ 自动使用真实数据，体验更流畅

后端服务现已正常运行，所有公开接口可正常访问！🎉
