# Alembic 数据库迁移指南

## 概述

Alembic 是 SQLAlchemy 的数据库迁移工具，用于管理数据库模式的版本控制。

## 已配置的迁移脚本

- **初始迁移**: `20250405_0001_initial.py` - 创建所有数据表

## 常用命令

### 1. 应用迁移（升级数据库）

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade 0001

# 升级 1 个版本
alembic upgrade +1
```

### 2. 回滚迁移（降级数据库）

```bash
# 回滚到上一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade 0001

# 回滚所有迁移
alembic downgrade base
```

### 3. 创建新的迁移脚本

```bash
# 根据模型变化自动生成迁移脚本
alembic revision --autogenerate -m "add new table"

# 手动创建空迁移脚本
alembic revision -m "manual migration"
```

### 4. 查看迁移状态

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看待执行的迁移
alembic history --indicate-current
```

## 工作流程

### 添加新表的步骤

1. **修改模型文件** (`app/storage/sqlite.py`):
```python
class NewTable(Base):
    __tablename__ = "new_table"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
```

2. **生成迁移脚本**:
```bash
alembic revision --autogenerate -m "add new_table"
```

3. **审查生成的脚本**:
   - 检查 `alembic/versions/` 下的新文件
   - 确认 `upgrade()` 和 `downgrade()` 函数

4. **应用迁移**:
```bash
alembic upgrade head
```

### 修改现有表的步骤

1. **修改模型** (例如添加字段):
```python
class StockInfo(Base):
    # ... 现有字段 ...
    new_field: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
```

2. **生成并应用迁移**:
```bash
alembic revision --autogenerate -m "add new_field to stock_info"
alembic upgrade head
```

## 配置文件说明

### alembic.ini
- 主配置文件
- 包含迁移脚本位置、日志配置等

### alembic/env.py
- 迁移环境配置
- 从项目配置读取数据库 URL
- 支持异步 SQLAlchemy

## 注意事项

1. **备份数据**: 在生产环境执行迁移前，务必备份数据库
2. **测试迁移**: 在开发环境测试迁移脚本后再应用到生产
3. **版本控制**: 将迁移脚本提交到 Git
4. **团队协作**: 合并代码时注意迁移脚本的冲突

## 故障排除

### 迁移失败

```bash
# 查看详细错误信息
alembic upgrade head --sql  # 仅显示 SQL，不执行
```

### 版本冲突

```bash
# 标记当前数据库版本
alembic stamp head

# 或者标记到指定版本
alembic stamp 0001
```

### 数据库被锁定

SQLite 在执行迁移时可能会锁定数据库，确保没有其他进程正在访问数据库。

## 项目集成

迁移工具已集成到项目配置中：

- 自动读取 `app.config.settings.DATABASE_URL`
- 支持异步数据库连接
- 包含所有模型的元数据

## 参考

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 迁移指南](https://docs.sqlalchemy.org/en/14/orm/extensions/declarative/basic_use.html)
