# 数据加载进度显示功能

## 功能概述

在后台拉取数据源数据时，前端实时显示加载进度、数据类型和数据源信息，提升用户体验。

## 技术架构

### 后端

#### 1. 进度管理模块

**文件**: `backend/app/utils/load_progress.py`

**核心类**:
- `LoadTaskStatus`: 任务状态枚举
- `DataType`: 数据类型枚举
- `DataSource`: 数据源枚举
- `LoadProgress`: 进度信息数据类
- `ProgressManager`: 进度管理器（单例）

**功能**:
- ✅ 创建加载任务
- ✅ 更新任务进度
- ✅ 查询任务状态
- ✅ 自动清理旧任务

#### 2. API 接口

**文件**: `backend/app/api/v1/endpoints/loading_progress.py`

**接口列表**:
- `GET /api/v1/loading/tasks` - 获取所有加载任务
- `GET /api/v1/loading/task/{task_id}` - 获取单个任务进度
- `DELETE /api/v1/loading/task/{task_id}` - 移除已完成任务
- `POST /api/v1/loading/cleanup` - 清理旧任务

#### 3. 数据加载器集成

**文件**: `backend/app/services/data_loader.py`

**集成点**:
```python
# 创建进度追踪任务
task_id = await progress_manager.create_task(
    task_name=f"加载 K 线数据 - {code}",
    data_type=DataType.KLINE,
    data_source=DataSource.MIXED,
    code=code,
    total=100
)

# 更新进度
await progress_manager.update_progress(
    task_id=task_id,
    status=LoadTaskStatus.RUNNING,
    message="正在从数据源获取数据...",
    current=30
)
```

### 前端

#### 1. API 服务

**文件**: `frontend/src/services/api.ts`

```typescript
export const loadingProgressApi = {
  getTasks: (status?: string, dataType?: string) =>
    api.get('/loading/tasks', { params: { status, data_type: dataType } }),
  getTask: (taskId: string) =>
    api.get(`/loading/task/${taskId}`),
  removeTask: (taskId: string) =>
    api.delete(`/loading/task/${taskId}`),
  cleanupTasks: (maxAgeHours: number = 24) =>
    api.post('/loading/cleanup', null, { params: { max_age_hours: maxAgeHours } }),
}
```

#### 2. 进度显示组件

**文件**: `frontend/src/components/LoadingProgressPanel.tsx`

**功能特性**:
- ✅ 实时轮询（3 秒/次）
- ✅ 状态筛选（全部/运行中/已完成/失败）
- ✅ 进度条动画
- ✅ 数据类型和数据源显示
- ✅ 错误信息提示
- ✅ 清理旧任务

#### 3. 设置页面集成

**文件**: `frontend/src/pages/Settings.tsx`

```typescript
import LoadingProgressPanel from '../components/LoadingProgressPanel'

const Settings: React.FC = () => {
  return (
    <Container maxW="container.xl" py={6}>
      <VStack spacing={6} align="stretch">
        <Heading size="lg">系统设置</Heading>
        <DataSourceControl />
        <LoadingProgressPanel />  {/* 新增进度面板 */}
      </VStack>
    </Container>
  )
}
```

## 使用流程

### 1. 开始加载数据

当用户触发数据加载操作时：

```python
# 后端自动创建进度追踪任务
task_id = await progress_manager.create_task(...)
```

### 2. 实时更新进度

加载过程中自动更新进度：

```python
# 开始加载
await progress_manager.update_progress(
    task_id=task_id,
    status=LoadTaskStatus.RUNNING,
    current=10,
    message="开始加载数据..."
)

# 获取数据中
await progress_manager.update_progress(
    task_id=task_id,
    current=30,
    message="正在从数据源获取数据..."
)

# 保存数据中
await progress_manager.update_progress(
    task_id=task_id,
    current=70,
    message="正在保存到数据库..."
)

# 完成
await progress_manager.update_progress(
    task_id=task_id,
    status=LoadTaskStatus.COMPLETED,
    current=100,
    message="加载完成"
)
```

### 3. 前端显示进度

前端自动轮询并显示：

```typescript
// 每 3 秒轮询一次
const { data: tasks, refetch } = useQuery<LoadingTask[]>({
  queryKey: ['loadingTasks'],
  queryFn: () => loadingProgressApi.getTasks(),
  refetchInterval: 3000,
})
```

## 界面展示

### 进度卡片信息

每个加载任务显示：

1. **标题栏**
   - 任务名称
   - 股票代码（如果有）
   - 状态徽章（运行中/已完成/失败）
   - 操作按钮（刷新/移除）

2. **数据类型和来源**
   - 数据类型：K 线数据、股票信息、板块数据等
   - 数据源：Tushare、AkShare、Baostock、YFinance、混合

3. **进度条**
   - 百分比显示
   - 颜色根据状态变化
   - 动画效果（运行中时）

4. **统计信息**
   - 已加载数据条数
   - 失败次数
   - 更新时间

5. **状态消息**
   - 当前操作描述
   - 错误信息（如果失败）

### 筛选功能

- **全部**: 显示所有任务
- **运行中**: 只显示正在加载的任务
- **已完成**: 显示成功完成的任务
- **失败**: 显示失败的任务

## 数据结构

### 后端进度对象

