# 依赖安装指南

本文档说明如何安装和管理 TickFlow 量化交易系统的依赖。

---

## 📋 依赖文件说明

项目提供了 3 个依赖文件，适用于不同场景：

| 文件 | 用途 | 大小 | 适用场景 |
|------|------|------|----------|
| `requirements-minimal.txt` | 最小化依赖 | ~100MB | 快速测试、轻量部署 |
| `requirements.txt` | 完整依赖 | ~500MB | 生产环境、完整功能 |
| `requirements-dev.txt` | 开发依赖 | ~800MB | 开发环境、CI/CD |

---

## 🚀 快速开始

### 1. 创建虚拟环境（推荐）

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate

# 或者使用 conda
conda create -n tickflow python=3.12
conda activate tickflow
```

### 2. 选择依赖文件

根据你的需求选择合适的依赖文件：

**场景 1: 快速测试**
```bash
pip install -r requirements-minimal.txt
```

**场景 2: 生产环境（推荐）**
```bash
pip install -r requirements.txt
```

**场景 3: 开发环境**
```bash
pip install -r requirements-dev.txt
```

---

## 📦 依赖分类说明

### 核心框架
- **FastAPI** - Web 框架
- **Uvicorn** - ASGI 服务器
- **Pydantic V2** - 数据验证（已迁移）

### 数据处理
- **Pandas** - 数据分析
- **Polars** - 高性能 DataFrame
- **NumPy** - 数值计算

### 数据源
- **efinance** - 东方财富（推荐，最稳定）
- **akshare** - 开源财经数据
- **baostock** - 证券数据
- **yfinance** - Yahoo Finance
- **tushare** - Tushare（已降级，多数 API 不可用）

### 技术指标
- **pandas-ta** - 技术指标库（推荐）
- **TA-Lib** - 技术分析库（可选，需要预编译）

### 数据存储
- **SQLAlchemy** - ORM 框架（支持 Async）
- **aiosqlite** - SQLite 异步驱动
- **pyarrow** - Parquet 支持
- **fastparquet** - Parquet 读写

### 工具库
- **loguru** - 日志库
- **httpx** - HTTP 客户端
- **python-dotenv** - 环境变量

---

## 🔧 安装问题排查

### 问题 1: TA-Lib 安装失败

**错误信息:**
```
error: command 'gcc' failed: No such file or directory
```

**解决方案:**
```bash
# 使用 pandas-ta 替代（推荐）
pip install pandas-ta

# 或者安装预编译版本（Windows）
# 下载：https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib‑0.4.28‑cp312‑cp312‑win_amd64.whl
```

### 问题 2: torch/tensorflow 安装慢

**解决方案:**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者跳过大型依赖
pip install fastapi uvicorn pydantic pandas numpy sqlalchemy loguru
```

### 问题 3: 依赖冲突

**解决方案:**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 清除缓存
pip cache purge

# 重新安装
pip install --no-cache-dir -r requirements.txt
```

---

## ✅ 验证安装

运行验证脚本检查依赖是否正确安装：

```bash
python verify_dependencies.py
```

**输出示例:**
```
============================================================
依赖安装验证
============================================================

核心依赖:
------------------------------------------------------------
✓ fastapi: 0.135.1
✓ uvicorn: 0.41.0
✓ pydantic: 2.12.5
...

核心依赖：18/18 已安装

总计：18/22 已安装
安装率：81.8%
============================================================

✓ 所有核心依赖已安装！
```

---

## 🔄 更新依赖

### 检查可更新的依赖

```bash
pip list --outdated
```

### 更新所有依赖

```bash
pip install --upgrade -r requirements.txt
```

### 更新单个依赖

```bash
pip install --upgrade package_name
```

---

## 📊 依赖统计

### requirements.txt
- **总包数:** ~30 个
- **核心包:** 18 个
- **可选包:** 4 个（torch, tensorflow, talib, redis）
- **安装大小:** ~500MB

### 安装时间估算
- **宽带 (100Mbps):** ~5 分钟
- **普通 (10Mbps):** ~30 分钟
- **慢速 (1Mbps):** ~5 小时

---

## 💡 最佳实践

### 1. 使用虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate   # Windows
```

### 2. 固定版本
生产环境建议使用固定的版本号：
```txt
fastapi==0.115.0
pydantic==2.10.0
```

### 3. 定期更新
```bash
# 每月检查一次
pip list --outdated

# 每季度更新一次
pip install --upgrade -r requirements.txt
```

### 4. 使用国内镜像（中国）
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📝 依赖文件结构

```
backend/
├── requirements.txt              # 完整依赖
├── requirements-dev.txt          # 开发依赖
├── requirements-minimal.txt      # 最小依赖
├── verify_dependencies.py        # 验证脚本
└── DEPENDENCIES_GUIDE.md         # 本文件
```

---

## 🔗 相关文档

- [API 参考](API_REFERENCE.md)
- [测试报告](FINAL_TEST_REPORT.md)
- [集成报告](INTEGRATION_REPORT.md)
- [完成报告](FINAL_COMPLETION_REPORT.md)

---

## ❓ 常见问题

### Q: 为什么有些依赖被注释掉了？
A: torch、tensorflow、TA-Lib 等大型依赖按需安装，避免不必要的下载。

### Q: Pydantic V1 和 V2 有什么区别？
A: V2 使用 `@field_validator` 替代了 V1 的 `@validator`，性能更好。项目已完成 V2 迁移。

### Q: 可以只安装部分依赖吗？
A: 可以，使用 `requirements-minimal.txt` 或手动安装需要的包。

### Q: 如何查看已安装的依赖？
A: 运行 `pip list` 或 `pip freeze`。

---

**文档版本:** 1.0  
**更新日期:** 2026-03-19  
**维护者:** AI Assistant
