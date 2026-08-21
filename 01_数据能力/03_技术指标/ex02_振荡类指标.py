"""
ex02: 振荡类技术指标（数据能力 · 技术指标）

对应《学习路线》2.3「技术指标计算」中的「振荡类」：
  - RSI —— 相对强弱指标
  - KDJ —— 随机指标
  - WR —— 威廉指标
  - CCI —— 顺势指标

振荡类指标回答的是：当前价格是「超买」（涨太多要回调）还是「超卖」（跌太多要反弹）？
它们通常在一个固定区间内上下摆动，所以叫「振荡」（oscillator）。

本脚本做两件事：
  1. 对全部 20 只股票批量计算四类振荡指标（复用 utils/technical_indicators.py）
  2. 挑一只股票画图，并演示「超买超卖计数」这类最直接的用法

使用方法：python ex02_振荡类指标.py
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

    # 批量计算四类振荡指标
    df = ta.rsi(df, timeperiod=14)
    df = ta.kdj(df)
    df = ta.wr(df, timeperiod=14)
    df = ta.cci(df, timeperiod=14)

    sub = df[df["code"] == DEMO_CODE]
    cols = ["date", "close", "rsi_14", "kdj_k", "kdj_d", "kdj_j",
            "wr_14", "cci_14"]
    print(f"=== {DEMO_CODE} 振荡指标最近 5 个交易日 ===")
    show = sub[cols].tail(5).copy()
    show["date"] = show["date"].dt.strftime("%Y-%m-%d")
    print(show.round(4).to_string(index=False))

    print("""
指标解读（注意各指标的取值范围不同）：
  - rsi_14：0~100，>70 超买 / <30 超卖
  - kdj_k/d/j：0~100，K 上穿 D 金叉、下穿死叉；>80 超买 / <20 超卖
  - wr_14：-100~0，>-20 超买 / <-80 超卖（方向与 RSI 相反）
  - cci_14：无固定上下界，>100 超买 / <-100 超卖
""")

    # 演示：超买超卖信号计数（对 DEMO_CODE 这只票）
    print("=== 超买超卖信号计数（DEMO_CODE） ===")
    print(f"  RSI > 70 超买天数：{(sub['rsi_14'] > 70).sum()}")
    print(f"  RSI < 30 超卖天数：{(sub['rsi_14'] < 30).sum()}")
    print(f"  KDJ J > 100 钝化天数：{(sub['kdj_j'] > 100).sum()}")
    print(f"  WR < -80 超卖天数：{(sub['wr_14'] < -80).sum()}")
    print(f"  CCI > 100 超买天数：{(sub['cci_14'] > 100).sum()}")
    print("\n  提示：振荡指标在震荡市好用，单边趋势市里会长期停留在超买/超卖区\n"
          "  （俗称「钝化」），所以通常要结合趋势类指标一起用。")

    # ------------------------------------------------------------------
    # 画图：RSI 和 KDJ 两张子图
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    # --- RSI ---
    ax = axes[0]
    ax.plot(sub["date"], sub["rsi_14"], color="blue", lw=1.2, label="RSI 14")
    ax.axhline(70, color="red", linestyle="--", lw=0.8, label="超买线 70")
    ax.axhline(30, color="green", linestyle="--", lw=0.8, label="超卖线 30")
    ax.set_ylim(0, 100)
    ax.set_title(f"{DEMO_CODE} RSI（相对强弱指标）")
    ax.set_ylabel("RSI")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- KDJ ---
    ax = axes[1]
    ax.plot(sub["date"], sub["kdj_k"], color="blue", lw=1.0, label="K")
    ax.plot(sub["date"], sub["kdj_d"], color="orange", lw=1.0, label="D")
    ax.plot(sub["date"], sub["kdj_j"], color="purple", lw=0.8, alpha=0.7, label="J")
    ax.axhline(80, color="red", linestyle="--", lw=0.8, label="超买线 80")
    ax.axhline(20, color="green", linestyle="--", lw=0.8, label="超卖线 20")
    ax.set_title("KDJ（随机指标）")
    ax.set_ylabel("KDJ")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex02_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n振荡指标图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
