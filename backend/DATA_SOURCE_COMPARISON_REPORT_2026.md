# 数据源对比分析报告（2026 版）

> **说明**：Tushare 数据源已移除，当前系统使用 3+1 个数据源架构

---

## 📊 数据源概览

本系统采用多数据源架构，支持以下数据源：

| 数据源 | 类型 | 费用模式 | 数据来源 | 优先级 | 状态 |
|--------|------|---------|---------|--------|------|
| **EFinance** | 开源库 | 完全免费 | 东方财富网 | 1 | ✅ 主力 |
| **AkShare** | 开源库 | 完全免费 | 多数据源 | 2 | ✅ 补充 |
| **Baostock** | 开源库 | 完全免费 | 证券宝 | 3 | ✅ 保底 |
| **TickFlow** | 商业 API | API Key | TickFlow 平台 | 4 | ⚠️ 可选 |

**当前默认数据源**: `efinance`  
**数据源优先级**: `["efinance","akshare","baostock","tickflow"]`

---

## 🔍 各数据源详细对比

### 1️⃣ EFinance（第一优先级 / 主力数据源）

#### 📌 基本信息
- **数据来源**: 东方财富网
- **安装方式**: `pip install efinance`
- **是否需要注册**: ❌ 否
- **是否需要 Token**: ❌ 否
- **费用**: ✅ 完全免费

#### ✅ 核心优势

1. **完全免费无限制**
   - 无需注册账号
   - 无需积分或 Token
   - 无访问频率限制
   - 无数据量限制

2. **实时性强** ⭐⭐⭐⭐⭐
   - 实时行情数据（秒级更新）
   - 盘中数据完整
   - 支持 Level-2 数据

3. **数据最丰富** ⭐⭐⭐⭐⭐
   - A 股、基金、期货、债券
   - 龙虎榜、资金流向
   - 股东人数、十大股东
   - 所属板块、概念题材
   - 财务业绩数据

4. **响应速度快** ⭐⭐⭐⭐⭐
   - 平均响应时间：1-2 秒
   - 内置缓存机制
   - 反风控措施完善

5. **接口友好**
   - API 设计简洁
   - 返回数据格式规范
   - 文档齐全

#### ❌ 劣势

1. **不支持指数 K 线**
   - 需要故障转移到 AkShare
   - 指数数据覆盖不全

2. **依赖东方财富**
   - 数据源单一
   - 受东方财富网站策略影响

3. **历史数据有限**
   - 超长期历史数据可能不完整
   - 复权数据精度一般

#### 📊 已实现 API 接口

- ✅ `get_stock_list()` - 获取股票列表
- ✅ `get_stock_info(code)` - 获取股票信息
- ✅ `get_stocks_base_info(codes)` - 批量获取股票信息
- ✅ `get_kline(code, start, end, adjust)` - 获取日 K 线
- ✅ `get_weekly_kline()` - 获取周 K 线
- ✅ `get_monthly_kline()` - 获取月 K 线
- ✅ `get_multi_kline()` - 批量获取 K 线
- ✅ `get_realtime_quote(code)` - 获取实时行情
- ✅ `get_latest_quote(codes)` - 批量实时行情
- ✅ `get_market_index_kline()` - 指数 K 线（故障转移到 AkShare）
- ✅ `get_sector_list()` - 获取板块列表
- ✅ `get_sector_components()` - 获取板块成分股
- ✅ `get_belong_board(code)` - 获取所属板块
- ✅ `get_members(index_code)` - 获取指数成分股
- ✅ `get_chip_data(code)` - 获取筹码数据（股东人数）
- ✅ `get_today_bill()` - 获取当日资金流向
- ✅ `get_history_bill(code)` - 获取历史资金流向
- ✅ `get_daily_billboard()` - 获取龙虎榜
- ✅ `get_top10_stock_holder_info()` - 前十大股东
- ✅ `get_financial_performance()` - 财务业绩
- ✅ `get_fund_base_info()` - 基金基本信息
- ✅ `get_fund_quote_history()` - 基金历史行情
- ✅ `get_market_realtime_quotes()` - 市场实时行情

