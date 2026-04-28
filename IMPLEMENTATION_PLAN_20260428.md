# Quant 系统优化实施计划

**创建时间**: 2026-04-28  
**基于报告**: PROJECT_IMPLEMENTATION_REPORT_20260428.md  

---

## 实施原则

1. **先易后难**: 优先清理简单但有价值的 TODO 标记
2. **风险可控**: 不破坏现有功能的前提下优化
3. **可验证**: 每个任务完成后必须有验证方式
4. **分阶段**: 按高、中、低优先级分阶段推进

---

## 阶段一：清理 TODO/FIXME 标记（优先级：高）

### 1.1 后端 security.py - DEBUG 模式安全加固

**文件**: `backend/app/core/security.py`  
**问题**: DEBUG 模式下打印默认密码到日志  
**修复方案**:
- 保留开发环境便利性的同时，增加安全警告
- 生产环境禁止打印任何敏感信息

### 1.2 后端 config.py - DEBUG 模式规范化

**文件**: `backend/app/config.py`  
**问题**: DEBUG 模式配置需增加注释说明  
**修复方案**: 增加环境变量配置指引

### 1.3 后端 market.py - 持久化迁移标记清理

**文件**: `backend/app/api/v1/endpoints/market.py`  
**问题**: 2 处 TODO 提示持久化功能未迁移  
**修复方案**:
- 实现 `save_market_ranking` 方法
- 实现 `get_market_ranking_history` 方法

### 1.4 后端 tickflow_adapter.py - 缓存和持久化

**文件**: `backend/app/adapters/tickflow_adapter.py`  
**问题**: 3 处 TODO 标记缓存和持久化未实现  
**修复方案**:
- 使用现有 `storage_service` 实现缓存功能
- 实现交易所数据持久化

### 1.5 前端 StockHolderPage - 注释完善

**文件**: `frontend/src/pages/StockHolderPage.tsx`  
**问题**: 注释中包含 XXX 占位符  
**修复方案**: 替换为实际说明文本

---

## 阶段二：完善 Rust 引擎核心功能（优先级：高）

### 2.1 订单匹配引擎 (matching.rs)

**文件**: `quantcore/rust-engine/src/engine/matching.rs`  
**实现内容**:
- 市价单匹配逻辑（使用 bar 的开盘价）
- 限价单匹配逻辑（检查价格条件）
- 滑点计算和应用
- 手续费计算（佣金 + 印花税）
- 成交记录生成

### 2.2 回测引擎 (backtest.rs)

**文件**: `quantcore/rust-engine/src/engine/backtest.rs`  
**实现内容**:
- 遍历 K 线数据执行策略
- 订单匹配和成交处理
- 每日账户价值记录
- 回测结果计算（调用 PerformanceAnalyzer）

### 2.3 风险管理器 (risk/manager.rs)

**文件**: `quantcore/rust-engine/src/risk/manager.rs`  
**实现内容**:
- 仓位检查（单只股票最大仓位）
- 订单金额检查
- 每日亏损检查
- 回撤检查

### 2.4 绩效分析器 (performance/analyzer.rs)

**文件**: `quantcore/rust-engine/src/performance/analyzer.rs`  
**实现内容**:
- 总收益率计算
- 年化收益率计算
- 夏普比率计算
- 最大回撤计算
- 胜率计算
- 盈亏比计算

### 2.5 策略上下文 (strategy/context.rs)

**文件**: `quantcore/rust-engine/src/strategy/context.rs`  
**实现内容**:
- 买入订单创建和验证
- 卖出订单创建和验证
- 订单提交到回测引擎

### 2.6 数据加载器 (data/loader.rs)

**文件**: `quantcore/rust-engine/src/data/loader.rs`  
**实现内容**:
- 数据源注册
- 历史数据加载接口实现
- 数据缓存机制

### 2.7 风险监控 (risk/monitor.rs)

**文件**: `quantcore/rust-engine/src/risk/monitor.rs`  
**实现内容**:
- 实时风险监控
- 预警触发机制

---

## 阶段三：测试覆盖提升（优先级：中）

### 3.1 后端服务层测试

- 为 `services/` 目录下的核心服务添加单元测试
- 建立 mock 数据源用于测试

### 3.2 前端组件测试

- 为关键组件添加测试（StatCard, RealtimeQuote 等）
- 建立测试基础设施

---

## 阶段四：LLM 集成完善（优先级：低）

### 4.1 financial_llm_router.py

**文件**: `backend/app/services/financial_llm_router.py`  
**实现内容**:
- 集成到 qwen_assistant.py
- 实现信号融合逻辑
- 完善 Ollama 模型加载/卸载

---

## 实施顺序

```
阶段一 (1-3): 清理 TODO 标记 (预计 1-2 天)
    ↓
阶段二 (1-7): Rust 引擎核心功能 (预计 3-5 天)
    ↓
阶段三 (1-2): 测试覆盖提升 (预计 2-3 天)
    ↓
阶段四 (1): LLM 集成完善 (预计 1-2 天)
```

---

## 验证标准

每个任务完成后必须：
1. 代码编译通过（无语法错误）
2. 现有测试全部通过
3. 新增功能有对应测试
4. TODO/FIXME 标记已移除或替换
