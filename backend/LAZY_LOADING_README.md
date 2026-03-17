# 按需加载模式使用说明

## 🚀 快速启动

### 启动后端服务

```bash
cd backend
python main.py
```

启动日志示例：
```
2026-03-16 22:00:00 | INFO     | app.main:lifespan:44 - 数据库初始化完成
2026-03-16 22:00:01 | INFO     | app.main:lifespan:50 - 数据源初始化完成，默认数据源：akshare
2026-03-16 22:00:01 | INFO     | app.main:lifespan:54 - 数据加载模式：按需加载（用户请求时才拉取数据）
2026-03-16 22:00:01 | INFO     | app.main:lifespan:63 - 性能监控已启动
2026-03-16 22:00:01 | INFO     | app.main:lifespan:67 - 数据目录初始化完成
```

**关键点**：启动时不会看到批量加载进度条，服务立即就绪。

---

## 📊 使用场景

### 场景 1：查看股票 K 线数据

**前端请求**：
```http
GET /api/v1/stock/kline?code=000001&start_date=20240101&end_date=20241231
```

**后端行为**：
1. ✅ 查询数据库缓存
2. ✅ 如果缓存不足，从数据源拉取
3. ✅ 保存到数据库
4. ✅ 返回数据

**日志输出**：
```
2026-03-16 22:05:00 | INFO     | app.services.stock_service:_load_kline_on_demand:130 - 数据库不足，从数据源拉取：000001
2026-03-16 22:05:02 | INFO     | app.services.stock_service:_load_kline_on_demand:151 - 从数据源拉取 242 条：000001
2026-03-16 22:05:02 | INFO     | app.services.data_persistence:save_klines:74 - 批量保存 242 条 K 线数据：000001
2026-03-16 22:05:02 | INFO     | app.services.stock_service:_load_kline_on_demand:155 - 已保存到数据库：000001, 242 条
```

### 场景 2：再次查看同一只股票

**前端请求**：
```http
GET /api/v1/stock/kline?code=000001&start_date=20240101&end_date=20241231
```

**后端行为**：
1. ✅ 查询数据库缓存
2. ✅ 数据库有足够数据，直接返回
3. ❌ 不再从数据源拉取

**日志输出**：
```
2026-03-16 22:10:00 | INFO     | app.services.stock_service:_load_kline_on_demand:124 - 数据库命中：000001, 242 条
```

### 场景 3：策略回测参数优化

**前端请求**：
```http
POST /api/v1/strategy/strategy_xxx/optimize
{
  "code": "000001",
  "start_date": "20240101",
  "end_date": "20241231",
  "strategy_type": "ma_cross",
  ...
}
```

**后端行为**：
1. ✅ 只拉取 `000001` 的 K 线数据
2. ✅ 进行参数优化
3. ❌ 不会批量拉取其他股票数据

**日志输出**：
```
2026-03-16 22:15:00 | INFO     | app.core.backtest.optimizer:optimize_strategy:214 - 开始优化 000001 的策略参数，日期范围：20240101 - 20241231
2026-03-16 22:15:02 | INFO     | app.services.data_persistence:save_klines:74 - 已保存 242 条 K 线数据：000001
```

---

## 🔍 验证按需加载

### 运行测试脚本

```bash
python test_lazy_loading.py
```

**预期输出**：
```
======================================================================
按需加载功能测试
======================================================================

1️⃣ 初始化数据源...
✅ 数据源初始化完成（未触发批量加载）

2️⃣ 检查数据库状态...
📊 数据库中 K 线数据总数：725 条

3️⃣ 请求单只股票数据（000001）...
✅ 获取到 242 条 K 线数据
📊 数据状态：complete
📊 后台加载：false

4️⃣ 再次请求同一只股票（应该从数据库读取）...
✅ 获取到 242 条 K 线数据

5️⃣ 请求另一只股票（000002）...
✅ 获取到 242 条 K 线数据

6️⃣ 检查数据库状态变化...
📊 数据库中 K 线数据总数：967 条
📈 新增数据：242 条

======================================================================
测试完成
======================================================================

验证结果：
✅ 启动时未批量预加载数据
✅ 只在请求时才拉取数据
✅ 拉取后数据保存到数据库
✅ 再次请求时从数据库读取
```

---

## 📈 性能监控

### 查看缓存命中率

```bash
# 查看缓存统计
curl http://localhost:8000/api/v1/cache/stats
```

### 查看数据库大小

```bash
# 检查数据库表大小
python check_database_data.py
```

---

## ⚙️ 配置选项

### 缓存配置

在 `.env` 文件中配置：

```bash
# 缓存过期时间（秒）
CACHE_TTL_KLINE=300        # K 线数据：5 分钟
CACHE_TTL_STOCK_LIST=1800  # 股票列表：30 分钟
CACHE_TTL_STOCK_INFO=600   # 股票信息：10 分钟
```

### 数据源配置

```bash
# 默认数据源
DEFAULT_DATA_SOURCE=akshare

# Tushare Token（可选）
TUSHARE_TOKEN=your_token_here
```

---

## 🐛 常见问题

### Q1: 为什么第一次请求股票数据比较慢？

**A**: 第一次请求时，系统需要从数据源拉取数据并保存到数据库。后续请求会直接从数据库读取，速度非常快。

### Q2: 如何清空缓存重新拉取数据？

**A**: 可以手动删除数据库文件或使用以下 API：

```bash
# 清理缓存
curl -X DELETE http://localhost:8000/api/v1/cache/clear
```

### Q3: 支持哪些数据源？

**A**: 支持以下数据源：
- AkShare（默认，免费）
- Tushare（需要 Token 和积分）
- Baostock（免费）
- YFinance（美股）

### Q4: 如何查看数据加载日志？

**A**: 日志文件位于 `backend/logs/` 目录，可以查看详细的加载过程。

---

## 📚 相关文档

- [数据加载策略优化报告](LAZY_LOADING_OPTIMIZATION.md)
- [数据目录检查报告](DATA_STORAGE_INSPECTION_REPORT.md)
- [性能优化文档](PERFORMANCE_OPTIMIZATION.md)

---

## 📞 技术支持

如有问题，请查看日志文件或提交 Issue。
