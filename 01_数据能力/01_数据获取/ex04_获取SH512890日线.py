"""
ex04: 获取 SH512890 日线数据（前复权）（数据能力 · 数据获取）

对应《学习路线》2.1 的延伸练习：在 ex01 基础上，针对单只场内基金/ETF
（512890，沪市，代码以 5 开头）拉取近 3 年日线行情（OHLCV），并做前复权处理。

与 ex01 的区别：
  1. ex01 批量拉 300 成分股，本脚本只拉单一标的，逻辑更精简；
  2. ETF 走 AKShare 的 fund_etf_hist_em 接口（stock_zh_a_hist 只认股票）；
  3. Baostock 回退时，交易所前缀按"5/6 开头=沪市、0/1/3 开头=深市"判断，
     修正了 ex01 里只按 6 判断导致 5 开头被误判为深市的问题。

数据源策略（三级回退）：
  1. AKShare·东财 fund_etf_hist_em  —— 直接返回前复权数据（数据最全，但某些网络/新版
     Python 的 TLS 指纹会被东财拒连）；
  2. AKShare·新浪 fund_etf_hist_sina —— 返回不复权数据 + 新浪 qfq.js 复权因子，
     手动算出前复权（新浪源覆盖最全，能从上市日拉到最新）；
  3. Baostock —— 完全免费无需注册，但个别 ETF 历史覆盖不全（可能只有最近几个月）。

使用方法：python ex04_获取SH512890日线.py
"""

# ------------------------------------------------------------------
# 0. 导入与后端设置
# ------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")          # 非交互式后端：只在内存画图然后存文件，不弹窗

import json
from pathlib import Path

import requests
import pandas as pd
import matplotlib.pyplot as plt

import akshare as ak
import baostock as bs

# ------------------------------------------------------------------
# 全局配置
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent.parent / "data" / "stock_daily"

CODE = "512890"                # 沪市 ETF 代码（5 开头），不带交易所前缀
YEARS = 3                      # 拉取近 3 年
ADJUST = "qfq"                 # 前复权：以最新价为基准折算历史价，便于直接算收益

# 统一输出的标准列（各数据源都映射成这个格式）
STD_COLS = ["date", "open", "high", "low", "close", "volume"]


def _sina_symbol(code):
    """6 位代码 -> 新浪带交易所前缀的代码（sh/sz）"""
    return f"sh{code}" if code.startswith(("5", "6", "9")) else f"sz{code}"


def _to_std(df):
    """把 date/open/... 统一转成标准格式：date 为 datetime，数值列转 float"""
    df = df[STD_COLS].copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in STD_COLS[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["close"]).reset_index(drop=True)


# ------------------------------------------------------------------
# 1. 获取单只 ETF 日线（OHLCV，前复权）
# ------------------------------------------------------------------
def get_daily_akshare(code, start_date, end_date):
    """数据源 1：AKShare·东财，直接返回前复权数据

    fund_etf_hist_em(symbol, period, start_date, end_date, adjust)
      - symbol    6 位 ETF 代码（如 "512890"），不带交易所后缀
      - period    daily / weekly / monthly
      - adjust    qfq=前复权 / hfq=后复权 / ""=不复权
    注意：ETF 的列顺序与股票接口不同，这里按列名映射，不做位置假设。
    """
    df = ak.fund_etf_hist_em(
        symbol=code,
        period="daily",
        start_date=start_date.replace("-", ""),   # 接口要 "20230101" 格式
        end_date=end_date.replace("-", ""),
        adjust=ADJUST,
    )
    rename = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
    }
    return _to_std(df.rename(columns=rename))