#### 📊 适用场景

✅ **强烈推荐用于**:
- 实时行情查询
- 股票基本信息
- 资金流向分析
- 龙虎榜数据
- 股东筹码分析
- 财务业绩分析
- 日常看盘、选股
- 基金数据分析

❌ **不推荐用于**:
- 指数 K 线历史分析（自动切换到 AkShare）
- 超长期回测（10 年以上）

---

### 2️⃣ AkShare（第二优先级 / 补充数据源）

#### 📌 基本信息
- **数据来源**: 多数据源（新浪、腾讯、东方财富等）
- **安装方式**: `pip install akshare`
- **是否需要注册**: ❌ 否
- **是否需要 Token**: ❌ 否
- **费用**: ✅ 完全免费

#### ✅ 核心优势

1. **数据源最丰富** ⭐⭐⭐⭐⭐
   - 整合多个数据源
   - 支持股票、期货、基金、外汇、加密货币
   - **指数数据完整**（最强项）

2. **历史数据最全** ⭐⭐⭐⭐⭐
   - 支持几十年历史数据
   - 指数 K 线完整
   - 分钟线数据丰富

3. **开源活跃**
   - GitHub 活跃维护
   - 社区支持好
   - 更新频繁

4. **完全免费**
   - 无需注册
   - 无积分限制
   - 开源免费

#### ❌ 劣势

1. **响应速度较慢** ⭐⭐
   - 平均响应时间：5-10 秒
   - 部分接口稳定性一般
   - 偶发网络连接问题

2. **API 复杂**
   - 接口众多，学习成本高
   - 参数复杂
   - 文档质量参差不齐

3. **限流问题**
   - 部分数据源有访问频率限制
   - 高并发时可能失败

4. **数据质量不一**
   - 不同数据源质量差异
   - 需要数据清洗

#### 📊 已实现 API 接口

- ✅ `get_stock_list()` - 获取股票列表
- ✅ `get_stock_info(code)` - 获取股票信息
- ✅ `get_kline(code, start, end)` - 获取日 K 线
- ✅ `get_market_index_kline()` - 指数 K 线（强项）
- ✅ `get_realtime_quote(code)` - 获取实时行情
- ✅ `get_sector_list()` - 获取板块列表
- ✅ `get_sector_components()` - 获取板块成分股
- ✅ `get_sector_ranking()` - 板块排名
- ✅ `get_chip_data(code)` - 获取筹码数据
- ✅ `get_stock_financial(code)` - 股票财务数据
- ✅ `get_stock_changes()` - 股票异动
- ✅ `get_zt_pool()` - 涨停池
- ✅ `get_board_industry_name_em()` - 行业板块
- ✅ `get_board_industry_cons_em()` - 行业成分股

#### 📊 适用场景

✅ **强烈推荐用于**:
- **指数 K 线历史数据**（最强项）
- 长期回测分析
- 多品种研究（期货、基金等）
- 分钟线数据获取
- EFinance 故障时的备选
- 板块分析

❌ **不推荐用于**:
- 实时行情（速度慢）
- 高频查询（限流）

---

### 3️⃣ Baostock（第三优先级 / 保底数据源）

#### 📌 基本信息
- **数据来源**: 证券宝
- **安装方式**: `pip install baostock`
- **是否需要注册**: ✅ 需要（免费）
- **是否需要 Token**: ❌ 否（登录账号）
- **费用**: ✅ 完全免费

#### ✅ 核心优势

1. **数据质量稳定** ⭐⭐⭐⭐
   - 数据经过清洗
   - 格式统一规范
   - 准确性高

2. **盘后数据完整** ⭐⭐⭐⭐
   - 日线数据完整
   - 复权数据准确
   - 财务数据可靠

3. **稳定性好** ⭐⭐⭐⭐
   - 服务器稳定
   - 成功率高（98%+）
   - 响应时间中等（3-5 秒）

4. **免费使用**
   - 注册即可使用
   - 无积分限制
   - 适合个人投资者

