# 前后端数据库检查报告

**检查时间**: 2026-03-12 18:23  
**问题**: 前端无数据展示  
**状态**: 🔴 已定位根本原因

---

## 🔍 问题诊断

### 1. 数据库配置检查 ✅

**后端数据库配置**:
```python
# backend/.env
SQLITE_DIR=./data/sqlite
PARQUET_DIR=./data/parquet

# backend/app/config.py
DATABASE_URL: str = "sqlite+aiosqlite:///./data/sqlite/quant.db"
```

**前端 API 配置**:
```typescript
// frontend/.env
VITE_API_BASE_URL=/api/v1

// frontend/src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
```

**结论**: ✅ **前后端数据库配置一致**
- 后端使用 SQLite 数据库：`d:\Project\Quant\backend\data\sqlite\quant.db`
- 前端通过 REST API (`/api/v1`) 调用后端获取数据
- 前端不直接连接数据库，通过后端服务间接访问

---

## ❌ 根本原因

### 数据库表数据量统计

| 表名 | 记录数 | 状态 | 影响 |
|------|--------|------|------|
| **stock_info** | 0 | ❌ 空表 | 前端无法显示股票列表、搜索结果 |
| **kline** | 18 | ⚠️ 数据过少 | K 线图只有 18 条数据，显示不完整 |
| **sector_info** | 0 | ❌ 空表 | 前端无法显示板块列表、板块分析 |
| **technical_indicators** | 0 | ❌ 空表 | 无技术指标数据 |
| **watchlist** | 0 | ❌ 空表 | 无自选股数据 |

### 问题根因

**前端无数据展示的根本原因是数据库中没有数据！**

具体表现：
1. `stock_info` 表为空 → 股票列表 API 返回空数组
2. `sector_info` 表为空 → 板块列表 API 返回空数组  
3. `kline` 表只有 18 条数据 → K 线数据不足

---

## 🔧 问题原因分析

### 为什么数据库是空的？

1. **Tushare Token 失效** 
   - Token: `54fed15e38...81c65`
   - 状态：❌ 无效（权限不足）
   - 日志：`抱歉，您没有接口访问权限`

2. **自动降级到 AkShare**
   - 当前使用数据源：AkShare
   - 状态：⚠️ 网络连接不稳定
   - 错误：`Remote end closed connection without response`

3. **数据未初始化**
   - 数据库表结构已创建 ✅
   - 基础数据未填充 ❌
   - 需要手动执行数据初始化

---

## 💡 解决方案

### 方案一：修复 Tushare Token（推荐）

**步骤**:

1. **获取新 Token**
   - 访问：https://tushare.pro/
   - 登录账号 → 个人主页 → 接口 TOKEN
   - 完善个人信息获得 120 积分

2. **更新配置文件**
   ```bash
   # 编辑 backend/.env
   TUSHARE_TOKEN=你的新 token
   DEFAULT_DATA_SOURCE=tushare
   ```

3. **重启后端服务**
   ```bash
   cd d:\Project\Quant\backend
   python -m uvicorn app.main:app --reload
   ```

4. **验证 Token**
   ```bash
   python test_token.py
   ```

5. **初始化数据**
   ```bash
   python init_data.py
   ```

**优点**:
- 数据质量高
- 接口稳定
- 支持更多功能

**缺点**:
- 需要注册账号
- 需要完善个人信息

---

### 方案二：使用 AkShare（临时方案）

**现状**:
- 当前默认配置已使用 AkShare
- 但网络连接不稳定

**优化建议**:

1. **增加重试机制**
   - AkShare 已实现重试，但需要检查网络环境

2. **使用 Baostock 备选**
   ```bash
   # 修改 backend/.env
   DEFAULT_DATA_SOURCE=baostock
   DATA_SOURCE_PRIORITY=baostock,akshare,tushare
   ```

3. **批量导入历史数据**
   - 从其他渠道导出 CSV
   - 使用 `init_data.py` 脚本导入

