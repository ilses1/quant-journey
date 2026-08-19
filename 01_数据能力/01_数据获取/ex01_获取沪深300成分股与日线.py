"""
ex01: 获取沪深 300 成分股列表 + 近 3 年日线行情（数据能力 · 数据获取）

对应《学习路线》2.1 的实操练习，完整走通三步：
  1. 获取沪深 300 成分股列表
  2. 获取每只成分股近 3 年日线行情（OHLCV），存入 DataFrame
  3. 计算每只股票的日收益率，画出累计收益曲线并可视化

数据源策略（真实工程里很常见）：优先用 AKShare（数据最全），
网络不通/接口异常时自动回退到 Baostock（完全免费、无需注册、走 socket 不受 HTTPS 限制）。

使用方法：
  1. 建议先在本目录运行：  python ex01_获取沪深300成分股与日线.py
  2. 想看全部 300 只，把下方 TOP_N 改成 300（会更慢，约 1~2 分钟）
"""

# ------------------------------------------------------------------
# 0. 导入与后端设置
# ------------------------------------------------------------------
import matplotlib
# Agg 是非交互式渲染后端：只在内存里画图然后保存文件，
# 不弹窗口、不阻塞，命令行/服务器环境下都能跑
matplotlib.use("Agg")

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import akshare as ak      # 数据最全的免费源（A股/期货/期权/宏观）
import baostock as bs     # 免费、无需注册，socket 连接，作为回退源

# ------------------------------------------------------------------
# 全局配置
# ------------------------------------------------------------------
# 本脚本所在目录（用 __file__ 定位，保证从任意工作目录运行都找得到路径）
BASE_DIR = Path(__file__).resolve().parent
# - __file__ — 当前 Python 脚本自身的路径（相对或绝对，取决于运行时传入的方式）
# - Path(__file__) — 把字符串路径包装成 Path 对象
# - .resolve() — 解析为绝对路径，并跟随符号链接、消除 .. 等
# - .parent — 取上一级目录（即脚本所在的文件夹）

# 数据统一存入 data/stock_daily/（该目录已被 .gitignore 排除，不会进版本库）
DATA_DIR = BASE_DIR.parent.parent / "data" / "stock_daily"

# 拉取多少只股票的日线做演示。沪深 300 共 300 只，
# 改成 300 就是完整版（下载更慢）；20 只足够看清"累计收益曲线"长什么样
TOP_N = 20

# 近 3 年：以运行当天往前推 3 年（用"天数"粗略换算，精确到交易日由数据源决定）
YEARS = 3

# 复权方式：qfq=前复权（用今天为基准往回折算历史价，最常用，便于直接算收益率）
ADJUST = "qfq"


# ------------------------------------------------------------------
# 1. 获取沪深 300 成分股列表
# ------------------------------------------------------------------
def get_constituents_akshare():
    """用 AKShare 获取沪深 300 成分股，返回统一格式 DataFrame[code, name]

    AKShare 有两个接口可选：
      - index_stock_cons_csindex("000300")  中证指数官网（字段全）
      - index_stock_cons("000300")          新浪源（字段少但更稳）
    这里两个都试，谁通谁用。
    """
    # 接口 1：中证指数官网。返回的"成分券代码"就是股票代码（如 "600519"）
    try:
        df = ak.index_stock_cons_csindex(symbol="000300")
        # 找到代码和名称列（不同版本列名可能不同，做一次兼容判断）
        code_col = [c for c in df.columns if "代码" in c and "指数" not in c][0]
        # 上面写法等价于 下面传统写法
        # result = []
        # for c in df.columns:
        #     if "代码" in c and "指数" not in c:
        #         result.append(c)

        # code_col = result[0]

        name_col = [c for c in df.columns if "名称" in c and "指数" not in c][0]
        out = pd.DataFrame({
            "code": df[code_col].astype(str),
            # .astype(str) — 把该列所有元素转成字符串（如把 600000 数字变成 "600000"）
            "name": df[name_col].astype(str),
        })
        return out
    except Exception:
        pass  # 第一个接口失败，继续试第二个

    # 接口 2：新浪源。列名为"品种代码 / 品种名称"
    df = ak.index_stock_cons(symbol="000300")
    out = pd.DataFrame({
        "code": df["品种代码"].astype(str),
        "name": df["品种名称"].astype(str),
    })
    return out


