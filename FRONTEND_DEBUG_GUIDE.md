# 前端登录界面调试指南

**问题**: 前端已启动但登录界面未显示  
**前端地址**: http://localhost:5174/  
**后端地址**: http://127.0.0.1:8000  

---

## 🔍 调试步骤

### 步骤 1: 检查浏览器访问

**请确认访问地址**: `http://localhost:5174/` (注意是 **5174** 端口)

**常见错误**:
- ❌ 访问了 `http://localhost:5173/` (错误端口)
- ❌ 访问了 `http://127.0.0.1:8000/` (后端地址)
- ✅ 正确：`http://localhost:5174/`

---

### 步骤 2: 打开浏览器开发者工具

**按 F12** 或 **右键 → 检查**

#### 2.1 检查 Console 面板

查看是否有以下错误：

**红色错误 (严重)**:
```
❌ Failed to load resource: net::ERR_CONNECTION_REFUSED
❌ Uncaught Error: Cannot find module
❌ React Router 错误
❌ Redux 错误
```

**黄色警告 (注意)**:
```
⚠️ React development mode warning
⚠️ ESLint warnings
```

#### 2.2 检查 Network 面板

1. 刷新页面 (F5)
2. 查看请求列表
3. 检查是否有失败的请求

**预期**:
- ✅ `localhost:5174/` - 状态码 200
- ✅ `localhost:5174/src/main.tsx` - 状态码 200
- ✅ `localhost:5174/src/App.tsx` - 状态码 200

---

### 步骤 3: 检查后端连接

**在浏览器中访问**: `http://localhost:8000/docs`

**预期**:
- ✅ 显示 Swagger API 文档
- ❌ 如果无法访问，说明后端未正确启动

**测试 API**:
```bash
# 在浏览器或 curl 测试
http://localhost:8000/api/v1/auth/login
```

---

### 步骤 4: 清除缓存

**Chrome/Edge**:
1. 按 `Ctrl + Shift + Delete`
2. 选择"缓存的图片和文件"
3. 点击"清除数据"

**或者使用无痕模式**:
- `Ctrl + Shift + N` (Chrome)
- `Ctrl + Shift + P` (Firefox)

---

### 步骤 5: 检查本地存储

**开发者工具 → Application → Local Storage**:

**检查内容**:
- 是否有 `access_token` 或 `refresh_token`
- 如果有，清除它们（可能 token 过期导致问题）

---

## 🐛 常见问题及解决方案

### 问题 1: 页面完全空白

**可能原因**:
1. JavaScript 错误
2. React 渲染失败
3. CSS 问题

**解决方案**:
```bash
# 重启前端服务
# 在终端按 Ctrl+C 停止
cd frontend
npm run dev
```

---

### 问题 2: 一直显示"加载中..."

**可能原因**:
1. Redux Store 初始化问题
2. getCurrentUser 调用卡住
3. Token 验证失败

**解决方案**:
```javascript
// 打开浏览器 Console，输入:
localStorage.clear()
location.reload()
```

---

### 问题 3: 显示错误边界页面

**可能原因**:
1. React 组件渲染错误
2. 缺少必要的 Provider
3. 路由配置问题

**解决方案**:
- 查看错误信息
- 检查 Console 中的详细错误
- 重启开发服务器

---

### 问题 4: 404 错误

**可能原因**:
1. 访问了错误的端口
2. 路由配置问题
3. Vite 配置问题

**解决方案**:
```bash
# 确认访问正确的端口
http://localhost:5174/  # ✅ 正确

# 检查 vite.config.ts
server: {
  port: 5173,
  strictPort: false,  // 允许使用备用端口
}
```

---

## 🔧 手动测试登录

如果能看到登录界面但无法登录：

**测试步骤**:
1. 打开浏览器开发者工具 → Network
2. 输入用户名：`admin`，密码：`admin123`
3. 点击登录
4. 查看 Network 中的请求

**预期请求**:
```
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json
Body: {"username":"admin","password":"admin123"}
```

**预期响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 📊 系统状态检查清单

- [ ] 后端服务运行在 `http://127.0.0.1:8000`
- [ ] 前端服务运行在 `http://localhost:5174`
- [ ] 浏览器访问 `http://localhost:5174/`
- [ ] 开发者工具 Console 无红色错误
- [ ] Network 面板无失败请求
- [ ] 可以访问 `http://localhost:8000/docs` 查看 API 文档
- [ ] LocalStorage 无过期 token

---

## 🎯 快速诊断命令

**检查端口占用**:
```bash
# Windows PowerShell
netstat -ano | findstr :5173
netstat -ano | findstr :5174
netstat -ano | findstr :8000
```

**检查进程**:
```bash
# 查看占用端口的进程
Get-Process -Id (Get-NetTCPConnection -LocalPort 5173).OwningProcess
```

**重启服务**:
```bash
# 停止后端 (在后端终端按 Ctrl+C)
# 停止前端 (在前端终端按 Ctrl+C)

# 重启后端
cd backend
python -m uvicorn app.main:app --reload

# 重启前端
cd frontend
npm run dev
```

---

## 📞 如果问题仍未解决

**请提供以下信息**:

1. **浏览器 Console 截图** - 显示所有错误和警告
2. **Network 面板截图** - 显示所有请求状态
3. **访问的 URL** - 确认端口正确
4. **错误信息** - 任何显示的错误文本
5. **浏览器版本** - Chrome/Firefox/Edge 等

---

**创建时间**: 2026-03-10  
**版本**: v1.0
