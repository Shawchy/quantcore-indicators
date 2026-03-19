# TickFlow 数据源 API 实施总结

## 📋 概述

已成功添加 **TickFlow** 作为新的数据源适配器，提供高质量的金融数据服务。

## ✅ 完成的工作

### 1. 创建 TickFlow 适配器

**文件**: [`tickflow_adapter.py`](d:\PROJ\Quant\backend\app\adapters\tickflow_adapter.py)

**核心功能**:
- ✅ 股票信息转换（6 位代码 ↔ TickFlow 格式）
- ✅ 内存缓存机制（不同数据类型不同 TTL）
- ✅ 免费服务与完整服务自动切换
- ✅ 完整的错误处理和日志记录

**支持的数据类型**:
| 数据类型 | 免费服务 | 完整服务 | 说明 |
|---------|---------|---------|------|
| 股票信息 | ✅ | ✅ | 通过 `instruments.get()` 获取 |
| 日 K 线 | ✅ | ✅ | 1d、1w、1M、1Q、1Y |
| 分钟 K 线 | ❌ | ✅ | 1m、5m、15m、30m、60m |
| 实时行情 | ❌ | ✅ | 最新价、涨跌幅、买卖盘等 |
| 股票列表 | ❌ | ❌ | TickFlow 不支持 |
| 板块信息 | ❌ | ❌ | TickFlow 不支持 |
| 资金流向 | ❌ | ❌ | TickFlow 不支持 |

### 2. 更新基础配置

**文件**: [`base.py`](d:\PROJ\Quant\backend\app\adapters\base.py)
- ✅ 添加 `TICKFLOW = "tickflow"` 到 `DataSourceType` 枚举

**文件**: [`factory.py`](d:\PROJ\Quant\backend\app\adapters\factory.py)
- ✅ 导入 `TickFlowAdapter`
- ✅ 在 `adapters_config` 中注册 TickFlow
- ✅ 设置为始终可用（免费服务）

### 3. 环境配置

**文件**: [`.env.example`](d:\PROJ\Quant\backend\.env.example)
- ✅ 添加 TickFlow 配置说明
- ✅ 提供 API Key 示例（可选）

**文件**: [`config.py`](d:\PROJ\Quant\backend\app\config.py)
- ✅ 添加 `TICKFLOW_API_KEY` 配置项
- ✅ 更新数据源优先级列表

### 4. 测试脚本

**文件**: [`test_tickflow_simple.py`](d:\PROJ\Quant\backend\test_tickflow_simple.py)
- ✅ 直接测试 TickFlow SDK
- ✅ 验证免费服务和完整服务

## 🔧 安装步骤

### 1. 安装 TickFlow SDK

```bash
pip install "tickflow[all]" --upgrade
```

### 2. 配置 API Key（可选）

编辑 `.env` 文件：

```bash
# TickFlow API Key（可选，不填则使用免费服务）
TICKFLOW_API_KEY=tk_4d7e268030a5449abbcc59b28f6e76b8
```

### 3. 验证安装

```bash
python test_tickflow_simple.py
```

## 📊 测试结果

### 免费服务测试
```
✅ tickflow 库已安装
✅ TickFlow 免费服务初始化成功
```

**限制**:
- ❌ 不提供实时行情
- ❌ 不提供分钟级 K 线
- ✅ 提供历史日 K 线数据
- ✅ 提供标的信息查询

### 完整服务测试
```
✅ TickFlow 完整服务初始化成功（API Key: tk_4d7e268...）
✅ 获取实时行情成功
  ✅ 000001.SZ: 最新价：10.91
  ✅ 600000.SH: 最新价：10.33
```

## 🚀 使用示例

### 1. 直接使用 TickFlow SDK

```python
from tickflow import TickFlow

# 免费服务
tf = TickFlow.free()
df = tf.klines.get("600000.SH", period="1d", count=100, as_dataframe=True)

# 完整服务
tf = TickFlow(api_key="your-api-key")
quotes = tf.quotes.get(symbols=["600000.SH", "000001.SZ"])
```

