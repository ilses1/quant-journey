"""
ex04: 量价类技术指标（数据能力 · 技术指标）

对应《学习路线》2.3「技术指标计算」中的「量价类」：
  - OBV —— 能量潮
  - MFI —— 资金流量指标
  - VWAP —— 成交量加权均价（TA-Lib 没有，用 pandas 自实现）

量价类指标的核心思想：价格是「果」，成交量是「因」——放量上涨比缩量上涨更可靠。
「量在价先」，量价是否配合是判断趋势真假的关键。

本脚本做两件事：
  1. 对全部 20 只股票批量计算 OBV / MFI / VWAP（复用 utils/technical_indicators.py）
  2. 挑一只股票画图，并演示「量价背离」的判断

使用方法：python ex04_量价类指标.py
"""

import matplotlib
matplotlib.use("Agg")

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# matplotlib 默认字体不含中文，画图标题里的中文会变成方框并刷出一堆
# 缺字警告。这里指定 Windows 自带中文字体，并关闭负号转义
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data_clean import parse_daily            # noqa: E402
from utils import technical_indicators as ta        # noqa: E402

CLEAN_CSV = PROJECT_ROOT / "data" / "stock_daily" / "hs300_daily_clean.csv"
DEMO_CODE = "600000"


def main():
    df = pd.read_csv(CLEAN_CSV)
    df = parse_daily(df)
    print(f"加载清洗数据：{len(df)} 行 × {df['code'].nunique()} 只股票\n")

    # 批量计算量价类指标
    df = ta.obv(df)
    df = ta.mfi(df, timeperiod=14)
    df = ta.vwap(df, timeperiod=20)

    sub = df[df["code"] == DEMO_CODE]
    cols = ["date", "close", "volume", "obv", "mfi_14", "vwap_20"]
    print(f"=== {DEMO_CODE} 量价指标最近 5 个交易日 ===")
    show = sub[cols].tail(5).copy()
    show["date"] = show["date"].dt.strftime("%Y-%m-%d")
    print(show.round(4).to_string(index=False))

    print("""
指标解读：
  - obv：累积能量潮，涨日加成交量、跌日减成交量（绝对值无意义，看趋势）
  - mfi_14：资金流量指标（成交额加权的 RSI），0~100，>80 超买 / <20 超卖
  - vwap_20：20 日成交量加权均价，比简单均线更贴近真实持仓成本
""")

    # 演示：量价背离判断
    # 价格创近 N 日新高的同时，OBV 是否也创新高？没有 → 背离，动能衰竭
    print(f"=== 量价背离演示（{DEMO_CODE}） ===")
    print(f"  最新收盘价 vs 近 60 日最高："
          f"{sub['close'].iloc[-1]:.4f} / {sub['close'].tail(60).max():.4f}")
    print(f"  最新 OBV vs 近 60 日最高："
          f"{sub['obv'].iloc[-1]:.0f} / {sub['obv'].tail(60).max():.0f}")
    print("  → 若价格创新高而 OBV 未创新高，说明上涨缺乏成交量配合，警惕回落")

    # ------------------------------------------------------------------
    # 画图：OBV 和 MFI 两张子图
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    # --- OBV ---
    ax = axes[0]
    ax.plot(sub["date"], sub["obv"], color="purple", lw=1.2, label="OBV")
    ax.set_title(f"{DEMO_CODE} OBV（能量潮）")
    ax.set_ylabel("OBV")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- MFI ---
    ax = axes[1]
    ax.plot(sub["date"], sub["mfi_14"], color="blue", lw=1.2, label="MFI 14")
    ax.axhline(80, color="red", linestyle="--", lw=0.8, label="超买线 80")
    ax.axhline(20, color="green", linestyle="--", lw=0.8, label="超卖线 20")
    ax.set_ylim(0, 100)
    ax.set_title("MFI（资金流量指标）")
    ax.set_ylabel("MFI")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex04_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n量价指标图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
