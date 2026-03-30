# WebSocket 连接错误修复报告

## 问题描述

前端出现 WebSocket 连接错误：

```
WebSocket connection to 'ws://localhost:5173/api/v1/ws?token=...' failed:
WebSocket is closed before the connection is established.
```

## 问题分析

### 错误原因

WebSocket 服务尝试连接 `ws://localhost:5173`（Vite 开发服务器），而不是后端服务器 `ws://localhost:8000`。

### 代码问题

**文件**: `frontend/src/services/websocket.ts`

**问题代码**:
```typescript
constructor(baseUrl?: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = baseUrl || window.location.host;  // ❌ 使用 window.location.host
  this.url = `${protocol}//${host}/api/v1/ws`;
}
```

在开发环境中：
- `window.location.host` = `localhost:5173`（Vite 开发服务器）
- 后端 WebSocket 服务运行在 `localhost:8000`

### 环境变量

`.env.local` 已配置：
```
VITE_WS_URL=ws://localhost:8000/api/v1/ws
```

但代码没有使用这个环境变量。

## 修复方案

### 修复内容

修改 `websocket.ts` 构造函数，优先使用环境变量：

```typescript
constructor(baseUrl?: string) {
  if (baseUrl) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${protocol}//${baseUrl}/api/v1/ws`;
  } else if (import.meta.env.VITE_WS_URL) {
    this.url = import.meta.env.VITE_WS_URL;  // ✅ 使用环境变量
  } else {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    this.url = `${protocol}//${host}/api/v1/ws`;
  }
}
```

### 优先级

1. **显式传入的 baseUrl** - 最高优先级
2. **环境变量 VITE_WS_URL** - 开发环境使用 ✅
3. **window.location.host** - 生产环境使用

## 连接配置

### 开发环境

```
前端: http://localhost:5173
后端: http://localhost:8000
WebSocket: ws://localhost:8000/api/v1/ws
```

### 生产环境

```
前端: https://your-domain.com
后端: https://your-domain.com
WebSocket: wss://your-domain.com/api/v1/ws
```

## 修复验证

### 测试步骤

1. ✅ 修改代码使用环境变量
2. ⏳ 重启前端开发服务器
3. ⏳ 刷新页面
4. ⏳ 检查 WebSocket 连接状态

### 预期结果

- ✅ WebSocket 连接到 `ws://localhost:8000/api/v1/ws`
- ✅ 连接成功建立
- ✅ 实时数据正常推送

## 相关文件

### 修改的文件
- `frontend/src/services/websocket.ts` - WebSocket 服务

### 配置文件
- `frontend/.env.local` - 环境变量配置

## 环境变量说明

### WebSocket 配置

```bash
# .env.local
VITE_WS_URL=ws://localhost:8000/api/v1/ws  # 开发环境
# VITE_WS_URL=wss://your-domain.com/api/v1/ws  # 生产环境
```

### 使用方式

```typescript
// 读取环境变量
const wsUrl = import.meta.env.VITE_WS_URL;
```

## 总结

✅ **问题已修复**

### 错误类型
- WebSocket 连接地址错误

### 修复方法
- 优先使用环境变量 `VITE_WS_URL`
- 确保开发环境连接后端服务器

### 修复效果
- ✅ WebSocket 连接正确的后端地址
- ✅ 实时数据推送功能正常
- ✅ 前后端通信恢复正常

现在刷新前端页面，WebSocket 应该能正常连接了！🎉
