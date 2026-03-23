# 东方财富功能更新日志 - v1.1

**更新日期：** 2026-03-20  
**版本：** v1.1  
**类型：** 功能增强

---

## 🎉 新增功能

### 1. 涨停板行情接口扩展

新增了 3 个东方财富涨停板相关接口：

#### 1.1 昨日涨停股池 (stock_zt_pool_previous_em)
- **接口路径：** `/api/v1/eastmoney/zt-pool-previous`
- **描述：** 获取昨日涨停的股票在今天的表现
- **参数：** `date` (可选，格式 YYYYMMDD，默认为昨日)
- **输出字段：**
  - 序号、代码、名称
  - 涨跌幅、最新价、涨停价
  - 成交额、流通市值、总市值
  - 换手率、涨速、振幅
  - 昨日封板时间、昨日连板数
  - 涨停统计、所属行业

#### 1.2 强势股池 (stock_zt_pool_strong_em)
- **接口路径：** `/api/v1/eastmoney/zt-pool-strong`
- **描述：** 获取市场强势股票
- **参数：** `date` (可选，格式 YYYYMMDD，默认为今日)
- **输出字段：**
  - 序号、代码、名称
  - 涨跌幅、最新价、涨停价
  - 成交额、流通市值、总市值
  - 换手率、涨速
  - 是否新高、量比
  - 涨停统计、入选理由
  - 所属行业

#### 1.3 次新股池 (stock_zt_pool_sub_new_em)
- **接口路径：** `/api/v1/eastmoney/zt-pool-sub-new`
- **描述：** 获取次新股股票
- **参数：** `date` (可选，格式 YYYYMMDD，默认为今日)
- **输出字段：**
  - 序号、代码、名称
  - 涨跌幅、最新价、涨停价
  - 成交额、流通市值、总市值
  - 转手率
  - 开板几日、开板日期
  - 上市日期
  - 是否新高、涨停统计
  - 所属行业

### 2. 综合涨停板行情页面

**文件：** `frontend/src/pages/EastMoneyZtBoardPage.tsx`

新建综合涨停板行情页面，通过 Tab 切换展示 4 种类型：
- 涨停股池
- 昨日涨停
- 强势股
- 次新股

**主要特性：**
- 📊 分类统计卡片
- 🎨 颜色标识涨跌幅（红色上涨、绿色下跌）
- 📅 日期选择器
- 🔄 一键刷新
- 📱 响应式表格布局

### 3. 数据模型扩展

**文件：** `backend/app/models/unified_models.py`

新增 3 个数据模型：
- `StockZtPrevious` - 昨日涨停股池数据模型
- `StockZtStrong` - 强势股池数据模型
- `StockZtSubNew` - 次新股池数据模型

### 4. 适配器方法扩展

**文件：** `backend/app/adapters/eastmoney_adapter.py`

新增 3 个适配器方法：
- `get_zt_pool_previous()` - 获取昨日涨停股池数据
- `get_zt_pool_strong()` - 获取强势股池数据
- `get_zt_pool_sub_new()` - 获取次新股池数据

**特性：**
- ✅ 支持日期参数
- ✅ 60 秒缓存机制
- ✅ 异步数据获取
- ✅ 基于 AKShare 实现

### 5. 前端服务扩展

**文件：** `frontend/src/services/eastmoney.ts`

新增 3 个 API 服务方法：
- `getZtPoolPrevious()` - 获取昨日涨停股池
- `getZtPoolStrong()` - 获取强势股池
- `getZtPoolSubNew()` - 获取次新股池

### 6. 菜单和路由更新

**文件：** 
- `frontend/src/App.tsx`
- `frontend/src/components/Sidebar.tsx`

新增菜单项：
- 东方财富（路径：/eastmoney/zt-board）
- 盘口异动（路径：/eastmoney/changes）

---

## 📝 改进说明

### 1. 功能增强
- 从单一的涨停股池扩展到 4 种涨停板相关数据类型
- 提供更全面的市场涨停板行情分析
- 支持昨日涨停表现追踪
- 支持强势股识别
- 支持次新股监控

### 2. 用户体验
- 一体化展示所有涨停板相关数据
- Tab 切换，避免页面跳转
- 分类统计，快速了解各类型概况
- 颜色标识，直观展示涨跌情况

### 3. 数据完整性
- 完整的字段映射
- 准确的数据类型转换
- 统一的错误处理
- 缓存机制优化

---

## 🔧 技术细节

### 后端实现

