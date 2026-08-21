"""
ex02: MACD 金叉死叉策略（策略入门 · 择时策略）

对应《学习路线》3.1「择时策略」清单里的「MACD 金叉死叉」。

策略逻辑：
  - DIF（快慢均线差）上穿 DEA（信号线）→ 金叉，买入
  - DIF 下穿 DEA → 死叉，卖出
  - 默认参数 (12, 26, 9) 是行业惯例

MACD 的构成（详情见 utils/technical_indicators.macd 的注释）：
  DIF = EMA(12) - EMA(26)      快慢均线差，反映短期动能相对长期的位置
  DEA = DIF 的 9 日 EMA         信号线，是 DIF 的平滑
  MACD 柱 = 2 × (DIF - DEA)     柱体正负代表金叉/死叉之后的动能

对比上一节的双均线：
  - 双均线用「快线 vs 慢线」的位置做信号，本质是 EMA 的原始比较
  - MACD 先做差（DIF），再对差做平滑（DEA），等于在"差值"这个层面再做一次
    均线交叉，信号更平滑，震荡市里能过滤掉一部分频繁翻转的假信号

关键概念：本脚本演示「事件型信号」的写法——用 DIF 与 DEA 的上下穿（crossover）
产生离散的买/卖事件，而不是直接拿状态。两种写法对"持有"是等价的，但事件型
更适合写"仅在金叉当天开仓"这类一次性规则。

使用方法：python ex02_MACD金叉死叉.py
"""

# ------------------------------------------------------------------
# 0. 导入与后端设置
# ------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")

import sys
from pathlib import Path

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

# MACD 参数（行业惯例）
FAST, SLOW, SIGNAL = 12, 26, 9
CODE = "512890"


def crossover(a: pd.Series, b: pd.Series) -> pd.Series:
    """a 上穿 b：当日 a>b 且前一日 a<=b。"""
    return (a > b) & (a.shift(1) <= b.shift(1))


def macd_signal(df: pd.DataFrame) -> pd.DataFrame:
    """计算 MACD 并生成持有信号（DIF 在 DEA 上方 = 持有）。"""
    df = ta.macd(df, fast=FAST, slow=SLOW, signal=SIGNAL)
    df["signal"] = (df["dif"] > df["dea"]).astype(int)
    return df


def main():
    df = pd.read_csv(DATA_CSV)
    df["code"] = CODE          # 原始 CSV 无 code 列，补上供工具按 code 分组
    df = parse_daily(df)
    df = macd_signal(df)
    print(f"加载 {CODE} 共 {len(df)} 个交易日，MACD 参数 ({FAST}, {SLOW}, {SIGNAL})\n")

    # ---------------- 单只 ETF 完整回测 ----------------
    sub = df.reset_index(drop=True)

    golden = crossover(sub["dif"], sub["dea"])   # DIF 上穿 DEA = 金叉
    death = crossover(sub["dea"], sub["dif"])    # DIF 下穿 DEA = 死叉

    result = summarize(sub["close"], sub["signal"])
    print(f"=== {CODE} MACD 金叉死叉 回测结果 ===")
    print(f"  金叉 {golden.sum()} 次 / 死叉 {death.sum()} 次")
    for k, v in result["指标"].items():
        print(f"  {k}: {v:.4f}")
    print(f"  交易次数: {result['交易']['交易次数']}，"
          f"胜率: {result['交易']['胜率']:.2%}，"
          f"盈亏比: {result['交易']['盈亏比']:.2f}")

    # ---------------- 画图：价格 + MACD 三线 + 买卖点 ----------------
    bt = run_backtest(sub["close"], sub["signal"])

    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

    ax = axes[0]
    ax.plot(sub["date"], sub["close"], color="black", lw=0.8, label="收盘价")
    buy_idx = sub.index[golden]
    sell_idx = sub.index[death]
    ax.scatter(sub["date"][buy_idx], sub["close"][buy_idx],
               marker="^", s=70, color="red", zorder=5, label="金叉(买)")
    ax.scatter(sub["date"][sell_idx], sub["close"][sell_idx],
               marker="v", s=70, color="green", zorder=5, label="死叉(卖)")
    ax.set_title(f"{CODE} MACD 金叉死叉策略")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    colors = sub["macd_hist"].map(lambda v: "red" if v >= 0 else "green")
    ax.bar(sub["date"], sub["macd_hist"], color=colors, width=1.0, label="MACD 柱")
    ax.plot(sub["date"], sub["dif"], color="blue", lw=1.0, label="DIF")
    ax.plot(sub["date"], sub["dea"], color="orange", lw=1.0, label="DEA")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_title("MACD (DIF / DEA / 柱)")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    ax.plot(sub["date"], bt["equity"], color="red", lw=1.5, label="策略净值")
    bh = (1 + sub["close"].pct_change().fillna(0)).cumprod()
    ax.plot(sub["date"], bh, color="gray", lw=1.0, linestyle="--", label="买入持有")
    ax.axhline(1.0, color="black", lw=0.6, linestyle="--")
    ax.set_title("策略净值 vs 买入持有")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex02_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n结果图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
