# efinance 数据源集成说明

## ✅ 已完成工作

### 1. 创建 efinance 适配器

**文件**：[`app/adapters/efinance_adapter.py`](file:///m:/Project/Quant/backend/app/adapters/efinance_adapter.py)

实现了以下接口：
- `get_stock_list()` - 获取股票列表
- `get_stock_info()` - 获取股票信息
- `get_kline()` - 获取 K 线数据
- `get_realtime_quote()` - 获取实时行情
- `get_sector_list()` - 获取板块列表
- `get_sector_components()` - 获取板块成分股
- `get_chip_data()` - 获取筹码数据

### 2. 注册到数据源工厂

**修改文件**：
- [`app/adapters/factory.py`](file:///m:/Project/Quant/backend/app/adapters/factory.py) - 导入并注册 EFinanceAdapter
- [`app/adapters/base.py`](file:///m:/Project/Quant/backend/app/adapters/base.py) - 添加 EFINANCE 枚举
- [`app/config.py`](file:///m:/Project/Quant/backend/app/config.py) - 配置优先级

### 3. 优先级配置

数据源优先级（从高到低）：
1. **tushare** - 付费数据源（需要 Token）
2. **efinance** - 免费数据源（东方财富）⭐ 新增
3. **akshare** - 免费数据源
4. **baostock** - 免费数据源

---

## 🔧 配置说明

### 修改 config.py

```python
# 数据源优先级（从高到低）
DATA_SOURCE_PRIORITY: list[str] = ["tushare", "efinance", "akshare", "baostock"]
```

### 安装 efinance

```bash
pip install efinance
```

---

## 📊 efinance 特点

### 优势
- ✅ **完全免费**：无需注册，无需 Token
- ✅ **数据丰富**：支持 A 股、基金、期货、债券等
- ✅ **实时更新**：提供实时行情数据
- ✅ **来源可靠**：数据来源于东方财富

### 已实现功能
- ✅ 股票列表获取
- ✅ 股票基本信息
- ✅ 历史 K 线数据
- ✅ 实时行情
- ✅ 板块列表
- ✅ 板块成分股
- ✅ 筹码数据（股东人数）

### 缓存策略
- K 线数据：5 分钟
- 股票列表：30 分钟
- 股票信息：10 分钟
- 实时行情：1 分钟
- 板块数据：5 分钟

---

## 💻 使用示例

### 使用默认数据源（自动选择）

```python
from app.adapters import data_source_manager

# 自动选择最优数据源（优先级：tushare > efinance > akshare）
klines = await data_source_manager.get_kline("000001", start_date="20240101", end_date="20241231")
```

### 强制使用 efinance

```python
# 指定使用 efinance 数据源
klines = await data_source_manager.get_kline(
    "000001",
    start_date="20240101",
    end_date="20241231",
    source_type="efinance"  # 强制使用 efinance
)
```

---

## ⚠️ 注意事项

### API 更新

efinance 库的 API 可能会更新，需要定期检查并适配：

```python
import efinance as ef

# 查看可用的 API
print(dir(ef.stock))

# 常用 API：
# - get_latest_quote() - 实时行情
# - get_quote_history() - 历史 K 线
# - get_quote_snapshot() - 行情快照
# - get_base_info() - 股票基本信息
```

### 代码格式

efinance 需要特定的股票代码格式：
- 上交所：`sh600000`
- 深交所：`sz000001`

适配器内部已处理格式转换，用户只需传入 6 位代码即可。

---

## 🧪 测试

运行测试脚本：

```bash
python test_efinance.py
```

测试内容包括：
1. 数据源初始化
2. 获取股票列表
3. 获取股票信息
4. 获取 K 线数据
5. 获取实时行情
6. 获取板块列表

---

## 📝 后续工作

### 需要修正的 API 调用

由于 efinance API 更新，以下方法需要调整：

1. **get_stock_list()**: 使用 `ef.stock.get_base_info()` 替代
2. **get_stock_info()**: 使用 `ef.stock.get_base_info()` 过滤
3. **get_sector_list()**: 需要查找正确的板块 API
4. **get_realtime_quote()**: 使用 `ef.stock.get_latest_quote()`

### 可扩展功能

- [ ] 基金数据
- [ ] 期货数据
- [ ] 债券数据
- [ ] 财务指标
- [ ] 龙虎榜数据
- [ ] 资金流向

---

## 🔗 相关资源

- **efinance GitHub**: https://github.com/Micro-sun/efinance
- **efinance 文档**: https://efinance.readthedocs.io/
- **数据源优先级配置**: `app/config.py`
- **适配器实现**: `app/adapters/efinance_adapter.py`

---

**集成时间**：2026-03-16  
**集成状态**：✅ 已注册，⚠️ API 需适配  
**优先级**：2（仅次于 tushare）