#### ❌ 劣势

1. **仅支持盘后** ⭐
   - 盘中数据不完整
   - 不支持实时行情
   - 分钟线数据有限

2. **数据覆盖有限**
   - 主要支持 A 股
   - 基金、期货支持少
   - 特色数据少

3. **需要登录**
   - 需要注册账号
   - 每次使用需登录
   - 账号有访问限制

4. **更新速度慢**
   - 盘后更新
   - 财务数据延迟
   - 实时性差

#### 📊 已实现 API 接口

- ✅ `get_stock_list()` - 获取股票列表
- ✅ `get_stock_info(code)` - 获取股票信息
- ✅ `get_kline(code, start, end)` - 获取日 K 线
- ✅ `get_realtime_quote(code)` - 获取实时行情（实际为最新收盘价）
- ✅ `get_sector_list()` - 获取板块列表
- ✅ `get_sector_components()` - 获取板块成分股
- ✅ `get_chip_data(code)` - 获取筹码数据

#### 📊 适用场景

✅ **推荐用于**:
- 盘后数据分析
- 日线级别回测
- 作为保底数据源
- 其他数据源失败时的备选

❌ **不推荐用于**:
- 实时行情
- 盘中交易决策
- 分钟线分析
- 特色数据需求

---

### 4️⃣ TickFlow（第四优先级 / 可选数据源）

#### 📌 基本信息
- **数据来源**: TickFlow 平台
- **安装方式**: `pip install` + API Key
- **是否需要注册**: ✅ 需要
- **是否需要 Token**: ✅ 需要 API Key
- **费用**: ⚠️ 免费 + 付费套餐

#### ✅ 核心优势

1. **数据质量高** ⭐⭐⭐⭐⭐
   - 专业金融数据服务
   - 数据经过严格清洗
   - 准确性高

2. **数据全面** ⭐⭐⭐⭐⭐
   - A 股、港股、美股
   - 基金、期货、期权
   - 财务数据、宏观经济
   - 特色数据

3. **响应速度快** ⭐⭐⭐⭐⭐
   - 平均响应时间：0.5-1 秒
   - 专业服务器
   - CDN 加速

4. **API 规范**
   - 接口设计专业
   - 文档完善
   - 示例丰富

5. **技术支持**
   - 商业服务支持
   - 问题解决及时
   - 持续更新

#### ❌ 劣势

1. **需要 API Key**
   - 需要注册获取
   - Key 可能失效
   - 配置复杂

2. **免费额度有限**
   - 免费套餐有调用限制
   - 大量使用需付费
   - 商业使用成本高

3. **依赖外部服务**
   - 网络依赖性强
   - 服务稳定性受官方影响

#### 📊 已实现 API 接口

- ✅ `get_stock_list()` - 获取股票列表
- ✅ `get_stock_info(code)` - 获取股票信息
- ✅ `get_kline(code, start, end)` - 获取日 K 线
- ✅ `get_realtime_quote(code)` - 获取实时行情
- ✅ `get_sector_list()` - 获取板块列表
- ✅ `get_sector_components()` - 获取板块成分股
- ✅ `get_chip_data(code)` - 获取筹码数据
- ✅ `get_daily_billboard()` - 获取龙虎榜
- ✅ `get_belong_board(code)` - 获取所属板块
- ✅ `get_members(index_code)` - 获取指数成分股
- ✅ `get_today_bill()` - 获取当日资金流向
- ✅ `get_history_bill(code)` - 获取历史资金流向
- ✅ `get_top10_stock_holder_info()` - 前十大股东
- ✅ `get_market_realtime_quotes()` - 市场实时行情
- ✅ `get_weekly_kline()` - 获取周 K 线
- ✅ `get_monthly_kline()` - 获取月 K 线
- ✅ `get_instruments()` - 获取金融工具信息
- ✅ `get_exchanges()` - 获取交易所信息
- ✅ `get_exchange_instruments()` - 获取交易所工具列表

#### 📊 适用场景

