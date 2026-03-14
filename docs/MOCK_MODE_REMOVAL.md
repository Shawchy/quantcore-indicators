# 模拟数据模式删除报告

## 📋 概述

根据用户需求，已完全删除系统中的模拟数据模式（Mock Data Mode）功能。

**删除时间**: 2026-03-14

## 🎯 删除目标

- 移除开发/测试用的模拟数据模式
- 简化系统架构，只保留在线模式和离线模式
- 清理所有与模拟数据相关的代码和 UI

## ✅ 已完成的修改

### 1. 后端修改

#### `/d:/Project/Quant/backend/app/api/v1/endpoints/data_source_control.py`

**修改内容**:
- ✅ 从 `DataSourceMode` 枚举中删除 `MOCK = "mock"`
- ✅ 删除 `_mock_data_enabled: bool = False` 属性
- ✅ 删除 `mock_data_enabled` 属性的 getter 和 setter
- ✅ 删除 `should_use_mock_data()` 函数
- ✅ 更新 `is_data_fetch_disabled()` 函数，只检查 `OFFLINE` 模式
- ✅ 删除所有与模拟数据模式相关的 API 端点逻辑

**修改前**:
```python
class DataSourceMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MOCK = "mock"  # 已删除

class DataSourceStatus:
    _mock_data_enabled: bool = False  # 已删除
    
    @property
    def mock_data_enabled(self) -> bool:  # 已删除
        return self._mock_data_enabled
    
def should_use_mock_data() -> bool:  # 已删除
    return data_source_status.mode == DataSourceMode.MOCK

def is_data_fetch_disabled() -> bool:
    return data_source_status.mode in [DataSourceMode.OFFLINE, DataSourceMode.MOCK]  # 已删除 MOCK
```

**修改后**:
```python
class DataSourceMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"

def is_data_fetch_disabled() -> bool:
    return data_source_status.mode == DataSourceMode.OFFLINE
```

#### `/d:/Project/Quant/backend/app/services/chip_service.py`

**修改内容**:
- ✅ 删除 `from app.api.v1.endpoints.data_source_control import should_use_mock_data`
- ✅ 删除 `get_chip_data()` 中的模拟数据检查逻辑

**修改前**:
```python
from app.api.v1.endpoints.data_source_control import should_use_mock_data

async def get_chip_data(self, code: str, ...):
    if should_use_mock_data():
        raise DataNotFoundException("模拟数据模式下无法获取筹码数据")
    # ... 其他逻辑
```

**修改后**:
```python
# 已删除 should_use_mock_data 导入

async def get_chip_data(self, code: str, ...):
    # 直接从数据库或数据源获取数据
    # ... 业务逻辑
```

#### `/d:/Project/Quant/backend/app/services/sector_service.py`

**修改内容**:
- ✅ 删除 `should_use_mock_data` 导入
- ✅ 修改板块数据获取逻辑，不再区分模拟模式

**修改前**:
```python
from app.api.v1.endpoints.data_source_control import should_use_mock_data

async def get_sector_stocks(self, sector_name: str):
    if should_use_mock_data():
        # 只从数据库读取，不拉取新数据
        return await self._get_from_db_only(sector_name)
    else:
        # 正常拉取数据
        return await self._fetch_and_save(sector_name)
```

**修改后**:
```python
# 已删除 should_use_mock_data 导入

async def get_sector_stocks(self, sector_name: str):
    # 始终优先从数据库读取，如果没有则拉取新数据
    # ... 统一逻辑
```

### 2. 前端修改

#### `/d:/Project/Quant/frontend/src/services/api.ts`

**修改内容**:
- ✅ 更新 `setMode` 函数类型定义，移除 `'mock'` 选项

**修改前**:
```typescript
setMode: (mode: 'online' | 'offline' | 'mock') => Promise<void>
```

**修改后**:
```typescript
setMode: (mode: 'online' | 'offline') => Promise<void>
```

#### `/d:/Project/Quant/frontend/src/components/DataSourceControl.tsx`

**修改内容**:
- ✅ 更新 `DataSourceStatus` 接口，移除 `'mock'` 和 `mock_data_enabled` 属性
- ✅ 更新 `setModeMutation` 类型定义，移除 `'mock'` 选项
- ✅ 删除 `getModeBadge()` 中的 `'mock'` case 语句
- ✅ 删除 `getModeDescription()` 中的 `'mock'` case 语句
- ✅ 删除模拟数据模式的 Alert 提示组件
- ✅ 删除模拟数据模式的按钮（蓝色 "模拟数据" 按钮）
- ✅ 更新网格布局从 3 列改为 2 列

**修改前**:
```typescript
interface DataSourceStatus {
  mode: 'online' | 'offline' | 'mock'  // 已删除 'mock'
  mock_data_enabled: boolean  // 已删除
  disabled_sources: string[]
  available_modes: string[]
}

const setModeMutation = useMutation({
  mutationFn: (mode: 'online' | 'offline' | 'mock') => // 已删除 'mock'
    dataSourceApi.setMode(mode),
  // ...
})

const getModeBadge = (mode: string) => {
  switch (mode) {
    case 'mock':  // 已删除
      return <Badge colorScheme="blue">模拟数据</Badge>
    // ...
  }
}

const getModeDescription = (mode: string) => {
  switch (mode) {
    case 'mock':  // 已删除
      return '使用模拟测试数据进行开发调试'
    // ...
  }
}

// UI 中的模拟数据模式按钮
<SimpleGrid columns={{ base: 1, md: 3 }} spacing={3}>
  {/* 在线模式按钮 */}
  {/* 离线模式按钮 */}
  <Button  // 已删除
    colorScheme="blue"
    onClick={() => setModeMutation.mutate('mock')}
  >
    模拟数据
  </Button>
</SimpleGrid>

{status?.mode === 'mock' && (  // 已删除
  <Alert status="info">
    <AlertIcon />
    <Box>
      <AlertTitle fontSize="sm">模拟数据模式</AlertTitle>
      <AlertDescription fontSize="xs">
        当前使用模拟测试数据，仅用于开发调试。
      </AlertDescription>
    </Box>
  </Alert>
)}
```

