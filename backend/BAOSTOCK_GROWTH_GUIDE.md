# BaoStock 季频成长能力数据查询使用指南

## 目录

- [概述](#概述)
- [API 接口说明](#api-接口说明)
- [参数说明](#参数说明)
- [返回数据说明](#返回数据说明)
- [使用示例](#使用示例)
- [成长能力指标详解](#成长能力指标详解)
- [数据分析应用](#数据分析应用)
- [常见问题](#常见问题)

---

## 概述

**季频成长能力**数据用于评估企业的成长性和发展潜力。通过 BaoStock 提供的 `query_growth_data()` API，可以获取上市公司的季度成长能力指标，反映企业各项财务指标的同比增长情况。

### 数据特点

- **数据范围**：2007 年至今
- **更新频率**：季度更新
- **数据源**：上市公司财报
- **适用场景**：成长股分析、投资价值评估、趋势预测

### 支持的指标

| 指标代码 | 指标名称 | 单位 |
|---------|---------|------|
| YOYEquity | 净资产同比增长率 | % |
| YOYAsset | 总资产同比增长率 | % |
| YOYNI | 净利润同比增长率 | % |
| YOYEPSBasic | 基本每股收益同比增长率 | % |
| YOYPNI | 归属母公司股东净利润同比增长率 | % |

---

## API 接口说明

### 方法签名

```python
async def get_growth_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]
```

### 功能描述

通过 API 接口获取季频成长能力信息，可以通过参数设置获取对应年份、季度数据。

### 调用流程

```
1. 登录系统 → 2. 查询数据 → 3. 解析结果 → 4. 登出系统
```

---

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| code | str | 是 | - | 股票代码，格式：sh.600000 或 sz.000001 |
| year | int | 否 | 当前年 | 统计年份，如：2023 |
| quarter | int | 否 | 当前季 | 统计季度，取值：1、2、3、4 |

### 参数详解

#### code（股票代码）

- **格式要求**：市场代码 + "." + 6 位数字代码
- **市场代码**：
  - `sh`：上海证券交易所
  - `sz`：深圳证券交易所
- **示例**：
  - `sh.600000`：浦发银行
  - `sz.000001`：平安银行
  - `sh.601398`：工商银行

#### year（统计年份）

- **取值范围**：2007 年至今
- **默认值**：当前年份
- **示例**：`2023`

#### quarter（统计季度）

- **取值**：1、2、3、4
  - `1`：第一季度（一季报）
  - `2`：第二季度（中报）
  - `3`：第三季度（三季报）
  - `4`：第四季度（年报）
- **默认值**：当前季度（根据当前月份自动计算）
- **季度计算规则**：
  - 1-3 月 → 第一季度
  - 4-6 月 → 第二季度
  - 7-9 月 → 第三季度
  - 10-12 月 → 第四季度

---

## 返回数据说明

### 返回类型

`List[Dict[str, Any]]`：成长能力数据列表，每个元素为一个字典。

### 返回字段

| 字段名 | 类型 | 说明 |
|-------|------|------|
| code | str | 证券代码 |
| pub_date | str | 公司发布财报的日期（YYYY-MM-DD） |
| stat_date | str | 财报统计的季度的最后一天（YYYY-MM-DD） |
| yoy_equity | float | 净资产同比增长率（%） |
| yoy_asset | float | 总资产同比增长率（%） |
| yoy_ni | float | 净利润同比增长率（%） |
| yoy_eps_basic | float | 基本每股收益同比增长率（%） |
| yoy_pni | float | 归属母公司股东净利润同比增长率（%） |

### 返回示例

```json
[
  {
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "yoy_equity": 8.52,
    "yoy_asset": 6.35,
    "yoy_ni": 12.45,
    "yoy_eps_basic": 12.30,
    "yoy_pni": 11.85
  }
]
```

---

## 使用示例

### 示例 1：获取最新季度成长能力数据

```python
import baostock as bs
import pandas as pd
from app.adapters.baostock_adapter import BaostockAdapter

async def get_latest_growth():
    # 创建适配器实例
    adapter = BaostockAdapter()
    
    # 初始化（自动登录）
    await adapter.initialize()
    
    try:
        # 获取浦发银行最新季度成长能力数据
        result = await adapter.get_growth_data(code="sh.600000")
        
        # 转换为 DataFrame 便于分析
        df = pd.DataFrame(result)
        print(df)
        
    finally:
        # 登出系统
        await adapter.close()
```

### 示例 2：获取指定年份季度数据

```python
async def get_specific_quarter():
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        # 获取工商银行 2023 年第二季度成长能力数据
        result = await adapter.get_growth_data(
            code="sh.601398",
            year=2023,
            quarter=2
        )
        
        for item in result:
            print(f"发布日期：{item['pub_date']}")
            print(f"统计日期：{item['stat_date']}")
            print(f"净资产同比增长率：{item['yoy_equity']}%")
            print(f"总资产同比增长率：{item['yoy_asset']}%")
            print(f"净利润同比增长率：{item['yoy_ni']}%")
            print(f"每股收益同比增长率：{item['yoy_eps_basic']}%")
            print(f"归母净利润同比增长率：{item['yoy_pni']}%")
            
    finally:
        await adapter.close()
```

### 示例 3：获取多年多季度数据（趋势分析）

```python
async def get_growth_trend():
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        all_data = []
        
        # 获取 2020-2023 年每年第二季度的数据
        for year in range(2020, 2024):
            result = await adapter.get_growth_data(
                code="sh.600000",
                year=year,
                quarter=2
            )
            all_data.extend(result)
        
        # 转换为 DataFrame
        df = pd.DataFrame(all_data)
        
        # 保存为 CSV 文件
        df.to_csv("growth_trend.csv", index=False, encoding='utf-8-sig')
        print(f"已保存 {len(df)} 条数据到 growth_trend.csv")
        
    finally:
        await adapter.close()
```

### 示例 4：批量获取多只股票数据

```python
async def get_multi_stocks_growth():
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        stock_codes = ["sh.600000", "sh.601398", "sz.000001"]
        all_results = []
        
        for code in stock_codes:
            result = await adapter.get_growth_data(code=code)
            all_results.extend(result)
            print(f"已获取 {code} 的成长能力数据")
        
        df = pd.DataFrame(all_results)
        print(f"共获取 {len(df)} 条记录")
        
    finally:
        await adapter.close()
```

### 示例 5：直接使用 BaoStock API

```python
import baostock as bs
import pandas as pd

# 登录系统
lg = bs.login()
print('login respond error_code:' + lg.error_code)
print('login respond  error_msg:' + lg.error_msg)

# 成长能力
growth_list = []
rs_growth = bs.query_growth_data(code="sh.600000", year=2023, quarter=2)
while (rs_growth.error_code == '0') & rs_growth.next():
    growth_list.append(rs_growth.get_row_data())

result_growth = pd.DataFrame(growth_list, columns=rs_growth.fields)

# 打印输出
print(result_growth)

# 结果集输出到 csv 文件
result_growth.to_csv("D:\\growth_data.csv", encoding="gbk", index=False)

# 登出系统
bs.logout()
```

---

## 成长能力指标详解

### 1. 净资产同比增长率 (YOYEquity)

#### 定义

反映企业净资产（股东权益）的同比增长速度，衡量企业资本积累能力。

#### 计算公式

```
净资产同比增长率 = (本期净资产 - 上年同期净资产) / |上年同期净资产| × 100%
```

#### 指标解读

- **正增长**：净资产增加，企业资本实力增强
- **负增长**：净资产减少，可能存在亏损或分红过多
- **高增长**：企业快速扩张，但需关注质量

#### 合理范围

| 企业类型 | 合理增长率 |
|---------|-----------|
| 成熟企业 | 5%-15% |
| 成长型企业 | 15%-30% |
| 初创企业 | 30% 以上 |
| 衰退企业 | 负增长 |

### 2. 总资产同比增长率 (YOYAsset)

#### 定义

反映企业总资产的同比增长速度，衡量企业规模扩张速度。

#### 计算公式

```
总资产同比增长率 = (本期总资产 - 上年同期总资产) / |上年同期总资产| × 100%
```

#### 指标解读

- **正增长**：企业规模扩张
- **负增长**：企业收缩资产规模
- **适度增长**：健康发展的标志
- **过快增长**：可能盲目扩张

#### 注意事项

- 需结合负债率分析
- 关注资产质量而非单纯规模
- 不同行业差异较大

### 3. 净利润同比增长率 (YOYNI)

#### 定义

反映企业净利润的同比增长速度，是衡量企业盈利成长性的核心指标。

#### 计算公式

```
净利润同比增长率 = (本期净利润 - 上年同期净利润) / |上年同期净利润| × 100%
```

#### 指标解读

- **正增长**：盈利能力增强
- **负增长**：盈利能力下降
- **高增长**：高速成长，投资价值高
- **持续负增长**：经营风险信号

#### 合理范围

| 增长阶段 | 合理增长率 |
|---------|-----------|
| 高速成长期 | 30% 以上 |
| 快速成长期 | 20%-30% |
| 稳定成长期 | 10%-20% |
| 成熟期 | 5%-10% |
| 衰退期 | 负增长 |

### 4. 基本每股收益同比增长率 (YOYEPSBasic)

#### 定义

反映企业基本每股收益的同比增长速度，从股东角度衡量盈利成长性。

#### 计算公式

```
基本每股收益同比增长率 = (本期基本每股收益 - 上年同期基本每股收益) / |上年同期基本每股收益| × 100%
```

#### 指标解读

- **正增长**：股东收益增加
- **负增长**：股东收益减少
- **高于净利润增长率**：可能存在股本缩减
- **低于净利润增长率**：可能存在股本扩张

#### 与净利润增长率的关系

- **一致**：正常情况
- **EPS 增长更快**：回购股票、股本减少
- **EPS 增长更慢**：增发股票、股本扩张

### 5. 归属母公司股东净利润同比增长率 (YOYPNI)

#### 定义

反映归属母公司股东的净利润的同比增长速度，是上市公司股东最关心的指标。

#### 计算公式

```
归属母公司股东净利润同比增长率 = (本期归属母公司股东净利润 - 上年同期归属母公司股东净利润) / |上年同期归属母公司股东净利润| × 100%
```

#### 指标解读

- **正增长**：母公司股东收益增加
- **负增长**：母公司股东收益减少
- **高于净利润增长率**：子公司少数股东损益占比下降
- **低于净利润增长率**：子公司少数股东损益占比上升

#### 重要性

- **最直接反映上市公司价值**
- **影响股价的核心因素**
- **投资者最关注的指标**

---

## 数据分析应用

### 1. 成长趋势分析

通过对比多个季度的成长能力指标，分析企业成长性的变化趋势。

```python
import pandas as pd
import matplotlib.pyplot as plt

async def analyze_growth_trend(code: str):
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        all_data = []
        
        # 获取近 4 年数据
        for year in range(2020, 2024):
            for quarter in [1, 2, 3, 4]:
                result = await adapter.get_growth_data(
                    code=code,
                    year=year,
                    quarter=quarter
                )
                all_data.extend(result)
        
        df = pd.DataFrame(all_data)
        df['stat_date'] = pd.to_datetime(df['stat_date'])
        df = df.sort_values('stat_date')
        
        # 绘制成长能力指标趋势图
        plt.figure(figsize=(14, 8))
        
        plt.plot(df['stat_date'], df['yoy_ni'], 'r-o', label='净利润增长率', linewidth=2)
        plt.plot(df['stat_date'], df['yoy_eps_basic'], 'b-o', label='每股收益增长率', linewidth=2)
        plt.plot(df['stat_date'], df['yoy_pni'], 'g-o', label='归母净利润增长率', linewidth=2)
        
        plt.axhline(y=0, color='gray', linestyle='--', linewidth=1)
        plt.axhline(y=20, color='green', linestyle='--', linewidth=1, alpha=0.5, label='成长线 (20%)')
        
        plt.title(f'{code} 成长能力指标趋势分析', fontsize=16)
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('增长率 (%)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{code}_growth_trend.png', dpi=300)
        
    finally:
        await adapter.close()
```

### 2. 同业对比

对比同行业多家公司的成长能力指标，评估相对成长性。

```python
async def compare_industry_growth():
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        # 银行业对比
        banks = {
            "sh.601398": "工商银行",
            "sh.601288": "农业银行",
            "sh.600036": "招商银行",
            "sh.600000": "浦发银行"
        }
        
        comparison = []
        for code, name in banks.items():
            result = await adapter.get_growth_data(code=code, year=2023, quarter=2)
            if result:
                data = result[0]
                comparison.append({
                    "代码": code,
                    "名称": name,
                    "净资产增长率": data.get('yoy_equity'),
                    "总资产增长率": data.get('yoy_asset'),
                    "净利润增长率": data.get('yoy_ni'),
                    "每股收益增长率": data.get('yoy_eps_basic'),
                    "归母净利润增长率": data.get('yoy_pni')
                })
        
        df = pd.DataFrame(comparison)
        print(df)
        
    finally:
        await adapter.close()
```

### 3. 综合成长评分

基于多个成长能力指标构建综合评价体系。

```python
def calculate_growth_score(df):
    """
    计算成长能力综合评分
    评分标准：
    - 净利润同比增长率：权重 35%
    - 归属母公司净利润增长率：权重 30%
    - 每股收益同比增长率：权重 20%
    - 净资产同比增长率：权重 15%
    """
    # 数据标准化（0-100 分）
    for col in ['yoy_ni', 'yoy_pni', 'yoy_eps_basic', 'yoy_equity']:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val > min_val:
                df[f'{col}_score'] = (df[col] - min_val) / (max_val - min_val) * 100
            else:
                df[f'{col}_score'] = 50  # 如果所有值相同，给中等分数
    
    # 加权计算综合评分
    df['composite_score'] = (
        df['yoy_ni_score'] * 0.35 +
        df['yoy_pni_score'] * 0.30 +
        df['yoy_eps_basic_score'] * 0.20 +
        df['yoy_equity_score'] * 0.15
    )
    
    return df
```

### 4. 成长性预警

识别成长能力指标异常的企业。

```python
def growth_warning_analysis(df, code: str):
    """
    成长能力预警分析
    
    预警信号：
    1. 净利润增长率连续下降
    2. 净利润增长率为负
    3. 每股收益增长率低于净利润增长率
    4. 净资产增长率为负
    """
    df = df.sort_values('stat_date')
    
    warnings = []
    
    # 检查净利润增长率趋势
    if len(df) >= 2:
        recent = df.iloc[-1]['yoy_ni']
        previous = df.iloc[-2]['yoy_ni']
        
        if recent and previous:
            if recent < 0:
                warnings.append("⚠️ 净利润增长率为负（负增长）")
            
            if recent < previous * 0.5:  # 下降超过 50%
                warnings.append("⚠️ 净利润增长率大幅下降")
    
    # 检查每股收益增长率
    if len(df) >= 1:
        eps_growth = df.iloc[-1]['yoy_eps_basic']
        ni_growth = df.iloc[-1]['yoy_ni']
        
        if eps_growth and ni_growth:
            if eps_growth < ni_growth * 0.8:  # 低于净利润增长率的 80%
                warnings.append("⚠️ 每股收益增长显著低于净利润增长")
    
    # 检查净资产增长率
    if len(df) >= 1:
        equity_growth = df.iloc[-1]['yoy_equity']
        if equity_growth and equity_growth < 0:
            warnings.append("⚠️ 净资产负增长")
    
    if warnings:
        print(f"\n{code} 成长能力预警：")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print(f"\n{code} 成长能力正常 ✓")
```

### 5. 成长股筛选

基于成长能力指标筛选高成长性股票。

```python
def screen_growth_stocks(data_dict):
    """
    筛选高成长股票
    
    筛选标准：
    1. 净利润增长率 > 20%
    2. 归属母公司净利润增长率 > 20%
    3. 每股收益增长率 > 15%
    4. 净资产增长率 > 10%
    5. 所有指标为正增长
    """
    growth_stocks = []
    
    for code, data in data_dict.items():
        if not data:
            continue
        
        item = data[0]
        
        # 检查各项指标
        conditions = [
            item.get('yoy_ni') and item['yoy_ni'] > 20,
            item.get('yoy_pni') and item['yoy_pni'] > 20,
            item.get('yoy_eps_basic') and item['yoy_eps_basic'] > 15,
            item.get('yoy_equity') and item['yoy_equity'] > 10,
            item.get('yoy_ni') and item['yoy_ni'] > 0,
        ]
        
        if all(conditions):
            growth_stocks.append({
                'code': code,
                'yoy_ni': item['yoy_ni'],
                'yoy_pni': item['yoy_pni'],
                'yoy_eps_basic': item['yoy_eps_basic'],
                'yoy_equity': item['yoy_equity'],
                'composite_score': (
                    item['yoy_ni'] * 0.35 +
                    item['yoy_pni'] * 0.30 +
                    item['yoy_eps_basic'] * 0.20 +
                    item['yoy_equity'] * 0.15
                )
            })
    
    # 按综合评分排序
    growth_stocks.sort(key=lambda x: x['composite_score'], reverse=True)
    
    return growth_stocks
```

---

## 常见问题

### Q1: 为什么某些指标返回 null？

**答**：可能原因：
1. 该季度财报未披露相关数据
2. 上年同期数据缺失（无法计算增长率）
3. 上年同期数据为 0（无法计算增长率）
4. 数据源本身缺失

**解决方案**：
- 尝试查询其他季度
- 查看企业财报原文
- 理解企业特殊情况

### Q2: 增长率为负数怎么办？

**答**：
- **短期负增长**：可能是周期性波动
- **持续负增长**：企业经营出现问题
- **行业普遍负增长**：行业周期性衰退

**建议**：
- 结合行业环境分析
- 对比历史数据
- 关注企业应对措施

### Q3: 如何获取年度数据？

**答**：设置 `quarter=4` 即可获取年报数据。

```python
# 获取 2023 年年报成长能力数据
result = await adapter.get_growth_data(
    code="sh.600000",
    year=2023,
    quarter=4  # 年报
)
```

### Q4: 数据何时更新？

**答**：
- **一季报**：4 月 1 日 -4 月 30 日
- **中报**：7 月 1 日 -8 月 31 日
- **三季报**：10 月 1 日 -10 月 31 日
- **年报**：次年 1 月 1 日 -4 月 30 日

具体更新时间以企业实际披露为准。

### Q5: 如何结合其他财务指标分析？

**答**：建议结合：
1. **盈利能力指标**（ROE、毛利率、净利率）
2. **营运能力指标**（周转率、周转天数）
3. **偿债能力指标**（流动比率、速动比率、资产负债率）

综合分析才能全面评估企业成长性。

### Q6: 增长率过高是否一定好？

**答**：不一定！
- **可持续增长**：健康的发展模式
- **过快增长**：可能存在风险
  - 盲目扩张
  - 财务造假
  - 不可持续

**建议**：
- 关注增长质量
- 分析增长来源
- 评估可持续性

---

## 最佳实践

### 1. 数据质量控制

```python
def validate_growth_data(data):
    """验证成长能力数据质量"""
    if not data:
        return False, "数据为空"
    
    item = data[0]
    
    # 检查必要字段
    required_fields = ['code', 'pub_date', 'stat_date']
    for field in required_fields:
        if not item.get(field):
            return False, f"缺少必要字段：{field}"
    
    # 检查指标合理性（增长率通常在 -100% 到 500% 之间）
    growth_fields = ['yoy_equity', 'yoy_asset', 'yoy_ni', 'yoy_eps_basic', 'yoy_pni']
    for field in growth_fields:
        value = item.get(field)
        if value:
            if value < -100 or value > 500:
                return False, f"{field} 异常：{value}%"
    
    return True, "数据有效"
```

### 2. 异常值处理

```python
def handle_growth_outliers(df):
    """处理成长能力数据异常值"""
    # 使用 IQR 方法识别异常值
    for col in ['yoy_equity', 'yoy_asset', 'yoy_ni', 'yoy_eps_basic', 'yoy_pni']:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # 标记异常值
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 替换异常值为边界值
            df[col] = df[col].clip(lower_bound, upper_bound)
    
    return df
```

### 3. 数据可视化

```python
def plot_growth_dashboard(df, code: str):
    """绘制成长能力仪表盘"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 净利润增长率
    axes[0, 0].plot(df['stat_date'], df['yoy_ni'], 'r-o')
    axes[0, 0].axhline(y=0, color='gray', linestyle='--', linewidth=1)
    axes[0, 0].axhline(y=20, color='green', linestyle='--', linewidth=1, alpha=0.5)
    axes[0, 0].set_title('净利润同比增长率')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 每股收益增长率
    axes[0, 1].plot(df['stat_date'], df['yoy_eps_basic'], 'b-o')
    axes[0, 1].axhline(y=0, color='gray', linestyle='--', linewidth=1)
    axes[0, 1].set_title('基本每股收益同比增长率')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 净资产增长率
    axes[1, 0].plot(df['stat_date'], df['yoy_equity'], 'g-o')
    axes[1, 0].axhline(y=0, color='gray', linestyle='--', linewidth=1)
    axes[1, 0].set_title('净资产同比增长率')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 总资产增长率
    axes[1, 1].plot(df['stat_date'], df['yoy_asset'], 'm-o')
    axes[1, 1].axhline(y=0, color='gray', linestyle='--', linewidth=1)
    axes[1, 1].set_title('总资产同比增长率')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.suptitle(f'{code} 成长能力指标仪表盘', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'{code}_growth_dashboard.png', dpi=300)
```

### 4. 成长性评级

```python
def rate_growth_potential(df):
    """
    成长性评级
    
    评级标准：
    - AAA: 综合评分 > 80，所有指标 > 30%
    - AA: 综合评分 > 70，所有指标 > 20%
    - A: 综合评分 > 60，所有指标 > 10%
    - BBB: 综合评分 > 50，所有指标 > 5%
    - BB: 综合评分 > 40，所有指标 > 0%
    - B: 综合评分 <= 40 或有负增长指标
    """
    # 计算最新季度的综合评分
    latest = df.iloc[-1]
    
    composite_score = (
        latest['yoy_ni'] * 0.35 +
        latest['yoy_pni'] * 0.30 +
        latest['yoy_eps_basic'] * 0.20 +
        latest['yoy_equity'] * 0.15
    )
    
    # 检查所有指标是否为正
    all_positive = all([
        latest['yoy_ni'] > 0,
        latest['yoy_pni'] > 0,
        latest['yoy_eps_basic'] > 0,
        latest['yoy_equity'] > 0
    ])
    
    # 评级
    if composite_score > 80 and all(latest[col] > 30 for col in ['yoy_ni', 'yoy_pni', 'yoy_eps_basic', 'yoy_equity']):
        rating = 'AAA'
    elif composite_score > 70 and all(latest[col] > 20 for col in ['yoy_ni', 'yoy_pni', 'yoy_eps_basic', 'yoy_equity']):
        rating = 'AA'
    elif composite_score > 60 and all(latest[col] > 10 for col in ['yoy_ni', 'yoy_pni', 'yoy_eps_basic', 'yoy_equity']):
        rating = 'A'
    elif composite_score > 50 and all(latest[col] > 5 for col in ['yoy_ni', 'yoy_pni', 'yoy_eps_basic', 'yoy_equity']):
        rating = 'BBB'
    elif composite_score > 40 and all_positive:
        rating = 'BB'
    else:
        rating = 'B'
    
    return rating, composite_score
```

---

## 相关文档

- [BaoStock 完整使用指南](./BAOSTOCK_COMPLETE_GUIDE.md)
- [季频盈利能力查询](./BAOSTOCK_PROFIT_GUIDE.md)
- [季频营运能力查询](./BAOSTOCK_OPERATION_GUIDE.md)
- [估值指标查询](./BAOSTOCK_VALUATION_GUIDE.md)
- [除权除息信息](./BAOSTOCK_DIVIDEND_GUIDE.md)
- [复权因子查询](./BAOSTOCK_FACTOR_GUIDE.md)
- [指数数据查询](./BAOSTOCK_INDEX_GUIDE.md)

---

## 参考资料

1. BaoStock 官网：http://www.baostock.com
2. 成长能力分析教程：https://www.investopedia.com/terms/g/growthrates.asp
3. 财务报表分析：https://www.investopedia.com/terms/f/financialratio.asp
4. 成长股投资理论：https://www.investopedia.com/terms/g/growthinvesting.asp

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| 1.0 | 2024-01-15 | 初始版本，完成基础文档 |
| 1.1 | 2024-01-20 | 添加数据分析应用示例 |
| 1.2 | 2024-01-25 | 完善指标解读和最佳实践 |

---

**文档最后更新**：2024-01-25  
**维护者**：Quant 团队  
**联系方式**：support@quant.com
