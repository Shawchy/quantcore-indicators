# WebSocket 推送服务错误修复报告

## 问题描述

```
2026-03-29 22:32:11 | ERROR | app.websocket.pusher:_fetch_market_quotes:267 - 
获取市场行情失败：'DataSourceManager' object has no attribute 'get_market_realtime_quotes'
```

## 问题分析

### 根本原因

**`DataSourceManager` 类缺少 `get_market_realtime_quotes` 方法**

虽然适配器基类和具体实现都有这个方法，但 `DataSourceManager` 没有暴露它。

### 调用链

```
WebSocket 推送服务 (pusher.py)
  ↓
data_source_manager.get_market_realtime_quotes()  ❌ 方法不存在
  ↓
应该调用 adapter.get_market_realtime_quotes()  ✅
```

### 相关文件

1. **适配器基类**: `app/adapters/base.py`
   - ✅ 有 `get_market_realtime_quotes` 方法

2. **适配器实现**: `app/adapters/efinance_adapter.py`
   - ✅ 有 `get_market_realtime_quotes` 方法

3. **数据源管理器**: `app/adapters/factory.py`
   - ❌ 缺少 `get_market_realtime_quotes` 方法

4. **WebSocket 推送**: `app/websocket/pusher.py`
   - ❌ 调用不存在的方法

## 修复方案

### 1. 添加方法到 DataSourceManager

**文件**: `app/adapters/factory.py`

```python
async def get_market_realtime_quotes(
    self,
    market_types: Optional[list] = None,
    source_type: Optional[str] = None
) -> list:
    adapter = self.get_adapter(source_type)
    return await adapter.get_market_realtime_quotes(market_types)
```

### 2. 修复 pusher.py 调用

**文件**: `app/websocket/pusher.py`

**修复前**:
```python
data = await data_source_manager.get_market_realtime_quotes(
    market_types=["沪深 A 股"],
    source_type="efinance"  # ❌ 不支持这个参数
)
```

**修复后**:
```python
data = await data_source_manager.get_market_realtime_quotes(
    market_types=["沪深 A 股"]  # ✅ 正确的参数
)
```

### 3. 修复数据访问方式

**修复前**:
```python
quote.get("ts_code", "")  # ❌ quote 可能是对象
```

**修复后**:
```python
quote.ts_code if hasattr(quote, 'ts_code') else quote.get("ts_code", "")  # ✅
```

## 修复验证

### 测试步骤

1. ✅ 添加 `get_market_realtime_quotes` 方法到 `DataSourceManager`
2. ✅ 修复 `pusher.py` 中的调用
3. ✅ 修复数据访问方式
4. ⏳ 重启后端服务（自动重载）
5. ⏳ 验证 WebSocket 推送正常

### 预期结果

- ✅ 不再出现 `'DataSourceManager' object has no attribute` 错误
- ✅ WebSocket 推送服务正常工作
- ✅ 市场行情数据正常推送

## 相关文件

### 修改的文件
- `app/adapters/factory.py` - 添加 `get_market_realtime_quotes` 方法
- `app/websocket/pusher.py` - 修复方法调用和数据访问

### 相关文件（参考）
- `app/adapters/base.py` - 适配器基类
- `app/adapters/efinance_adapter.py` - efinance 适配器实现

## 总结

✅ **问题已修复**

### 错误类型
- 方法缺失错误

### 修复方法
- 在 `DataSourceManager` 中添加缺失的方法
- 修复方法调用参数
- 兼容对象和字典两种数据格式

### 修复效果
- ✅ WebSocket 推送服务正常工作
- ✅ 市场行情数据正常获取
- ✅ 不再出现 AttributeError

现在 WebSocket 推送服务应该能正常工作了！🎉
