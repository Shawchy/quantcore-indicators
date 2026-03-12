# Tushare 数据源配置指南

## 概述

本系统现已支持 **Tushare** 作为优先数据源，实现多数据源智能切换（Tushare → AkShare → Baostock）。

## 为什么使用 Tushare？

Tushare 是一个免费、开源的金融数据接口库，提供：
- ✅ 高质量的 A 股历史行情数据
- ✅ 实时行情数据
- ✅ 分钟级 K 线数据（1/5/15/30/60 分钟）
- ✅ 指数数据
- ✅ 财务数据
- ✅ 更稳定的数据源
- ✅ 更好的数据质量

## 配置步骤

### 方法一：直接修改 .env 文件（推荐）

1. 打开 `backend/.env` 文件
2. 添加或修改以下配置：

```env
# 设置默认数据源为 Tushare
DEFAULT_DATA_SOURCE=tushare

# 填写您的 Tushare Token
TUSHARE_TOKEN=your-tushare-token-here
```

### 方法二：使用环境变量

在启动服务前，设置环境变量：

**Windows PowerShell:**
```powershell
$env:DEFAULT_DATA_SOURCE="tushare"
$env:TUSHARE_TOKEN="your-tushare-token-here"
```

**Linux/Mac:**
```bash
export DEFAULT_DATA_SOURCE=tushare
export TUSHARE_TOKEN=your-tushare-token-here
```

## 获取 Tushare Token

### 步骤 1: 注册账号

访问 [Tushare 官网](https://tushare.pro/) 注册免费账号

### 步骤 2: 获取 Token

1. 登录后进入个人中心
2. 点击左侧菜单 "接口TOKEN"
3. 复制您的 Token（一串 40 位的字母数字组合）

### 步骤 3: 提高积分（可选）

Tushare 采用积分制，默认注册送 100 积分，基础积分即可满足日常使用：
- 100 积分：基础行情数据（日线、分钟线等）
- 500 积分：更多财务数据、资金流向等
- 1000+ 积分：高级数据、实时行情等

**提示**: 对于本系统的基础功能，100 积分已经足够使用。

## 数据源优先级

系统会自动按照以下优先级选择数据源：

1. **Tushare** (优先) - 需要配置 Token
2. **AkShare** (备选) - 免费，无需配置
3. **Baostock** (保底) - 免费，无需配置

### 智能切换逻辑

- 如果 Tushare Token 配置成功 → 使用 Tushare
- 如果 Tushare Token 未配置或失效 → 自动切换到 AkShare
- 如果 AkShare 不可用 → 切换到 Baostock

## 验证配置

启动后端服务后，查看日志输出：

```
[INFO] 数据源 tushare 初始化成功（优先级：1)
[INFO] 数据源工厂初始化完成，可用数据源：['tushare', 'akshare', 'baostock']
[INFO] 当前默认数据源：tushare (实际使用：tushare)
```

如果看到以上日志，说明 Tushare 配置成功！

## 常见问题

### Q1: Token 配置后仍然使用 AkShare？

**原因**: Token 无效或积分不足

**解决方案**:
1. 检查 Token 是否正确复制（40 位，无空格）
2. 登录 Tushare 官网验证 Token 有效性
3. 查看日志中的错误信息

### Q2: 如何切换回 AkShare？

修改 `.env` 文件：
```env
DEFAULT_DATA_SOURCE=akshare
```

### Q3: Token 安全吗？

**重要提示**: 
- ✅ Token 已添加到 `.env` 文件，不会被提交到 Git
- ✅ `.env` 文件已在 `.gitignore` 中排除
- ⚠️ 不要将 Token 分享给他人
- ⚠️ 定期更换 Token 以提高安全性

### Q4: 分钟线数据如何使用？

Tushare 支持多周期分钟线数据，系统已自动集成：

```python
# 获取 5 分钟 K 线（前复权）
data = await data_source_manager.get_stock_zh_a_minute(
    symbol="600519",
    period="5",
    adjust="qfq"
)

# 获取 1 分钟分时数据
data = await data_source_manager.get_stock_intraday_em(symbol="000001")
```

## 已实现的 Tushare API

系统已完整实现以下 Tushare API：

### 基础数据
- ✅ `get_stock_list()` - 股票列表
- ✅ `get_stock_info()` - 股票信息

### K 线数据
- ✅ `get_kline()` - 日线 K 线（支持复权）
- ✅ `get_market_index_kline()` - 指数 K 线
- ✅ `get_stock_zh_a_minute()` - 分钟 K 线（1/5/15/30/60 分钟）

### 实时数据
- ✅ `get_realtime_quote()` - 实时行情
- ✅ `get_all_a_shares_realtime()` - 全市场实时行情
- ✅ `get_stock_intraday_em()` - 分时数据

### 其他数据
- ✅ `get_sector_list()` - 板块列表
- ✅ `get_sector_components()` - 板块成分股
- ✅ `get_chip_data()` - 筹码数据

## 技术实现

### 数据源工厂模式

系统采用工厂模式管理多个数据源：

```python
# 自动选择最优数据源
adapter = DataSourceFactory.get_adapter()  # 返回 Tushare

# 指定数据源
adapter = DataSourceFactory.get_adapter("akshare")  # 返回 AkShare

# 智能降级
adapter = DataSourceFactory.get_adapter("tushare")  # 如果 Tushare 不可用，自动返回 AkShare
```

### 无感切换

所有 API 调用保持一致的接口，无需修改业务代码：

```python
# 无论使用哪个数据源，调用方式相同
kline = await data_source_manager.get_kline("600519", "2024-01-01", "2024-12-31")
```

## 性能对比

| 数据源 | 日线速度 | 分钟线速度 | 稳定性 | 数据质量 |
|--------|---------|-----------|--------|---------|
| Tushare | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| AkShare | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Baostock | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## 下一步

配置完成后，系统会自动使用 Tushare 作为默认数据源，享受更快速、更稳定的数据服务！

如有问题，请查看日志文件 `logs/app.log` 获取详细信息。
