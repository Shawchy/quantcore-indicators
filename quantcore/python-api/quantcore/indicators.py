# -*- coding: utf-8 -*-
"""
技术指标库

提供常用技术指标：
- MA: 移动平均
- EMA: 指数平均
- MACD: 异同移动平均
- RSI: 相对强弱指标
- BOLL: 布林带
"""

from typing import List


def ma(prices: List[float], period: int) -> List[float]:
    """
    移动平均线
    
    Args:
        prices: 价格列表
        period: 周期
        
    Returns:
        MA 值列表
    """
    if len(prices) < period:
        return []
    
    result = []
    for i in range(period - 1, len(prices)):
        avg = sum(prices[i - period + 1:i + 1]) / period
        result.append(avg)
    
    return result


def ema(prices: List[float], period: int) -> List[float]:
    """
    指数移动平均线
    
    Args:
        prices: 价格列表
        period: 周期
        
    Returns:
        EMA 值列表
    """
    if len(prices) < period:
        return []
    
    multiplier = 2 / (period + 1)
    result = [sum(prices[:period]) / period]  # 第一个值为 SMA
    
    for i in range(period, len(prices)):
        ema_value = (prices[i] - result[-1]) * multiplier + result[-1]
        result.append(ema_value)
    
    return result


def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    MACD 指标
    
    Args:
        prices: 价格列表
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
        
    Returns:
        包含 MACD、Signal、Histogram 的字典
    """
    if len(prices) < slow:
        return {'macd': [], 'signal': [], 'histogram': []}
    
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    
    # 对齐长度
    min_len = min(len(fast_ema), len(slow_ema))
    fast_ema = fast_ema[-min_len:]
    slow_ema = slow_ema[-min_len:]
    
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal) if len(macd_line) >= signal else []
    
    histogram = []
    if signal_line:
        histogram = [m - s for m, s in zip(macd_line[-len(signal_line):], signal_line)]
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    RSI 相对强弱指标
    
    Args:
        prices: 价格列表
        period: 周期
        
    Returns:
        RSI 值列表
    """
    if len(prices) < period + 1:
        return []
    
    result = []
    
    for i in range(period, len(prices)):
        gains = []
        losses = []
        
        for j in range(i - period + 1, i + 1):
            change = prices[j] - prices[j - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_value = 100 - (100 / (1 + rs))
            result.append(rsi_value)
    
    return result


def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> dict:
    """
    布林带
    
    Args:
        prices: 价格列表
        period: 周期
        std_dev: 标准差倍数
        
    Returns:
        包含 upper、middle、lower 的字典
    """
    if len(prices) < period:
        return {'upper': [], 'middle': [], 'lower': []}
    
    middle = ma(prices, period)
    upper = []
    lower = []
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = variance ** 0.5
        
        upper.append(mean + std_dev * std)
        lower.append(mean - std_dev * std)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def kdj(prices: List[float], n: int = 9, m1: int = 3, m2: int = 3) -> dict:
    """
    KDJ 指标（随机指标）
    
    Args:
        prices: 价格列表（使用收盘价）
        n: KDJ 周期，默认 9
        m1: K 值平滑周期，默认 3
        m2: D 值平滑周期，默认 3
        
    Returns:
        字典 {'k': List, 'd': List, 'j': List}
    """
    if len(prices) < n:
        return {'k': [], 'd': [], 'j': []}
    
    # 简化版本：假设最高价和最低价与收盘价相近
    # 实际使用应该传入 high_prices 和 low_prices
    k = 50.0  # 初始值
    d = 50.0  # 初始值
    
    k_list = []
    d_list = []
    j_list = []
    
    for i in range(n - 1, len(prices)):
        # 计算最近 N 天的最高价和最低价
        recent_prices = prices[i - n + 1:i + 1]
        low_n = min(recent_prices)
        high_n = max(recent_prices)
        current_price = prices[i]
        
        # 计算 RSV
        if high_n == low_n:
            rsv = 50.0
        else:
            rsv = ((current_price - low_n) / (high_n - low_n)) * 100
        
        # 计算 K, D, J
        k = (2/3) * k + (1/3) * rsv
        d = (2/3) * d + (1/3) * k
        j = 3 * k - 2 * d
        
        k_list.append(k)
        d_list.append(d)
        j_list.append(j)
    
    return {'k': k_list, 'd': d_list, 'j': j_list}


def atr(high_prices: List[float], low_prices: List[float], 
       close_prices: List[float], period: int = 14) -> List[float]:
    """
    ATR 指标（平均真实波幅）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期，默认 14
        
    Returns:
        ATR 值列表
    """
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    tr_list = []
    
    # 计算真实波幅 TR
    for i in range(len(high_prices)):
        if i == 0:
            tr = high_prices[i] - low_prices[i]
        else:
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i-1])
            tr3 = abs(low_prices[i] - close_prices[i-1])
            tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    # 计算 ATR
    atr_list = []
    
    # 第一个 ATR 是前 period 个 TR 的平均值
    first_atr = sum(tr_list[:period]) / period
    atr_list.append(first_atr)
    
    # 后续使用平滑方法
    for i in range(period, len(tr_list)):
        atr = (atr_list[-1] * (period - 1) + tr_list[i]) / period
        atr_list.append(atr)
    
    return atr_list