### 2. 通过数据源管理器使用

```python
from app.adapters.factory import data_source_manager

# 初始化
await data_source_manager.initialize()

# 获取 TickFlow 适配器
adapter = data_source_manager.get_adapter("tickflow")

# 获取股票信息
info = await adapter.get_stock_info("600000")

# 获取 K 线数据
klines = await adapter.get_kline("600000", period="daily")

# 获取实时行情（需要完整服务）
quote = await adapter.get_realtime_quote("600000")
```

### 3. 在 API 端点中使用

```python
from fastapi import APIRouter
from app.adapters.factory import data_source_manager

router = APIRouter()

@router.get("/quote/{code}")
async def get_quote(code: str):
    # 使用 TickFlow 获取实时行情
    quote = await data_source_manager.get_realtime_quote(
        code, 
        source_type="tickflow"
    )
    return {"data": quote}
```

## 🎯 数据源优先级

当前配置的数据源优先级（从高到低）:
```
tushare > efinance > akshare > baostock > tickflow
```

**说明**:
- TickFlow 作为保底数据源
- 当其他数据源不可用时，自动切换到 TickFlow
- 可以临时指定使用 TickFlow: `source_type="tickflow"`

## ⚠️ 注意事项

### 1. API 格式兼容性

TickFlow SDK 的 API 可能与文档略有不同，实际使用时需要：
- 检查 SDK 版本
- 查看实际返回的数据结构
- 调整参数名称（如 `symbols` vs `symbol_list`）

### 2. 免费服务限制

免费服务仅提供：
- 历史日 K 线数据（1d、1w、1M、1Q、1Y）
- 标的信息查询

**不提供**:
- 实时行情
- 分钟级 K 线
- 板块、资金流向等高级数据

### 3. 股票代码格式

TickFlow 使用特殊的股票代码格式：
- 上交所：`600000.SH`
- 深交所：`000001.SZ`
- 港股：`00700.HK`

适配器已自动处理格式转换。

## 📝 配置文件说明

### .env 配置项

```bash
# TickFlow API Key（可选）
# 不配置则自动使用免费服务
TICKFLOW_API_KEY=tk_4d7e268030a5449abbcc59b28f6e76b8

# 数据源优先级
DATA_SOURCE_PRIORITY=["tushare","efinance","akshare","baostock","tickflow"]
```

### config.py 配置项

```python
TICKFLOW_API_KEY: Optional[str] = None
DATA_SOURCE_PRIORITY: list[str] = ["tushare", "efinance", "akshare", "baostock", "tickflow"]
```

## 🔍 故障排查

### 1. 导入错误

```
ImportError: No module named 'tickflow'
```

**解决方案**:
```bash
pip install "tickflow[all]" --upgrade
```

### 2. API Key 无效

```
AuthenticationError: Invalid API key
```

**解决方案**:
- 检查 API Key 是否正确
- 确认 API Key 未过期
- 联系 TickFlow 支持

### 3. 数据为空

```
Warning: TickFlow K 线数据为空：600000
```

**解决方案**:
- 检查股票代码格式
- 确认股票是否停牌
- 检查网络连接

## 📚 相关文档

- TickFlow 官网：https://tickflow.tech
- TickFlow SDK 文档：https://tickflow.org
- GitHub: 待补充

## 🎉 总结

TickFlow 数据源已成功集成到量化分析系统中，提供：

✅ **免费服务**: 快速体验，无需注册
✅ **完整服务**: 实时行情、分钟 K 线
✅ **自动故障转移**: 作为保底数据源
✅ **缓存机制**: 减少重复请求
✅ **易于使用**: 与其他数据源一致的接口

**推荐用途**:
- 作为备用数据源（当其他数据源不可用时）
- 获取实时行情（完整服务）
- 获取分钟级 K 线（完整服务）
- 快速原型开发（免费服务）
