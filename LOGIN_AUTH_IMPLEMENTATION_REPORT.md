# 登录功能实现检查报告

## 📋 执行摘要

**检查日期**: 2026-03-10  
**检查范围**: 前端 + 后端完整登录认证流程  

### 核心发现

| 模块 | 状态 | 完成度 |
|------|------|--------|
| **后端认证 API** | ✅ 已实现 | 95% |
| **后端 JWT 认证** | ✅ 已实现 | 100% |
| **后端权限控制** | ⚠️ 部分实现 | 60% |
| **前端登录页面** | ❌ 未实现 | 0% |
| **前端认证状态管理** | ❌ 未实现 | 0% |
| **前端认证 API 封装** | ❌ 未实现 | 0% |
| **前端路由守卫** | ❌ 未实现 | 0% |

**结论**: 后端认证系统已基本就绪，但**前端完全没有实现登录功能**。系统目前所有页面都是公开访问的，没有任何认证保护。

---

## 🔐 后端认证系统检查

### 1. 核心文件结构

```
backend/
├── app/
│   ├── core/
│   │   └── security.py          ✅ JWT 认证核心（完整）
│   ├── api/
│   │   ├── deps.py              ✅ 依赖注入（完整）
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── auth.py      ✅ 认证端点（完整）
│   │       └── endpoints/
│   │           ├── stock.py     ⚠️  未添加认证保护
│   │           ├── sector.py    ⚠️  未添加认证保护
│   │           └── ...          ⚠️  未添加认证保护
│   └── config.py                ✅ JWT 配置（完整）
```

### 2. 后端认证功能详情

#### ✅ 已实现功能

**认证端点** ([`auth.py`](d:\Project\Quant\backend\app\api\v1\endpoints\auth.py)):

| 端点 | 方法 | 功能 | 状态 |
|------|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 | ✅ 完成 |
| `/api/v1/auth/refresh` | POST | 刷新令牌 | ✅ 完成 |
| `/api/v1/auth/me` | GET | 获取当前用户信息 | ✅ 完成 |
| `/api/v1/auth/logout` | POST | 用户登出 | ✅ 完成 |

**JWT 令牌管理** ([`security.py`](d:\Project\Quant\backend\app\core\security.py)):

- ✅ Access Token (24 小时有效期)
- ✅ Refresh Token (7 天有效期)
- ✅ 令牌生成 (`create_access_token`, `create_refresh_token`)
- ✅ 令牌验证 (`verify_access_token`, `verify_refresh_token`)
- ✅ 令牌解码 (`decode_token`)
- ✅ 密码加密 (`bcrypt`)

**依赖注入** ([`deps.py`](d:\Project\Quant\backend\app\api\deps.py)):

- ✅ `get_current_user` - 获取当前用户
- ✅ `get_current_active_user` - 获取活跃用户
- ✅ `get_current_admin_user` - 获取管理员用户
- ✅ HTTP Bearer 认证

**默认测试账户**:

```python
# 管理员账户
用户名：admin
密码：admin123
角色：admin

# 普通用户账户
用户名：user
密码：user123
角色：user
```

#### ⚠️ 存在的问题

**1. 业务端点未强制认证**

当前所有业务接口（股票、板块、策略等）**都没有添加认证保护**：

```python
# stock.py - 没有认证保护
@router.get("/basic/{code}")
async def get_stock_basic(code: str):
    data = await stock_service.get_stock_basic(code)
    return ResponseModel(data=data)
```

**应该改为**:

```python
from app.api.deps import CurrentUser

@router.get("/basic/{code}")
async def get_stock_basic(code: str, current_user: CurrentUser):
    data = await stock_service.get_stock_basic(code)
    return ResponseModel(data=data)
```

**2. 使用模拟用户数据库**

