"""
utils/backtest.py —— 向量化回测引擎 + 绩效指标（跨阶段复用的公共工具）

对应《学习路线》3.3「策略评价体系」和 4.1「回测框架」的「自建最小回测」。
择时策略的特点是：单一资产、满仓/空仓，只有 0/1 两个状态，不需要事件驱动
引擎的复杂度，用「向量化」就能快速回测——把一整列信号一次算完，而不是
逐日循环下单。本模块把「信号 → 持仓 → 收益 → 指标」这条流水线封装成函数，
供 02_策略入门/01_择时策略 及 05_实战项目 复用。

核心约定（务必理解，这是避免前视偏差的命门）：
  1. 信号 signal 是「第 t 天收盘后」决定的目标仓位（1=持有 / 0=空仓），
     最早只能在「第 t+1 天」成交（A 股 T+1），所以持仓 = signal.shift(1)。
     如果信号用了当天的收盘价，又按当天收盘价成交，就是典型的未来函数。
  2. 收益用「日收盘价涨跌幅」pct_change，且第 t 天的持仓只吃第 t 天的收益。
  3. 交易成本（佣金 + 印花税 + 滑点）在仓位变动当天按「单边成本率」扣除，
     否则换手越高的策略越被高估。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# A 股一年约 252 个交易日，年化指标统一用这个数折算
PERIODS_PER_YEAR = 252

# 默认单边交易成本率：佣金约万 2.5 + 印花税（卖出 0.05%）+ 过户费 + 滑点。
# 买入和卖出各收一次，一次"完整交易（买+卖）"约 0.12% ~ 0.2%，
# 这里取 0.12% 作为保守默认值，可按需调整。
DEFAULT_COST_RATE = 0.0012


# ------------------------------------------------------------------
# 回测主流程
# ------------------------------------------------------------------
def run_backtest(close, signal, cost_rate: float = DEFAULT_COST_RATE) -> pd.DataFrame:
    """向量化回测：对单一资产跑「满仓/空仓」择时策略。

    参数
    ----
    close      : 单一资产的日收盘价 Series（按时间升序，索引与 signal 对齐）
    signal     : 与 close 等长的目标持仓信号（1=持有 / 0=空仓），
                 表示「第 t 天收盘后」决定的次日目标仓位
    cost_rate  : 单边交易成本率（仓位每变动一次扣一次），默认 0.0012

    返回
    ----
    DataFrame，索引为交易日，列：
      signal          当日收盘后决定的目标仓位
      position        当日实际持仓（= 上一日 signal，次日执行）
      asset_return    资产当日收益率（收盘价涨跌幅）
      strategy_return 策略当日净收益（已扣交易成本）
      equity          策略净值曲线（从 1 开始）
    """
    close = pd.Series(close, dtype=float)
    signal = pd.Series(signal, index=close.index).fillna(0).astype(int)

    # 资产的日收益率（收盘价 → 收盘价），首日无前收盘记为 0
    asset_return = close.pct_change().fillna(0.0)

    # 关键：信号滞后一天才变成持仓，规避「用今天收盘价在今天成交」的前视偏差
    position = signal.shift(1).fillna(0).astype(int)

    # 仓位变动量 = 当天换手（0→1 或 1→0 记为 1 次，成本各收一次）
    turnover = position.diff().abs().fillna(0)

    gross = position * asset_return          # 未扣成本的收益
    cost = turnover * cost_rate              # 交易成本只发生在调仓当天
    net = gross - cost
    equity = (1 + net).cumprod()

    return pd.DataFrame(
        {
            "signal": signal,
            "position": position,
            "asset_return": asset_return,
            "strategy_return": net,
            "equity": equity,
        },
        index=close.index,
    )


# ------------------------------------------------------------------
# 绩效指标
# ------------------------------------------------------------------
def performance(equity, periods_per_year: int = PERIODS_PER_YEAR,
                rf: float = 0.0) -> dict:
    """从净值曲线计算绩效指标（对应《学习路线》3.3 表格）。

    返回 dict，键为中文指标名：
      累计收益率、年化收益率、年化波动率、夏普比率、最大回撤、卡玛比率
    """
    equity = pd.Series(equity, dtype=float)
    n = len(equity)
    if n == 0 or equity.iloc[0] == 0:
        return {}

    total_return = equity.iloc[-1] / equity.iloc[0] - 1

    # 年化收益率：按复利折算，而不是简单地 (total/n)*252（简单法会高估波动大的曲线）
    ann_return = (1 + total_return) ** (periods_per_year / n) - 1

    # 年化波动率：日收益率标准差 × √252
    ret = equity.pct_change().fillna(0.0)
    ann_vol = float(ret.std(ddof=1) * np.sqrt(periods_per_year))

    sharpe = (ann_return - rf) / ann_vol if ann_vol > 0 else 0.0

    # 最大回撤：净值从历史高点到后续低点的最大跌幅
    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_dd = float(drawdown.min())

    calmar = ann_return / abs(max_dd) if max_dd < 0 else float("nan")

    return {
        "累计收益率": float(total_return),
        "年化收益率": float(ann_return),
        "年化波动率": ann_vol,
        "夏普比率": float(sharpe),
        "最大回撤": max_dd,
        "卡玛比率": float(calmar),
    }


def trade_stats(asset_return, position) -> dict:
    """把持仓序列切分成若干次「完整交易」，计算胜率与盈亏比（对应《学习路线》3.3）。

    一次「完整交易」= 一段连续的持仓期（从 0→1 开仓，到 1→0 平仓）。
    每段持仓期内，第 t 天持仓吃第 t 天的收益，累计收益 = Π(1+r) - 1。
    这里用「未扣成本」的收益算胜率/盈亏比，成本会另行从净值里扣掉。

    返回 dict：
      交易次数、胜率、盈亏比、平均单笔收益
    """
    asset_return = pd.Series(asset_return).fillna(0.0)
    position = pd.Series(position).astype(int)

    # 给每段连续持仓编号：仓位变化时 run_id 递增，同一段持仓 run_id 相同
    run_id = (position != position.shift(1).fillna(0)).cumsum()

    held = asset_return[position == 1]      # 只有持仓日的收益
    runs = run_id[position == 1]            # 每个持仓日属于哪一段持仓

    if len(held) == 0:
        return {"交易次数": 0, "胜率": float("nan"), "盈亏比": float("nan"),
                "平均单笔收益": float("nan")}

    trade_returns = (1 + held).groupby(runs).prod() - 1  # 每段持仓的累计收益
    n = len(trade_returns)
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns <= 0]

    win_rate = len(wins) / n
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(-losses.mean()) if len(losses) else 0.0
    pl_ratio = avg_win / avg_loss if avg_loss > 0 else float("nan")

    return {
        "交易次数": int(n),
        "胜率": float(win_rate),
        "盈亏比": float(pl_ratio),
        "平均单笔收益": float(trade_returns.mean()),
    }


# ------------------------------------------------------------------
# 一键汇总
# ------------------------------------------------------------------
def summarize(close, signal, cost_rate: float = DEFAULT_COST_RATE) -> dict:
    """跑一次回测并汇总所有指标，返回一个 dict（含净值曲线）。

    用法：
      result = summarize(close, signal)
      result["equity"]  # 净值曲线 Series
      result["指标"]     # performance() 的 dict
      result["交易"]     # trade_stats() 的 dict
    """
    bt = run_backtest(close, signal, cost_rate)
    return {
        "回测": bt,
        "指标": performance(bt["equity"]),
        "交易": trade_stats(bt["asset_return"], bt["position"]),
    }
