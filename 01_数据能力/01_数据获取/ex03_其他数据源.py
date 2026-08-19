"""
ex03: 其他数据源对比（数据能力 · 数据获取）

《学习路线》2.1 列了 5 个免费数据源，本脚本演示除 AKShare 之外的三个：
  1. Baostock  —— A股历史日线/分钟线，完全免费、无需注册、socket 连接（最稳）
  2. Tushare   —— A股日线/分钟线/财务，老牌稳定，但需注册拿 token（积分制）
  3. yfinance  —— 美股/港股/全球指数，基于 Yahoo Finance

对比要点：
  - Baostock 走 TCP socket，不依赖 HTTPS，几乎不受网络/TLS 环境影响
  - Tushare 是 HTTP API，需 token；免费积分够拉日线，财务/分钟线需更高积分
  - yfinance 面向海外市场，A 股数据用不到它

使用方法：
  1. python ex03_其他数据源.py
  2. Tushare 部分需要 token：脚本会自动读取项目根目录 .env 中的
      TUSHARE_TOKEN（也可临时用环境变量 $env:TUSHARE_TOKEN 覆盖）
"""

import os
from pathlib import Path

import pandas as pd

import baostock as bs      # 免费、无需注册
import tushare as ts       # 需注册拿 token
import yfinance as yf      # 美股/港股/全球指数


def load_env():
    """读取项目根目录的 .env 文件，把 KEY=VALUE 写入环境变量。

    约定：.env 位于仓库根目录（d:/testQunt/.env），本脚本在
    01_数据能力/01_数据获取/ 下，向上两级即项目根。
    只解析简单的 KEY=VALUE 行，跳过注释和空行；
    已有同名环境变量时优先保留环境变量，不覆盖。
    """
    project_root = Path(__file__).resolve().parents[2]
    env_file = project_root / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key:
            os.environ.setdefault(key, value)


load_env()

# Tushare token：优先取环境变量，其次可在脚本顶部直接赋值
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")


# ------------------------------------------------------------------
# 1. Baostock —— 免费无注册，socket 连接
# ------------------------------------------------------------------
def baostock_demo():
    print("\n" + "=" * 60)
    print("1. Baostock（A股历史行情，免费无需注册）")
    print("=" * 60)

    # login 返回的 error_code 为 "0" 表示成功
    lg = bs.login()
    print(f"login: {lg.error_code} {lg.error_msg}")

    # --- 日线：贵州茅台前复权 ---
    # query_history_k_data_plus(代码, 字段串, start, end, frequency, adjustflag)
    #   frequency: d=日 w=周 m=月 5=5分钟线 15=15分钟线 ...
    #   adjustflag: 1=后复权 2=前复权 3=不复权
    rs = bs.query_history_k_data_plus(
        "sh.600519",
        "date,open,high,low,close,volume",
        start_date="2026-01-01", end_date="2026-01-10",
        frequency="d", adjustflag="2",
    )
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    print("\n贵州茅台 2024 年初前 5 个交易日（前复权）：")
    print(df.head().to_string(index=False))

    # --- 分钟线：5 分钟 ---
    rs2 = bs.query_history_k_data_plus(
        "sh.600519",
        "date,time,close,volume",
        start_date="2024-01-05", end_date="2024-01-05",
        frequency="5", adjustflag="2",
    )
    rows2 = []
    while rs2.next():
        rows2.append(rs2.get_row_data())
    print(f"\n贵州茅台 2024-01-05 的 5 分钟线，共 {len(rows2)} 条")

    bs.logout()
    print("logout 完成")


# ------------------------------------------------------------------
# 2. Tushare —— 需注册拿 token，积分制
# ------------------------------------------------------------------
def tushare_demo():
    print("\n" + "=" * 60)
    print("2. Tushare（A股日线，需 token） 未复权")
    print("=" * 60)

    if not TUSHARE_TOKEN:
        print("[提示] 未设置 token，跳过。请把 token 填到脚本顶部 TUSHARE_TOKEN，")
        print("  或运行前先设置环境变量： $env:TUSHARE_TOKEN=\"你的token\"")
        return

    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()

    try:
        # 日线：ts_code 需要带交易所后缀（.SH / .SZ）
        df = pro.daily(ts_code="600519.SH", start_date="20260101", end_date="20260110")
        if len(df) == 0:
            print("返回空数据。可能原因：token 积分不足/过期，或该接口需要更高权限。")
            print("基础积分(120)可拉日线；若拿不到，请到 tushare.pro 检查积分。")
        else:
            print(df.head().to_string(index=False))
    except Exception as e:
        print(f"Tushare 请求失败：{type(e).__name__}: {e}")


# ------------------------------------------------------------------
# 3. yfinance —— 美股 / 港股 / 全球指数
# ------------------------------------------------------------------
def yfinance_demo():
    print("\n" + "=" * 60)
    print("3. yfinance（美股/全球指数，基于 Yahoo Finance）")
    print("=" * 60)

    try:
        # 下载苹果公司近一年日线。auto_adjust=False 保留原始 OHLC（含拆分红股影响）
        aapl = yf.download("AAPL", period="1y", auto_adjust=False, progress=False)
        print("苹果(AAPL)日线尾 5 行：")
        print(aapl.tail().to_string())

        # 标普500 指数（^GSPC）
        spx = yf.download("^GSPC", period="3mo", auto_adjust=False, progress=False)
        print("\n标普500(^GSPC)日线尾 5 行：")
        print(spx.tail().to_string())
    except Exception as e:
        print(f"yfinance 请求失败：{type(e).__name__}: {e}")
        print("（Yahoo 数据源在某些网络环境下也可能超时，属正常现象）")


def main():
    baostock_demo()
    tushare_demo()
    yfinance_demo()

    print("\n" + "=" * 60)
    print("小结：学习阶段建议 Baostock(免费无门槛) + AKShare(数据最全) 搭配使用，")
    print("Tushare 注册后作为备用，yfinance 只在涉及海外市场时用。")
    print("=" * 60)


if __name__ == "__main__":
    main()