def get_daily_sina(code, start_date, end_date):
    """数据源 2：AKShare·新浪，不复权数据 + 复权因子手动算前复权

    fund_etf_hist_sina 只给不复权价格，且只覆盖到"最新"，
    但新浪另有 qfq.js 接口返回每个除权除息日的"前复权因子"：
      前复权价 = 不复权价 / 前复权因子
    因子按日期做前向填充（ffill）：事件日之前用旧的因子，事件日之后用新的。
    """
    symbol = _sina_symbol(code)
    df = ak.fund_etf_hist_sina(symbol=symbol)
    df = df.rename(columns={"date": "date"})       # 新浪列名本身已是英文
    df = _to_std(df)

    # 拉取前复权因子：qfq.js 内容形如 var xxx={"data":[{"d":"2021-10-25","f":"1","s":"1.0","u":"0"}, ...]}
    url = f"https://finance.sina.com.cn/realstock/company/{symbol}/qfq.js"
    r = requests.get(url, timeout=15)
    text = r.text.split("=", 1)[1].split("/*", 1)[0].strip()
    payload = json.loads(text)
    factor_df = pd.DataFrame(payload["data"])[["d", "s"]]
    factor_df.columns = ["date", "qfq_factor"]
    factor_df["date"] = pd.to_datetime(factor_df["date"])
    factor_df["qfq_factor"] = pd.to_numeric(factor_df["qfq_factor"], errors="coerce")

    # outer 合并（把基线 1900-01-01 也并进来），按日期排序后 ffill，让每行拿到正确因子
    df = df.merge(factor_df, on="date", how="outer").sort_values("date").reset_index(drop=True)
    df["qfq_factor"] = df["qfq_factor"].ffill().fillna(1.0)
    df = df.dropna(subset=["close"])

    for col in ["open", "high", "low", "close"]:
        df[col] = df[col] / df["qfq_factor"]

    return _to_std(df[STD_COLS])


def get_daily_baostock(code, start_date, end_date):
    """数据源 3：Baostock 日线（前复权，兜底）

    交易所前缀判断：5/6 开头=沪市(sh)，0/1/3 开头=深市(sz)。
    Baostock 的 ETF 与股票一样用 query_history_k_data_plus 接口。
    """
    prefix = "sh" if code.startswith(("5", "6", "9")) else "sz"
    bs_code = f"{prefix}.{code}"

    lg = bs.login()
    try:
        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume",
            start_date=start_date,
            end_date=end_date,
            frequency="d",       # d=日线
            adjustflag="2",      # 2=前复权，等价于 AKShare 的 qfq
        )
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        df = pd.DataFrame(rows, columns=STD_COLS)
        return _to_std(df)
    finally:
        bs.logout()


def get_daily(code, start_date, end_date):
    """日线获取总入口：东财 -> 新浪 -> Baostock 三级回退"""
    sources = [
        ("AKShare·东财", lambda: get_daily_akshare(code, start_date, end_date)),
        ("AKShare·新浪", lambda: get_daily_sina(code, start_date, end_date)),
        ("Baostock",     lambda: get_daily_baostock(code, start_date, end_date)),
    ]
    for name, func in sources:
        try:
            df = func()
            if len(df) > 0:
                print(f"[数据源] {name} 获取成功")
                return df
            print(f"[数据源] {name} 返回空数据，尝试下一个 ...")
        except Exception as e:
            print(f"[数据源] {name} 失败（{type(e).__name__}: {str(e)[:100]}），尝试下一个 ...")
    raise RuntimeError("所有数据源均失败，请检查网络后重试")


# ------------------------------------------------------------------
# 2. 主流程
# ------------------------------------------------------------------
def main():
    end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.today() - pd.DateOffset(years=YEARS)).strftime("%Y-%m-%d")
    print(f"标的：{CODE}（前复权）")
    print(f"数据区间：{start_date} ~ {end_date}")

    data = get_daily(CODE, start_date, end_date)

    # 只保留请求区间内的数据
    mask = (data["date"] >= pd.to_datetime(start_date)) & (data["date"] <= pd.to_datetime(end_date))
    data = data[mask].reset_index(drop=True)

    print(f"共 {len(data)} 行数据，区间 {data['date'].min().date()} ~ {data['date'].max().date()}")
    print(data.head(10).to_string(index=False))
    print(data.tail(5).to_string(index=False))

    # --- 保存数据，供后续阶段使用 ---
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / f"sh{CODE}_daily.csv"
    data.to_csv(csv_path, index=False)
    print(f"\n行情数据已保存到：{csv_path}")

    # --- 简单可视化：前复权收盘价曲线 ---
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(data["date"], data["close"], linewidth=1.2, label=f"{CODE} close (qfq)")
    ax.set_title(f"SH{CODE} Daily Close (qfq)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Close Price")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out_png = BASE_DIR / "ex04_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"收盘价曲线已保存到：{out_png}")

    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
