"""
utils/technical_indicators.py —— 技术指标计算（跨阶段复用的公共工具）

对应《学习路线》2.3「技术指标计算」，把常用技术指标封装成可复用函数，
供 01_数据能力/03_技术指标 及后续阶段（02 择时策略、04 因子、05 实战项目）
直接调用，避免每个脚本重写一遍指标公式。

指标分四大类（与《学习路线》2.3 表格一致）：
  趋势类 —— sma/ema/wma（移动平均）、macd、adx
  振荡类 —— rsi、kdj、wr（威廉指标）、cci
  波动类 —— boll（布林带）、atr
  量价类 —— obv、mfi、vwap（TA-Lib 无此函数，用 pandas 自实现）

约定：
  - 输入 df 为「长表」格式：每行 = 某只股票某一天，
    列含 code, date, open, high, low, close, volume（与 data/stock_daily 一致）
  - 所有函数都返回 df 的副本，并追加新列，不改动原数据
  - 指标列名统一带周期后缀（如 sma_20、rsi_14），
    复合指标用固定名（dif/dea/macd_hist、kdj_k/d/j、boll_up/mid/low）
  - 技术指标都是「按股票分别算」的：先用 groupby("code") 分组，
    否则跨股票的价格会被错误地串在一起

依赖：TA-Lib（Windows 需预编译 whl，见 00_前置基础/04_工具脚本 的安装说明）。
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import talib


# ------------------------------------------------------------------
# 内部工具：按股票分组应用 TA-Lib
# ------------------------------------------------------------------
def _group_apply(df: pd.DataFrame, func) -> pd.DataFrame:
    """按 code 分组，对每组调用 func，再把各组结果拼接回原行。

    func 接收「单只股票」的子 DataFrame（保留原索引），返回与子表等长的
    Series 或 DataFrame。groupby 按出现顺序遍历（sort=False），
    拼接后结果再通过索引对齐写回 df，顺序不会错乱。

    为什么不直接对整个 df 调 talib？因为 talib 把输入当一条连续时间序列，
    而长表里多只股票首尾相接，直接算会把 A 股最后一天和 B 股第一天
    当成相邻两天。所以必须 groupby 分组后逐股算。
    """
    return pd.concat([func(g) for _, g in df.groupby("code", sort=False)])


def _talib_1d(g: pd.DataFrame, col: str, talib_func, *args) -> pd.Series:
    """对单只股票的某一列调 TA-Lib 单输出函数，返回等长 Series。

    talib 要求 float64 数组，pandas Series 直接传进去会因 dtype 报错，
    所以先 to_numpy(dtype=float) 转成纯数组。
    """
    arr = g[col].to_numpy(dtype=np.float64)
    return pd.Series(talib_func(arr, *args), index=g.index)


# ------------------------------------------------------------------
# 趋势类
# ------------------------------------------------------------------
def sma(df: pd.DataFrame, timeperiod: int = 20, col: str = "close") -> pd.DataFrame:
    """简单移动平均 SMA：过去 N 天收盘价的算术平均。

    SMA = (P_t + P_{t-1} + ... + P_{t-N+1}) / N
    每个价位权重相同，缺点是滞后且对旧数据和新数据一视同仁。
    结果列：sma_{timeperiod}
    """
    df = df.copy()
    name = f"sma_{timeperiod}"
    df[name] = _group_apply(df, lambda g: _talib_1d(g, col, talib.SMA, timeperiod))
    return df


def ema(df: pd.DataFrame, timeperiod: int = 12, col: str = "close") -> pd.DataFrame:
    """指数移动平均 EMA：越近的价格权重越大，比 SMA 更灵敏。

    EMA_t = α·P_t + (1-α)·EMA_{t-1}，其中 α = 2/(N+1)
    EMA 是 MACD 的底层部件，也是趋势跟随策略常用的快线。
    结果列：ema_{timeperiod}
    """
    df = df.copy()
    name = f"ema_{timeperiod}"
    df[name] = _group_apply(df, lambda g: _talib_1d(g, col, talib.EMA, timeperiod))
    return df


def wma(df: pd.DataFrame, timeperiod: int = 20, col: str = "close") -> pd.DataFrame:
    """加权移动平均 WMA：给近期价格线性递增的权重（比 SMA 灵敏，比 EMA 直观）。

    与 SMA/EMA 并称三均线，横向比较三者可观察平滑速度差异。
    结果列：wma_{timeperiod}
    """
    df = df.copy()
    name = f"wma_{timeperiod}"
    df[name] = _group_apply(df, lambda g: _talib_1d(g, col, talib.WMA, timeperiod))
    return df


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26,
         signal: int = 9, col: str = "close") -> pd.DataFrame:
    """指数平滑异同移动平均 MACD（最常用的趋势/动能指标之一）。

    三根线：
      DIF        = EMA(fast) - EMA(slow)         快慢均线差
      DEA        = DIF 的 signal 日 EMA           信号线
      MACD 柱    = 2 × (DIF - DEA)                红绿柱，代表动能强弱

    用法：DIF 上穿 DEA（金叉）看多，下穿（死叉）看空；
         柱体由负转正为买入动能增强。默认参数 (12, 26, 9) 是行业惯例。
    结果列：dif, dea, macd_hist
    """
    df = df.copy()

    def _apply(g):
        arr = g[col].to_numpy(dtype=np.float64)
        dif, dea, hist = talib.MACD(arr, fastperiod=fast,
                                    slowperiod=slow, signalperiod=signal)
        return pd.DataFrame({"dif": dif, "dea": dea, "macd_hist": hist},
                            index=g.index)

    out = _group_apply(df, _apply)
    df["dif"], df["dea"], df["macd_hist"] = out["dif"], out["dea"], out["macd_hist"]
    return df


def adx(df: pd.DataFrame, timeperiod: int = 14) -> pd.DataFrame:
    """平均趋向指数 ADX：衡量趋势「强度」（不判断方向）。

    取值 0~100：<20 无趋势（震荡市），20~40 趋势形成，>40 强趋势，
    >60 罕见且往往见顶。ADX 配合 DMI 的 +DI/-DI 才能判断方向。
    结果列：adx_{timeperiod}
    """
    df = df.copy()
    name = f"adx_{timeperiod}"

    def _apply(g):
        high = g["high"].to_numpy(dtype=np.float64)
        low = g["low"].to_numpy(dtype=np.float64)
        close = g["close"].to_numpy(dtype=np.float64)
        return pd.Series(talib.ADX(high, low, close, timeperiod=timeperiod),
                         index=g.index)

    df[name] = _group_apply(df, _apply)
    return df


# ------------------------------------------------------------------
# 振荡类
# ------------------------------------------------------------------
def rsi(df: pd.DataFrame, timeperiod: int = 14, col: str = "close") -> pd.DataFrame:
    """相对强弱指标 RSI：衡量近期涨跌力量的对比，取值 0~100。

    RS = N 日平均涨幅 / N 日平均跌幅
    RSI = 100 - 100/(1 + RS)
    常用阈值：>70 超买（可能回调），<30 超卖（可能反弹）。
    结果列：rsi_{timeperiod}
    """
    df = df.copy()
    name = f"rsi_{timeperiod}"
    df[name] = _group_apply(df, lambda g: _talib_1d(g, col, talib.RSI, timeperiod))
    return df


def kdj(df: pd.DataFrame, fastk: int = 9, slowk: int = 3,
        slowd: int = 3) -> pd.DataFrame:
    """随机指标 KDJ：判断超买超卖与金叉死叉。

    基于「RSV（未成熟随机值）= (收盘 - N 日最低) / (N 日最高 - N 日最低)」，
    K 是 RSV 的移动平均，D 是 K 的移动平均，J = 3K - 2D（J 更灵敏、易钝化）。
    K 上穿 D 为金叉，下穿为死叉；K/D >80 超买、<20 超卖。
    TA-Lib 用 STOCH 得到 K、D，J 由公式手算。
    结果列：kdj_k, kdj_d, kdj_j
    """
    df = df.copy()

    def _apply(g):
        high = g["high"].to_numpy(dtype=np.float64)
        low = g["low"].to_numpy(dtype=np.float64)
        close = g["close"].to_numpy(dtype=np.float64)
        k, d = talib.STOCH(high, low, close, fastk_period=fastk,
                           slowk_period=slowk, slowd_period=slowd)
        j = 3 * k - 2 * d
        return pd.DataFrame({"kdj_k": k, "kdj_d": d, "kdj_j": j}, index=g.index)

    out = _group_apply(df, _apply)
    df["kdj_k"], df["kdj_d"], df["kdj_j"] = out["kdj_k"], out["kdj_d"], out["kdj_j"]
    return df


def wr(df: pd.DataFrame, timeperiod: int = 14) -> pd.DataFrame:
    """威廉指标 WR：衡量收盘价在近期高低区间中的位置，取值 -100~0。

    WR = (N 日最高价 - 收盘价) / (N 日最高价 - N 日最低价) × -100
    越接近 0 越强（收盘接近区间高点），越接近 -100 越弱。
    常用阈值：>-20 超买、<-80 超卖（注意与 RSI 的区间方向相反）。
    结果列：wr_{timeperiod}
    """
    df = df.copy()
    name = f"wr_{timeperiod}"

    def _apply(g):
        high = g["high"].to_numpy(dtype=np.float64)
        low = g["low"].to_numpy(dtype=np.float64)
        close = g["close"].to_numpy(dtype=np.float64)
        return pd.Series(talib.WILLR(high, low, close, timeperiod=timeperiod),
                         index=g.index)

    df[name] = _group_apply(df, _apply)
    return df


def cci(df: pd.DataFrame, timeperiod: int = 14) -> pd.DataFrame:
    """顺势指标 CCI：衡量价格相对其统计均值的偏离程度（无固定上下界）。

    CCI = (典型价格 - 典型价格均值) / (0.015 × 平均绝对偏差)
    典型价格 = (high + low + close) / 3。
    用法：>100 超买（强势），<-100 超卖；突破 ±100 常被视为趋势启动信号。
    结果列：cci_{timeperiod}
    """
    df = df.copy()
    name = f"cci_{timeperiod}"

    def _apply(g):
        high = g["high"].to_numpy(dtype=np.float64)
        low = g["low"].to_numpy(dtype=np.float64)
        close = g["close"].to_numpy(dtype=np.float64)
        return pd.Series(talib.CCI(high, low, close, timeperiod=timeperiod),
                         index=g.index)

    df[name] = _group_apply(df, _apply)
    return df


# ------------------------------------------------------------------
# 波动类
# ------------------------------------------------------------------
def boll(df: pd.DataFrame, timeperiod: int = 20,
         nbdev: float = 2.0, col: str = "close") -> pd.DataFrame:
    """布林带 BOLL：中轨 = MA，上下轨 = 中轨 ± nbdev 倍标准差。

      上轨 = MA(N) + nbdev × std(N)
      中轨 = MA(N)
      下轨 = MA(N) - nbdev × std(N)
    布林带基于「价格围绕均值波动」的假设，带宽会随波动率变化。
    用法：触及上轨可能超买、触及下轨可能超卖；带宽收窄预示变盘。
    结果列：boll_up, boll_mid, boll_low
    """
    df = df.copy()

    def _apply(g):
        arr = g[col].to_numpy(dtype=np.float64)
        up, mid, low = talib.BBANDS(arr, timeperiod=timeperiod,
                                    nbdevup=nbdev, nbdevdn=nbdev)
        return pd.DataFrame({"boll_up": up, "boll_mid": mid, "boll_low": low},
                            index=g.index)

    out = _group_apply(df, _apply)
    df["boll_up"], df["boll_mid"], df["boll_low"] = (
        out["boll_up"], out["boll_mid"], out["boll_low"]
    )
    return df


def atr(df: pd.DataFrame, timeperiod: int = 14) -> pd.DataFrame:
    """平均真实波幅 ATR：衡量价格波动幅度（不是方向），常用于设定止损距离。

    TR（真实波幅）取三者最大：当日高低差、|高-昨收|、|低-昨收|，
    ATR = TR 的 N 日移动平均。
    用法：止损价 = 入场价 - k×ATR；ATR 越大说明波动越大，止损应放越宽。
    结果列：atr_{timeperiod}
    """
    df = df.copy()
    name = f"atr_{timeperiod}"

    def _apply(g):
        high = g["high"].to_numpy(dtype=np.float64)
        low = g["low"].to_numpy(dtype=np.float64)
        close = g["close"].to_numpy(dtype=np.float64)
        return pd.Series(talib.ATR(high, low, close, timeperiod=timeperiod),
                         index=g.index)

    df[name] = _group_apply(df, _apply)
    return df


# ------------------------------------------------------------------
# 量价类
# ------------------------------------------------------------------
def obv(df: pd.DataFrame) -> pd.DataFrame:
    """能量潮 OBV：用成交量累加确认价格趋势，判断量价是否配合。

      收盘价上涨 → 当日 OBV += 当日成交量
      收盘价下跌 → 当日 OBV -= 当日成交量
      收盘价持平 → 当日 OBV 不变
    用法：价格创新高而 OBV 未同步创新高 → 量价背离，上涨动能衰竭。
    结果列：obv
    """
    df = df.copy()

    def _apply(g):
        close = g["close"].to_numpy(dtype=np.float64)
        vol = g["volume"].to_numpy(dtype=np.float64)
        return pd.Series(talib.OBV(close, vol), index=g.index)

    df["obv"] = _group_apply(df, _apply)
    return df


def mfi(df: pd.DataFrame, timeperiod: int = 14) -> pd.DataFrame:
    """资金流量指标 MFI：成交量加权的 RSI，又称「量能相对强弱」。

    先算典型价格 = (high+low+close)/3，再算资金流量 = 典型价格 × 成交量；
    资金流量上涨日为正、下跌日为负，MFI = 100 - 100/(1 + 正流量/负流量)。
    用法与 RSI 类似（>80 超买、<20 超卖），但多了成交量信息，更稳健。
    结果列：mfi_{timeperiod}
    """
    df = df.copy()
    name = f"mfi_{timeperiod}"

    def _apply(g):
        high = g["high"].to_numpy(dtype=np.float64)
        low = g["low"].to_numpy(dtype=np.float64)
        close = g["close"].to_numpy(dtype=np.float64)
        vol = g["volume"].to_numpy(dtype=np.float64)
        return pd.Series(talib.MFI(high, low, close, vol, timeperiod=timeperiod),
                         index=g.index)

    df[name] = _group_apply(df, _apply)
    return df


def vwap(df: pd.DataFrame, timeperiod: int = 20) -> pd.DataFrame:
    """成交量加权均价 VWAP（TA-Lib 没有，这里用 pandas 自实现，示范自定义指标）。

    VWAP = Σ(典型价格 × 成交量) / Σ(成交量)
    典型价格 = (high + low + close) / 3

    严格意义上的 VWAP 是「日内」指标（每个交易日从开盘累加到收盘），
    日线数据没有日内切分，这里改成「滚动 N 日」的成交量加权均价，
    思路一致：让成交量大、有「筹码」的价格对均值贡献更大，比简单均线更贴合
    真实持仓成本。停牌日成交量为 0，求均值时按 NaN 跳过，避免除以 0。
    结果列：vwap_{timeperiod}
    """
    df = df.copy()
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = typical * df["volume"]  # 资金流 = 价格 × 量

    def _apply(g):
        pv_g = pv.loc[g.index]
        vol_g = df["volume"].loc[g.index]
        # rolling 求和得到「滚动 N 日资金流 / 滚动 N 日成交量」，
        # 按 code 分组后每只股票独立滚动，不会串到别的股票
        num = pv_g.rolling(timeperiod, min_periods=1).sum()
        den = vol_g.rolling(timeperiod, min_periods=1).sum()
        return pd.Series(num / den.replace(0, np.nan), index=g.index)

    df[f"vwap_{timeperiod}"] = _group_apply(df, _apply)
    return df