[`security.py`](d:\Project\Quant\backend\app\core\security.py#L128-L146) 使用硬编码的用户数据：

```python
fake_users_db = {
    "admin": {
        "user_id": 1,
        "username": "admin",
        "password": get_password_hash("admin123"),
        "role": "admin"
    },
    "user": {...}
}
```

**生产环境需要**:
- 创建用户表（数据库）
- 实现用户注册功能
- 实现密码找回功能

**3. 密码验证逻辑简化**

[`authenticate_user`](d:\Project\Quant\backend\app\core\security.py#L157-L171) 函数使用硬编码验证：

```python
async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await get_user(username)
    if not user:
        return None
    
    # 硬编码验证（问题）
    if username == "admin" and password == "admin123":
        return user
    elif username == "user" and password == "user123":
        return user
    
    return None
```

**应该改为**:

```python
async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await get_user(username)
    if not user:
        return None
    
    # 从数据库获取密码哈希并验证
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
```

**4. 缺少令牌黑名单机制**

登出功能只是记录日志，没有真正使令牌失效：

```python
@router.post("/logout")
async def logout(current_user: CurrentUser):
    logger.info(f"用户 {current_user.username} 登出")
    return {"message": "登出成功"}
```

**建议**: 使用 Redis 实现令牌黑名单，在令牌过期前阻止其再次使用。

---

## 🎨 前端认证系统检查

### 1. 前端文件结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.tsx           ⚠️  有登录 UI 但无功能
│   │   └── Layout.tsx           ✅ 布局组件
│   ├── pages/
│   │   ├── Dashboard.tsx        ⚠️  无路由保护
│   │   ├── StockDetail.tsx      ⚠️  无路由保护
│   │   └── ...                  ⚠️  所有页面无保护
│   ├── services/
│   │   └── api.ts               ❌ 缺少认证 API 封装
│   ├── store/
│   │   ├── index.ts             ❌ 无认证状态
│   │   └── slices/
│   │       └── appSlice.ts      ❌ 无用户状态
│   └── App.tsx                  ❌ 无路由守卫
```

### 2. 前端缺失的功能

#### ❌ 1. 登录页面组件

**现状**: 完全不存在登录页面

**需要创建**:
- `pages/Login.tsx` - 登录页面
- `components/LoginForm.tsx` - 登录表单（可选）

**应包含功能**:
- 用户名/密码输入框
- 表单验证
- 错误提示
- 登录按钮
- "记住我"选项（可选）

#### ❌ 2. 认证状态管理

**现状**: Redux store 中没有任何认证相关状态

[`store/index.ts`](d:\Project\Quant\frontend\src\store\index.ts):
```typescript
export const store = configureStore({
  reducer: {
    app: appReducer,  // 只有应用状态
  },
})
```

[`appSlice.ts`](d:\Project\Quant\frontend\src\store\slices\appSlice.ts):
```typescript
interface AppState {
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  searchKeyword: string
  // ❌ 缺少：user, token, isAuthenticated
}
```

**需要创建** `authSlice`:
```typescript
interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}
```

#### ❌ 3. 认证 API 封装

**现状**: [`api.ts`](d:\Project\Quant\frontend\src\services\api.ts) 中没有认证相关 API

**当前 API 列表**:
- ✅ `stockApi` - 股票信息
- ✅ `watchlistApi` - 自选股
- ✅ `sectorApi` - 板块分析
- ✅ `chipApi` - 筹码选股
- ✅ `screenerApi` - 选股筛选
- ✅ `strategyApi` - 策略管理
- ✅ `backtestApi` - 回测系统
- ❌ **缺少 `authApi`**

**需要添加**:
```typescript
export const authApi = {
  login: (username: string, password: string) => 
    api.post('/auth/login', { username, password }),
  
  logout: () => api.post('/auth/logout'),
  
  refreshToken: (refreshToken: string) => 
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: () => api.get('/auth/me'),
}
```

#### ❌ 4. HTTP 请求拦截器

**现状**: 只有响应拦截器，没有请求拦截器

[`api.ts`](d:\Project\Quant\frontend\src\services\api.ts#L11-L17):
```typescript
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)
// ❌ 缺少请求拦截器（自动添加 Token）
// ❌ 缺少 401 错误处理（Token 过期自动刷新）
```

**需要添加**:
```typescript
// 请求拦截器 - 自动携带 Token
api.interceptors.request.use(
  (config) => {
    const state = store.getState()
    const token = state.auth.token
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理 401 错误
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token 过期，尝试刷新
      // 或者跳转到登录页
    }
    return Promise.reject(error)
  }
)
```

#### ❌ 5. 路由守卫

**现状**: 所有路由都是公开的

[`App.tsx`](d:\Project\Quant\frontend\src\App.tsx):
```typescript
<Routes>
  <Route path="/" element={<Layout />}>
    <Route index element={<Dashboard />} />
    <Route path="stock/:code" element={<StockDetail />} />
    // ❌ 所有页面都没有保护
  </Route>