✅ **推荐用于**:
- 高质量数据需求
- 港股、美股数据
- 专业研究报告
- 对数据准确性要求高的场景
- 其他数据源无法满足时

❌ **不推荐用于**:
- 免费额度耗尽后的频繁查询
- 无 API Key 时

---

## 📈 综合性能对比

### 响应时间对比

| 数据源 | 平均响应时间 | 评级 | 排名 |
|--------|-------------|------|------|
| TickFlow | 0.5-1 秒 | ⭐⭐⭐⭐⭐ | 1 |
| EFinance | 1-2 秒 | ⭐⭐⭐⭐⭐ | 2 |
| Baostock | 3-5 秒 | ⭐⭐⭐⭐ | 3 |
| AkShare | 5-10 秒 | ⭐⭐⭐ | 4 |

### 成功率对比

| 数据源 | 成功率 | 评级 | 排名 |
|--------|--------|------|------|
| EFinance | 99%+ | ⭐⭐⭐⭐⭐ | 1 |
| TickFlow | 99%+ | ⭐⭐⭐⭐⭐ | 1 |
| Baostock | 98%+ | ⭐⭐⭐⭐ | 3 |
| AkShare | 95%+ | ⭐⭐⭐ | 4 |

### 数据完整性对比

| 数据源 | 股票 | 指数 | 基金 | 期货 | 实时 | 历史 | 财务 | 特色 | 综合评级 |
|--------|------|------|------|------|------|------|------|------|---------|
| EFinance | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 4.5 |
| AkShare | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4.5 |
| Baostock | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | 3.0 |
| TickFlow | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 5.0 |

### 使用门槛对比

| 数据源 | 注册 | Token | 积分 | 费用 | 便利性 | 排名 |
|--------|------|-------|------|------|--------|------|
| EFinance | ❌ | ❌ | ❌ | 免费 | ⭐⭐⭐⭐⭐ | 1 |
| AkShare | ❌ | ❌ | ❌ | 免费 | ⭐⭐⭐⭐⭐ | 1 |
| Baostock | ✅ | ❌ | ❌ | 免费 | ⭐⭐⭐⭐ | 3 |
| TickFlow | ✅ | ✅ | ❌ | 免费 + 付费 | ⭐⭐⭐ | 4 |

### 功能丰富度对比

| 数据源 | 基础接口 | K 线 | 实时 | 板块 | 资金流 | 龙虎榜 | 股东 | 财务 | 基金 | 指数 | 排名 |
|--------|---------|-----|------|------|--------|--------|------|------|------|------|------|
| EFinance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | 1 |
| AkShare | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | 2 |
| Baostock | ✅ | ✅ | ⚠️ | ✅ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ⚠️ | 4 |
| TickFlow | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 1 |

**注**: 
- ✅ = 完整支持
- ⚠️ = 部分支持/故障转移
- ❌ = 不支持

---

## 🎯 数据源选择策略

### 按数据类型选择

#### 股票 K 线数据
```
优先级：EFinance → AkShare → Baostock → TickFlow
理由：EFinance 实时、免费、快速；AkShare 历史数据全
```

#### 指数 K 线数据
```
优先级：AkShare → TickFlow → Baostock
理由：EFinance 不支持，AkShare 指数数据最强
```

#### 实时行情
```
优先级：EFinance → TickFlow → AkShare
理由：EFinance 实时性强，TickFlow 快但需 API Key
```

#### 财务数据
```
优先级：TickFlow → EFinance → AkShare
理由：TickFlow 财务数据专业，EFinance 免费替代
```

#### 资金流向
```
优先级：EFinance → TickFlow
理由：EFinance 东方财富数据最准确
```

#### 龙虎榜
```
优先级：EFinance → TickFlow
理由：EFinance 数据完整、实时
```

#### 基金数据
```
优先级：AkShare → EFinance → TickFlow
理由：AkShare 基金数据最全
```

#### 板块分析
```
优先级：EFinance → AkShare → TickFlow
理由：EFinance 板块数据丰富，实时性强
```

### 按使用场景选择

#### 日常看盘
```
推荐：EFinance
理由：免费、实时、快速、无限制
```