```python
# 适配器方法示例
async def get_zt_pool_strong(self, date: Optional[str] = None) -> List[StockZtStrong]:
    """获取强势股池数据"""
    if not date:
        date = datetime.now().strftime('%Y%m%d')
    
    # 缓存检查
    cache_key = self._get_cache_key('zt_strong', date=date)
    cached = self._get_from_cache(cache_key)
    if cached:
        return cached
    
    # 调用 AKShare
    import akshare as ak
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(
        None,
        lambda: ak.stock_zt_pool_strong_em(date=date)
    )
    
    # 数据转换
    zt_stocks = []
    for _, row in df.iterrows():
        zt_stocks.append(StockZtStrong(
            serial_no=int(row.get('序号', 0)),
            code=str(row.get('代码', '')),
            # ... 更多字段
        ))
    
    return zt_stocks
```

### 前端实现

```typescript
// Tab 切换展示
<Tabs onChange={(index) => setActiveTab(index)} colorScheme="blue">
  <TabList>
    <Tab>涨停股池</Tab>
    <Tab>昨日涨停</Tab>
    <Tab>强势股</Tab>
    <Tab>次新股</Tab>
  </TabList>
  
  <TabPanels>
    <TabPanel>
      {/* 涨停股池内容 */}
    </TabPanel>
    <TabPanel>
      {/* 昨日涨停内容 */}
    </TabPanel>
    {/* ... */}
  </TabPanels>
</Tabs>
```

---

## 📊 接口示例

### 1. 获取昨日涨停

```bash
GET /api/v1/eastmoney/zt-pool-previous?date=20240415
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 156 只股票",
  "data": [
    {
      "serial_no": 1,
      "code": "001202",
      "name": "炬申股份",
      "change_pct": -5.52,
      "latest_price": 14.03,
      "limit_up_price": 15.56,
      "turnover": 123456789,
      "float_mv": 2345678901,
      "total_mv": 3456789012,
      "turnover_rate": 12.34,
      "speed_pct": 1.23,
      "amplitude": 18.59,
      "yesterday_seal_time": "09:39:57",
      "yesterday_continuous": 1,
      "zt_stats": "2/1",
      "industry": "物流行业"
    }
  ]
}
```

### 2. 获取强势股

```bash
GET /api/v1/eastmoney/zt-pool-strong?date=20241231
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 127 只强势股",
  "data": [
    {
      "serial_no": 1,
      "code": "301202",
      "name": "朗威股份",
      "change_pct": 19.99,
      "latest_price": 45.67,
      "limit_up_price": 46.20,
      "turnover": 234567890,
      "float_mv": 4567890123,
      "total_mv": 5678901234,
      "turnover_rate": 15.67,
      "speed_pct": 2.34,
      "is_new_high": "是",
      "volume_ratio": 2.30,
      "zt_stats": "1/1",
      "reason": "60 日新高",
      "industry": "通用设备"
    }
  ]
}
```

### 3. 获取次新股

```bash
GET /api/v1/eastmoney/zt-pool-sub-new?date=20241231
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 91 只次新股",
  "data": [
    {
      "serial_no": 1,
      "code": "001391",
      "name": "C 国货航",
      "change_pct": -0.97,
      "latest_price": 9.21,
      "limit_up_price": 9.30,
      "turnover": 345678901,
      "float_mv": 5678901234,
      "total_mv": 6789012345,
      "turnover_rate": 23.45,
      "open_days": 1,
      "open_date": "2024-12-30",
      "list_date": "2024-12-30",
      "is_new_high": "否",
      "zt_stats": "0/0",
      "industry": "物流行业"
    }
  ]
}
```

---

## 🎯 使用场景

### 1. 昨日涨停监控
- 追踪昨日涨停股票今日表现
- 分析涨停持续性
- 判断市场情绪

### 2. 强势股挖掘
- 识别市场强势股票
- 发现创新高个股
- 捕捉强势板块

### 3. 次新股机会
- 监控新上市股票表现
- 发现开板机会
- 追踪次新股行情

---

## ⚠️ 注意事项

### 1. 数据限制
- 所有接口只能获取近期数据
- 历史数据支持有限
- 建议在交易时间使用

### 2. 性能考虑
- 已实现 60 秒缓存
- 建议合理设置刷新频率
- 大数据量时使用分页

### 3. 错误处理
- 网络超时：10 秒
- 数据为空：返回空数组
- 异常捕获：记录日志并返回友好提示

---

## 📚 相关文档

- 功能说明：`EASTMONEY_FEATURE.md`
- 接口文档：`backend/app/api/v1/endpoints/eastmoney.py`
- 数据模型：`backend/app/models/unified_models.py`
- 前端服务：`frontend/src/services/eastmoney.ts`

---

## 🔗 相关链接

- 东方财富网：http://quote.eastmoney.com/
- 涨停板行情：https://quote.eastmoney.com/ztb/detail
- AKShare 文档：https://akshare.akfamily.xyz/

---

**更新完成！** 🎉
