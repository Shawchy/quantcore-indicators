# Tushare 测试账号配置

## ✅ 已配置的测试账号

### 测试 Token 信息

**Token**: `25879cba3233f4ddc5554690d46364a3f777fc8375c6398acccbc5de`

**配置位置**: `backend/.env`

**配置状态**: ✅ 已配置

### 当前积分状态

**TUSHARE_POINTS**: `120` 分（默认）

**可用权限**:
- ✅ 日线行情（daily）
- ✅ 复权因子（adj_factor）
- ✅ 股票列表（stock_basic）
- ✅ 指数列表（index_basic）
- ✅ 指数日线（index_daily）
- ✅ 基金数据（fund_basic）
- ✅ 分红送股（dividend）
- ✅ 交易日历（trade_cal）
- ✅ 停复牌信息（suspend_d）
- ✅ 宏观数据（GDP、CPI、PPI 等）
- ✅ 股东人数（stk_holdernumber）

**需要更高级别**:
- 🔒 龙虎榜（需要 200 分）
- 🔒 业绩预告（需要 800 分）
- 🔒 周线/月线（需要 2000 分）
- 🔒 分钟 K 线（需要 5000 分）
- 🔒 Level-2 数据（需要 10000 分）

## 🧪 测试配置

### 配置文件

**文件**: `backend/.env`

```env
# 数据源配置
DEFAULT_DATA_SOURCE=tushare

# Tushare 配置
TUSHARE_TOKEN=25879cba3233f4ddc5554690d46364a3f777fc8375c6398acccbc5de

# Tushare 积分配置（默认 120 分）
TUSHARE_POINTS=120
```

### 快速测试

#### 1. 验证 Token 配置

```bash
cd backend
python -c "from app.config import settings; print(f'Token: {settings.TUSHARE_TOKEN[:10]}...{settings.TUSHARE_TOKEN[-5:]}')"
```

#### 2. 测试 Tushare 连接

```bash
cd backend
python test_tushare_points.py
```

#### 3. 测试 API 注册表

```bash
cd backend
python test_api_registry.py
```

## 📊 测试场景

### 场景 1: 日线 K 线数据（120 分可用）

```python
# 使用测试账号调用日线数据
from app.adapters.factory import DataSourceManager
import asyncio

async def test_daily():
    manager = DataSourceManager()
    await manager.initialize()
    
    # 获取日线数据（120 分权限）
    klines = await manager.get_kline("600519", "2024-01-01", "2024-12-31")
    print(f"获取到 {len(klines)} 条日线数据")

asyncio.run(test_daily())
```

**预期结果**: ✅ 成功获取数据

### 场景 2: 周线 K 线数据（需要 2000 分）

```python
# 使用测试账号调用周线数据
async def test_weekly():
    manager = DataSourceManager()
    await manager.initialize()
    
    # 获取周线数据（需要 2000 分，当前 120 分）
    adapter = manager.get_adapter("tushare")
    
    if hasattr(adapter, 'get_weekly_kline'):
        klines = await adapter.get_weekly_kline("600519")
        print(f"获取到 {len(klines)} 条周线数据")
    else:
        print("Tushare 不可用，已降级到其他数据源")

asyncio.run(test_weekly())
```

**预期结果**: ⚠️ 积分不足，自动降级到 AkShare

### 场景 3: 股票列表（120 分可用）

```python
# 获取股票列表
async def test_stock_list():
    manager = DataSourceManager()
    await manager.initialize()
    
    stocks = await manager.get_stock_list()
    print(f"获取到 {len(stocks)} 只股票")

asyncio.run(test_stock_list())
```

**预期结果**: ✅ 成功获取数据

## 🔍 验证步骤

### 步骤 1: 检查 Token 配置

```bash
cd backend
python -c "
from app.config import settings
print('=' * 60)
print('Tushare 配置检查')
print('=' * 60)
print(f'Token: {settings.TUSHARE_TOKEN[:10]}...{settings.TUSHARE_TOKEN[-5:]}')
print(f'积分：{settings.TUSHARE_POINTS}分')
print(f'数据源：{settings.DEFAULT_DATA_SOURCE}')
print('=' * 60)
"
```

