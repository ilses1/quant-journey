"""
ex01: 双均线交叉策略（策略入门 · 择时策略）

对应《学习路线》3.1「择时策略」中的首个、也是最经典的策略——双均线交叉。

策略逻辑（摘自《学习路线》3.1 示例）：
  - 当 5 日均线 ＞ 20 日均线 → 视为多头，持有（买入）
  - 当 5 日均线 ＜ 20 日均线 → 视为空头，空仓（卖出）
  - 快线上穿慢线 = 金叉（买入信号）；快线下穿慢线 = 死叉（卖出信号）

本脚本对单只 ETF（512890，红利低波）走完整流程：
  1. 算均线 → 生成信号 → 检测金叉/死叉事件 → 向量化回测 → 打印绩效指标
  2. 用一个小表直观展示「信号 → 次日持仓」的时序关系，看懂 shift 的作用
  3. 把策略净值与「买入持有」对照画图，直观看出择时策略是否带来超额

关键概念（务必理解）：
  - 信号与成交的先后：第 t 天收盘后算出信号，最早第 t+1 天才能成交，
    所以回测里持仓 = 信号.shift(1)。这就是"避免未来函数"的核心写法。
  - 均线交叉是"状态"策略：持有条件是「快线在慢线上方」这个状态，
    金叉/死叉只是状态翻转的那一天，两者等价，但状态写法更简洁不易出错。

使用方法：python ex01_双均线交叉.py
"""

# ------------------------------------------------------------------
# 0. 导入与后端设置
# ------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")  # 非交互后端：只画图存文件，不弹窗口

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# 中文字体（避免图里中文变方框） + 负号正常显示
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 本脚本在 02_策略入门/01_择时策略/ 下，向上三级才是项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data_clean import parse_daily            # noqa: E402
from utils import technical_indicators as ta        # noqa: E402
from utils.backtest import run_backtest, summarize  # noqa: E402

# 日线行情数据（单只 ETF）
DATA_CSV = PROJECT_ROOT / "data" / "stock_daily" / "sh512890_daily.csv"

# 双均线参数（《学习路线》3.1 给的典型值：(5, 20) 或 (10, 60)）
FAST, SLOW = 5, 20

# 目标标的代码（512890 红利低波 ETF）
CODE = "512890"


# ------------------------------------------------------------------
# 1. 信号生成：双均线
# ------------------------------------------------------------------
def dual_ma_signal(df: pd.DataFrame, fast: int = FAST, slow: int = SLOW) -> pd.DataFrame:
    """给数据加两列均线和一列信号。

    df: 含 date/close 的日线数据（单只标的）
    返回 df 的副本，新增列：
      ma_fast / ma_slow  快、慢均线
      signal             目标仓位（快线>慢线 = 1，否则 = 0）

    注意：signal 是「第 t 天收盘后」得到的状态，还没做 shift，
    回测时由 run_backtest 内部执行 signal.shift(1) 完成次日成交。
    """
    df = ta.sma(df, timeperiod=fast)     # 快线（5 日均线）
    df = ta.sma(df, timeperiod=slow)     # 慢线（20 日均线）
    df["ma_fast"] = df[f"sma_{fast}"]
    df["ma_slow"] = df[f"sma_{slow}"]
    df["signal"] = (df["ma_fast"] > df["ma_slow"]).astype(int)
    return df


def crossover(a: pd.Series, b: pd.Series) -> pd.Series:
    """a 上穿 b（金叉）事件：当日 a>b 且前一日 a<=b。返回布尔 Series。

    用途：把「状态」转成「事件」，方便在图上标记买卖点、以及解释信号。
    死叉同理，只需交换 a、b 的位置。
    """
    return (a > b) & (a.shift(1) <= b.shift(1))


