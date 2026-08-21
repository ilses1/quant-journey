"""
ex01: 趋势类技术指标（数据能力 · 技术指标）

对应《学习路线》2.3「技术指标计算」中的「趋势类」：
  - MA（SMA / EMA / WMA）—— 三种移动平均线的对比
  - MACD —— 快慢均线差 + 信号线 + 柱体
  - ADX —— 趋势强度（不判断方向）

趋势类指标回答的是：当前市场处于上升趋势、下降趋势还是震荡？

本脚本做两件事：
  1. 用上一阶段清洗好的 data/stock_daily/hs300_daily_clean.csv，
     对全部 20 只股票 groupby 分组后批量计算三类趋势指标（复用
     utils/technical_indicators.py）
  2. 挑一只股票（600000 浦发银行）画三张子图，直观看出每类指标的形态

使用方法：python ex01_趋势类指标.py
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

# matplotlib 默认字体不含中文，画图标题里的中文会变成方框并刷出一堆
# 缺字警告。这里指定 Windows 自带中文字体，并关闭负号转义（否则坐标轴负号
# 也会因字体问题显示异常）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 本脚本在 01_数据能力/03_技术指标/ 下，向上两级才是项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data_clean import parse_daily            # noqa: E402
from utils import technical_indicators as ta        # noqa: E402

# 清洗后的行情数据（上一阶段 ex02 数据管线产出）
CLEAN_CSV = PROJECT_ROOT / "data" / "stock_daily" / "hs300_daily_clean.csv"

# 用于画图演示的单只股票（浦发银行，数据里第一只）
DEMO_CODE = "600000"


# ------------------------------------------------------------------
# 1. 加载并批量计算
# ------------------------------------------------------------------
def main():
    df = pd.read_csv(CLEAN_CSV)
    df = parse_daily(df)  # date 转 datetime + 排序
    print(f"加载清洗数据：{len(df)} 行 × {df['code'].nunique()} 只股票\n")

    # 批量计算三类趋势指标（内部都是 groupby("code") 后逐股算，
    # 不会把不同股票的价格串在一起）
    df = ta.sma(df, timeperiod=20)
    df = ta.ema(df, timeperiod=12)
    df = ta.wma(df, timeperiod=20)
    df = ta.macd(df)
    df = ta.adx(df, timeperiod=14)

    # 看某只股票最新几天的指标值
    sub = df[df["code"] == DEMO_CODE]
    cols = ["date", "close", "sma_20", "ema_12", "wma_20",
            "dif", "dea", "macd_hist", "adx_14"]
    print(f"=== {DEMO_CODE} 趋势指标最近 5 个交易日 ===")
    show = sub[cols].tail(5).copy()
    show["date"] = show["date"].dt.strftime("%Y-%m-%d")  # date 转字符串再 round，避免对 datetime 报警告
    print(show.round(4).to_string(index=False))

    # 简单解释各列含义
    print("""
指标解读：
  - sma_20 / wma_20：两条 20 日均线，wma 给近期更高权重，通常比 sma 更贴价
  - ema_12：12 日指数均线，是 MACD 的快线
  - dif = EMA12 - EMA26，dea = dif 的 9 日 EMA，macd_hist = 2×(dif-dea)
  - adx_14：趋势强度，>40 为强趋势，<20 为震荡市
""")

    # ------------------------------------------------------------------
    # 2. 画图：三张子图
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

    # --- 子图 1：收盘价 + 三种移动平均线 ---
    ax = axes[0]
    ax.plot(sub["date"], sub["close"], color="black", lw=0.8, label="close")
    ax.plot(sub["date"], sub["sma_20"], color="orange", lw=1.2, label="SMA 20")
    ax.plot(sub["date"], sub["ema_12"], color="red", lw=1.0, label="EMA 12")
    ax.plot(sub["date"], sub["wma_20"], color="green", lw=1.0, label="WMA 20")
    ax.set_title(f"{DEMO_CODE} 趋势类指标（均线）")
    ax.set_ylabel("Price")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- 子图 2：MACD ---
    ax = axes[1]
    # 柱体：正红负绿（A 股习惯红涨绿跌）
    colors = sub["macd_hist"].map(lambda v: "red" if v >= 0 else "green")
    ax.bar(sub["date"], sub["macd_hist"], color=colors, width=1.0, label="MACD hist")
    ax.plot(sub["date"], sub["dif"], color="blue", lw=1.0, label="DIF")
    ax.plot(sub["date"], sub["dea"], color="orange", lw=1.0, label="DEA")
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_title("MACD (DIF / DEA / Hist)")
    ax.set_ylabel("MACD")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # --- 子图 3：ADX ---
    ax = axes[2]
    ax.plot(sub["date"], sub["adx_14"], color="purple", lw=1.2, label="ADX 14")
    ax.axhline(20, color="gray", linestyle="--", lw=0.8, label="20 (震荡/趋势分界)")
    ax.axhline(40, color="gray", linestyle="--", lw=0.8, label="40 (强趋势)")
    ax.set_title("ADX（趋势强度）")
    ax.set_ylabel("ADX")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = Path(__file__).resolve().parent / "ex01_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n趋势指标图已保存到：{out_png}")
    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
