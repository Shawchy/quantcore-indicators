# QuantCore 可视化模块使用指南

## 概述

QuantCore 提供了完整的可视化功能，用于展示回测结果和策略绩效。可视化模块基于 matplotlib 构建，支持生成多种专业图表。

## 安装依赖

在使用可视化功能之前，需要安装必要的依赖包：

```bash
pip install matplotlib numpy scipy
```

或者使用提供的 requirements 文件：

```bash
pip install -r requirements_visualization.txt
```

## 图表类型

### 1. 资金曲线图 (Equity Curve)

展示账户资产随时间的变化趋势。

```python
from quantcore.plotting import plot_equity_curve

# 基础用法
plot_equity_curve(
    daily_values=result['daily_values'],
    initial_capital=1000000,
    title="策略资金曲线"
)

# 带基准对比
plot_equity_curve(
    daily_values=strategy_values,
    initial_capital=1000000,
    title="策略 vs 基准",
    benchmark_values=benchmark_values,  # 基准数据
    save_path="equity_curve.png",
    show=False  # 不显示，只保存
)
```

**参数说明：**
- `daily_values`: 每日资产值列表
- `initial_capital`: 初始资金
- `title`: 图表标题
- `benchmark_values`: 基准资产值（可选）
- `save_path`: 保存路径（可选）
- `show`: 是否显示图表

### 2. 回撤曲线图 (Drawdown Curve)

展示账户从历史最高点的回撤情况。

```python
from quantcore.plotting import plot_drawdown_curve

plot_drawdown_curve(
    daily_values=result['daily_values'],
    title="策略回撤分析",
    save_path="drawdown_curve.png"
)
```

**特点：**
- 自动计算并标注最大回撤
- 红色填充区域直观展示风险
- 显示回撤百分比

### 3. 收益分布图 (Return Distribution)

展示日收益率的分布情况，包括正态分布拟合。

```python
from quantcore.plotting import plot_return_distribution

plot_return_distribution(
    daily_values=result['daily_values'],
    title="日收益分布",
    bins=30,  # 直方图分组数
    save_path="return_distribution.png"
)
```

**显示信息：**
- 收益率直方图
- 正态分布拟合曲线
- 均值、标准差、偏度、峰度等统计指标

### 4. 月度收益图 (Monthly Returns)

以柱状图形式展示每月的收益率。

```python
from quantcore.plotting import plot_monthly_returns

plot_monthly_returns(
    daily_values=result['daily_values'],
    initial_capital=1000000,
    title="月度收益",
    save_path="monthly_returns.png"
)
```

**特点：**
- 绿色表示正收益，红色表示负收益
- 每个柱子上显示具体收益率数值

### 5. 策略对比图 (Strategy Comparison)

对比多个策略的资金曲线。

```python
from quantcore.plotting import plot_strategy_comparison

results = {
    'MACD': {'daily_values': macd_values},
    'RSI': {'daily_values': rsi_values},
    'BOLL': {'daily_values': boll_values}
}

plot_strategy_comparison(
    results_dict=results,
    title="多策略对比",
    save_path="strategy_comparison.png"
)
```

## 综合使用

### 一键生成所有图表

```python
from quantcore.plotting import plot_all_charts

# 运行回测后
result = portfolio.run(bars)

# 生成所有图表
plot_all_charts(
    result=result,
    title="MACD 策略绩效分析",
    save_dir="./output/charts",  # 保存目录
    show=False  # 不显示，只保存
)
```

这会生成以下文件：
- `equity_curve.png` - 资金曲线图
- `drawdown_curve.png` - 回撤曲线图
- `return_distribution.png` - 收益分布图
- `monthly_returns.png` - 月度收益图

## 完整示例

### 示例 1: 单策略可视化

```python
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.plotting import plot_all_charts

# 创建并运行策略
portfolio = StrategyPortfolio(initial_capital=1000000)
portfolio.add_strategy("MACD", MACDStrategy(), weight=1.0)

result = portfolio.run(bars, tplus1=True)

# 生成可视化图表
plot_all_charts(
    result=result,
    title="MACD 策略完整分析",
    save_dir="./macd_analysis"
)
```

### 示例 2: 多策略组合可视化

