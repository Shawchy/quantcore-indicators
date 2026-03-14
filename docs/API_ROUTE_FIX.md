# API 路由修复说明

## 🔧 问题描述

前端请求 `/api/v1/loading/tasks` 时返回 404 错误。

**错误日志**:
```
GET http://localhost:5173/api/v1/loading/tasks 404 (Not Found)
```

## 🎯 根本原因

路由路径重复问题：
- 在 `__init__.py` 中已经配置了前缀：`prefix="/loading"`
- 但在 `loading_progress.py` 中的路由定义又包含了 `/loading`：`@router.get("/loading/tasks")`
- 导致实际路径变成：`/api/v1/loading/loading/tasks`（重复了 `/loading`）

## ✅ 已完成的修复

修改了 [`loading_progress.py`](file:///d:/Project/Quant/backend/app/api/v1/endpoints/loading_progress.py) 文件，移除了所有路由定义中的 `/loading` 前缀：

### 修改内容

**修改前**:
```python
@router.get("/loading/tasks", ...)
@router.get("/loading/task/{task_id}", ...)
@router.delete("/loading/task/{task_id}", ...)
@router.post("/loading/cleanup", ...)
```

**修改后**:
```python
@router.get("/tasks", ...)
@router.get("/task/{task_id}", ...)
@router.delete("/task/{task_id}", ...)
@router.post("/cleanup", ...)
```

### 最终路由路径

结合 `__init__.py` 中的前缀配置，最终的路由路径为：

| 端点 | 完整路径 | 说明 |
|------|---------|------|
| GET | `/api/v1/loading/tasks` | 获取所有加载任务 |
| GET | `/api/v1/loading/task/{task_id}` | 获取单个任务进度 |
| DELETE | `/api/v1/loading/task/{task_id}` | 移除任务 |
| POST | `/api/v1/loading/cleanup` | 清理旧任务 |

## 🚀 需要执行的操作

**重要**: 需要重启后端服务器才能使修改生效。

### 步骤 1: 停止当前运行的后端服务

如果后端服务正在运行，请先停止它（Ctrl+C）。

### 步骤 2: 重启后端服务

```bash
cd d:\Project\Quant\backend
uvicorn app.main:app --reload --port 8000
```

### 步骤 3: 验证修复

重启后，前端应该能够正常访问加载进度 API。打开浏览器开发者工具，查看网络请求，应该能看到：

```
✅ GET http://localhost:5173/api/v1/loading/tasks 200 (OK)
```

## 📝 相关文件

- **修改的文件**:
  - [`backend/app/api/v1/endpoints/loading_progress.py`](file:///d:/Project/Quant/backend/app/api/v1/endpoints/loading_progress.py)

- **路由配置文件**:
  - [`backend/app/api/v1/__init__.py`](file:///d:/Project/Quant/backend/app/api/v1/__init__.py)

- **前端调用代码**:
  - [`frontend/src/services/api.ts`](file:///d:/Project/Quant/frontend/src/services/api.ts#L347-L356)
  - [`frontend/src/components/LoadingProgressPanel.tsx`](file:///d:/Project/Quant/frontend/src/components/LoadingProgressPanel.tsx)

## 🎓 经验总结

### FastAPI 路由前缀规则

当使用 `APIRouter` 时：

```python
# 主路由文件 (__init__.py)
api_router.include_router(some_router, prefix="/some-prefix", tags=["标签"])

# 子路由文件 (some_router.py)
@router.get("/endpoint")  # ✅ 正确：不要重复前缀
# @router.get("/some-prefix/endpoint")  # ❌ 错误：会导致路径重复
```

最终访问路径：`/some-prefix/endpoint`

### 最佳实践

1. **子路由文件**：只定义具体的端点路径，不要包含模块前缀
2. **主路由文件**：统一配置所有模块的前缀
3. **保持一致性**：确保前端 API 调用路径与后端路由匹配

## 🔍 验证清单

重启后端后，请检查以下内容：

- [ ] 后端启动成功，无报错
- [ ] 访问 `http://localhost:8000/docs` 能看到 `/loading/tasks` 端点
- [ ] 前端页面加载时，`GET /api/v1/loading/tasks` 返回 200 状态码
- [ ] 加载进度面板能正常显示任务列表
- [ ] 任务详情、删除、清理等功能正常工作

如有问题，请查看后端日志：
```bash
# 查看后端启动日志
# 注意观察路由注册信息
```