</Routes>
```

**需要实现**:
```typescript
// 受保护的路由组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAppSelector(state => state.auth)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

// 使用
<Routes>
  <Route path="/login" element={<Login />} />
  <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
    <Route index element={<Dashboard />} />
    // ...
  </Route>
</Routes>
```

#### ⚠️ 6. Header 组件的登录 UI

**现状**: 有登录相关的 UI，但没有实际功能

[`Header.tsx`](d:\Project\Quant\frontend\src\components\Header.tsx#L123-L158):
```tsx
<Menu>
  <MenuButton>
    <Avatar icon={<FiUser />} />  // 用户头像
  </MenuButton>
  <MenuList>
    <MenuItem icon={<FiUser />}>个人中心</MenuItem>
    <MenuItem icon={<FiSettings />}>系统设置</MenuItem>
    <MenuItem 
      icon={<FiLogOut />} 
      color="red.500"
    >
      退出登录  // ❌ 点击无反应
    </MenuItem>
  </MenuList>
</Menu>
```

**问题**:
- 用户信息是硬编码的（头像图标）
- 没有登录/登出功能实现
- 没有权限控制

---

## 🔍 完整登录流程分析

### 理想的登录流程

```
1. 用户访问系统
   ↓
2. 检查是否已登录（本地存储 Token）
   ↓ 未登录
3. 重定向到登录页
   ↓
4. 用户输入用户名密码
   ↓
5. 调用 /api/v1/auth/login
   ↓
6. 后端验证并返回 Token
   ↓
7. 前端存储 Token 和用户信息
   ↓
8. 重定向到首页
   ↓
9. 后续请求自动携带 Token（请求拦截器）
   ↓
10. Token 过期时自动刷新（401 处理）
```

### 当前系统状态

```
1. 用户访问系统
   ↓
✅ 直接进入首页（无认证检查）
   ↓
✅ 所有页面都可访问（无路由保护）
   ↓
✅ API 请求不携带 Token（无请求拦截器）
   ↓
