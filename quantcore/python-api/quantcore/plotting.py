# -*- coding: utf-8 -*-
"""
可视化模块

提供回测结果的可视化功能：
- 资金曲线图
- 收益分布图
- 回撤曲线图
- 策略对比图
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os


def plot_equity_curve(
    daily_values: List[float],
    initial_capital: float = 1000000.0,
    title: str = "资金曲线",
    save_path: Optional[str] = None,
    show: bool = True,
    benchmark_values: Optional[List[float]] = None
) -> Optional[Any]:
    """
    绘制资金曲线图
    
    Args:
        daily_values: 每日资产值列表
        initial_capital: 初始资金
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
        benchmark_values: 基准资产值列表（可选）
        
    Returns:
        matplotlib Figure 对象（如果成功）
        
    Example:
    ```python
    from quantcore.plotting import plot_equity_curve
    
    # 绘制资金曲线
    plot_equity_curve(
        daily_values=result['daily_values'],
        initial_capital=1000000,
        title="策略资金曲线"
    )
    ```
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("错误：需要安装 matplotlib。请运行：pip install matplotlib")
        return None
    
    if not daily_values or len(daily_values) < 2:
        print("错误：数据不足，无法绘制")
        return None
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 生成 x 轴数据（交易日索引）
    days = list(range(len(daily_values)))
    
    # 绘制资金曲线
    ax.plot(days, daily_values, 'b-', linewidth=2, label='策略资金')
    
    # 绘制基准曲线（如果提供）
    if benchmark_values and len(benchmark_values) == len(daily_values):
        ax.plot(days, benchmark_values, 'g--', linewidth=1.5, label='基准')
    
    # 添加初始资金参考线
    ax.axhline(y=initial_capital, color='gray', linestyle='--', linewidth=1, alpha=0.7, 
               label='初始资金')
    
    # 设置标题和标签
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('交易日', fontsize=12)
    ax.set_ylabel('资产值', fontsize=12)
    
    # 格式化 y 轴（显示为万元或百万元）
    if max(daily_values) > 10000000:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000000:.1f}M'))
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/10000:.0f}K'))
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加图例
    ax.legend(loc='upper left')
    
    # 添加收益标注
    if len(daily_values) >= 2:
        total_return = (daily_values[-1] - daily_values[0]) / daily_values[0] * 100
        color = 'green' if total_return >= 0 else 'red'
        ax.annotate(
            f'总收益：{total_return:+.2f}%',
            xy=(len(daily_values)-1, daily_values[-1]),
            xytext=(len(daily_values)-50, daily_values[-1]),
            fontsize=10,
            color=color,
            fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到：{save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    return fig


def plot_drawdown_curve(
    daily_values: List[float],
    title: str = "回撤曲线",
    save_path: Optional[str] = None,
    show: bool = True
) -> Optional[Any]:
    """
    绘制回撤曲线图
    
    Args:
        daily_values: 每日资产值列表
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
        
    Returns:
        matplotlib Figure 对象（如果成功）
        
    Example:
    ```python
    from quantcore.plotting import plot_drawdown_curve
    
    plot_drawdown_curve(
        daily_values=result['daily_values'],
        title="策略回撤"
    )
    ```
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("错误：需要安装 matplotlib。请运行：pip install matplotlib")
        return None
    
    if not daily_values or len(daily_values) < 2:
        print("错误：数据不足，无法绘制")
        return None
    
    # 计算回撤
    drawdowns = []
    peak = daily_values[0]
    for value in daily_values:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100 if peak > 0 else 0
        drawdowns.append(drawdown)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # 生成 x 轴数据
    days = list(range(len(drawdowns)))
    
    # 绘制回撤曲线（填充区域）
    ax.fill_between(days, 0, drawdowns, alpha=0.5, color='red', label='回撤')
    ax.plot(days, drawdowns, 'r-', linewidth=1, alpha=0.8)
    
    # 设置标题和标签
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('交易日', fontsize=12)
    ax.set_ylabel('回撤 (%)', fontsize=12)
    
    # 添加最大回撤标注
    max_dd = max(drawdowns)
    max_dd_idx = drawdowns.index(max_dd)
    ax.annotate(
        f'最大回撤：{max_dd:.2f}%',
        xy=(max_dd_idx, max_dd),
        xytext=(max_dd_idx + 20, max_dd - 2),
        fontsize=10,
        color='darkred',
        fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
        arrowprops=dict(arrowstyle='->', color='darkred')
    )
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加图例
    ax.legend(loc='upper right')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到：{save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    return fig


def plot_return_distribution(
    daily_values: List[float],
    title: str = "收益分布",
    save_path: Optional[str] = None,
    show: bool = True,
    bins: int = 30
) -> Optional[Any]:
    """
    绘制收益分布图（直方图 + 密度曲线）
    
    Args:
        daily_values: 每日资产值列表
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
        bins: 直方图分组数
        
    Returns:
        matplotlib Figure 对象（如果成功）
        
    Example:
    ```python
    from quantcore.plotting import plot_return_distribution
    
    plot_return_distribution(
        daily_values=result['daily_values'],
        title="日收益分布"
    )
    ```
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("错误：需要安装 matplotlib 和 numpy。请运行：pip install matplotlib numpy")
        return None
    
    if not daily_values or len(daily_values) < 2:
        print("错误：数据不足，无法绘制")
        return None
    
    # 计算日收益率
    daily_returns = []
    for i in range(1, len(daily_values)):
        prev_value = daily_values[i-1]
        curr_value = daily_values[i]
        if prev_value > 0:
            daily_return = (curr_value - prev_value) / prev_value * 100
            daily_returns.append(daily_return)
    
    if not daily_returns:
        print("错误：无法计算收益率")
        return None
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制直方图
    n, bins_arr, patches = ax.hist(daily_returns, bins=bins, alpha=0.7, 
                                    color='skyblue', edgecolor='black', 
                                    density=True, label='收益率分布')
    
    # 添加正态分布拟合曲线
    try:
        from scipy import stats
        mu, sigma = np.mean(daily_returns), np.std(daily_returns)
        x = np.linspace(min(daily_returns), max(daily_returns), 100)
        pdf = stats.norm.pdf(x, mu, sigma)
        ax.plot(x, pdf, 'r-', linewidth=2, label=f'正态拟合\nμ={mu:.2f}%, σ={sigma:.2f}%')
    except ImportError:
        # 如果没有 scipy，只绘制均值线
        mu = np.mean(daily_returns)
        ax.axvline(x=mu, color='red', linestyle='--', linewidth=2, 
                   label=f'均值={mu:.2f}%')
    
    # 添加零轴参考线
    ax.axvline(x=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    
    # 设置标题和标签
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('日收益率 (%)', fontsize=12)
    ax.set_ylabel('概率密度', fontsize=12)
    
    # 添加统计信息
    stats_text = f'均值：{np.mean(daily_returns):.2f}%\n'
    stats_text += f'标准差：{np.std(daily_returns):.2f}%\n'
    stats_text += f'偏度：{skewness(daily_returns):.2f}\n'
    stats_text += f'峰度：{kurtosis(daily_returns):.2f}'
    
    ax.text(0.98, 0.95, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加图例
    ax.legend(loc='upper left')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到：{save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    return fig


def plot_strategy_comparison(
    results_dict: Dict[str, Dict[str, Any]],
    title: str = "策略对比",
    save_path: Optional[str] = None,
    show: bool = True
) -> Optional[Any]:
    """
    绘制多策略对比图
    
    Args:
        results_dict: 策略结果字典 {策略名：{'daily_values': [...], ...}}
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
        
    Returns:
        matplotlib Figure 对象（如果成功）
        
    Example:
    ```python
    from quantcore.plotting import plot_strategy_comparison
    
    results = {
        'MACD': {'daily_values': macd_values},
        'RSI': {'daily_values': rsi_values},
        'BOLL': {'daily_values': boll_values}
    }
    plot_strategy_comparison(results, title="多策略对比")
    ```
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("错误：需要安装 matplotlib。请运行：pip install matplotlib")
        return None
    
    if not results_dict or len(results_dict) < 2:
        print("错误：至少需要 2 个策略的数据")
        return None
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # 颜色列表
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray']
    
    # 绘制每个策略的资金曲线
    for idx, (name, result) in enumerate(results_dict.items()):
        daily_values = result.get('daily_values', [])
        if not daily_values:
            continue
        
        color = colors[idx % len(colors)]
        days = list(range(len(daily_values)))
        ax.plot(days, daily_values, linewidth=2, label=name, color=color)
    
    # 设置标题和标签
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('交易日', fontsize=12)
    ax.set_ylabel('资产值', fontsize=12)
    
    # 格式化 y 轴
    all_values = []
    for result in results_dict.values():
        all_values.extend(result.get('daily_values', []))
    
    if all_values:
        max_val = max(all_values)
        if max_val > 10000000:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1000000:.1f}M'))
        else:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/10000:.0f}K'))
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加图例
    ax.legend(loc='upper left')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到：{save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    return fig


def plot_monthly_returns(
    daily_values: List[float],
    initial_capital: float = 1000000.0,
    title: str = "月度收益",
    save_path: Optional[str] = None,
    show: bool = True
) -> Optional[Any]:
    """
    绘制月度收益热力图
    
    Args:
        daily_values: 每日资产值列表
        initial_capital: 初始资金
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
        
    Returns:
        matplotlib Figure 对象（如果成功）
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("错误：需要安装 matplotlib 和 numpy。请运行：pip install matplotlib numpy")
        return None
    
    if not daily_values or len(daily_values) < 30:
        print("错误：数据不足（至少需要 30 天数据）")
        return None
    
    # 计算月度收益
    monthly_returns = []
    month_labels = []
    
    # 假设每月 21 个交易日
    trading_days_per_month = 21
    
    for i in range(0, len(daily_values) - trading_days_per_month, trading_days_per_month):
        start_value = daily_values[i]
        end_value = daily_values[min(i + trading_days_per_month, len(daily_values) - 1)]
        monthly_return = (end_value - start_value) / start_value * 100
        monthly_returns.append(monthly_return)
        month_labels.append(f'M{i//trading_days_per_month + 1}')
    
    if not monthly_returns:
        print("错误：无法计算月度收益")
        return None
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # 绘制柱状图
    x_pos = np.arange(len(monthly_returns))
    colors = ['green' if r >= 0 else 'red' for r in monthly_returns]
    bars = ax.bar(x_pos, monthly_returns, color=colors, alpha=0.7, edgecolor='black')
    
    # 添加零轴参考线
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1)
    
    # 设置标题和标签
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('月收益率 (%)', fontsize=12)
    
    # 设置 x 轴刻度
    ax.set_xticks(x_pos)
    ax.set_xticklabels(month_labels, rotation=45)
    
    # 添加数值标签
    for i, (bar, ret) in enumerate(zip(bars, monthly_returns)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{ret:.1f}%',
                ha='center', va='bottom' if height > 0 else 'top',
                fontsize=9)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到：{save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    return fig


def plot_all_charts(
    result: Dict[str, Any],
    title: str = "策略绩效分析",
    save_dir: Optional[str] = None,
    show: bool = True
) -> None:
    """
    绘制所有图表（综合分析报告）
    
    Args:
        result: 回测结果字典（包含 daily_values 等）
        title: 总标题
        save_dir: 保存目录（可选）
        show: 是否显示图表
        
    Example:
    ```python
    from quantcore.plotting import plot_all_charts
    
    # 运行回测后
    result = portfolio.run(bars)
    
    # 绘制所有图表
    plot_all_charts(result, title="MACD 策略绩效分析")
    ```
    """
    daily_values = result.get('daily_values', [])
    initial_capital = result.get('total_initial_capital', 1000000.0)
    
    if not daily_values:
        print("错误：没有数据可绘制")
        return
    
    # 创建保存目录
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("正在生成可视化图表...")
    print("="*60)
    
    # 1. 资金曲线图
    print("\n1. 绘制资金曲线图...")
    save_path = os.path.join(save_dir, "equity_curve.png") if save_dir else None
    plot_equity_curve(
        daily_values=daily_values,
        initial_capital=initial_capital,
        title=f"{title} - 资金曲线",
        save_path=save_path,
        show=show
    )
    
    # 2. 回撤曲线图
    print("2. 绘制回撤曲线图...")
    save_path = os.path.join(save_dir, "drawdown_curve.png") if save_dir else None
    plot_drawdown_curve(
        daily_values=daily_values,
        title=f"{title} - 回撤分析",
        save_path=save_path,
        show=show
    )
    
    # 3. 收益分布图
    print("3. 绘制收益分布图...")
    save_path = os.path.join(save_dir, "return_distribution.png") if save_dir else None
    plot_return_distribution(
        daily_values=daily_values,
        title=f"{title} - 收益分布",
        save_path=save_path,
        show=show
    )
    
    # 4. 月度收益图
    print("4. 绘制月度收益图...")
    save_path = os.path.join(save_dir, "monthly_returns.png") if save_dir else None
    plot_monthly_returns(
        daily_values=daily_values,
        initial_capital=initial_capital,
        title=f"{title} - 月度收益",
        save_path=save_path,
        show=show
    )
    
    print("\n" + "="*60)
    print("所有图表生成完成！")
    if save_dir:
        print(f"图表已保存到目录：{save_dir}")
    print("="*60)


# 辅助函数
def skewness(data: List[float]) -> float:
    """计算偏度"""
    import numpy as np
    n = len(data)
    if n < 3:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return np.mean(((data - mean) / std) ** 3)


def kurtosis(data: List[float]) -> float:
    """计算峰度"""
    import numpy as np
    n = len(data)
    if n < 4:
        return 0.0
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    return np.mean(((data - mean) / std) ** 4) - 3


# 导入 matplotlib 的 FuncFormatter
try:
    from matplotlib.ticker import FuncFormatter
except ImportError:
    pass