def cci(high_prices: List[float], low_prices: List[float], 
      close_prices: List[float], period: int = 14) -> List[float]:
    """
    CCI 指标（顺势指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期，默认 14
        
    Returns:
        CCI 值列表
    """
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    cci_list = []
    
    for i in range(period - 1, len(close_prices)):
        # 计算典型价格 TP
        tp_list = []
        for j in range(i - period + 1, i + 1):
            tp = (high_prices[j] + low_prices[j] + close_prices[j]) / 3
            tp_list.append(tp)
        
        # 计算 TP 的移动平均
        ma_tp = sum(tp_list) / period
        
        # 计算平均偏差
        deviations = [abs(tp - ma_tp) for tp in tp_list]
        mean_deviation = sum(deviations) / period
        
        # 计算 CCI
        if mean_deviation == 0:
            cci = 0.0
        else:
            tp_current = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
            cci = (tp_current - ma_tp) / (0.015 * mean_deviation)
        
        cci_list.append(cci)
    
    return cci_list


def williams_r(high_prices: List[float], low_prices: List[float], 
               close_prices: List[float], period: int = 14) -> List[float]:
    """
    Williams %R 指标（威廉指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期，默认 14
        
    Returns:
        Williams %R 值列表（范围 -100 到 0）
    """
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    wr_list = []
    
    for i in range(period - 1, len(close_prices)):
        # 计算最近 N 天的最高价和最低价
        highest = max(high_prices[i - period + 1:i + 1])
        lowest = min(low_prices[i - period + 1:i + 1])
        current_close = close_prices[i]
        
        # 计算 Williams %R
        if highest == lowest:
            wr = -50.0
        else:
            wr = ((highest - current_close) / (highest - lowest)) * -100
        
        wr_list.append(wr)
    
    return wr_list


def obv(close_prices: List[float], volumes: List[int]) -> List[float]:
    """
    OBV 指标（能量潮）
    
    Args:
        close_prices: 收盘价列表
        volumes: 成交量列表
        
    Returns:
        OBV 值列表
    """
    if len(close_prices) != len(volumes) or len(close_prices) < 2:
        return []
    
    obv_list = [0.0]  # 初始 OBV 为 0
    
    for i in range(1, len(close_prices)):
        if close_prices[i] > close_prices[i-1]:
            obv = obv_list[-1] + volumes[i]
        elif close_prices[i] < close_prices[i-1]:
            obv = obv_list[-1] - volumes[i]
        else:
            obv = obv_list[-1]
        
        obv_list.append(obv)
    
    return obv_list


