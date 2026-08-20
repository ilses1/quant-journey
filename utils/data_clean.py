"""
utils/data_clean.py —— A 股日线行情数据清洗（跨阶段复用的公共工具）

对应《学习路线》2.2「数据清洗与存储」，把常见脏数据的检测与处理封装成
可复用函数，供 01_数据能力/02_数据清洗 及后续阶段（技术指标、回测、
实战项目）直接调用，避免每个脚本重写一遍清洗逻辑。

覆盖 5 类脏数据（见《学习路线》2.2 表格）：
  1. 缺失值      —— isna() 统计；价格前向填充 ffill、成交量填 0
  2. 异常值      —— 单日涨跌幅绝对值超过阈值（默认 11%）标记/剔除
  3. 停牌        —— 成交量为 0 或 NaN，标记 is_suspended（回测中跳过）
  4. 复权不一致  —— 单日跳空超过阈值，提示检查复权方式
  5. 重复数据    —— 按 (code, date) 去重

字段名约定：与 data/stock_daily/*.csv 保持一致
  code, date, open, high, low, close, volume, return, nav
"""

from __future__ import annotations

import pandas as pd

# 价格类字段，缺失时用前向填充（停牌期间沿用上一交易日价格）
PRICE_COLS = ["open", "high", "low", "close"]

# A 股主板涨跌停幅度为 ±10%，单日涨跌幅超过 11% 基本可断定是脏数据
# （新股、北交所 ±30%、ST ±5% 等特殊情况这里不细分，阈值可按需调整）
MAX_PCT_CHANGE = 0.11


def parse_daily(df: pd.DataFrame) -> pd.DataFrame:
    """规整日线数据：code 转 6 位字符串、date 转 datetime、排序、重置索引。

    从 CSV 读入时有两个坑必须在这里处理：
      - code 列会被 pandas 自动推断成整数，前导 0 丢失（如 "000001" 变 1），
        所以统一 astype(str) 再 zfill(6) 补回 6 位代码
      - date 列是字符串，必须先转成 datetime，否则 groupby().diff() 等
        按时间运算会报错（字符串不能相减）
    """
    df = df.copy()
    if "code" in df.columns:
        df["code"] = df["code"].astype(str).str.zfill(6)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["code", "date"]).reset_index(drop=True)
    return df


def report_missing(df: pd.DataFrame) -> pd.Series:
    """统计每一列的缺失值个数，等价于 df.isna().sum()。"""
    return df.isna().sum()


def drop_duplicate_rows(df: pd.DataFrame, subset=("code", "date")) -> pd.DataFrame:
    """删除重复行：同一只股票同一天出现多行时只保留最后一行。

    subset 指定"什么算重复"的判定键，默认 (code, date)。
    keep="last" 保留最后出现的一行（假设后写入的数据更新）。
    """
    return df.drop_duplicates(subset=list(subset), keep="last")


def flag_outliers(df: pd.DataFrame, col: str = "close",
                  threshold: float = MAX_PCT_CHANGE) -> pd.Series:
    """标记异常值：单日涨跌幅绝对值超过阈值的行（返回布尔 Series）。

    先按股票分组算日涨跌幅 pct_change()，再判断是否超阈值。
    注意：涨跌幅必须"按股票分组"算，不同股票之间的价格差异不是涨跌幅。
    """
    pct = df.groupby("code")[col].pct_change()
    return pct.abs() > threshold


def flag_suspension(df: pd.DataFrame) -> pd.Series:
    """标记停牌：成交量为 0 或 NaN 的交易日（返回布尔 Series）。

    停牌是合法状态而非错误——当天没有成交。回测时应"跳过"这些交易日，
    所以这里用"标记"而不是"删除"。
    """
    return (df["volume"].isna()) | (df["volume"] <= 0)


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """填充缺失值。

    策略（按列类型区分）：
      - 价格列 open/high/low/close：ffill 前向填充（停牌期间沿用上一交易日价格）
      - volume：填 0（停牌期间没有成交）
      - return / nav：不动（每只股票第一天的收益本就是 NaN，是 pct_change 的正常结果）
    """
    df = df.copy()
    for col in PRICE_COLS:
        if col in df.columns:
            df[col] = df[col].ffill()
    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0.0)
    return df


def check_adjust_jump(df: pd.DataFrame, col: str = "close",
                      threshold: float = MAX_PCT_CHANGE) -> pd.Series:
    """复权一致性检查：找出单日涨跌幅绝对值超过阈值的行。

    如果用的是前复权数据，除权日价格已经被修正过，不应出现超过涨跌停
    （±10%）的跳空；一旦出现，多半是复权方式不一致导致（比如部分数据
    用了不复权、部分用了前复权），需要回到数据源统一复权口径。
    检测手段与 flag_outliers 相同，但根因不同，故单独命名以强调用途。
    """
    pct = df.groupby("code")[col].pct_change()
    return pct.abs() > threshold


def clean_daily(df: pd.DataFrame, drop_outliers: bool = True,
                mark_suspension: bool = True) -> tuple[pd.DataFrame, dict]:
    """日线清洗总入口：按固定顺序依次处理，返回 (清洗后数据, 处理报告)。

    处理顺序很重要（先规整、再去重、再填充、再标记/剔除）：
      1. parse_daily       规整日期并排序
      2. drop_duplicate_rows  去重
      3. fill_missing      填充缺失值
      4. flag_suspension   标记停牌（新增 is_suspended 列）
      5. flag_outliers     标记异常涨跌（新增 is_outlier 列），可选剔除

    report 是 dict，记录每一步处理了多少行，方便核对清洗是否达到预期。
    """
    report: dict = {}
    raw_len = len(df)

    df = parse_daily(df)
    df = drop_duplicate_rows(df)
    report["去重删除行数"] = raw_len - len(df)

    df = fill_missing(df)
    report["缺失值已填充"] = True

    if mark_suspension and "volume" in df.columns:
        df["is_suspended"] = flag_suspension(df)
        report["停牌交易日数"] = int(df["is_suspended"].sum())

    outliers = flag_outliers(df)
    df["is_outlier"] = outliers
    report["异常涨跌行数"] = int(outliers.sum())
    if drop_outliers:
        df = df[~outliers]
        report["异常值已剔除"] = True

    return df, report
