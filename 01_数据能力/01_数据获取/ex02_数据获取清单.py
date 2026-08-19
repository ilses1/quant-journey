"""
ex02: 数据获取清单（数据能力 · 数据获取）

对应《学习路线》2.1 的"典型数据获取清单"，逐项演示 8 类数据的获取接口：
  □ 股票日线行情（OHLCV）        —— 已在 ex01 完成，这里只列接口
  □ 股票分钟线行情（5min）       —— stock_zh_a_hist_min_em
  □ 指数日线（沪深300/中证500/中证1000）
  □ 财务数据（利润表/资产负债表/现金流量表摘要）
  □ 估值数据（PE / PB / PS / 股息率）
  □ 资金流向（北向资金、融资融券余额）
  □ 宏观经济数据（GDP / CPI / PMI）
  □ 行业分类（申万一级 / 东财行业板块）

每个函数都是独立的 try/except，某一项失败不影响其它项，
最后打印一份"成功/失败"清单。数据源以 AKShare 为主（最全），
部分接口附带 Baostock 备选。

使用方法：python ex02_数据获取清单.py
"""

import akshare as ak
import pandas as pd


def item_stock_minute(symbol="600519", period="5"):
    """股票分钟线（5 分钟），东财源"""
    df = ak.stock_zh_a_hist_min_em(symbol=symbol, period=period, adjust="qfq")
    return df.head()


def item_index_daily(symbol="000300"):
    """指数日线。000300=沪深300, 000905=中证500, 000852=中证1000"""
    df = ak.index_zh_a_hist(symbol=symbol, period="daily")
    return df.tail()


def item_financial(symbol="600519"):
    """财务数据摘要：每股收益、营收、净利、ROE 等（东财源）"""
    df = ak.stock_financial_abstract(symbol=symbol)
    return df.head()


def item_valuation(symbol="600519"):
    """估值数据：PE/PB/PS/股息率/总市值（东财源）"""
    df = ak.stock_value_em(symbol=symbol)
    return df.head()


def item_fund_flow_north():
    """北向资金（沪股通/深股通）当日汇总"""
    df = ak.stock_hsgt_fund_flow_summary_em()
    return df.head()


def item_fund_flow_margin():
    """融资融券余额（上交所某交易日明细）"""
    df = ak.stock_margin_detail_sse(date="20250102")
    return df.head()


def item_macro_gdp():
    """宏观：中国 GDP 年度数据"""
    return ak.macro_china_gdp()


def item_macro_cpi():
    """宏观：中国 CPI"""
    return ak.macro_china_cpi()


def item_macro_pmi():
    """宏观：中国 PMI"""
    return ak.macro_china_pmi()


def item_industry_sw():
    """行业分类：申万一级行业"""
    return ak.sw_index_first_info()


def item_industry_em():
    """行业分类：东方财富行业板块"""
    return ak.stock_board_industry_name_em()


def main():
    # 每个清单项 = (名称, 函数)，逐项执行并记录结果
    checklist = [
        ("股票分钟线(5min)",      item_stock_minute),
        ("指数日线(沪深300)",      item_index_daily),
        ("财务数据摘要",           item_financial),
        ("估值数据(PE/PB/PS)",    item_valuation),
        ("资金流向·北向资金",      item_fund_flow_north),
        ("资金流向·融资融券",      item_fund_flow_margin),
        ("宏观·GDP",              item_macro_gdp),
        ("宏观·CPI",              item_macro_cpi),
        ("宏观·PMI",              item_macro_pmi),
        ("行业分类·申万一级",      item_industry_sw),
        ("行业分类·东财板块",      item_industry_em),
    ]

    print("=" * 60)
    print("数据获取清单执行结果")
    print("=" * 60)

    for name, func in checklist:
        try:
            df = func()
            ok = df is not None and len(df) > 0
            status = "成功" if ok else "失败(空数据)"
            print(f"[{status}] {name:<18} 行数={len(df) if df is not None else 0}")
            if ok:
                # 每个接口的列名不同，只打印前几列帮助理解
                cols = list(df.columns)[:6]
                print(f"        列名(前6)={cols}")
        except Exception as e:
            print(f"[失败] {name:<18} {type(e).__name__}: {str(e)[:80]}")

    print("=" * 60)
    print("提示：AKShare 依赖 requests 访问东财/新浪等 HTTPS 接口，")
    print("个别网络环境（尤其新版 Python/TLS 指纹）可能出现 SSL 报错。")
    print("遇到报错的接口，可改用 Baostock（见 ex03）或换网络环境重试。")
    print("=" * 60)


if __name__ == "__main__":
    main()