# 11. ADX - 平均趋向指标
def adx(high_prices: List[float], low_prices: List[float], 
        close_prices: List[float], period: int = 14) -> List[float]:
    """
    ADX 指标（Average Directional Index，平均趋向指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期，默认 14
        
    Returns:
        ADX 值列表
    """
    if len(high_prices) < period + 1:
        return []
    
    # 计算 +DM 和 -DM
    plus_dm = []
    minus_dm = []
    
    for i in range(1, len(high_prices)):
        up_move = high_prices[i] - high_prices[i-1]
        down_move = low_prices[i-1] - low_prices[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0.0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0.0)
    
    # 计算 TR
    tr_list = []
    for i in range(len(high_prices)):
        if i == 0:
            tr = high_prices[i] - low_prices[i]
        else:
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i-1])
            tr3 = abs(low_prices[i] - close_prices[i-1])
            tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    # 计算 +DI 和 -DI
    plus_di = []
    minus_di = []
    
    for i in range(len(plus_dm)):
        if i < period:
            plus_di.append(0.0)
            minus_di.append(0.0)
        else:
            sum_plus_dm = sum(plus_dm[i-period+1:i+1])
            sum_minus_dm = sum(minus_dm[i-period+1:i+1])
            sum_tr = sum(tr_list[i-period+1:i+1])
            
            plus_di.append((sum_plus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
            minus_di.append((sum_minus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
    
    # 计算 DX
    dx_list = []
    for i in range(len(plus_di)):
        if plus_di[i] + minus_di[i] > 0:
            dx = abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i]) * 100
        else:
            dx = 0.0
        dx_list.append(dx)
    
    # 计算 ADX（DX 的 MA）
    adx_list = []
    for i in range(len(dx_list)):
        if i < period:
            adx_list.append(0.0)
        else:
            adx = sum(dx_list[i-period+1:i+1]) / period
            adx_list.append(adx)
    
    return adx_list


# 12. SAR - 抛物线转向指标
def sar(high_prices: List[float], low_prices: List[float], 
        af: float = 0.02, max_af: float = 0.2) -> List[float]:
    """
    SAR 指标（Parabolic SAR，抛物线转向指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        af: 加速因子，默认 0.02
        max_af: 最大加速因子，默认 0.2
        
    Returns:
        SAR 值列表
    """
    if len(high_prices) < 3:
        return []
    
    sar_list = [low_prices[0]]  # 初始 SAR
    
    long_pos = True  # 多头仓位
    ep = high_prices[0]  # 极值点
    current_af = af
    
    for i in range(1, len(high_prices)):
        # 计算 SAR
        prev_sar = sar_list[-1]
        sar = prev_sar + current_af * (ep - prev_sar)
        
        # 更新极值点和加速因子
        if long_pos:
            if high_prices[i] > ep:
                ep = high_prices[i]
                current_af = min(current_af + af, max_af)
            
            # 检查是否转向
            if low_prices[i] < sar:
                long_pos = False
                sar = ep
                ep = low_prices[i]
                current_af = af
        else:
            if low_prices[i] < ep:
                ep = low_prices[i]
                current_af = min(current_af + af, max_af)
            
            # 检查是否转向
            if high_prices[i] > sar:
                long_pos = True
                sar = ep
                ep = high_prices[i]
                current_af = af
        
        sar_list.append(sar)
    
    return sar_list


# 13. STOCH - 随机指标
def stoch(high_prices: List[float], low_prices: List[float], 
          close_prices: List[float], k_period: int = 14, 
          d_period: int = 3) -> dict:
    """
    STOCH 指标（Stochastic Oscillator，随机指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        k_period: %K 周期，默认 14
        d_period: %D 周期，默认 3
        
    Returns:
        包含 %K 和 %D 的字典
    """
    if len(high_prices) < k_period:
        return {'k': [], 'd': []}
    
    k_list = []
    d_list = []
    
    for i in range(len(close_prices)):
        if i < k_period - 1:
            k_list.append(50.0)  # 初始值
            d_list.append(50.0)
        else:
            highest = max(high_prices[i-k_period+1:i+1])
            lowest = min(low_prices[i-k_period+1:i+1])
            
            if highest == lowest:
                k = 50.0
            else:
                k = ((close_prices[i] - lowest) / (highest - lowest)) * 100
            
            k_list.append(k)
            
            # 计算 %D（%K 的 MA）
            if len(k_list) >= d_period:
                d = sum(k_list[-d_period:]) / d_period
            else:
                d = 50.0
            d_list.append(d)
    
    return {'k': k_list, 'd': d_list}


# 14. ROC - 变动率指标
def roc(prices: List[float], period: int = 12) -> List[float]:
    """
    ROC 指标（Rate of Change，变动率指标）
    
    Args:
        prices: 价格列表
        period: 周期，默认 12
        
    Returns:
        ROC 值列表
    """
    if len(prices) < period + 1:
        return []
    
    roc_list = []
    
    for i in range(period, len(prices)):
        if prices[i - period] != 0:
            roc = ((prices[i] - prices[i - period]) / prices[i - period]) * 100
        else:
            roc = 0.0
        roc_list.append(roc)
    
    return roc_list


# 15. MFI - 资金流量指标
def mfi(high_prices: List[float], low_prices: List[float], 
        close_prices: List[float], volumes: List[int], 
        period: int = 14) -> List[float]:
    """
    MFI 指标（Money Flow Index，资金流量指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        volumes: 成交量列表
        period: 周期，默认 14
        
    Returns:
        MFI 值列表
    """
    if len(high_prices) < period + 1:
        return []
    
    # 计算典型价格
    typical_prices = [(high_prices[i] + low_prices[i] + close_prices[i]) / 3 
                      for i in range(len(high_prices))]
    
    # 计算资金流量
    money_flow = []
    for i in range(len(typical_prices)):
        mf = typical_prices[i] * volumes[i]
        money_flow.append(mf)
    
    # 计算正负资金流量
    positive_flow = []
    negative_flow = []
    
    for i in range(1, len(typical_prices)):
        if typical_prices[i] > typical_prices[i-1]:
            positive_flow.append(money_flow[i])
            negative_flow.append(0.0)
        elif typical_prices[i] < typical_prices[i-1]:
            positive_flow.append(0.0)
            negative_flow.append(money_flow[i])
        else:
            positive_flow.append(0.0)
            negative_flow.append(0.0)
    
    # 计算 MFI
    mfi_list = []
    for i in range(len(positive_flow)):
        if i < period - 1:
            mfi_list.append(50.0)
        else:
            sum_positive = sum(positive_flow[i-period+1:i+1])
            sum_negative = sum(negative_flow[i-period+1:i+1])
            
            if sum_negative == 0:
                mfi = 100.0
            else:
                money_ratio = sum_positive / sum_negative
                mfi = 100 - (100 / (1 + money_ratio))
            
            mfi_list.append(mfi)
    
    return mfi_list


# 16. AROON - 阿隆指标
def aroon(high_prices: List[float], low_prices: List[float], 
          period: int = 25) -> dict:
    """
    AROON 指标（Aroon Indicator，阿隆指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        period: 周期，默认 25
        
    Returns:
        包含 Aroon Up 和 Aroon Down 的字典
    """
    if len(high_prices) < period + 1:
        return {'up': [], 'down': []}
    
    aroon_up = []
    aroon_down = []
    
    for i in range(period, len(high_prices)):
        # 寻找周期内最高价和最低价的位置
        highest_high = max(high_prices[i-period+1:i+1])
        lowest_low = min(low_prices[i-period+1:i+1])
        
        # 计算距离周期结束的天数
        days_since_high = high_prices[i-period+1:i+1][::-1].index(highest_high)
        days_since_low = low_prices[i-period+1:i+1][::-1].index(lowest_low)
        
        # 计算 Aroon Up 和 Down
        up = ((period - days_since_high) / period) * 100
        down = ((period - days_since_low) / period) * 100
        
        aroon_up.append(up)
        aroon_down.append(down)
    
    # 填充前面的值
    for i in range(period):
        aroon_up.insert(0, 50.0)
        aroon_down.insert(0, 50.0)
    
    return {'up': aroon_up, 'down': aroon_down}


# 17. VWAP - 成交量加权平均价
def vwap(high_prices: List[float], low_prices: List[float], 
         close_prices: List[float], volumes: List[int]) -> List[float]:
    """
    VWAP 指标（Volume Weighted Average Price，成交量加权平均价）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        volumes: 成交量列表
        
    Returns:
        VWAP 值列表
    """
    if len(high_prices) < 2:
        return []
    
    vwap_list = []
    cumulative_pv = 0.0
    cumulative_volume = 0
    
    for i in range(len(high_prices)):
        typical_price = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
        pv = typical_price * volumes[i]
        
        cumulative_pv += pv
        cumulative_volume += volumes[i]
        
        if cumulative_volume > 0:
            vwap = cumulative_pv / cumulative_volume
        else:
            vwap = typical_price
        
        vwap_list.append(vwap)
    
    return vwap_list


# 18. PPO - 价格震荡百分比指标
def ppo(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    PPO 指标（Percentage Price Oscillator，价格震荡百分比指标）
    
    Args:
        prices: 价格列表
        fast: 快速周期，默认 12
        slow: 慢速周期，默认 26
        signal: 信号线周期，默认 9
        
    Returns:
        包含 PPO、Signal 和 Histogram 的字典
    """
    if len(prices) < slow:
        return {'ppo': [], 'signal': [], 'histogram': []}
    
    # 计算 EMA
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    
    # 计算 PPO
    ppo_list = []
    for i in range(len(prices)):
        if slow_ema[i] != 0:
            ppo = ((fast_ema[i] - slow_ema[i]) / slow_ema[i]) * 100
        else:
            ppo = 0.0
        ppo_list.append(ppo)
    
    # 计算信号线
    signal_list = ema(ppo_list, signal)
    
    # 计算柱状图
    histogram_list = [ppo_list[i] - signal_list[i] for i in range(len(ppo_list))]
    
    return {'ppo': ppo_list, 'signal': signal_list, 'histogram': histogram_list}


# 19. TRIX - 三重指数平滑移动平均
def trix(prices: List[float], period: int = 14) -> List[float]:
    """
    TRIX 指标（Triple Exponential Average，三重指数平滑移动平均）
    
    Args:
        prices: 价格列表
        period: 周期，默认 14
        
    Returns:
        TRIX 值列表
    """
    if len(prices) < period * 3:
        return []
    
    # 三次 EMA 平滑
    ema1 = ema(prices, period)
    ema2 = ema(ema1, period)
    ema3 = ema(ema2, period)
    
    # 计算 TRIX
    trix_list = []
    for i in range(len(ema3)):
        if i == 0 or ema3[i-1] == 0:
            trix_list.append(0.0)
        else:
            trix = ((ema3[i] - ema3[i-1]) / ema3[i-1]) * 100
            trix_list.append(trix)
    
    return trix_list


# 20. DMI - 动向指标
def dmi(high_prices: List[float], low_prices: List[float], 
        close_prices: List[float], period: int = 14) -> dict:
    """
    DMI 指标（Directional Movement Index，动向指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        period: 周期，默认 14
        
    Returns:
        包含 +DI、-DI 和 ADX 的字典
    """
    adx_values = adx(high_prices, low_prices, close_prices, period)
    
    # 计算 +DM 和 -DM
    plus_dm = []
    minus_dm = []
    
    for i in range(1, len(high_prices)):
        up_move = high_prices[i] - high_prices[i-1]
        down_move = low_prices[i-1] - low_prices[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0.0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0.0)
    
    # 计算 TR
    tr_list = []
    for i in range(len(high_prices)):
        if i == 0:
            tr = high_prices[i] - low_prices[i]
        else:
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i-1])
            tr3 = abs(low_prices[i] - close_prices[i-1])
            tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    # 计算 +DI 和 -DI
    plus_di = [0.0]
    minus_di = [0.0]
    
    for i in range(len(plus_dm)):
        if i < period:
            plus_di.append(0.0)
            minus_di.append(0.0)
        else:
            sum_plus_dm = sum(plus_dm[i-period+1:i+1])
            sum_minus_dm = sum(minus_dm[i-period+1:i+1])
            sum_tr = sum(tr_list[i-period+1:i+1])
            
            plus_di.append((sum_plus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
            minus_di.append((sum_minus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
    
    return {'plus_di': plus_di, 'minus_di': minus_di, 'adx': adx_values}


# 导出所有指标
__all__ = [
    'ma',
    'ema', 
    'macd',
    'rsi',
    'bollinger_bands',
    'kdj',
    'atr',
    'cci',
    'williams_r',
    'obv',
    'adx',
    'sar',
    'stoch',
    'roc',
    'mfi',
    'aroon',
    'vwap',
    'ppo',
    'trix',
    'dmi',
]