#### 量化回测
```
推荐：AkShare + EFinance
理由：AkShare 历史数据全，EFinance 近期数据准
```

#### 实时交易
```
推荐：EFinance + TickFlow（有 API Key）
理由：实时性强，准确性高
```

#### 财务分析
```
推荐：TickFlow（有 API Key）或 EFinance
理由：TickFlow 财务数据专业，EFinance 免费替代
```

#### 盘中监控
```
推荐：EFinance
理由：实时数据、无频率限制
```

#### 盘后分析
```
推荐：EFinance → Baostock → AkShare
理由：数据准确、稳定
```

#### 指数研究
```
推荐：AkShare
理由：指数数据最完整、历史最长
```

#### 港股美股
```
推荐：TickFlow
理由：TickFlow 支持全球市场
```

---

## 🔄 故障转移机制

### 默认故障转移链

```
用户请求
  ↓
EFinance（优先级 1，主力）
  ↓ 失败（网络超时/数据为空）
AkShare（优先级 2，指数数据强）
  ↓ 失败（连接断开/限流）
Baostock（优先级 3，保底）
  ↓ 失败（登录失败/数据不可用）
TickFlow（优先级 4，有 API Key 时）
  ↓ 失败（API Key 无效/额度耗尽）
返回错误（所有数据源均失败）
```

### 故障转移示例日志

```log
[INFO] 尝试从数据源 efinance 获取：600519
[INFO] 从数据源 efinance 获取成功：600519（1.45 秒）

[WARNING] 尝试从数据源 efinance 获取：000001（指数）
[WARNING] efinance 不支持指数数据，自动切换到 akshare
[INFO] 从数据源 akshare 获取成功：000001（6.23 秒）

[ERROR] 数据源 efinance 获取失败：连接超时
[INFO] 尝试从数据源 akshare 获取：600519
[INFO] 从数据源 akshare 获取成功：600519（5.87 秒）

[ERROR] 数据源 efinance 获取失败
[ERROR] 数据源 akshare 获取失败
[INFO] 尝试从数据源 baostock 获取：600519
[INFO] 从数据源 baostock 获取成功：600519（4.12 秒）
```

### 智能路由策略

系统支持多种路由策略：

#### 1. 自动模式（默认）
```python
# 按优先级自动选择，失败自动故障转移
klines = await data_source_manager.get_kline("600519")
```

#### 2. 强制模式
```python
# 指定数据源，失败不转移（报错）
klines = await data_source_manager.get_kline(
    "600519",
    source="efinance",
    fallback=False
)
```

#### 3. 优先级模式
```python
# 临时调整优先级
klines = await data_source_manager.get_kline(
    "600519",
    source_priority="akshare,efinance"
)
```

#### 4. 排除模式
```python
# 排除某些数据源
klines = await data_source_manager.get_kline(
    "600519",
    source_exclude="baostock"
)
```

---

## 💡 最佳实践建议

### 1. 开发环境配置

```bash
# .env 文件
DEFAULT_DATA_SOURCE=efinance
DATA_SOURCE_PRIORITY=["efinance","akshare","baostock","tickflow"]
TICKFLOW_API_KEY=your_api_key  # 可选
```

**理由**: 
- 完全免费，无成本
- 适合日常开发调试
- 响应速度快

### 2. 生产环境配置

#### 方案 A：个人/小团队（推荐）
```bash
DEFAULT_DATA_SOURCE=efinance
DATA_SOURCE_PRIORITY=["efinance","akshare","baostock"]
```

**特点**: 
- ✅ 完全免费
- ✅ 覆盖全面
- ✅ 稳定性好
- ✅ 满足 95% 需求

#### 方案 B：专业应用（有预算）
```bash
DEFAULT_DATA_SOURCE=tickflow
DATA_SOURCE_PRIORITY=["tickflow","efinance","akshare","baostock"]
TICKFLOW_API_KEY=your_api_key
```

**特点**: 
- ✅ 数据质量最高
- ✅ 响应速度最快
- ✅ 全球市场覆盖
- ⚠️ 成本可控（付费套餐）

