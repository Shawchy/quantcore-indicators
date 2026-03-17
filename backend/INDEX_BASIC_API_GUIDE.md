# Tushare index_basic 接口使用说明

## 📊 接口概述

**接口名称**：指数基础信息  
**接口代码**：`index_basic`  
**所需积分**：120 分  
**描述**：获取指数基础信息，包括指数代码、名称、市场、发布方、类别、基期等详细信息。

---

## 🔧 代码实现

### 1. Tushare 适配器方法

**文件**：`app/adapters/tushare_adapter.py`

```python
@api_call_cache(ttl=1800)  # 缓存 30 分钟
async def get_index_basic(
    self,
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    market: Optional[str] = None,
    publisher: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取指数基础信息"""
```

### 2. 数据源管理器方法

**文件**：`app/adapters/factory.py`

```python
async def get_index_basic(
    self,
    ts_code: Optional[str] = None,
    name: Optional[str] = None,
    market: Optional[str] = None,
    publisher: Optional[str] = None,
    category: Optional[str] = None,
    source_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取指数基础信息"""
```

---

## 📝 输入参数

| 名称 | 类型 | 必选 | 描述 |
|------|------|------|------|
| ts_code | str | 否 | 指数代码（如：000001.SH） |
| name | str | 否 | 指数简称（如：上证指数） |
| market | str | 否 | 交易所或服务商（默认 SSE） |
| publisher | str | 否 | 发布商 |
| category | str | 否 | 指数类别 |

---

## 📤 输出参数

| 名称 | 类型 | 描述 |
|------|------|------|
| ts_code | str | TS 代码 |
| name | str | 简称 |
| fullname | str | 指数全称 |
| market | str | 市场 |
| publisher | str | 发布方 |
| index_type | str | 指数风格 |
| category | str | 指数类别 |
| base_date | str | 基期 |
| base_point | float | 基点 |
| list_date | str | 发布日期 |
| weight_rule | str | 加权方式 |
| desc | str | 描述 |
| exp_date | str | 终止日期 |

---

## 🏛️ 市场说明 (market)

| 市场代码 | 说明 |
|---------|------|
| MSCI | MSCI 指数 |
| CSI | 中证指数 |
| SSE | 上交所指数 |
| SZSE | 深交所指数 |
| CICC | 中金指数 |
| SW | 申万指数 |
| OTH | 其他指数 |

---

## 📋 指数类别

- 主题指数
- 规模指数
- 策略指数
- 风格指数
- 综合指数
- 成长指数
- 价值指数
- 有色指数
- 化工指数
- 能源指数
- 其他指数
- 外汇指数
- 基金指数
- 商品指数
- 债券指数
- 行业指数
- 贵金属指数
- 农副产品指数
- 软商品指数
- 油脂油料指数
- 非金属建材指数
- 煤焦钢矿指数
- 谷物指数

---

## 💻 使用示例

### 示例 1：获取所有申万指数

```python
from app.adapters import data_source_manager

# 获取申万指数
sw_indexes = await data_source_manager.get_index_basic(market='SW')

for item in sw_indexes[:5]:
    print(f"{item['name']} ({item['ts_code']})")
    print(f"  市场：{item['market']}")
    print(f"  类别：{item['category']}")
    print(f"  基期：{item['base_date']}")
    print(f"  基点：{item['base_point']}")
```

**输出**：
```
申万 50 (801001.SI)
  市场：SW
  类别：规模指数
  基期：19991230
  基点：1000.0

申万中小 (801002.SI)
  市场：SW
  类别：规模指数
  基期：20040705
  基点：1000.0
```

---

### 示例 2：获取特定指数

```python
# 获取上证指数
sh_index = await data_source_manager.get_index_basic(ts_code='000001.SH')

if sh_index:
    item = sh_index[0]
    print(f"代码：{item['ts_code']}")
    print(f"名称：{item['name']}")
    print(f"市场：{item['market']}")
    print(f"类别：{item['category']}")
    print(f"基期：{item['base_date']}")
    print(f"基点：{item['base_point']}")
```

**输出**：
```
代码：000001.SH
名称：上证指数
市场：SSE
类别：综合指数
基期：19901219
基点：100.0
```

---

### 示例 3：获取沪深 300

```python
# 获取沪深 300
hs300 = await data_source_manager.get_index_basic(ts_code='000300.SH')

if hs300:
    item = hs300[0]
    print(f"代码：{item['ts_code']}")
    print(f"名称：{item['name']}")
    print(f"类别：{item['category']}")
    print(f"基期：{item['base_date']}")
    print(f"基点：{item['base_point']}")
```