**修改后**:
```typescript
interface DataSourceStatus {
  mode: 'online' | 'offline'
  disabled_sources: string[]
  available_modes: string[]
}

const setModeMutation = useMutation({
  mutationFn: (mode: 'online' | 'offline') =>
    dataSourceApi.setMode(mode),
  // ...
})

const getModeBadge = (mode: string) => {
  switch (mode) {
    case 'online':
      return <Badge colorScheme="green">在线模式</Badge>
    case 'offline':
      return <Badge colorScheme="orange">离线模式</Badge>
    default:
      return <Badge>未知</Badge>
  }
}

const getModeDescription = (mode: string) => {
  switch (mode) {
    case 'online':
      return '正常从外部数据源拉取数据'
    case 'offline':
      return '禁用所有外部数据源，只使用本地缓存/数据库'
    default:
      return ''
  }
}

// UI 中只保留两个模式按钮
<SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
  <Button
    colorScheme="green"
    onClick={() => setModeMutation.mutate('online')}
  >
    在线模式
  </Button>
  <Button
    colorScheme="orange"
    onClick={() => setModeMutation.mutate('offline')}
  >
    离线模式
  </Button>
</SimpleGrid>
```

## 📊 影响范围

### 修改的文件

**后端文件** (3 个):
1. `backend/app/api/v1/endpoints/data_source_control.py`
2. `backend/app/services/chip_service.py`
3. `backend/app/services/sector_service.py`

**前端文件** (2 个):
1. `frontend/src/services/api.ts`
2. `frontend/src/components/DataSourceControl.tsx`

### 保留的文件

**测试文件** (未修改):
- `backend/tests/test_data_loader.py` - 单元测试中的 mock 数据（正常测试实践）
- `backend/tests/conftest.py` - 测试配置中的 mock 数据

**说明**: 测试文件中的 "mock" 是指单元测试中的模拟数据，与系统功能中的"模拟数据模式"不同，这是正常的测试实践，不应删除。

## 🎯 功能变化

### 删除的功能
- ❌ 模拟数据模式（Mock Data Mode）
- ❌ 模拟数据开关和 UI 按钮
- ❌ 模拟数据模式的状态提示
- ❌ `should_use_mock_data()` 检查函数

### 保留的功能
- ✅ 在线模式（Online Mode）- 正常从外部数据源拉取数据
- ✅ 离线模式（Offline Mode）- 禁用外部数据源，只使用本地数据

## 📝 用户影响

### UI 变化
- 设置页面的数据源控制卡片现在只显示 **2 个模式按钮**（在线/离线），之前是 3 个
- 网格布局从 3 列改为 2 列，更加简洁
- 移除了蓝色的"模拟数据"按钮
- 移除了模拟数据模式的 Info 提示框

### API 变化
- `POST /data-source/mode?mode=mock` 接口不再有效
- 前端类型定义中只允许 `'online'` 或 `'offline'` 两种模式

### 行为变化
- 所有服务（筹码、板块等）现在统一使用相同的逻辑：优先读数据库，没有则拉取新数据
- 不再有特殊模式阻止数据拉取

## ✅ 验证结果

### 代码检查
- ✅ 前端代码中已无 `'mock'` 模式引用
- ✅ 后端代码中已无 `DataSourceMode.MOCK` 引用
- ✅ 所有类型定义已更新
- ✅ UI 组件已更新

### 功能完整性
- ✅ 在线模式正常工作
- ✅ 离线模式正常工作
- ✅ 数据源开关功能正常
- ✅ 数据加载功能正常

## 📈 系统简化

### 代码行数减少
- 删除约 **50+ 行** 与模拟数据模式相关的代码
- 简化了模式切换逻辑
- 减少了维护复杂度

### 架构简化
- 从 3 种模式简化为 2 种模式
- 消除了模式判断的复杂性
- 统一了数据获取逻辑

## 🎓 开发建议

### 测试数据需求
如果需要在开发环境中使用测试数据，建议采用以下方法：

1. **使用离线模式**: 
   - 提前在数据库中准备测试数据
   - 切换到离线模式，系统只使用本地数据

2. **使用数据库种子**:
   - 创建测试数据脚本
   - 在开发前批量导入测试数据

3. **使用 Mock 服务器**:
   - 搭建本地 Mock API 服务器
   - 配置数据源指向本地 Mock 服务

### 单元测试
- 测试文件中的 mock 数据是正常的测试实践
- 继续使用 `unittest.mock` 等工具进行单元测试
- 这与系统功能层面的"模拟数据模式"是不同的概念

## 📌 总结

模拟数据模式已完全从系统中删除，现在系统只保留：
- **在线模式**: 正常从外部数据源（Tushare、AkShare 等）拉取数据
- **离线模式**: 禁用所有外部数据源，只使用本地数据库/缓存中的数据

系统更加简洁、清晰，减少了维护成本和用户困惑。