# ------------------------------------------------------------------
# 2. 主流程
# ------------------------------------------------------------------
def main():
    df = pd.read_csv(DATA_CSV)
    df["code"] = CODE          # 原始 CSV 无 code 列，补上供工具按 code 分组
    df = parse_daily(df)
    df = dual_ma_signal(df)
    print(f"加载 {CODE} 共 {len(df)} 个交易日")
    print(f"参数：快线 MA{FAST}，慢线 MA{SLOW}\n")

    # ---------------- 步骤 1：完整走一遍 ----------------
    sub = df.reset_index(drop=True)

    # 金叉 / 死叉事件（用于图上标记 + 打印）
    golden = crossover(sub["ma_fast"], sub["ma_slow"])   # 快线上穿慢线
    death = crossover(sub["ma_slow"], sub["ma_fast"])    # 慢线上穿快线（=快线下穿慢线）

    # 回测（信号会 shift(1) 次日成交）
    bt = run_backtest(sub["close"], sub["signal"])
    result = summarize(sub["close"], sub["signal"])

    print(f"=== {CODE} 双均线(MA{FAST}/{SLOW}) 回测结果 ===")
    print(f"  信号天数：金叉 {golden.sum()} 次，死叉 {death.sum()} 次")
    for k, v in result["指标"].items():
        print(f"  {k}: {v:.4f}")
    print(f"  交易次数: {result['交易']['交易次数']}，"
          f"胜率: {result['交易']['胜率']:.2%}，"
          f"盈亏比: {result['交易']['盈亏比']:.2f}")

    # 用一个小表直观展示「信号 → 次日持仓」的时序关系，看懂 shift 的作用
    show = sub[["date", "close", "ma_fast", "ma_slow", "signal"]].copy()
    show = show.merge(
        bt["position"].rename("position"), left_index=True, right_index=True
    )
    # 只打印出现过信号翻转的日期（signal 与 position 相差一天，最容易看懂）
    flip = show["signal"] != show["signal"].shift(1)
    print("\n信号翻转的交易日（signal=当日收盘后决策，position=次日实际持仓）：")
    print(show[flip][["date", "close", "signal", "position"]]
          .tail(12).to_string(index=False))

    # ---------------- 步骤 2：策略 vs 买入持有 ----------------
    # 买入持有：一直满仓，收益就是资产本身涨跌幅，直接用净值曲线对照
    buyhold_equity = (1 + bt["asset_return"]).cumprod()
    strat_equity = bt["equity"]

    print("\n=== 策略 vs 买入持有（单只 ETF） ===")
    print(f"  双均线策略 累计收益: {strat_equity.iloc[-1] - 1: .4f}")
    print(f"  买入持有   累计收益: {buyhold_equity.iloc[-1] - 1: .4f}")

    # ---------------- 画图 ----------------
    fig, axes = plt.subplots(2, 1, figsize=(13, 9))

    # 子图 1：价格 + 均线 + 买卖点
    ax = axes[0]
    ax.plot(sub["date"], sub["close"], color="black", lw=0.8, label="收盘价")
    ax.plot(sub["date"], sub["ma_fast"], color="red", lw=1.0, label=f"MA{FAST} 快线")
    ax.plot(sub["date"], sub["ma_slow"], color="blue", lw=1.0, label=f"MA{SLOW} 慢线")
    buy_idx = sub.index[golden]
    sell_idx = sub.index[death]
    ax.scatter(sub["date"][buy_idx], sub["close"][buy_idx],
               marker="^", s=70, color="red", zorder=5, label="金叉(买)")
    ax.scatter(sub["date"][sell_idx], sub["close"][sell_idx],
               marker="v", s=70, color="green", zorder=5, label="死叉(卖)")
    ax.set_title(f"{CODE} 双均线交叉策略 (MA{FAST} / MA{SLOW})")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # 子图 2：策略净值 vs 买入持有
    ax = axes[1]
    ax.plot(strat_equity.index, strat_equity, color="red", lw=1.5, label="双均线策略")
    ax.plot(buyhold_equity.index, buyhold_equity, color="gray", lw=1.2,
            linestyle="--", label="买入持有")
    ax.axhline(1.0, color="black", lw=0.6, linestyle="--")
    ax.set_title("净值曲线：双均线策略 vs 买入持有")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex01_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n结果图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