✅ 后端业务接口不验证 Token（无认证依赖）
```

**结论**: 系统目前处于**完全开放状态**，没有任何认证保护。

---

## 📝 需要实现的功能清单

### 后端（优先级：高）

#### 1. 为业务端点添加认证保护

**文件**: 所有 `backend/app/api/v1/endpoints/*.py`

```python
# 示例：stock.py
from app.api.deps import CurrentUser

@router.get("/basic/{code}")
async def get_stock_basic(code: str, current_user: CurrentUser):
    # current_user 会自动验证 Token
    data = await stock_service.get_stock_basic(code)
    return ResponseModel(data=data)
```

**影响文件**:
- `stock.py` - 5 个端点
- `sector.py` - 4 个端点
- `chip.py` - 4 个端点
- `screener.py` - 4 个端点
- `strategy.py` - 6 个端点
- `backtest.py` - 6 个端点
- `watchlist.py` - 5 个端点

**总计**: 约 34 个端点需要添加认证

#### 2. 修复密码验证逻辑

**文件**: [`security.py`](d:\Project\Quant\backend\app\core\security.py#L157-L171)

```python
async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await get_user(username)
    if not user:
        return None
    
    # 使用 verify_password 函数
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
```

#### 3. 实现令牌黑名单机制（可选）

**建议使用 Redis**:
```python
# 登出时将 Token 加入黑名单
@router.post("/logout")
async def logout(current_user: CurrentUser, token: str = Depends(get_token)):
    expire_time = decode_token(token).exp
    await redis.setex(f"blacklist:{token}", expire_time - time.time(), 1)
    return {"message": "登出成功"}
```

#### 4. 创建数据库用户表

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 前端（优先级：高）

#### 1. 创建认证状态管理

**文件**: `src/store/slices/authSlice.ts` (新建)

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { authApi } from '../../services/api'

interface User {
  user_id: number
  username: string
  email?: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,
}

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }: { username: string; password: string }) => {
    const response = await authApi.login(username, password)
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    return response
  }
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      state.user = null
      state.token = null
      state.refreshToken = null
      state.isAuthenticated = false
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false
        state.token = action.payload.access_token
        state.refreshToken = action.payload.refresh_token
        state.isAuthenticated = true
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || '登录失败'
      })
  },
})

export const { logout } = authSlice.actions
export default authSlice.reducer
```

**更新**: `src/store/index.ts`

```typescript
import { configureStore } from '@reduxjs/toolkit'
import appReducer from './slices/appSlice'
import authReducer from './slices/authSlice'  // 新增

export const store = configureStore({
  reducer: {
    app: appReducer,
    auth: authReducer,  // 新增
  },
})
```

#### 2. 创建登录页面

**文件**: `src/pages/Login.tsx` (新建)

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../store/hooks'
import { login } from '../store/slices/authSlice'
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Input,
  Heading,
  Text,
  Alert,
  AlertIcon,
} from '@chakra-ui/react'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { isLoading, error } = useAppSelector((state) => state.auth)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      await dispatch(login({ username, password })).unwrap()
      navigate('/')  // 登录成功跳转到首页
    } catch (err) {
      // 错误已在 authSlice 中处理
    }
  }

  return (
    <Container maxW="md">
      <Box 
        bg="light.card" 
        p={8} 
        borderRadius="xl"
        boxShadow="lg"
        mt={20}
      >
        <Heading textAlign="center" mb={8}>
          量化分析系统
        </Heading>
        
        {error && (
          <Alert status="error" mb={4}>
            <AlertIcon />
            {error}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <FormControl mb={4}>
            <FormLabel>用户名</FormLabel>
            <Input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
            />
          </FormControl>
          
          <FormControl mb={6}>
            <FormLabel>密码</FormLabel>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
            />
          </FormControl>
          
          <Button
            type="submit"
            colorScheme="blue"
            width="full"
            isLoading={isLoading}
          >
            登录
          </Button>
        </form>
      </Box>
    </Container>
  )
}

export default Login
```

#### 3. 添加认证 API 封装

**文件**: 更新 `src/services/api.ts`

```typescript
// 新增 authApi
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  logout: () => api.post('/auth/logout'),
  
  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: () => api.get('/auth/me'),
}
```

**添加请求拦截器**:

```typescript
// 在 api.ts 开头添加
import { store } from '../store'

// 请求拦截器 - 自动携带 Token
api.interceptors.request.use(
  (config) => {
    const state = store.getState()
    const token = state.auth.token
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理 401 错误
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      // 尝试刷新 Token
      const state = store.getState()
      const refreshToken = state.auth.refreshToken
      
      if (refreshToken) {
        try {
          const response = await authApi.refreshToken(refreshToken)
          store.dispatch({
            type: 'auth/tokenRefreshed',
            payload: response.access_token,
          })
          
          originalRequest.headers.Authorization = `Bearer ${response.access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          // 刷新失败，跳转到登录页
          store.dispatch({ type: 'auth/logout' })
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }
    
    return Promise.reject(error)
  }
)
```

#### 4. 实现路由守卫

**文件**: 更新 `src/App.tsx`

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAppSelector } from './store/hooks'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
// ... 其他页面导入

// 受保护的路由组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAppSelector((state) => state.auth)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 公开路由 */}
        <Route path="/login" element={<Login />} />
        
        {/* 受保护的路由 */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="stock/:code" element={<StockDetail />} />
          <Route path="watchlist" element={<Watchlist />} />
          <Route path="sector" element={<SectorAnalysis />} />
          <Route path="chip" element={<ChipSelection />} />
          <Route path="screener" element={<Screener />} />
          <Route path="strategy" element={<Strategy />} />
          <Route path="backtest" element={<Backtest />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

#### 5. 更新 Header 组件

**文件**: 更新 `src/components/Header.tsx`

```tsx
import { useAppDispatch, useAppSelector } from '../store/hooks'
import { logout } from '../store/slices/authSlice'

const Header = ({ onMenuClick }: HeaderProps) => {
  const dispatch = useAppDispatch()
  const { user, isAuthenticated } = useAppSelector((state) => state.auth)
  const navigate = useNavigate()

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  return (
    // ... 其他代码
    
    <Menu>
      <MenuButton>
        <Avatar 
          size="sm" 
          name={user?.username}  // 显示用户名
          icon={<FiUser />}
          bg="brand.500"
          color="white"
        />
      </MenuButton>
      <MenuList>
        <MenuItem icon={<FiUser />}>
          {user?.username || '个人中心'}
        </MenuItem>
        <MenuItem icon={<FiSettings />}>
          系统设置
        </MenuItem>
        <MenuItem 
          icon={<FiLogOut />} 
          onClick={handleLogout}  // 添加点击事件
          color="red.500"
        >
          退出登录
        </MenuItem>
      </MenuList>
    </Menu>
  )
}
```

---

## 🎯 实施建议

### 第一阶段：后端认证保护（1-2 天）

1. ✅ 修复 `authenticate_user` 函数
2. ⬜ 为所有业务端点添加 `CurrentUser` 依赖
3. ⬜ 测试认证流程

### 第二阶段：前端基础认证（2-3 天）

1. ⬜ 创建 `authSlice`
2. ⬜ 创建登录页面
3. ⬜ 添加认证 API 封装
4. ⬜ 添加请求拦截器

### 第三阶段：前端路由保护（1 天）

1. ⬜ 实现路由守卫
2. ⬜ 更新 Header 组件
3. ⬜ 测试登录流程

### 第四阶段：功能完善（可选）

1. ⬜ 实现令牌黑名单
2. ⬜ 创建数据库用户表
3. ⬜ 实现用户注册功能
4. ⬜ 添加密码找回功能
5. ⬜ 实现记住我功能

---

## 📊 测试清单

### 后端测试

- [ ] 登录接口（正确凭证）
- [ ] 登录接口（错误凭证）
- [ ] Token 刷新接口
- [ ] 获取用户信息接口
- [ ] 登出接口
- [ ] 业务接口（无 Token）
- [ ] 业务接口（有效 Token）
- [ ] 业务接口（过期 Token）

### 前端测试

- [ ] 登录页面显示
- [ ] 登录表单验证
- [ ] 登录成功跳转
- [ ] 登录失败提示
- [ ] Token 自动携带
- [ ] Token 过期自动刷新
- [ ] 路由守卫生效
- [ ] 登出功能
- [ ] 页面刷新保持登录状态

---

## 🔚 总结

### 当前状态

- ✅ **后端认证系统**: 基本完成，但业务接口未添加保护
- ❌ **前端认证系统**: 完全没有实现

### 风险评估

**高风险**:
1. 所有业务接口目前都是公开的，任何人都可以访问
2. 没有用户权限控制
3. 敏感数据（股票数据、策略等）无保护

### 建议

**立即实施**:
1. 为后端业务接口添加认证保护
2. 实现前端登录功能
3. 添加路由守卫

**生产环境必须**:
1. 修改 `SECRET_KEY`（环境变量）
2. 修改默认用户密码
3. 实现数据库用户存储
4. 启用 HTTPS

---

**报告生成时间**: 2026-03-10  
**检查人员**: AI Assistant  
**版本**: v1.0