**输出**：
```
代码：000300.SH
名称：沪深 300
类别：规模指数
基期：20041231
基点：1000.0
```

---

### 示例 4：按名称搜索

```python
# 搜索医药相关指数
pharma_indexes = await data_source_manager.get_index_basic(name='医药')

for item in pharma_indexes:
    print(f"{item['name']} ({item['ts_code']})")
    print(f"  全称：{item['fullname']}")
    print(f"  市场：{item['market']}")
```

---

### 示例 5：按类别筛选

```python
# 获取规模指数
scale_indexes = await data_source_manager.get_index_basic(category='规模指数')

print(f"获取到 {len(scale_indexes)} 条规模指数")

for item in scale_indexes[:10]:
    print(f"{item['name']} ({item['ts_code']}) - {item['market']}")
```

---

### 示例 6：获取中证指数列表

```python
# 获取所有中证指数
csi_indexes = await data_source_manager.get_index_basic(market='CSI')

print(f"获取到 {len(csi_indexes)} 条中证指数")

# 查看前 10 条
for item in csi_indexes[:10]:
    print(f"{item['name']} ({item['ts_code']}) - {item['category']}")
```

---

## 🎯 实际应用场景

### 场景 1：获取行业指数列表

```python
# 获取申万一级行业指数
industry_indexes = await data_source_manager.get_index_basic(
    market='SW',
    category='一级行业指数'
)

for item in industry_indexes:
    print(f"{item['name']}: {item['ts_code']}")
```

### 场景 2：获取主题指数

```python
# 获取主题指数
theme_indexes = await data_source_manager.get_index_basic(category='主题指数')

print(f"获取到 {len(theme_indexes)} 条主题指数")
```

### 场景 3：获取特定市场的指数

```python
# 获取上交所指数
sse_indexes = await data_source_manager.get_index_basic(market='SSE')

print(f"获取到 {len(sse_indexes)} 条上交所指数")
```

---

## 📊 测试脚本

运行测试脚本查看完整示例：

```bash
python test_index_basic.py
```

**测试内容**：
1. ✅ 获取所有申万指数
2. ✅ 获取中证指数
3. ✅ 获取上证指数
4. ✅ 获取沪深 300
5. ✅ 按名称搜索指数
6. ✅ 按类别筛选指数

---

## ⚠️ 注意事项

### 1. 积分要求

- **最低积分**：120 分
- **当前权限**：120 分可正常使用

### 2. 访问频率限制

```
每分钟最多访问 5 次
```

**解决方案**：
- 使用缓存（已实现，缓存 30 分钟）
- 批量获取后本地存储
- 避免频繁调用相同参数

### 3. 数据完整性

部分指数的 `fullname`、`weight_rule`、`desc` 字段可能为空，这是正常现象。

---

## 🔗 相关接口

### 配套使用的接口

1. **指数日线行情** (`index_daily`)
   - 获取指数 K 线数据
   - 所需积分：2000 分

2. **指数成分和权重** (`index_weight`)
   - 获取指数成分股
   - 所需积分：2000 分

3. **板块指数分类** (`index_classify`)
   - 获取板块分类
   - 所需积分：120 分

---

## 📚 官方文档

- [Tushare 官方文档 - index_basic](https://tushare.pro/document/2?doc_id=23)
- [Tushare 权限说明](https://tushare.pro/document/1?doc_id=108)
- [积分获取办法](https://tushare.pro/document/1?doc_id=25)

---

## 🐛 常见问题

### Q1: 为什么获取到的数据为空？

**A**: 可能的原因：
1. 参数不匹配（如代码格式错误）
2. 积分不足
3. 访问频率超限
4. 该指数不存在

### Q2: 如何获取指数 K 线数据？

**A**: 使用 `index_daily` 接口（需要 2000 积分）：

```python
df = pro.index_daily(ts_code='000001.SH', start_date='20240101', end_date='20241231')
```

### Q3: 如何获取指数成分股？

**A**: 使用 `index_member` 接口（需要 2000 积分）：

```python
df = pro.index_member(index_code='000300.SH')
```

### Q4: 为什么有些字段为空？

**A**: Tushare 数据源中部分指数的详细信息（如全称、描述）可能缺失，这是正常现象。

---

## 📝 更新日志

- **2026-03-16**: 实现 `index_basic` 接口
  - 添加 `get_index_basic` 方法到 Tushare 适配器
  - 添加 `get_index_basic` 方法到数据源管理器
  - 创建测试脚本 `test_index_basic.py`
  - 创建使用说明文档

---

**更新时间**：2026-03-16  
**适用版本**：120 积分及以上  
**测试状态**：✅ 通过
