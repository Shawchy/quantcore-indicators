# BaoStock 季频营运能力数据查询使用指南

## 目录

- [概述](#概述)
- [API 接口说明](#api-接口说明)
- [参数说明](#参数说明)
- [返回数据说明](#返回数据说明)
- [使用示例](#使用示例)
- [营运能力指标详解](#营运能力指标详解)
- [数据分析应用](#数据分析应用)
- [常见问题](#常见问题)

---

## 概述

**季频营运能力**数据用于评估企业的资产管理效率和运营能力。通过 BaoStock 提供的 `query_operation_data()` API，可以获取上市公司的季度营运能力指标。

### 数据特点

- **数据范围**：2007 年至今
- **更新频率**：季度更新
- **数据源**：上市公司财报
- **适用场景**：财务分析、基本面分析、投资决策

### 支持的指标

| 指标代码 | 指标名称 | 单位 |
|---------|---------|------|
| NRTurnRatio | 应收账款周转率 | 次 |
| NRTurnDays | 应收账款周转天数 | 天 |
| INVTurnRatio | 存货周转率 | 次 |
| INVTurnDays | 存货周转天数 | 天 |
| CATurnRatio | 流动资产周转率 | 次 |
| AssetTurnRatio | 总资产周转率 | 次 |

---

## API 接口说明

### 方法签名

```python
async def get_operation_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]
```

### 功能描述

通过 API 接口获取季频营运能力信息，可以通过参数设置获取对应年份、季度数据。

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

`List[Dict[str, Any]]`：营运能力数据列表，每个元素为一个字典。

### 返回字段

| 字段名 | 类型 | 说明 |
|-------|------|------|
| code | str | 证券代码 |
| pub_date | str | 公司发布财报的日期（YYYY-MM-DD） |
| stat_date | str | 财报统计的季度的最后一天（YYYY-MM-DD） |
| nr_turn_ratio | float | 应收账款周转率（次） |
| nr_turn_days | float | 应收账款周转天数（天） |
| inv_turn_ratio | float | 存货周转率（次） |
| inv_turn_days | float | 存货周转天数（天） |
| ca_turn_ratio | float | 流动资产周转率（次） |
| asset_turn_ratio | float | 总资产周转率（次） |

### 返回示例

```json
[
  {
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "nr_turn_ratio": 2.5,
    "nr_turn_days": 72.0,
    "inv_turn_ratio": null,
    "inv_turn_days": null,
    "ca_turn_ratio": 0.15,
    "asset_turn_ratio": 0.05
  }
]
```

---

## 使用示例

### 示例 1：获取最新季度营运能力数据

```python
import baostock as bs
import pandas as pd
from app.adapters.baostock_adapter import BaostockAdapter

async def get_latest_operation():
    # 创建适配器实例
    adapter = BaostockAdapter()
    
    # 初始化（自动登录）
    await adapter.initialize()
    
    try:
        # 获取浦发银行最新季度营运能力数据
        result = await adapter.get_operation_data(code="sh.600000")
        
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
        # 获取工商银行 2023 年第二季度数据
        result = await adapter.get_operation_data(
            code="sh.601398",
            year=2023,
            quarter=2
        )
        
        for item in result:
            print(f"发布日期：{item['pub_date']}")
            print(f"统计日期：{item['stat_date']}")
            print(f"应收账款周转率：{item['nr_turn_ratio']}")
            print(f"应收账款周转天数：{item['nr_turn_days']} 天")
            print(f"流动资产周转率：{item['ca_turn_ratio']}")
            print(f"总资产周转率：{item['asset_turn_ratio']}")
            
    finally:
        await adapter.close()
```

### 示例 3：获取多年多季度数据（趋势分析）

```python
async def get_operation_trend():
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        all_data = []
        
        # 获取 2020-2023 年每年第二季度的数据
        for year in range(2020, 2024):
            result = await adapter.get_operation_data(
                code="sh.600000",
                year=year,
                quarter=2
            )
            all_data.extend(result)
        
        # 转换为 DataFrame
        df = pd.DataFrame(all_data)
        
        # 保存为 CSV 文件
        df.to_csv("operation_trend.csv", index=False, encoding='utf-8-sig')
        print(f"已保存 {len(df)} 条数据到 operation_trend.csv")
        
    finally:
        await adapter.close()
```

### 示例 4：批量获取多只股票数据

```python
async def get_multi_stocks_operation():
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        stock_codes = ["sh.600000", "sh.601398", "sz.000001"]
        all_results = []
        
        for code in stock_codes:
            result = await adapter.get_operation_data(code=code)
            all_results.extend(result)
            print(f"已获取 {code} 的数据")
        
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

# 营运能力
operation_list = []
rs_operation = bs.query_operation_data(code="sh.600000", year=2023, quarter=2)
while (rs_operation.error_code == '0') & rs_operation.next():
    operation_list.append(rs_operation.get_row_data())

result_operation = pd.DataFrame(operation_list, columns=rs_operation.fields)

# 打印输出
print(result_operation)

# 结果集输出到 csv 文件
result_operation.to_csv("D:\\operation_data.csv", encoding="gbk", index=False)

# 登出系统
bs.logout()
```

---

## 营运能力指标详解

### 1. 应收账款周转率 (NRTurnRatio)

#### 定义

反映企业应收账款周转速度的比率，衡量企业收账速度和管理效率。

#### 计算公式

```
应收账款周转率 (次) = 营业收入 / [(期初应收票据及应收账款净额 + 期末应收票据及应收账款净额) / 2]
```

#### 指标解读

- **数值越高**：说明收账速度快，资金使用效率高
- **数值越低**：说明收账速度慢，可能存在坏账风险
- **行业差异**：不同行业差异较大，应与同行业比较

#### 合理范围

| 行业类型 | 合理周转率 (次/年) |
|---------|------------------|
| 制造业 | 4-8 |
| 批发零售业 | 8-15 |
| 服务业 | 6-12 |
| 金融业 | 不适用 |

### 2. 应收账款周转天数 (NRTurnDays)

#### 定义

企业从取得应收账款权利到收回款项平均需要的天数。

#### 计算公式

```
应收账款周转天数 (天) = 季报天数 / 应收账款周转率
```

#### 季报天数标准

| 报告期 | 天数 |
|-------|------|
| 一季报 | 90 天 |
| 中报 | 180 天 |
| 三季报 | 270 天 |
| 年报 | 360 天 |

#### 指标解读

- **天数越短**：说明资金回收快，营运效率高
- **天数越长**：说明资金占用时间长，可能影响现金流

#### 示例计算

```
假设中报应收账款周转率 = 2.5 次
应收账款周转天数 = 180 / 2.5 = 72 天
```

### 3. 存货周转率 (INVTurnRatio)

#### 定义

反映企业存货周转速度的指标，衡量存货管理效率。

#### 计算公式

```
存货周转率 (次) = 营业成本 / [(期初存货净额 + 期末存货净额) / 2]
```

#### 指标解读

- **数值越高**：说明存货销售快，资金占用少
- **数值越低**：说明存货积压，可能存在滞销风险
- **适度原则**：过高可能导致缺货，过低表明滞销

#### 行业特点

| 行业 | 特点 | 周转率参考 |
|-----|------|-----------|
| 食品零售 | 保质期短，周转快 | 10-20 次 |
| 汽车制造 | 单价高，周转慢 | 4-8 次 |
| 房地产 | 开发周期长 | 0.3-0.8 次 |
| 电子产品 | 更新快 | 6-12 次 |

### 4. 存货周转天数 (INVTurnDays)

#### 定义

企业从取得存货到售出存货平均需要的天数。

#### 计算公式

```
存货周转天数 (天) = 季报天数 / 存货周转率
```

#### 指标解读

- **天数越短**：说明销售速度快，库存管理好
- **天数越长**：说明产品滞销，库存压力大

#### 示例

```
某零售企业年报显示：
存货周转率 = 12 次/年
存货周转天数 = 360 / 12 = 30 天
```

### 5. 流动资产周转率 (CATurnRatio)

#### 定义

反映企业流动资产利用效率的指标，衡量流动资产的周转速度。

#### 计算公式

```
流动资产周转率 (次) = 营业总收入 / [(期初流动资产 + 期末流动资产) / 2]
```

#### 指标解读

- **数值越高**：说明流动资产利用效率高
- **数值越低**：说明流动资产闲置，利用不充分

#### 流动资产包括

- 货币资金
- 交易性金融资产
- 应收账款
- 存货
- 其他流动资产

### 6. 总资产周转率 (AssetTurnRatio)

#### 定义

综合评价企业全部资产经营质量和利用效率的重要指标。

#### 计算公式

```
总资产周转率 (次) = 营业总收入 / [(期初资产总额 + 期末资产总额) / 2]
```

#### 指标解读

- **数值越高**：说明全部资产利用效率高，经营能力强
- **数值越低**：说明资产利用不充分，经营效率低

#### 合理范围参考

| 企业类型 | 合理周转率 (次/年) |
|---------|------------------|
| 轻资产企业 | 1.0-2.0 |
| 重资产企业 | 0.5-1.0 |
| 金融企业 | 0.1-0.3 |

---

## 数据分析应用

### 1. 趋势分析

通过对比多个季度的营运能力指标，分析企业运营效率的变化趋势。

```python
import pandas as pd
import matplotlib.pyplot as plt

async def analyze_operation_trend(code: str):
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        all_data = []
        
        # 获取近 4 年数据
        for year in range(2020, 2024):
            for quarter in [1, 2, 3, 4]:
                result = await adapter.get_operation_data(
                    code=code,
                    year=year,
                    quarter=quarter
                )
                all_data.extend(result)
        
        df = pd.DataFrame(all_data)
        df['stat_date'] = pd.to_datetime(df['stat_date'])
        df = df.sort_values('stat_date')
        
        # 绘制应收账款周转率趋势图
        plt.figure(figsize=(12, 6))
        plt.plot(df['stat_date'], df['nr_turn_ratio'], marker='o')
        plt.title('应收账款周转率趋势')
        plt.xlabel('日期')
        plt.ylabel('周转率 (次)')
        plt.grid(True)
        plt.savefig('nr_turnover_trend.png')
        
    finally:
        await adapter.close()
```

### 2. 同业对比

对比同行业多家公司的营运能力指标，评估相对竞争力。

```python
async def compare_industry():
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
            result = await adapter.get_operation_data(code=code, year=2023, quarter=2)
            if result:
                data = result[0]
                comparison.append({
                    "代码": code,
                    "名称": name,
                    "应收账款周转率": data.get('nr_turn_ratio'),
                    "总资产周转率": data.get('asset_turn_ratio'),
                    "流动资产周转率": data.get('ca_turn_ratio')
                })
        
        df = pd.DataFrame(comparison)
        print(df)
        
    finally:
        await adapter.close()
```

### 3. 综合评分

基于多个营运能力指标构建综合评价体系。

```python
def calculate_operation_score(df):
    """
    计算营运能力综合评分
    评分标准：
    - 应收账款周转率：权重 30%
    - 存货周转率：权重 25%
    - 流动资产周转率：权重 25%
    - 总资产周转率：权重 20%
    """
    # 数据标准化（0-100 分）
    df['nr_ratio_score'] = (df['nr_turn_ratio'] - df['nr_turn_ratio'].min()) / \
                           (df['nr_turn_ratio'].max() - df['nr_turn_ratio'].min()) * 100
    
    df['inv_ratio_score'] = (df['inv_turn_ratio'] - df['inv_turn_ratio'].min()) / \
                            (df['inv_turn_ratio'].max() - df['inv_turn_ratio'].min()) * 100
    
    df['ca_ratio_score'] = (df['ca_turn_ratio'] - df['ca_turn_ratio'].min()) / \
                           (df['ca_turn_ratio'].max() - df['ca_turn_ratio'].min()) * 100
    
    df['asset_ratio_score'] = (df['asset_turn_ratio'] - df['asset_turn_ratio'].min()) / \
                              (df['asset_turn_ratio'].max() - df['asset_turn_ratio'].min()) * 100
    
    # 加权计算综合评分
    df['composite_score'] = (
        df['nr_ratio_score'] * 0.30 +
        df['inv_ratio_score'] * 0.25 +
        df['ca_ratio_score'] * 0.25 +
        df['asset_ratio_score'] * 0.20
    )
    
    return df
```

### 4. 预警分析

识别营运能力指标异常的企业。

```python
def operation_warning_analysis(df, code: str):
    """
    营运能力预警分析
    
    预警信号：
    1. 应收账款周转率连续下降
    2. 存货周转率大幅下降
    3. 总资产周转率低于行业平均 50%
    """
    df = df.sort_values('stat_date')
    
    warnings = []
    
    # 检查应收账款周转率趋势
    if len(df) >= 2:
        recent = df.iloc[-1]['nr_turn_ratio']
        previous = df.iloc[-2]['nr_turn_ratio']
        if recent < previous * 0.8:  # 下降超过 20%
            warnings.append("⚠️ 应收账款周转率大幅下降")
    
    # 检查存货周转率
    if len(df) >= 2:
        recent = df.iloc[-1]['inv_turn_ratio']
        previous = df.iloc[-2]['inv_turn_ratio']
        if recent and previous and recent < previous * 0.7:  # 下降超过 30%
            warnings.append("⚠️ 存货周转率显著下降")
    
    # 检查总资产周转率
    if len(df) >= 1:
        asset_ratio = df.iloc[-1]['asset_turn_ratio']
        if asset_ratio and asset_ratio < 0.1:  # 低于 0.1
            warnings.append("⚠️ 总资产周转率偏低")
    
    if warnings:
        print(f"\n{code} 营运能力预警：")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print(f"\n{code} 营运能力正常 ✓")
```

---

## 常见问题

### Q1: 为什么某些指标返回 null？

**答**：可能原因：
1. 该季度财报未披露相关数据
2. 企业性质特殊（如金融业某些指标不适用）
3. 数据源本身缺失

**解决方案**：
- 尝试查询其他季度
- 查看企业财报原文
- 理解行业特殊性

### Q2: 应收账款周转率为 0 或异常高怎么办？

**答**：
- **为 0**：可能企业无应收账款（如零售业）
- **异常高**：可能营业收入大幅增长或应收账款大幅减少

**建议**：
- 结合利润表分析
- 对比历史数据
- 参考同行业水平

### Q3: 如何获取年度数据？

**答**：设置 `quarter=4` 即可获取年报数据。

```python
# 获取 2023 年年报数据
result = await adapter.get_operation_data(
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
2. **偿债能力指标**（流动比率、速动比率、资产负债率）
3. **成长能力指标**（营收增长率、净利润增长率）

综合分析才能全面评估企业状况。

### Q6: 为什么银行股的营运能力指标特殊？

**答**：银行业特殊性：
- 主要资产是贷款，不是存货
- 应收账款概念不同
- 流动资产和总资产结构特殊

**建议**：银行业应使用专门的财务分析指标。

---

## 最佳实践

### 1. 数据质量控制

```python
def validate_operation_data(data):
    """验证营运能力数据质量"""
    if not data:
        return False, "数据为空"
    
    item = data[0]
    
    # 检查必要字段
    required_fields = ['code', 'pub_date', 'stat_date']
    for field in required_fields:
        if not item.get(field):
            return False, f"缺少必要字段：{field}"
    
    # 检查指标合理性
    if item.get('nr_turn_ratio') and item['nr_turn_ratio'] < 0:
        return False, "应收账款周转率不能为负"
    
    if item.get('asset_turn_ratio') and item['asset_turn_ratio'] < 0:
        return False, "总资产周转率不能为负"
    
    return True, "数据有效"
```

### 2. 异常值处理

```python
def handle_outliers(df):
    """处理异常值"""
    # 使用 IQR 方法识别异常值
    for col in ['nr_turn_ratio', 'inv_turn_ratio', 'ca_turn_ratio', 'asset_turn_ratio']:
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
def plot_operation_dashboard(df, code: str):
    """绘制营运能力仪表盘"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 应收账款周转率
    axes[0, 0].plot(df['stat_date'], df['nr_turn_ratio'], 'b-o')
    axes[0, 0].set_title('应收账款周转率')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 存货周转率
    if df['inv_turn_ratio'].notna().any():
        axes[0, 1].plot(df['stat_date'], df['inv_turn_ratio'], 'g-o')
        axes[0, 1].set_title('存货周转率')
        axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 流动资产周转率
    axes[1, 0].plot(df['stat_date'], df['ca_turn_ratio'], 'r-o')
    axes[1, 0].set_title('流动资产周转率')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 总资产周转率
    axes[1, 1].plot(df['stat_date'], df['asset_turn_ratio'], 'm-o')
    axes[1, 1].set_title('总资产周转率')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.suptitle(f'{code} 营运能力指标仪表盘', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'{code}_operation_dashboard.png', dpi=300)
```

---

## 相关文档

- [BaoStock 完整使用指南](./BAOSTOCK_COMPLETE_GUIDE.md)
- [季频盈利能力查询](./BAOSTOCK_PROFIT_GUIDE.md)
- [估值指标查询](./BAOSTOCK_VALUATION_GUIDE.md)
- [除权除息信息](./BAOSTOCK_DIVIDEND_GUIDE.md)
- [复权因子查询](./BAOSTOCK_FACTOR_GUIDE.md)
- [指数数据查询](./BAOSTOCK_INDEX_GUIDE.md)

---

## 参考资料

1. BaoStock 官网：http://www.baostock.com
2. 营运能力分析教程：https://www.investopedia.com/terms/o/operatingratio.asp
3. 财务报表分析：https://www.investopedia.com/terms/f/financialratio.asp

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
