"""
ex03: 波动类技术指标（数据能力 · 技术指标）

对应《学习路线》2.3「技术指标计算」中的「波动类」：
  - 布林带（Bollinger Bands）—— 中轨 + 上下轨（±2 倍标准差）
  - ATR —— 平均真实波幅

波动类指标回答的是：价格波动的「幅度」有多大？
波动率是风险的核心度量：波动大的股票，止损要放得宽，仓位要放得小。

本脚本做两件事：
  1. 对全部 20 只股票批量计算布林带和 ATR（复用 utils/technical_indicators.py）
  2. 挑一只股票画布林带填充图，并用 ATR 演示「止损距离」的估算

使用方法：python ex03_波动类指标.py
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

    # 批量计算波动类指标
    df = ta.boll(df, timeperiod=20, nbdev=2.0)
    df = ta.atr(df, timeperiod=14)

    sub = df[df["code"] == DEMO_CODE]
    cols = ["date", "close", "boll_up", "boll_mid", "boll_low", "atr_14"]
    print(f"=== {DEMO_CODE} 波动指标最近 5 个交易日 ===")
    show = sub[cols].tail(5).copy()
    show["date"] = show["date"].dt.strftime("%Y-%m-%d")
    print(show.round(4).to_string(index=False))

    print("""
指标解读：
  - boll_up/mid/low：中轨是 20 日均线，上下轨 = 中轨 ± 2 倍标准差
      价格触及上轨可能超买、触及下轨可能超卖；带宽收窄预示即将变盘
  - atr_14：14 日平均真实波幅，衡量「每天大概波动多少钱」，单位与价格相同
""")

    # 演示：用 ATR 估算止损距离
    last_close = sub["close"].iloc[-1]
    last_atr = sub["atr_14"].iloc[-1]
    print(f"=== ATR 止损距离演示（{DEMO_CODE} 最后一天） ===")
    print(f"  收盘价：{last_close:.4f}")
    print(f"  ATR(14)：{last_atr:.4f}")
    print(f"  若用 2 倍 ATR 做止损：止损价 = {last_close:.4f} - 2×{last_atr:.4f}"
          f" = {last_close - 2 * last_atr:.4f}")
    print("  → 波动越大 ATR 越大，止损放得越宽，避免被正常波动扫出场")

    # ------------------------------------------------------------------
    # 画图：布林带填充图
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(sub["date"], sub["close"], color="black", lw=0.9, label="close")
    ax.plot(sub["date"], sub["boll_mid"], color="orange", lw=1.0, label="中轨 MA20")
    ax.plot(sub["date"], sub["boll_up"], color="blue", lw=1.0, linestyle="--",
            label="上轨 +2σ")
    ax.plot(sub["date"], sub["boll_low"], color="blue", lw=1.0, linestyle="--",
            label="下轨 -2σ")
    # 上下轨之间填充，直观看出「带宽」随波动率变化
    ax.fill_between(sub["date"], sub["boll_up"], sub["boll_low"],
                    alpha=0.1, color="blue")
    ax.set_title(f"{DEMO_CODE} 布林带（20 日，±2 倍标准差）")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex03_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n布林带图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
