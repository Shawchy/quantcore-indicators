# Tushare 120 积分配置说明

## ✅ 问题解决

**问题**：Tushare 接口一直初始化失败，提示"没有接口访问权限"

**原因**：代码使用 `trade_cal`（交易日历）接口做连接测试，该接口需要 **2000 积分**，而账户只有 120 积分。

**解决方案**：将连接测试接口改为 `new_share`（新股列表），只需 **120 积分** 即可访问。

---

## 📊 120 积分可用接口

根据 Tushare 官方文档，120 积分可以访问以下接口：

### ✅ 可用接口（120 分）

| 接口名称 | API | 描述 | 用途 |
|---------|-----|------|------|
| **日线行情** | `daily` | 全部历史日线数据 | **K 线分析、回测** |
| **新股列表** | `new_share` | IPO 新股发行数据 | 新股信息 |
| **股票基本信息** | `stock_basic` | 股票代码、名称等 | 股票列表 |
| **指数日线** | `index_daily` | 大盘指数日线数据 | 大盘分析 |
| **沪深股通持股** | `hk_hold` | 北向资金持股数据 | 资金流向 |
| **涨跌停价格** | `stk_limit` | 每日涨跌停价 | 涨跌停分析 |

### ❌ 不可用接口（需要更高分）

| 接口名称 | API | 所需积分 |
|---------|-----|---------|
| 交易日历 | `trade_cal` | 2000 分 |
| 周线行情 | `weekly` | 2000 分 |
| 月线行情 | `monthly` | 2000 分 |
| 复权因子 | `adj_factor` | 2000 分 |
| 龙虎榜 | `top_list` | 2000 分 |
| 资金流向 | `moneyflow` | 2000 分 |
| 财务数据 | `income`/`balancesheet` | 2000 分 |
| 筹码数据 | `chip` | 10000 分 |

---

## 🔧 修改内容

### 修改文件
`app/adapters/tushare_adapter.py`

### 修改前
```python
# 测试连接
df = self._pro.trade_cal(exchange='', start_date='20240101', end_date='20240107', fields='pre_cal_flag')
```

### 修改后
```python
# 测试连接（使用 120 积分可访问的接口）
df = self._pro.new_share(ts_code='', start_date='20240101', end_date='20240110')
```

---

## 📝 使用建议

### 120 积分能做什么？

✅ **可以进行的操作**：
- 获取股票日线 K 线数据（`daily`）
- 获取股票基本信息（`stock_basic`）
- 获取大盘指数数据（`index_daily`）
- 基本的技术分析和回测
- 查看北向资金持股（`hk_hold`）

❌ **无法进行的操作**：
- 获取筹码数据（需要 10000 分）
- 获取龙虎榜数据（需要 2000 分）
- 获取财务数据（需要 2000 分）
- 获取分钟线数据（需要 5000 分）

### 推荐配置

**方案 1：120 积分 + AkShare 双数据源**
```bash
# .env 文件
DEFAULT_DATA_SOURCE=akshare  # 默认使用 AkShare（免费无限制）
TUSHARE_TOKEN=your_token     # Tushare 作为备选
```

**方案 2：纯 Tushare（120 分）**
```bash
DEFAULT_DATA_SOURCE=tushare
TUSHARE_TOKEN=your_token
```

> **建议**：使用 AkShare 作为主要数据源，Tushare 作为补充。AkShare 免费且数据全面。

---

## 📈 积分升级建议

如果需要更多接口，可以通过以下方式获取积分：

### 获取积分方式
1. **每日签到**：+10 积分/天
2. **邀请好友**：+100 积分/人
3. **贡献数据**：+500~2000 积分
4. **充值**：直接购买积分

### 推荐升级目标

| 积分 | 价格 | 解锁接口 | 推荐度 |
|------|------|---------|--------|
| 120 分 | 免费 | 日线、股票列表 | ⭐⭐⭐ |
| 2000 分 | ~¥200 | 财务数据、龙虎榜、复权因子 | ⭐⭐⭐⭐⭐ |
| 5000 分 | ~¥500 | 分钟线数据 | ⭐⭐⭐⭐ |
| 10000 分 | ~¥1000 | 筹码数据 | ⭐⭐⭐ |

> **建议**：对于个人量化分析，2000 积分性价比最高，解锁了大部分实用接口。

---

## 🔍 验证测试

运行以下命令验证 Tushare 是否正常初始化：

```bash
python -c "import asyncio; from app.adapters import data_source_manager; asyncio.run(data_source_manager.initialize())"
```

**成功标志**：
```
Tushare 适配器初始化成功（120 积分权限）
当前可用接口：日线行情 (daily)、新股列表 (new_share) 等基础接口
数据源 tushare 初始化成功（优先级：1)
```

---

## 📚 相关文档

- [Tushare 官方权限文档](https://tushare.pro/document/1?doc_id=108)
- [Tushare 积分获取办法](https://tushare.pro/document/1?doc_id=25)
- [数据加载策略优化报告](LAZY_LOADING_OPTIMIZATION.md)

---

## 📞 常见问题

### Q1: 为什么显示"可用接口：11 个"？
A: 120 积分解锁了 11 个基础接口，包括日线、股票列表、指数数据等。

### Q2: 能否获取复权 K 线数据？
A: 不能。复权因子（`adj_factor`）需要 2000 积分。但可以使用 AkShare 获取复权数据。

### Q3: 能否进行策略回测？
A: 可以！日线数据（`daily`）只需要 120 积分，完全满足回测需求。

### Q4: 如何查看自己有多少积分？
A: 登录 Tushare 官网 https://tushare.pro/user/token 查看。

---

**更新时间**：2026-03-16  
**适用版本**：120 积分账户
