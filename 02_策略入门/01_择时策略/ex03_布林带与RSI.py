"""
ex03: 布林带 + RSI 均值回归策略（策略入门 · 择时策略）

对应《学习路线》3.1「择时策略」清单里的两个"振荡/均值回归"类策略：
  - 布林带：价格跌破下轨买入（超卖），突破上轨卖出（超买），参数 (20, 2)
  - RSI：RSI < 30 买入（超卖），RSI > 70 卖出（超买），参数 (14, 30, 70)

它们和 ex01/ex02 的"趋势跟随"思路相反：
  - 趋势策略追涨杀跌：价格创新高才买，赌趋势延续
  - 均值回归低买高卖：价格跌过头才买，赌价格回到均值
  两类策略在"趋势市"和"震荡市"里表现互补，这也是为什么实战中常做策略组合。

关键概念：带"滞回"的状态机信号（hysteresis）。
  布林带和 RSI 的规则是"触发一次就切换一次状态"：
    - 触发买入条件 → 持仓（状态 = 1）
    - 触发卖出条件 → 空仓（状态 = 0）
    - 都没触发 → 保持上一次状态不变
  这种"保持上次状态"的逻辑无法用纯向量化的 where 一次写出来（因为第 t 天
  的状态依赖第 t-1 天的状态），这里用一个显式 for 循环实现，反而更直观。

使用方法：python ex03_布林带与RSI.py
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

# 参数
BOLL_N, BOLL_DEV = 20, 2        # 布林带 (20, 2)
RSI_N = 14                       # RSI 周期
RSI_LOW, RSI_HIGH = 30, 70       # RSI 超卖/超买阈值
CODE = "512890"


# ------------------------------------------------------------------
# 1. 信号生成
# ------------------------------------------------------------------
def hysteresis(entry: pd.Series, exit_: pd.Series) -> pd.Series:
    """带滞回的状态机：entry 为真时置 1（买入），exit_ 为真时置 0（卖出），
    两者都不为真时保持上一次状态。

    entry/exit_ 都是与时间对齐的布尔 Series。返回值是 0/1 状态 Series，
    代表「第 t 天收盘后」应持有的目标仓位（还没 shift，回测时次日成交）。

    为什么不能向量化：第 t 天的状态依赖第 t-1 天的状态（有反馈），
    pandas 的 where/select 都是一次性算整列、看不到前一行，所以用循环。
    数据量小（几百行）时循环的开销可忽略，可读性优先。
    """
    state = 0
    out = np.zeros(len(entry), dtype=int)
    for i in range(len(entry)):
        if entry.iloc[i]:
            state = 1
        elif exit_.iloc[i]:
            state = 0
        out[i] = state
    return pd.Series(out, index=entry.index)


def boll_signal(df: pd.DataFrame) -> pd.DataFrame:
    """布林带均值回归：跌破下轨买入，突破上轨卖出，其余保持。"""
    df = ta.boll(df, timeperiod=BOLL_N, nbdev=BOLL_DEV)
    buy = df["close"] < df["boll_low"]     # 跌破下轨 = 超卖
    sell = df["close"] > df["boll_up"]     # 突破上轨 = 超买
    df["signal"] = hysteresis(buy, sell)
    return df


def rsi_signal(df: pd.DataFrame) -> pd.DataFrame:
    """RSI 超买超卖：RSI < 30 买入，RSI > 70 卖出，其余保持。"""
    df = ta.rsi(df, timeperiod=RSI_N)
    buy = df[f"rsi_{RSI_N}"] < RSI_LOW
    sell = df[f"rsi_{RSI_N}"] > RSI_HIGH
    df["signal"] = hysteresis(buy, sell)
    return df


# ------------------------------------------------------------------
# 2. 主流程
# ------------------------------------------------------------------
def main():
    df = pd.read_csv(DATA_CSV)
    df["code"] = CODE          # 原始 CSV 无 code 列，补上供工具按 code 分组
    df = parse_daily(df)
    df = boll_signal(df)
    df = df.rename(columns={"signal": "signal_boll"})   # 布林带信号列改名，避免冲突
    df = rsi_signal(df)
    df = df.rename(columns={"signal": "signal_rsi"})    # RSI 信号列同样改名

    print(f"加载 {CODE} 共 {len(df)} 个交易日\n")

    # ---------------- 单只 ETF 对比两个策略 ----------------
    sub = df.reset_index(drop=True)
    r_boll = summarize(sub["close"], sub["signal_boll"])
    r_rsi = summarize(sub["close"], sub["signal_rsi"])

    print(f"=== {CODE} 布林带 vs RSI 回测对比 ===")
    print(f"{'指标':<12}{'布林带':>12}{'RSI':>12}")
    for k in ["年化收益率", "夏普比率", "最大回撤", "卡玛比率"]:
        print(f"{k:<12}{r_boll['指标'][k]:>12.4f}{r_rsi['指标'][k]:>12.4f}")
    print(f"{'交易次数':<12}{r_boll['交易']['交易次数']:>12}{r_rsi['交易']['交易次数']:>12}")
    print(f"{'胜率':<12}{r_boll['交易']['胜率']:>11.2%}{r_rsi['交易']['胜率']:>11.2%}")

    # ---------------- 画图 ----------------
    bt_boll = run_backtest(sub["close"], sub["signal_boll"])
    bt_rsi = run_backtest(sub["close"], sub["signal_rsi"])
    bh = (1 + sub["close"].pct_change().fillna(0)).cumprod()

    fig, axes = plt.subplots(2, 1, figsize=(13, 9))

    # 子图 1：布林带 —— 价格 + 三轨
    ax = axes[0]
    ax.plot(sub["date"], sub["close"], color="black", lw=0.8, label="收盘价")
    ax.plot(sub["date"], sub["boll_up"], color="red", lw=0.8, linestyle="--", label="上轨")
    ax.plot(sub["date"], sub["boll_mid"], color="orange", lw=0.8, label="中轨")
    ax.plot(sub["date"], sub["boll_low"], color="green", lw=0.8, linestyle="--", label="下轨")
    ax.set_title(f"{CODE} 布林带均值回归 (N={BOLL_N}, {BOLL_DEV}σ)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # 子图 2：两个策略 + 买入持有 的净值对比
    ax = axes[1]
    ax.plot(sub["date"], bt_boll["equity"], color="red", lw=1.4, label="布林带")
    ax.plot(sub["date"], bt_rsi["equity"], color="blue", lw=1.4, label="RSI")
    ax.plot(sub["date"], bh, color="gray", lw=1.0, linestyle="--", label="买入持有")
    ax.axhline(1.0, color="black", lw=0.6, linestyle="--")
    ax.set_title("净值对比：布林带 / RSI / 买入持有")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex03_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n结果图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