def get_constituents_baostock():
    """用 Baostock 获取沪深 300 成分股（回退方案）"""
    lg = bs.login()
    try:
        rs = bs.query_hs300_stocks()          # 查询沪深 300 成分股
        rows = []
        # rs.next() 是 Baostock 查询结果集的迭代方法。
        # - bs.query_hs300_stocks() 返回一个结果集对象 rs，它像一个游标/迭代器
        # - rs.next() 每次调用把游标移到下一行，并返回布尔值：还有下一行返回 True，读完返回 False
        # - 配合 while rs.next(): 循环遍历所有行，每行用 rs.get_row_data() 取当前行的数据
        while rs.next():
            rows.append(rs.get_row_data())     # 每行 [日期, 代码(sh.600000), 名称]
        # 代码形如 "sh.600519"，去掉交易所前缀只留数字代码
        out = pd.DataFrame(rows, columns=["date", "code", "name"])
        out["code"] = out["code"].str.split(".").str[1]
        # out["code"] 是 pandas 的 Series（一列数据，带索引），其中每个元素是字符串。 说它是带标签的一维数组
        # - out["code"].str — 对该列每个元素做字符串操作
        # - .split(".") — 按 . 分割，"sh.600519" → ["sh", "600519"]
        # - .str[1] — 取分割后的第 2 个元素（索引 1），即 "600519"
        # - 结果写回 out["code"]
        return out[["code", "name"]]
    finally:
        bs.logout()


def get_constituents():
    """成分股获取总入口：AKShare 优先，失败回退 Baostock"""
    try:
        df = get_constituents_akshare()
        print(f"[成分股] AKShare 获取成功，共 {len(df)} 只")
        return df
    except Exception as e:
        print(f"[成分股] AKShare 失败（{type(e).__name__}: {e}），回退到 Baostock ...")
        df = get_constituents_baostock()
        print(f"[成分股] Baostock 获取成功，共 {len(df)} 只")
        return df


# ------------------------------------------------------------------
# 2. 获取单只股票近 3 年日线（OHLCV）
# ------------------------------------------------------------------
def get_daily_akshare(code, start_date, end_date):
    """用 AKShare 获取单只股票日线，返回统一格式 [date, open, high, low, close, volume]

    stock_zh_a_hist(symbol, period, start_date, end_date, adjust)
      - symbol   6 位股票代码（如 "600519"），不用带交易所后缀
      - period   daily / weekly / monthly
      - adjust   qfq=前复权 / hfq=后复权 / ""=不复权
    """
    df = ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=start_date.replace("-", ""),   # 接口要 "20230101" 格式
        end_date=end_date.replace("-", ""),
        adjust=ADJUST,
    )
    # AKShare 返回中文列名，统一映射成标准英文列名
    rename = {
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
    }
    df = df.rename(columns=rename)
    keep = ["date", "open", "high", "low", "close", "volume"]
    df = df[keep].copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_daily_baostock(code, start_date, end_date):
    """用 Baostock 获取单只股票日线（回退方案）

    Baostock 代码要带交易所前缀：sh=上交所，sz=深交所。
    6 开头是沪市，其余基本是深市（0/3 开头），这里做个简单判断。
    """
    prefix = "sh" if code.startswith("6") else "sz"
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
        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    finally:
        bs.logout()


def get_daily(code, start_date, end_date):
    """日线获取总入口：AKShare 优先，失败回退 Baostock"""
    try:
        return get_daily_akshare(code, start_date, end_date)
    except Exception:
        return get_daily_baostock(code, start_date, end_date)