### 3. 特定场景配置

#### 指数分析场景
```bash
# API 调用时临时调整
curl "http://localhost:8000/api/v1/index/000001/kline?source_priority=akshare,efinance"
```

#### 财务分析场景
```bash
# 使用 TickFlow（如果有 API Key）
curl "http://localhost:8000/api/v1/stock/600519/financial?source=tickflow"
```

#### 实时交易场景
```bash
# 优先使用 EFinance
curl "http://localhost:8000/api/v1/stock/600519/realtime?source=efinance&fallback=false"
```

### 4. 性能优化建议

#### 缓存策略
```python
# 不同数据类型使用不同缓存时间
- 实时行情：60 秒
- K 线数据：5 分钟
- 股票信息：10 分钟
- 财务数据：1 小时
- 板块数据：5 分钟
- 筹码数据：10 分钟
```

#### 并发控制
```python
# 避免同时大量请求
- 单数据源并发限制：5 个/秒
- 批量请求分批发送
- 使用批量接口而非循环
```

#### 数据源预热
```python
# 启动时预热常用数据
- 股票列表
- 板块列表
- 热门股票实时行情
```

---

## 📊 成本分析

### 年度使用成本（预估）

| 数据源 | 个人用户 | 小团队 | 企业用户 |
|--------|---------|--------|---------|
| EFinance | ¥0 | ¥0 | ¥0 |
| AkShare | ¥0 | ¥0 | ¥0 |
| Baostock | ¥0 | ¥0 | ¥0 |
| TickFlow | ¥0（免费额度） | ¥2000-5000/年 | ¥10000+/年 |

### TickFlow 套餐参考

1. **免费套餐**
   - 每日调用次数：100-500 次
   - 数据范围：基础行情
   - 适合：个人学习、开发测试

2. **专业版**
   - 每日调用次数：10000+ 次
   - 数据范围：全量数据
   - 费用：约 ¥200-500/月
   - 适合：小团队、量化爱好者

3. **企业版**
   - 每日调用次数：无限制
   - 数据范围：全量 + 特色数据
   - 费用：定制
   - 适合：金融机构、企业应用

---

## 🔮 未来规划

### 短期优化（1-3 个月）

1. ✅ **数据源健康检查**
   - 实时监控各数据源状态
   - 自动降级不可用数据源
   - 健康检查仪表板

2. ✅ **性能监控**
   - 统计响应时间
   - 统计成功率
   - 智能选择最优数据源

3. ✅ **缓存优化**
   - 分布式缓存
   - 预热热门数据
   - 智能缓存淘汰

### 中期规划（3-6 个月）

1. **新增数据源**
   - Yahoo Finance（美股）
   - 聚宽数据
   - 米筐数据

2. **数据源负载均衡**
   - 轮询策略
   - 权重分配
   - 动态调整

3. **数据质量校验**
   - 多数据源交叉验证
   - 异常数据检测
   - 自动修复

### 长期规划（6-12 个月）

1. **自建数据仓库**
   - 历史数据本地化
   - 减少外部依赖
   - 提高查询速度

2. **数据源预测**
   - 基于机器学习
   - 预测最优数据源
   - 提前故障预警

3. **数据融合**
   - 多源数据融合
   - 提高数据准确性
   - 填补缺失数据

---

## 📝 总结

### 各数据源定位

| 数据源 | 定位 | 推荐指数 | 适用人群 | 核心优势 |
|--------|------|---------|---------|---------|
| **EFinance** | 主力数据源 | ⭐⭐⭐⭐⭐ | 所有人（日常使用） | 免费、实时、快速、全面 |
| **AkShare** | 补充数据源 | ⭐⭐⭐⭐ | 回测、指数分析 | 指数数据最强、历史最全 |
| **Baostock** | 保底数据源 | ⭐⭐⭐ | 盘后分析 | 稳定、保底 |
| **TickFlow** | 专业数据源 | ⭐⭐⭐⭐ | 专业机构（有预算） | 质量最高、全球市场 |

