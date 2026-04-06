# 股票数据同步指南

## 数据流程

```
Baostock API → Baostock 适配器 → StockInfoService (数据处理层) → 数据库
```

### 流程说明

1. **数据源层**: Baostock 提供原始股票数据
2. **适配器层**: `BaostockAdapter` 负责与 Baostock API 交互，返回标准化的 `StockBasicInfo` 对象
3. **服务层**: `StockInfoService` 负责数据清洗、验证和持久化
4. **存储层**: SQLite 数据库存储最终数据

## 目录结构

```
backend/
├── app/
│   ├── adapters/
│   │   ├── base.py              # 基础适配器类和数据模型
│   │   └── baostock_adapter.py  # Baostock 适配器
│   ├── services/
│   │   └── stock_info_service.py  # 股票信息服务层
│   └── storage/
│       └── sqlite.py            # 数据库模型
```

## 使用方法

### 1. 同步所有股票信息

```bash
cd backend

# 清空数据库后同步
python -m app.services.stock_info_service --clear

# 增量同步（保留现有数据）
python -m app.services.stock_info_service
```

### 2. 在代码中使用

```python
from app.services.stock_info_service import get_stock_info_service

# 获取服务实例
service = get_stock_info_service()

# 同步数据
await service.sync_all_stocks(clear_first=False)

# 查询股票数量
count = await service.get_stock_count()

# 查询单只股票
stock = await service.get_stock_by_code('000001')

# 关闭服务
await service.close()
```

## 数据字段说明

### StockBasicInfo 数据模型

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| code | str | 股票代码 | 000001 |
| name | str | 股票名称 | 平安银行 |
| market | str | 市场标识 | SH/SZ/BJ |
| type | int | 证券类型 | 1-股票，2-指数 |
| status | int | 上市状态 | 1-上市，0-退市 |
| list_date | str | 上市日期 | 1991-07-15 |
| delist_date | str | 退市日期 | None |
| industry | str | 行业 | None |
| sector | str | 板块 | None |
| area | str | 地区 | None |
| total_shares | float | 总股本 | None |
| float_shares | float | 流通股 | None |

### 证券类型 (type)

| 值 | 描述 |
|----|------|
| 1 | 股票 |
| 2 | 指数 |
| 3 | 其它 |
| 4 | 可转债 |
| 5 | ETF |

### 上市状态 (status)

| 值 | 描述 |
|----|------|
| 1 | 上市 |
| 0 | 退市 |

## 数据处理流程

### 1. 数据获取
```python
# 从 Baostock 获取原始数据
stock_list = await adapter.get_stock_list()
```

### 2. 数据清洗
```python
# 服务层自动执行以下清洗步骤：
# - 验证必填字段 (code, name)
# - 代码格式标准化 (补齐 6 位)
# - 市场标识标准化 (SH/SZ/BJ)
# - 日期格式验证 (YYYY-MM-DD)
# - 类型和状态验证
```

### 3. 数据持久化
```python
# 保存到数据库
# - 检查现有记录
# - 存在则更新，不存在则插入
# - 批量提交 (每 1000 条)
```

## 日志输出示例

```
============================================================
开始同步股票信息
============================================================
Baostock 适配器初始化成功
StockInfoService 初始化成功
从 Baostock 获取股票列表...
成功获取 8680 只股票
数据清洗和验证...
清洗后有效数据：8680 只

同步完成:
  新增：8545 只
  更新：135 只
  总计：8680 只

✅ 同步成功
数据库共有 8545 只股票
```

## 注意事项

1. **首次同步**: 建议使用 `--clear` 参数清空旧数据
2. **增量更新**: 日常更新直接运行，无需清空
3. **数据验证**: 服务层会自动验证和清洗数据
4. **错误处理**: 单条记录失败不影响整体同步
5. **性能优化**: 批量提交，每 1000 条记录提交一次

## 常见问题

### Q: 为什么有些字段是 None？
A: Baostock 只提供基础信息（code, name, market, type, status, list_date, delist_date），行业、板块、地区、股本等信息需要其他数据源补充。

### Q: 如何获取行业信息？
A: 等待 akshare 接口恢复后，可以通过其他数据源补充行业、板块等信息。

### Q: 同步失败怎么办？
A: 检查日志输出，常见原因：
- 网络连接问题
- Baostock 登录失败
- 数据库锁定

### Q: 数据如何更新？
A: 直接运行同步命令，服务层会自动：
- 检测现有记录
- 更新缺失字段（如上市日期）
- 保留已有数据（如行业信息）

## 相关文档

- [Baostock 官方文档](http://baostock.com/)
- 数据库模型：`backend/app/storage/sqlite.py`
- 适配器实现：`backend/app/adapters/baostock_adapter.py`
- 服务层实现：`backend/app/services/stock_info_service.py`