# ------------------------------------------------------------------
# 3. 主流程
# ------------------------------------------------------------------
def main():
    # 计算近 3 年的起止日期
    end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.today() - pd.DateOffset(years=YEARS)).strftime("%Y-%m-%d")
    print(f"数据区间：{start_date} ~ {end_date}")

    # --- 步骤 1：成分股列表 ---
    cons = get_constituents()
    print(cons.head(10).to_string(index=False))

    # --- 步骤 2：逐只拉取日线，拼成一张长表（long format） ---
    # 长表结构：每行 = 某只股票某一天，列 = code, date, open, high, low, close, volume
    # 这种"一列存股票代码"的格式最方便后续 groupby 做截面计算
    print(f"\n开始下载前 {TOP_N} 只成分股日线 ...")
    frames = []
    # try:
    #     # 正常代码
    # except Exception as e:
    #     # 出错时执行
    # finally:
    #     # 无论成功或失败，都一定执行
    for i, (_, row) in enumerate(cons.head(TOP_N).iterrows(), 1):
        code = row["code"]
        try:
            daily = get_daily(code, start_date, end_date)
            daily.insert(0, "code", code)          # 在最前面插入股票代码列
            frames.append(daily)
            if i % 10 == 0:
                print(f"  已下载 {i}/{TOP_N}")
        except Exception as e:
            print(f"  [跳过] {code} 下载失败：{e}")
        time.sleep(0.1)  # 轻微限速，避免对数据源造成压力

    data = pd.concat(frames, ignore_index=True)
    print(f"\n共 {data['code'].nunique()} 只股票，{len(data)} 行数据")
    print(data.head(10).to_string(index=False))

    # --- 步骤 3：计算每只股票的日收益率 ---
    # groupby("code") 按股票分组，pct_change() 算相对前一交易日的涨跌幅
    # 分组后每组内部是时间有序的，第一行收益率为 NaN（没有前一天）
    data["return"] = data.groupby("code")["close"].pct_change()

    # 看一眼某只股票的收益率分布
    # iloc 是 pandas 里按整数位置取数据的索引器（integer location 的缩写）。
    one = data[data["code"] == data["code"].iloc[0]]
    print(f"\n=== 示例股票 {data['code'].iloc[0]} 的日收益率统计 ===")
    print(one["return"].describe().to_string())

    # --- 步骤 4：累计收益曲线 ---
    # 累计收益 = 把每日收益加 1 后连乘（cumprod），等价于"净值曲线"
    # 公式：净值_t = (1+r1)(1+r2)...(1+rt)
    # lambda 是 Python 的匿名函数（没有名字、一行写完的小函数）。先看语法，再看这段代码里的用法。
    # lambda 语法
    # lambda 参数: 返回值表达式
    # 等价于：
    # def 函数名(参数):
    #     return 返回值表达式
    # 比如：
    # lambda x: x * 2          # 等价于 def f(x): return x * 2
    # lambda a, b: a + b       # 等价于 def f(a, b): return a + b
    # 特点：只能有一个表达式，不能写多行逻辑；适合作为参数直接传给别的函数。
    data["nav"] = data.groupby("code")["return"].transform(
        lambda r: (1 + r.fillna(0)).cumprod()
    )

    # 画图：每只股票画一条"从 1 开始的净值曲线"，再加一条等权组合均线
    fig, ax = plt.subplots(figsize=(14, 7))

    pivot = data.pivot(index="date", columns="code", values="nav")
    pivot.plot(ax=ax, legend=False, linewidth=0.6, alpha=0.7)

    # 等权组合：所有股票净值求平均（每列代表一只股票，横向平均）
    portfolio = pivot.mean(axis=1)
    portfolio.plot(ax=ax, color="black", linewidth=2.5, label="Equal-Weight Portfolio")

    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.8)  # 起点基准线
    ax.set_title(f"HS300 Top {TOP_N} Cumulative Return (normalized to 1.0)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return (x)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_png = BASE_DIR / "ex01_output.png"
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"\n累计收益曲线已保存到：{out_png}")

    # --- 步骤 5：保存数据，供下一阶段（数据清洗）使用 ---
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / "hs300_daily.csv"
    data.to_csv(csv_path, index=False)
    print(f"行情数据已保存到：{csv_path}")

    print("\n=== 练习完成 ===")


if __name__ == "__main__":
    main()