---

### 方案三：手动导入数据（快速解决）

**步骤**:

1. **下载股票列表 CSV**
   - 来源：东方财富、同花顺等
   - 格式：code,name,market,industry,...

2. **转换为 SQL 插入语句**
   ```python
   import pandas as pd
   df = pd.read_csv('stock_list.csv')
   for _, row in df.iterrows():
       cursor.execute("INSERT INTO stock_info ...")
   ```

3. **导入数据库**
   ```bash
   python import_csv.py
   ```

---

## 📋 立即执行的操作

### 1. 检查网络环境

```bash
# 测试 AkShare 连接
python -c "import akshare as ak; print(ak.__version__)"
```

### 2. 尝试使用 Baostock

```bash
# 修改 backend/.env
DEFAULT_DATA_SOURCE=baostock

# 重启后端
# 重新运行初始化
python init_data.py
```

### 3. 验证数据库数据

```bash
python check_database_data.py
```

期望输出：
```
✅ stock_info              :      5000+ 条记录
✅ kline                   :     10000+ 条记录
✅ sector_info             :       100+ 条记录
```

### 4. 测试后端 API

```bash
python test_api.py
```

期望输出：
```
✅ 成功获取股票列表：5000 只股票
✅ 成功获取 K 线数据：100 条
✅ 成功获取板块列表：100 个板块
```

### 5. 检查前端展示

打开浏览器访问：http://localhost:5173
- 查看股票列表是否显示
- 查看 K 线图是否有数据
- 查看板块分析是否正常

---

## 📊 数据初始化脚本

已创建脚本：[`init_data.py`](d:\Project\Quant\backend\init_data.py)

**功能**:
- 初始化股票列表
- 初始化板块列表
- 批量拉取 K 线数据（最近 60 天，20 只热门股票）

**使用方法**:
```bash
cd d:\Project\Quant\backend
python init_data.py
```

**当前状态**: ❌ 因网络问题执行失败  
**下一步**: 修复数据源连接后重新执行

---

## 🎯 验证清单

### 数据库层面
- [ ] `stock_info` 表有 5000+ 条记录
- [ ] `kline` 表每只股票有 100+ 条记录
- [ ] `sector_info` 表有 100+ 条记录
- [ ] `technical_indicators` 表有数据

### API 层面
- [ ] `GET /api/v1/stock/search?keyword=平安` 返回股票列表
- [ ] `GET /api/v1/kline/000001` 返回 K 线数据
- [ ] `GET /api/v1/sector/list?sector_type=industry` 返回板块列表
- [ ] `GET /api/v1/market/realtime?index_codes=000001` 返回指数行情

### 前端层面
- [ ] 首页显示股票列表
- [ ] K 线图正常渲染
- [ ] 板块分析页面显示板块排行
- [ ] 自选股功能正常

---

## 📝 总结

### 核心问题
1. ✅ **前后端数据库配置一致**（无问题）
2. ❌ **数据库表中没有数据**（根本原因）
3. ❌ **数据源连接失败**（直接原因）

### 解决优先级
1. **P0 - 修复数据源连接**
   - 方案 A: 获取新的 Tushare Token（推荐）
   - 方案 B: 修复 AkShare 网络连接
   - 方案 C: 切换到 Baostock

2. **P1 - 初始化基础数据**
   - 执行 `python init_data.py`
   - 验证数据量
   - 测试 API

3. **P2 - 验证前端展示**
   - 刷新浏览器
   - 检查数据展示
   - 验证交互功能

---

## 🔗 相关文档

- [数据存储检查报告](DATA_STORAGE_INSPECTION_REPORT.md)
- [数据存储总结](DATA_STORAGE_SUMMARY.md)
- [Tushare Token 修复指南](TUSHARE_TOKEN_FIX.md)

---

**报告生成时间**: 2026-03-12 18:23  
**状态**: 🔴 待修复  
**下一步**: 获取新的 Tushare Token 或修复网络连接