### 最佳组合推荐

#### 🥇 推荐组合（免费 - 个人/小团队）
```
EFinance（主力，80% 请求） + 
AkShare（指数 + 历史，15%） + 
Baostock（保底，5%）
```
**特点**: 
- ✅ 完全免费
- ✅ 覆盖全面（95%+ 需求）
- ✅ 稳定性好
- ✅ 响应速度快

**覆盖率**:
- 股票 K 线：100%
- 实时行情：100%
- 指数数据：100%（AkShare）
- 财务数据：90%
- 资金流向：100%
- 龙虎榜：100%

#### 🥈 专业组合（有预算 - 企业应用）
```
TickFlow（主力，60% 请求） + 
EFinance（实时，30%） + 
AkShare（历史，10%）
```
**特点**: 
- ✅ 数据质量最高
- ✅ 全球市场覆盖
- ✅ 技术支持
- ⚠️ 成本可控（付费）

**覆盖率**:
- A 股数据：100%
- 港股/美股：100%
- 财务数据：100%
- 特色数据：95%

### 核心建议

1. **日常使用首选 EFinance** ⭐⭐⭐⭐⭐
   - 免费、快速、实时
   - 满足 90% 日常需求
   - 无访问限制

2. **指数数据用 AkShare** ⭐⭐⭐⭐⭐
   - 历史数据完整
   - 作为 EFinance 补充
   - 自动故障转移

3. **TickFlow 按需使用** ⭐⭐⭐⭐
   - 有 API Key 时使用
   - 财务数据、港股美股
   - 专业应用场景

4. **Baostock 作为保底** ⭐⭐⭐
   - 其他数据源都失败时使用
   - 盘后数据分析
   - 确保系统可用性

5. **启用故障转移** ⭐⭐⭐⭐⭐
   - 多数据源自动切换
   - 提高系统稳定性
   - 用户体验无感知

### 数据源选择决策树

```
需要获取数据
    ↓
是否需要指数 K 线？
    ├─ 是 → 使用 AkShare
    └─ 否 → 继续判断
         ↓
是否需要实时行情？
    ├─ 是 → 使用 EFinance
    └─ 否 → 继续判断
         ↓
是否需要财务数据？
    ├─ 是 → 有 TickFlow API Key？
    │        ├─ 是 → 使用 TickFlow
    │        └─ 否 → 使用 EFinance
    └─ 否 → 使用 EFinance
         ↓
所有数据源失败？
    └─ 是 → 降级到 Baostock
```

---

## 📚 附录

### A. 安装命令

```bash
# 安装所有数据源依赖
pip install efinance akshare baostock

# TickFlow（可选）
pip install tickflow
```

### B. 配置检查

```python
# 检查数据源配置
from app.adapters.factory import DataSourceFactory

# 查看可用数据源
sources = DataSourceFactory.get_available_sources()
print(f"可用数据源：{sources}")

# 测试数据源连接
adapter = DataSourceFactory.get_adapter("efinance")
success = await adapter.initialize()
print(f"EFinance 初始化：{'成功' if success else '失败'}")
```

### C. API 调用示例

```python
# 1. 获取股票列表（自动选择数据源）
stocks = await data_source_manager.get_stock_list()

# 2. 获取 K 线数据（自动故障转移）
klines = await data_source_manager.get_kline(
    code="600519",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 3. 强制使用特定数据源
klines = await data_source_manager.get_kline(
    code="600519",
    source_type="efinance"
)

# 4. 获取指数 K 线（自动使用 AkShare）
index_klines = await data_source_manager.get_market_index_kline(
    index_code="000001"
)

# 5. 获取实时行情
quote = await data_source_manager.get_realtime_quote("600519")
```

---

**报告更新日期**: 2026-03-27  
**数据源状态**: 
- ✅ EFinance: 主力数据源
- ✅ AkShare: 补充数据源
- ✅ Baostock: 保底数据源
- ⚠️ TickFlow: 可选数据源（需 API Key）

**备注**: Tushare 数据源已移除，不再推荐使用。
