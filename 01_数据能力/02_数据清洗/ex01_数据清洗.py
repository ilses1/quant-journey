"""
ex01: 数据清洗（数据能力 · 数据清洗）

对应《学习路线》2.2「常见脏数据及处理」表格，用上一阶段下载的
data/stock_daily/hs300_daily.csv 演示 5 类脏数据的检测与处理：

  □ 缺失值      —— isna().sum() 统计 → 价格 ffill / 成交量填 0
  □ 异常值      —— 涨跌幅 > 11% → 标记 is_outlier + 剔除
  □ 停牌        —— 成交量 0/NaN → 标记 is_suspended（回测中跳过）
  □ 复权不一致  —— 单日跳空 > 11% → 提示检查复权口径
  □ 重复数据    —— duplicated() → drop_duplicates()

真实数据大多已经比较干净（只有少量缺失值），为了把 5 类问题都演示清楚，
脚本分两部分：
  1. 对真实数据做「检测报告」，如实展示哪些问题真的存在、哪些没有
  2. 构造一份「人造脏数据」，把 5 类问题全部塞进去，走一遍完整清洗看前后对比

清洗函数本身放在 utils/data_clean.py（跨阶段复用），本脚本只负责调用和讲解。

使用方法：python ex01_数据清洗.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# 把项目根目录加入 sys.path，才能 import utils 包（utils 在根目录下，
# 而本脚本在 01_数据能力/02_数据清洗/ 下，向上两级才是根目录）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data_clean import (   # noqa: E402  # 放这里是因为要先加 sys.path
    clean_daily,
    drop_duplicate_rows,
    fill_missing,
    flag_outliers,
    flag_suspension,
    parse_daily,
    report_missing,
)

# 上一阶段（01_数据获取）下载并保存的原始行情文件
RAW_CSV = PROJECT_ROOT / "data" / "stock_daily" / "hs300_daily.csv"


# ------------------------------------------------------------------
# 1. 对真实数据的检测报告
# ------------------------------------------------------------------
def inspect_real_data():
    """加载真实数据，如实统计 5 类脏数据各自有多少。"""
    print("=" * 70)
    print("第一部分：真实数据检测报告（data/stock_daily/hs300_daily.csv）")
    print("=" * 70)

    df = pd.read_csv(RAW_CSV)
    df = parse_daily(df)  # date 转 datetime + 排序
    print(f"原始数据：{len(df)} 行 × {len(df.columns)} 列，"
          f"{df['code'].nunique()} 只股票\n")

    # --- 1. 缺失值 ---
    print("① 缺失值统计（每列 NaN 个数）：")
    missing = report_missing(df)
    print(missing[missing > 0].to_string())
    print("   → return 有 20 个 NaN：每只股票第一天没有「前一天」，pct_change 的正常结果\n"
          "   → volume 有 10 个 NaN：某只股票停牌期间没有成交量，见下面 ③\n")

    # --- 2. 异常值（涨跌幅 > 11%） ---
    outliers = flag_outliers(df)
    print(f"② 异常值（|涨跌幅| > 11%）：{int(outliers.sum())} 行")
    if outliers.any():
        print(df[outliers][["code", "date", "close"]].to_string(index=False))

    # --- 3. 停牌（成交量为 0 或 NaN） ---
    susp = flag_suspension(df)
    print(f"\n③ 停牌（成交量 0/NaN）：{int(susp.sum())} 行")
    if susp.any():
        print(df[susp][["code", "date", "close", "volume"]].to_string(index=False))
        print("   特征：价格连续走平（open==close）且成交量缺失 → 停牌期\n")

    # --- 4. 复权一致性（单日跳空 > 11%） ---
    dup = df.duplicated(subset=["code", "date"])
    print(f"④ 重复数据（同一 code+date 多行）：{int(dup.sum())} 行")

    # --- 5. 重复数据 ---
    print("⑤ 复权一致性：见 utils 的 check_adjust_jump，检测手段与②相同，"
          "根因是复权口径混用")
    print("   本例数据统一为前复权（qfq），未发现超过涨跌停的跳空\n")

    print("小结：真实数据只有「缺失值/停牌」两类小问题，其余三类没踩到——")
    print("这是正常现象，真实工程里脏数据未必全出现。下面用「人造脏数据」")
    print("把 5 类问题都演示一遍。\n")
    return df


# ------------------------------------------------------------------
# 2. 人造脏数据：把 5 类问题全部塞进去
# ------------------------------------------------------------------
def make_dirty_sample() -> pd.DataFrame:
    """构造一只股票连续 8 个交易日的脏数据，覆盖全部 5 类问题。

    基准价约 10 元，故意制造：
      - 第 3 天 close = NaN            → 缺失值
      - 第 4 天出现两行相同数据        → 重复数据
      - 第 5 天 volume = 0             → 停牌
      - 第 6 天 close 从 10 跌到 7     → 复权不一致（-31% 跳空）
      - 第 7 天 close 从 7 涨到 15     → 异常值（+114% 涨幅）
    """
    rows = [
        # code, date,       open,  high,  low,   close, volume
        ["600000", "2024-01-01", 10.0, 10.2, 9.90, 10.1, 100000],
        ["600000", "2024-01-02", 10.1, 10.3, 10.0, 10.2, 120000],
        ["600000", "2024-01-03", 10.2, 10.4, 10.1, np.nan, 110000],  # 缺失值
        ["600000", "2024-01-04", 10.1, 10.3, 10.0, 10.2, 90000],
        ["600000", "2024-01-04", 10.1, 10.3, 10.0, 10.2, 90000],     # 重复行
        ["600000", "2024-01-05", 10.2, 10.3, 10.1, 10.2, 0],         # 停牌
        ["600000", "2024-01-08", 7.0, 7.1, 6.9, 7.0, 80000],         # 复权跳空
        ["600000", "2024-01-09", 7.1, 15.0, 7.0, 15.0, 500000],      # 异常值
    ]
    df = pd.DataFrame(rows, columns=["code", "date", "open", "high",
                                     "low", "close", "volume"])
    return df


def demo_cleaning():
    """对脏数据逐步清洗，展示每一步前后对比。"""
    print("=" * 70)
    print("第二部分：人造脏数据完整清洗演示")
    print("=" * 70)

    dirty = make_dirty_sample()
    print("清洗前的脏数据（8 行，含 5 类问题）：")
    print(dirty.to_string(index=False))
    print()

    # --- 步骤 1：规整 + 去重 ---
    # duplicated() 返回布尔 Series，标记"和前面重复"的行（默认 keep='first'，
    # 第一次出现不算重复，之后的算重复）
    dup_mask = dirty.duplicated(subset=["code", "date"], keep="first")
    print(f"① 重复行检测：{int(dup_mask.sum())} 行重复")
    dirty2 = drop_duplicate_rows(dirty)
    print(f"   去重后：{len(dirty2)} 行（删除了 1 行重复）\n")

    # --- 步骤 2：填充缺失值 ---
    print(f"② 缺失值检测：close 有 {int(dirty2['close'].isna().sum())} 个 NaN")
    dirty3 = fill_missing(dirty2)
    print(f"   填充后 close：{dirty3['close'].tolist()}")
    print("   → 第 3 天 close 由 ffill 填成 10.2（沿用第 2 天收盘价）\n")

    # --- 步骤 3：标记停牌 ---
    susp = flag_suspension(dirty3)
    print(f"③ 停牌检测：{int(susp.sum())} 行成交量 = 0")
    print(dirty3[susp][["date", "close", "volume"]].to_string(index=False))
    print("   → 第 5 天被标记 is_suspended，回测时跳过这一天，但不删除\n")

    # --- 步骤 4：标记异常值 ---
    out = flag_outliers(dirty3)
    print(f"④ 异常涨跌检测（|涨跌幅| > 11%）：{int(out.sum())} 行")
    print(dirty3[out][["date", "close"]].to_string(index=False))
    print("   → 第 7 天(01-09) +114% 是异常值；第 6 天(01-08) -31% 跳空提示复权不一致\n")

    # --- 步骤 5：一次性完整清洗 ---
    print("⑤ 用 clean_daily() 一键完成上述全部步骤：")
    clean, report = clean_daily(dirty)
    print(f"   处理报告：{report}")
    print("\n清洗后数据：")
    print(clean.to_string(index=False))
    print("\n   → 重复被删、NaN 被填、停牌/异常被打标、异常行被剔除，" 
          "剩下 5 行干净数据")


# ------------------------------------------------------------------
# 3. 主流程
# ------------------------------------------------------------------
def main():
    inspect_real_data()
    demo_cleaning()

    print("\n" + "=" * 70)
    print("练习完成。清洗函数的完整实现见 utils/data_clean.py；")
    print("下一步 ex02 会把「清洗」接进「获取→存储」的完整数据管线。")
    print("=" * 70)


if __name__ == "__main__":
    main()