```python
@dataclass
class LoadProgress:
    task_id: str                    # 任务 ID（UUID）
    task_name: str                  # 任务名称
    status: LoadTaskStatus          # 状态
    data_type: DataType             # 数据类型
    data_source: DataSource         # 数据源
    code: Optional[str]             # 股票代码
    start_date: Optional[str]       # 开始日期
    end_date: Optional[str]         # 结束日期
    total: int                      # 总任务数
    current: int                    # 当前完成数
    progress_percent: float         # 进度百分比
    message: str                    # 状态消息
    error_message: Optional[str]    # 错误信息
    loaded_count: int               # 已加载条数
    failed_count: int               # 失败次数
    created_at: datetime            # 创建时间
    started_at: Optional[datetime]  # 开始时间
    completed_at: Optional[datetime]# 完成时间
    updated_at: datetime            # 更新时间
```

### 前端接口返回

```typescript
interface LoadingTask {
  task_id: string
  task_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial'
  data_type: string
  data_source: string
  code?: string
  start_date?: string
  end_date?: string
  progress_percent: number
  total: number
  current: number
  loaded_count: number
  failed_count: number
  message: string
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  updated_at: string
}
```

## 性能优化

### 后端优化

1. **异步锁**: 使用 `asyncio.Lock` 保证并发安全
2. **自动清理**: 定期清理超过 24 小时的旧任务
3. **内存管理**: 任务完成后从内存中移除

### 前端优化

1. **智能轮询**: 3 秒轮询一次，避免频繁请求
2. **React Query 缓存**: 利用缓存减少重复请求
3. **筛选功能**: 减少渲染数据量
4. **懒加载**: 按需加载组件

## 扩展性

### 支持更多数据类型

```python
class DataType(str, Enum):
    KLINE = "kline"
    STOCK_INFO = "stock_info"
    SECTOR = "sector"
    CHIP = "chip"
    MONEYFLOW = "moneyflow"
    INDEX = "index"
    REALTIME = "realtime"
    # 添加新类型
    FINANCIAL = "financial"  # 财务数据
    NEWS = "news"  # 新闻数据
```

### 支持更多数据源

```python
class DataSource(str, Enum):
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    YFINANCE = "yfinance"
    MIXED = "mixed"
    # 添加新数据源
    WIND = "wind"  # Wind 数据
    CHOICE = "choice"  # Choice 数据
```

### 自定义进度更新

```python
# 在其他数据加载方法中集成
async def load_stock_info(code: str):
    task_id = await progress_manager.create_task(
        task_name=f"加载股票信息 - {code}",
        data_type=DataType.STOCK_INFO,
        data_source=DataSource.TUSHARE,
        code=code
    )
    
    try:
        # 加载数据...
        await progress_manager.update_progress(
            task_id=task_id,
            current=50,
            message="正在获取股票信息..."
        )
        
        await progress_manager.update_progress(
            task_id=task_id,
            status=LoadTaskStatus.COMPLETED,
            current=100
        )
    except Exception as e:
        await progress_manager.update_progress(
            task_id=task_id,
            status=LoadTaskStatus.FAILED,
            error_message=str(e)
        )
```

## 测试方法

### 后端测试

```bash
# 测试进度管理
python -c "
from app.utils.load_progress import get_progress_manager
import asyncio

async def test():
    pm = get_progress_manager()
    
    # 创建任务
    task_id = await pm.create_task(
        task_name='测试任务',
        data_type='kline',
        data_source='tushare',
        code='000001',
        total=100
    )
    
    # 更新进度
    await pm.update_progress(
        task_id=task_id,
        current=50,
        status='running',
        message='测试中...'
    )
    
    # 获取进度
    progress = await pm.get_progress(task_id)
    print(f'进度：{progress[\"progress_percent\"]}%')
    
    # 完成
    await pm.update_progress(
        task_id=task_id,
        status='completed',
        current=100
    )

asyncio.run(test())
"
```

### 前端测试

1. **启动后端服务**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **启动前端服务**
   ```bash
   cd frontend
   npm run dev
   ```

3. **访问设置页面**
   - 打开浏览器访问：http://localhost:5173/settings
   - 查看"数据加载进度"面板

4. **触发数据加载**
   - 访问股票详情页面
   - 触发 K 线数据加载
   - 返回设置页面查看进度

## 文件清单

### 后端文件

1. `backend/app/utils/load_progress.py` - 进度管理模块
2. `backend/app/api/v1/endpoints/loading_progress.py` - 进度 API
3. `backend/app/api/v1/__init__.py` - 路由注册
4. `backend/app/services/data_loader.py` - 数据加载器（已集成）

### 前端文件

1. `frontend/src/services/api.ts` - API 服务（已添加）
2. `frontend/src/components/LoadingProgressPanel.tsx` - 进度显示组件
3. `frontend/src/pages/Settings.tsx` - 设置页面（已集成）

## 总结

### 功能特性

✅ **实时进度显示**: 3 秒轮询，实时更新
✅ **数据类型显示**: K 线、股票信息、板块等
✅ **数据源显示**: Tushare、AkShare、Baostock 等
✅ **状态筛选**: 全部/运行中/已完成/失败
✅ **错误提示**: 友好的错误信息展示
✅ **自动清理**: 24 小时后自动清理旧任务
✅ **进度动画**: 运行中时显示动画效果

### 用户体验提升

- **透明度**: 用户清楚知道数据加载进度
- **可控性**: 可以筛选和清理任务
- **反馈及时**: 错误信息实时显示
- **视觉友好**: 进度条动画和颜色变化

### 技术优势

- **异步安全**: 使用锁保证并发安全
- **内存管理**: 自动清理旧任务
- **易于扩展**: 支持新的数据类型和来源
- **性能优化**: 智能轮询和缓存

---

**开发完成时间**: 2026-03-14  
**状态**: ✅ 已完成  
**测试状态**: 待验证
