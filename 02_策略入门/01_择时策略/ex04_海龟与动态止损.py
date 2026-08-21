"""
ex04: 海龟交易法则（唐奇安通道突破 + ATR 动态止损）（策略入门 · 择时策略）

对应《学习路线》3.1「择时策略」清单里的两个 ⭐⭐ 策略：
  - 海龟交易法则：唐奇安通道突破（20 日/55 日）入场 + ATR 动态止损
  - 动态止盈止损：基于波动率(ATR)的移动止损

海龟交易是趋势跟随的经典代表，核心思想是"截断亏损、让利润奔跑"：
  - 入场：价格突破过去 N 日的最高价（唐奇安通道上轨），赌趋势启动
  - 出场：价格跌破过去 M 日的最低价（通道下轨），趋势结束离场
  - 动态止损：持仓期间，只要价格从「入场以来的最高点」回撤超过 k 倍 ATR
    就无条件离场——ATR 越大波动越大，止损放得越宽，让止损距离自动适应当前波动

本脚本对比两种出场方式（入场都用 20 日突破）：
  A. 通道出场：跌破 10 日低点离场（经典海龟 System 1）
  B. ATR 移动止损出场：从持仓峰值回撤 3×ATR 离场（动态止盈止损）

关键概念：
  - 唐奇安通道用 shift(1) 取「过去 N 日（不含今天）」的最高价，
    避免"今天的价格突破今天就成交"的前视；再叠加回测引擎的次日成交，
    形成"今天突破 → 明天买入"的正确时序。
  - ATR 移动止损需要一个状态机（见 ex03 的 hysteresis 思路），
    因为"持仓峰值"会随行情不断更新，必须逐日维护。

使用方法：python ex04_海龟与动态止损.py
"""

# ------------------------------------------------------------------
# 0. 导入与后端设置
# ------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data_clean import parse_daily            # noqa: E402
from utils import technical_indicators as ta        # noqa: E402
from utils.backtest import run_backtest, summarize  # noqa: E402

# 日线行情数据（单只 ETF）
DATA_CSV = PROJECT_ROOT / "data" / "stock_daily" / "sh512890_daily.csv"

# 参数：20 日突破入场，10 日低点出场；ATR 周期 20，止损倍数 3
ENTRY_N, EXIT_N = 20, 10
ATR_N, ATR_MULT = 20, 3.0
CODE = "512890"


# ------------------------------------------------------------------
# 1. 信号生成
# ------------------------------------------------------------------
def donchian_signal(sub: pd.DataFrame) -> pd.Series:
    """海龟 System 1：20 日突破入场，10 日低点出场（状态机）。"""
    # 过去 ENTRY_N 日（不含今天）的最高价 / 过去 EXIT_N 日（不含今天）的最低价
    entry = sub["close"] > sub["high"].rolling(ENTRY_N).max().shift(1)
    exit_ = sub["close"] < sub["low"].rolling(EXIT_N).min().shift(1)

    state = 0
    out = np.zeros(len(sub), dtype=int)
    for i in range(len(sub)):
        if entry.iloc[i]:
            state = 1
        elif exit_.iloc[i]:
            state = 0
        out[i] = state
    return pd.Series(out, index=sub.index)


def atr_trailing_signal(sub: pd.DataFrame) -> pd.Series:
    """突破入场 + ATR 移动止损出场：持仓峰值回撤 3×ATR 即离场。"""
    entry = sub["close"] > sub["high"].rolling(ENTRY_N).max().shift(1)
    atr = sub[f"atr_{ATR_N}"].to_numpy(dtype=float)
    close = sub["close"].to_numpy(dtype=float)

    state = 0
    peak = 0.0                       # 本次持仓以来的最高收盘价
    out = np.zeros(len(sub), dtype=int)
    for i in range(len(sub)):
        if state == 0:
            if entry.iloc[i]:
                state = 1
                peak = close[i]
        else:
            peak = max(peak, close[i])                     # 更新峰值
            if close[i] < peak - ATR_MULT * atr[i]:        # 回撤超过 k×ATR
                state = 0
        out[i] = state
    return pd.Series(out, index=sub.index)


# ------------------------------------------------------------------
# 2. 主流程
# ------------------------------------------------------------------
def main():
    df = pd.read_csv(DATA_CSV)
    df["code"] = CODE          # 原始 CSV 无 code 列，补上供工具按 code 分组
    df = parse_daily(df)
    df = ta.atr(df, timeperiod=ATR_N)      # 先算 ATR（两种出场都用得上）
    print(f"加载 {CODE} 共 {len(df)} 个交易日，入场 {ENTRY_N} 日突破，"
          f"ATR 止损 {ATR_MULT}×ATR({ATR_N})\n")

    # ---------------- 单只 ETF 两种出场方式对比 ----------------
    sub = df.reset_index(drop=True)
    sig_donchian = donchian_signal(sub)
    sig_atr = atr_trailing_signal(sub)

    r_don = summarize(sub["close"], sig_donchian)
    r_atr = summarize(sub["close"], sig_atr)

    print(f"=== {CODE} 海龟交易：通道出场 vs ATR 移动止损 ===")
    print(f"{'指标':<12}{'通道出场':>12}{'ATR止损':>12}")
    for k in ["年化收益率", "夏普比率", "最大回撤", "卡玛比率"]:
        print(f"{k:<12}{r_don['指标'][k]:>12.4f}{r_atr['指标'][k]:>12.4f}")
    print(f"{'交易次数':<12}{r_don['交易']['交易次数']:>12}{r_atr['交易']['交易次数']:>12}")
    print(f"{'胜率':<12}{r_don['交易']['胜率']:>11.2%}{r_atr['交易']['胜率']:>11.2%}")

    # ---------------- 画图 ----------------
    bt_don = run_backtest(sub["close"], sig_donchian)
    bt_atr = run_backtest(sub["close"], sig_atr)
    bh = (1 + sub["close"].pct_change().fillna(0)).cumprod()

    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

    ax = axes[0]
    ax.plot(sub["date"], sub["close"], color="black", lw=0.8, label="收盘价")
    # 画唐奇安通道（20 日高 / 10 日低，用不含当天的值）
    up = sub["high"].rolling(ENTRY_N).max().shift(1)
    lo = sub["low"].rolling(EXIT_N).min().shift(1)
    ax.plot(sub["date"], up, color="red", lw=0.8, linestyle="--", label=f"{ENTRY_N}日高点")
    ax.plot(sub["date"], lo, color="green", lw=0.8, linestyle="--", label=f"{EXIT_N}日低点")
    ax.set_title(f"{CODE} 海龟交易：唐奇安通道突破")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(sub["date"], bt_don["equity"], color="red", lw=1.4, label="通道出场")
    ax.plot(sub["date"], bt_atr["equity"], color="blue", lw=1.4, label="ATR 移动止损")
    ax.plot(sub["date"], bh, color="gray", lw=1.0, linestyle="--", label="买入持有")
    ax.axhline(1.0, color="black", lw=0.6, linestyle="--")
    ax.set_title("净值对比：通道出场 / ATR 移动止损 / 买入持有")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex04_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n结果图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