### 步骤 2: 初始化数据源

```bash
cd backend
python -c "
import asyncio
from app.adapters.factory import DataSourceFactory

async def test():
    await DataSourceFactory.initialize()
    available = DataSourceFactory.get_available_sources()
    print(f'可用数据源：{available}')

asyncio.run(test())
"
```

### 步骤 3: 测试 API 调用

```bash
cd backend
python -c "
import asyncio
from app.adapters.factory import DataSourceManager

async def test():
    manager = DataSourceManager()
    await manager.initialize()
    
    # 测试股票列表
    stocks = await manager.get_stock_list()
    print(f'股票列表：{len(stocks)}只')
    
    # 测试日线数据
    klines = await manager.get_kline('600519')
    print(f'贵州茅台日线：{len(klines)}条')

asyncio.run(test())
"
```

## ⚠️ 注意事项

### 1. Token 安全

- ✅ Token 已配置在 `.env` 文件中
- ✅ `.env` 文件已在 `.gitignore` 中排除
- ⚠️ **不要**将 Token 分享给他人
- ⚠️ **不要**将 Token 提交到 Git 仓库

### 2. 积分限制

- 当前积分：120 分
- 可用 API：11 个
- 不可用 API：26 个
- 建议：完成任务获取更多积分

### 3. 调用频率

- 120 分：20 次/分钟，500 次/天
- 避免频繁调用
- 使用缓存机制

## 📈 获取积分方法

### 免费获取

1. **注册账号**: +100 分（已完成）
2. **完善信息**: +20 分（建议完成）
3. **关注公众号**: +50 分（建议完成）
4. **邀请好友**: +50 分/人

### 推荐任务

**优先级 1** (立即可做):
- ✅ 注册账号（已完成）
- 📝 完善个人信息（+20 分）
- 📱 关注公众号（+50 分）

**优先级 2** (有时间再做):
- 👥 邀请好友（+50 分/人）

**总计**: 免费可获得 220 分

### 积分用途

- **120 分**: 日线回测、基本面分析 ✅ 当前可用
- **200 分**: 龙虎榜、大宗交易 🔒 还差 80 分
- **800 分**: 财务数据、业绩预告 🔒 还差 680 分
- **2000 分**: 周线/月线 🔒 还差 1880 分
- **5000 分**: 分钟 K 线 🔒 还差 4880 分

## 🎯 下一步

### 立即行动

1. **验证配置**: 运行测试脚本验证 Token 配置
2. **完善信息**: 登录 Tushare 官网完善个人信息
3. **关注公众号**: 关注"Tushare 社区"公众号
4. **测试功能**: 运行示例代码测试 API 调用

### 登录 Tushare 官网

**网址**: https://tushare.pro/

**操作**:
1. 使用账号登录
2. 进入个人中心
3. 完善个人信息（+20 分）
4. 关注公众号（+50 分）
5. 查看积分详情

## 📚 相关文档

1. **配置指南**: [`TUSHARE_SETUP.md`](file:///d:/Project/Quant/backend/TUSHARE_SETUP.md)
2. **积分配置**: [`TUSHARE_POINTS_GUIDE.md`](file:///d:/Project/Quant/backend/TUSHARE_POINTS_GUIDE.md)
3. **API 分组**: [`TUSHARE_API_GROUPING_COMPLETE.md`](file:///d:/Project/Quant/backend/TUSHARE_API_GROUPING_COMPLETE.md)
4. **BUG 修复**: [`BUG_FIX_REPORT.md`](file:///d:/Project/Quant/backend/BUG_FIX_REPORT.md)

---

**配置时间**: 2026-03-12  
**Token 状态**: ✅ 已配置  
**积分状态**: 120 分  
**可用 API**: 11 个  
**测试状态**: ⏳ 等待验证
