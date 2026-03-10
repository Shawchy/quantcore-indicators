# bcrypt 兼容性修复报告

**修复日期**: 2026-03-10  
**问题**: bcrypt 和 passlib 版本兼容性问题  
**状态**: ✅ 已修复  

---

## 🐛 问题描述

启动后端时出现 bcrypt 版本兼容性错误：

```
(trapped) error reading bcrypt version
Traceback (most recent call last):
  File "C:\Users\shawc\AppData\Local\Programs\Python\Python312\Lib\site-packages\passlib\handlers\bcrypt.py", line 620, in _load_backend_mixin
    version = _bcrypt.__about__.__version__
              ^^^^^^^^^^^^^^^^^
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**错误原因**: 
- 新版本的 `bcrypt` (4.0.0+) 移除了 `__about__` 属性
- 旧版 `passlib[bcrypt]` 依赖这个属性来检测 bcrypt 版本
- 导致密码哈希功能无法正常工作

---

## ✅ 修复方案

### 1. 更新 requirements.txt

**文件**: `backend/requirements.txt`

```diff
# 认证与安全
PyJWT>=2.8.0
python-jose[cryptography]>=3.3.0
- passlib[bcrypt]>=1.7.4
+ bcrypt>=4.0.0
+ passlib>=1.7.4
python-multipart>=0.0.6
```

**说明**:
- 分离 `bcrypt` 和 `passlib` 依赖
- 使用最新版本的 `bcrypt>=4.0.0`

---

### 2. 修改 security.py 使用原生 bcrypt

**文件**: `backend/app/core/security.py`

```python
# 修改前
from passlib.context import CryptContext

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

```python
# 修改后
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')
```

**说明**:
- 移除对 `passlib` 的依赖
- 直接使用 `bcrypt` 库进行密码哈希
- 更简单、更现代的 API

---

### 3. 更新环境变量

**文件**: `backend/.env`

```env
# 默认用户密码（开发环境）
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_USER_PASSWORD=user123
```

---

## 📝 修改文件清单

1. ✅ `backend/requirements.txt` - 更新依赖配置
2. ✅ `backend/app/core/security.py` - 使用原生 bcrypt
3. ✅ `backend/.env` - 添加默认密码配置

---

## 🔧 安装步骤

重新安装依赖：

```bash
cd backend
pip uninstall bcrypt passlib -y
pip install -r requirements.txt
```

---

## 🧪 测试验证

启动后端：
```bash
cd backend
python -m uvicorn app.main:app --reload
```

**预期输出**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [21716] using WatchFiles
2026-03-10 XX:XX:XX.XXX | INFO     | app.storage.cache:__init__:129 - 缓存管理器初始化完成
INFO:     Application startup complete.
```

**测试登录**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
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

## 📊 影响评估

**影响范围**: 
- 用户认证
- 密码哈希
- 登录功能

**修复效果**:
- ✅ 解决 bcrypt 版本兼容性问题
- ✅ 使用更现代的密码哈希 API
- ✅ 减少对 passlib 的依赖
- ✅ 代码更简洁清晰

---

## 🎯 技术说明

### bcrypt 版本变化

**bcrypt 4.0.0 变化**:
- 移除了 `__about__` 属性
- 导致 passlib 无法检测版本
- passlib 无法正常工作

### 解决方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **降级 bcrypt** | 简单快速 | 安全性降低，不推荐 |
| **使用原生 bcrypt** | 代码简洁，依赖减少 | 需要修改代码 ✅ |
| **等待 passlib 更新** | 无需修改代码 | 不确定性高 |

**选择**: 使用原生 bcrypt - 最可靠和推荐的方案

---

## 📚 参考资料

- [bcrypt 4.0.0 变更日志](https://github.com/pyca/bcrypt/blob/main/CHANGELOG.rst)
- [bcrypt 官方文档](https://bcrypt.readthedocs.io/)
- [Passlib 项目状态](https://passlib.readthedocs.io/)

---

**修复时间**: 2026-03-10  
**修复人员**: AI Assistant  
**版本**: v1.3  
**状态**: ✅ 已修复
