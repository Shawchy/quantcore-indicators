# 后端日志问题修复报告

## 问题描述

后端服务启动失败，出现语法错误：

```
SyntaxError: 'await' outside async function
```

---

## 根本原因

在修复回测优化器的持久化缺失问题时，在普通函数中错误地使用了 `await` 关键字。

**错误代码位置**: `backend/app/core/backtest/optimizer.py` 第 218 行

```python
# ❌ 错误：在普通函数中使用 await
def optimize(
    self,
    code: str,
    start_date: str,
    end_date: str,
    strategy_type: str,
    param_ranges: Dict[str, List[Any]],
    initial_capital: float = 1000000,
    n_iterations: int = 20,
    method: str = "bayesian"
) -> OptimizationResult:  # ← 普通函数，不是 async def
    # ...
    
    # 持久化保存到数据库和 Parquet
    if klines:
        from app.services.data_persistence import data_persistence
        try:
            await data_persistence.save_klines(code, klines, "qfq")  # ❌ await 在非异步函数中
            logger.info(f"回测优化：已保存 {len(klines)} 条 K 线数据：{code}")
        except Exception as e:
            logger.warning(f"回测优化：保存 K 线数据失败：{e}")
```

---

## 修复方案

由于 `optimize()` 方法是普通函数（不是异步函数），需要使用 `asyncio.run()` 来运行异步函数。

**修复后代码**:

```python
# ✅ 正确：使用 asyncio.run() 运行异步函数
def optimize(
    self,
    code: str,
    start_date: str,
    end_date: str,
    strategy_type: str,
    param_ranges: Dict[str, List[Any]],
    initial_capital: float = 1000000,
    n_iterations: int = 20,
    method: str = "bayesian"
) -> OptimizationResult:
    # ...
    
    # 持久化保存到数据库和 Parquet
    if klines:
        from app.services.data_persistence import data_persistence
        try:
            # 使用 asyncio.run() 运行异步函数
            asyncio.run(data_persistence.save_klines(code, klines, "qfq"))
            logger.info(f"回测优化：已保存 {len(klines)} 条 K 线数据：{code}")
        except Exception as e:
            logger.warning(f"回测优化：保存 K 线数据失败：{e}")
```

---

## 对比：Backtest API 端点的正确用法

**文件**: `backend/app/api/v1/endpoints/backtest.py`

```python
# ✅ 正确：异步函数可以使用 await
@router.post("/run", response_model=ResponseModel[dict])
async def run_backtest(
    backtest_request: BacktestRequest,
    current_user: CurrentUser = Depends
):
    # ...
    
    klines = await data_source_manager.get_kline(code, start_date, end_date, "qfq")
    
    # 持久化保存到数据库和 Parquet
    if klines:
        from app.services.data_persistence import data_persistence
        try:
            await data_persistence.save_klines(code, klines, "qfq")  # ✅ await 在异步函数中
            logger.info(f"回测任务：已保存 {len(klines)} 条 K 线数据：{code}")
        except Exception as e:
            logger.warning(f"回测任务：保存 K 线数据失败：{e}")
```

---

## 关键区别

| 特性 | 普通函数 | 异步函数 |
|------|---------|---------|
| 定义方式 | `def func():` | `async def func():` |
| 调用异步函数 | `asyncio.run(async_func())` | `await async_func()` |
| 返回值 | 直接返回 | 返回 `Awaitable[T]` |
| 使用场景 | 同步代码、CPU 密集型 | IO 密集型、并发操作 |

---

## 修复验证

### 启动日志

```
2026-03-11 01:38:02 | INFO | app.main:startup_event:84 - 数据库初始化完成
2026-03-11 01:38:02 | INFO | app.adapters.akshare_adapter:initialize:107 - AkShare 适配器初始化成功
2026-03-11 01:38:02 | INFO | app.adapters.factory:initialize:52 - 数据源 akshare 初始化成功
2026-03-11 01:38:02 | INFO | app.adapters.baostock_adapter:initialize:33 - Baostock 适配器初始化成功
2026-03-11 01:38:02 | INFO | app.services.data_loader:start:75 - 数据加载器已启动（3 个 worker 并发）
2026-03-11 01:38:02 | INFO | app.main:startup_event:93 - 数据加载器已启动（按需加载模式）
INFO: Application startup complete.
```

✅ 后端服务已成功启动，无语法错误

---

## 经验教训

### 1. 识别函数类型

在添加 `await` 之前，先确认函数是异步函数：

```python
# ❌ 错误示例
def sync_function():
    await async_function()  # SyntaxError!

# ✅ 正确示例
async def async_function():
    await async_function()

# ✅ 正确示例
def sync_function():
    asyncio.run(async_function())
```

### 2. 使用 asyncio.run() 的场景

当需要在以下场景运行异步代码时，使用 `asyncio.run()`：

- 普通函数中调用异步函数
- 类的方法（非异步）中调用异步函数
- 脚本入口点运行异步主函数

### 3. 代码审查要点

在代码审查时，检查：
- ✅ `await` 是否在 `async def` 函数内
- ✅ 普通函数是否使用 `asyncio.run()`
- ✅ 混合使用同步和异步代码时的正确性

---

## 相关文件

- `backend/app/core/backtest/optimizer.py` - 已修复
- `backend/app/api/v1/endpoints/backtest.py` - 正确示例
- `backend/app/services/data_persistence.py` - 异步持久化服务

---

## 总结

本次问题是由于在修复持久化遗漏时，在普通函数中错误使用了 `await` 导致的语法错误。通过改用 `asyncio.run()` 成功修复。

**关键点**:
- ✅ 普通函数使用 `asyncio.run()` 调用异步函数
- ✅ 异步函数使用 `await` 调用异步函数
- ✅ 代码审查时注意检查函数类型和调用方式

后端服务现已正常启动运行。
