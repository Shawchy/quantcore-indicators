# index_basic 接口快速参考

## 🚀 快速开始

```python
from app.adapters import data_source_manager

# 获取指数信息
index_info = await data_source_manager.get_index_basic(ts_code='000001.SH')
```

---

## 📋 参数速查

### 输入参数

```python
await data_source_manager.get_index_basic(
    ts_code='000001.SH',    # 指数代码
    name='上证指数',         # 指数名称
    market='SSE',           # 市场：SSE/SZSE/CSI/SW/MSCI/CICC/OTH
    publisher='中证指数',    # 发布方
    category='综合指数'      # 类别
)
```

### 输出字段

```python
{
    'ts_code': '000001.SH',     # TS 代码
    'name': '上证指数',          # 简称
    'fullname': '上证综合指数',  # 全称
    'market': 'SSE',            # 市场
    'publisher': '中证指数',    # 发布方
    'index_type': '',           # 风格
    'category': '综合指数',     # 类别
    'base_date': '19901219',    # 基期
    'base_point': 100.0,        # 基点
    'list_date': '19910715',    # 上市日期
    'weight_rule': '',          # 加权方式
    'desc': '',                 # 描述
    'exp_date': ''              # 终止日期
}
```

---

## 🎯 常用示例

### 1. 获取单个指数

```python
# 上证指数
index = await data_source_manager.get_index_basic(ts_code='000001.SH')

# 沪深 300
index = await data_source_manager.get_index_basic(ts_code='000300.SH')

# 中证 500
index = await data_source_manager.get_index_basic(ts_code='000905.SH')
```

### 2. 获取某市场所有指数

```python
# 申万指数
sw_indexes = await data_source_manager.get_index_basic(market='SW')

# 中证指数
csi_indexes = await data_source_manager.get_index_basic(market='CSI')

# 上交所指数
sse_indexes = await data_source_manager.get_index_basic(market='SSE')
```

### 3. 按类别筛选

```python
# 规模指数
scale = await data_source_manager.get_index_basic(category='规模指数')

# 行业指数
industry = await data_source_manager.get_index_basic(category='行业指数')

# 主题指数
theme = await data_source_manager.get_index_basic(category='主题指数')
```

### 4. 组合查询

```python
# 申万行业指数
sw_industry = await data_source_manager.get_index_basic(
    market='SW',
    category='一级行业指数'
)

# 中证规模指数
csi_scale = await data_source_manager.get_index_basic(
    market='CSI',
    category='规模指数'
)
```

---

## 🏛️ 市场代码

| 代码 | 说明 | 示例 |
|------|------|------|
| SSE | 上交所 | 000001.SH |
| SZSE | 深交所 | 399001.SZ |
| CSI | 中证指数 | 000300.SH |
| SW | 申万指数 | 801010.SI |
| MSCI | MSCI 指数 | - |
| CICC | 中金指数 | - |
| OTH | 其他 | - |

---

## 📊 指数类别

### 主要类别

- **规模指数**：沪深 300、中证 500 等
- **行业指数**：医药、金融、科技等
- **主题指数**：新能源、芯片、消费等
- **风格指数**：成长、价值等
- **综合指数**：上证指数、深证成指等

### 申万行业分类

```python
# 一级行业
level1 = await data_source_manager.get_index_basic(
    market='SW',
    category='一级行业指数'
)

# 二级行业
level2 = await data_source_manager.get_index_basic(
    market='SW',
    category='二级行业指数'
)
```

---

## ⚡ 注意事项

### 1. 积分要求

- **最低**：120 分 ✅
- **当前**：120 分

### 2. 频率限制

```
每分钟最多 5 次
```

**解决方案**：使用缓存（已实现 30 分钟缓存）

### 3. 数据字段

部分字段可能为空：
- `fullname`：全称
- `weight_rule`：加权方式
- `desc`：描述

这是正常的，数据源本身可能缺失这些信息。

---

## 🐛 常见问题

### Q: 为什么返回空列表？

**A**: 检查：
1. 参数是否正确
2. 指数代码是否存在
3. 是否超过频率限制

### Q: 如何获取指数 K 线？

**A**: 使用 `index_daily` 接口（需 2000 分）

### Q: 如何获取成分股？

**A**: 使用 `index_member` 接口（需 2000 分）

---

## 📚 完整文档

- [详细使用指南](INDEX_BASIC_API_GUIDE.md)
- [集成总结](INDEX_BASIC_INTEGRATION_SUMMARY.md)
- [测试脚本](test_index_basic.py)

---

## 🔗 官方链接

- [接口文档](https://tushare.pro/document/2?doc_id=23)
- [权限说明](https://tushare.pro/document/1?doc_id=108)

---

**最后更新**：2026-03-16