```python
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.plotting import plot_strategy_comparison, plot_all_charts

# 创建多策略组合
portfolio = StrategyPortfolio(initial_capital=1000000)
portfolio.add_strategy("MACD", MACDStrategy(), weight=0.5)
portfolio.add_strategy("RSI", RSIStrategy(), weight=0.5)

result = portfolio.run(bars, tplus1=True)

# 生成组合的完整分析
plot_all_charts(
    result=result,
    title="多策略组合绩效分析",
    save_dir="./portfolio_analysis"
)

# 对比各策略表现
strategy_results = portfolio.get_all_results()
comparison_data = {
    name: {'daily_values': engine.daily_values}
    for name, (strategy, engine) in portfolio.strategies.items()
}

plot_strategy_comparison(
    results_dict=comparison_data,
    title="组合内策略对比",
    save_path="./portfolio_analysis/strategy_comparison.png"
)
```

### 示例 3: 带基准对比

```python
from quantcore.plotting import plot_equity_curve

# 生成基准数据（买入持有）
benchmark_values = []
base_price = bars[0].close
shares = initial_capital / base_price

for bar in bars:
    benchmark_value = shares * bar.close
    benchmark_values.append(benchmark_value)

# 绘制对比图
plot_equity_curve(
    daily_values=strategy_values,
    initial_capital=initial_capital,
    title="策略 vs 基准",
    benchmark_values=benchmark_values,
    save_path="vs_benchmark.png"
)
```

## 图表定制

### 修改图表样式

```python
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文显示
plt.rcParams['axes.unicode_minus'] = False  # 负号显示

# 设置图表大小
fig, ax = plt.subplots(figsize=(14, 7))

# 自定义颜色
plot_equity_curve(
    daily_values=values,
    # ... 其他参数
)

# 获取图表对象进行修改
fig = plot_equity_curve(..., show=False)
ax = fig.gca()
ax.set_facecolor('#f5f5f5')  # 背景色
```

### 保存高质量图表

```python
# 高分辨率保存
plot_equity_curve(
    daily_values=values,
    save_path="high_quality.png",
    show=False
)

# 保存为 PDF（矢量图）
plot_equity_curve(
    daily_values=values,
    save_path="vector_plot.pdf",
    show=False
)

# 保存为 SVG
plot_equity_curve(
    daily_values=values,
    save_path="vector_plot.svg",
    show=False
)
```

## 输出示例

### 资金曲线图包含的信息：
- 资产变化趋势
- 初始资金参考线
- 总收益标注
- Y 轴自动格式化（K/M 单位）

### 回撤曲线图包含的信息：
- 回撤时间序列
- 最大回撤标注
- 回撤持续时间

### 收益分布图包含的信息：
- 收益率直方图
- 正态分布拟合
- 统计指标（均值、标准差、偏度、峰度）

## 常见问题

### Q: 中文显示乱码？
A: 设置合适的中文字体：
```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
```

### Q: 图表不显示？
A: 确保 `show=True`，并且安装了 GUI 后端：
```bash
pip install PyQt5
```

### Q: 保存的图片模糊？
A: 增加 DPI 参数：
```python
plot_equity_curve(
    ...,
    save_path="output.png",
    show=False
)
# 在 plotting.py 中修改 dpi=300 或更高
```

## API 参考

### plot_equity_curve()
```python
plot_equity_curve(
    daily_values: List[float],
    initial_capital: float = 1000000.0,
    title: str = "资金曲线",
    save_path: Optional[str] = None,
    show: bool = True,
    benchmark_values: Optional[List[float]] = None
) -> Optional[Figure]
```

### plot_drawdown_curve()
```python
plot_drawdown_curve(
    daily_values: List[float],
    title: str = "回撤曲线",
    save_path: Optional[str] = None,
    show: bool = True
) -> Optional[Figure]
```

### plot_return_distribution()
```python
plot_return_distribution(
    daily_values: List[float],
    title: str = "收益分布",
    save_path: Optional[str] = None,
    show: bool = True,
    bins: int = 30
) -> Optional[Figure]
```

### plot_monthly_returns()
```python
plot_monthly_returns(
    daily_values: List[float],
    initial_capital: float = 1000000.0,
    title: str = "月度收益",
    save_path: Optional[str] = None,
    show: bool = True
) -> Optional[Figure]
```

### plot_strategy_comparison()
```python
plot_strategy_comparison(
    results_dict: Dict[str, Dict[str, Any]],
    title: str = "策略对比",
    save_path: Optional[str] = None,
    show: bool = True
) -> Optional[Figure]
```

### plot_all_charts()
```python
plot_all_charts(
    result: Dict[str, Any],
    title: str = "策略绩效分析",
    save_dir: Optional[str] = None,
    show: bool = True
) -> None
```

## 更多信息

- 示例代码：`examples/visualization_example.py`
- 测试代码：`test_visualization.py`
- 模块源码：`python-api/quantcore/plotting.py`
