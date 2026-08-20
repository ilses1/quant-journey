"""
ex02: 数据管线 + 增量更新（数据能力 · 数据清洗）

对应《学习路线》2.2 的三条实操练习：
  1. 数据管线脚本：获取 → 清洗 → 存储为 Parquet
  2. 增量更新：只拉取最新交易日，追加而非全量覆盖
  3. 数据字典：见同目录 数据字典.md

本脚本分两部分：

  Part A · 全量管线
      读取上一阶段下载的原始 CSV → 清洗（utils/data_clean）→ 存为 Parquet。
      环境没装 pyarrow 时自动回退存 CSV，并提示安装命令。

  Part B · 增量更新
      读取已存储数据 → 找到最后交易日 → 只拉取该日之后的新数据（Baostock，
      socket 连接最稳）→ 「追加 + 去重 + 重存」，保证不产生重复行。
      网络不通时回退到一份人造"新数据"演示追加逻辑。

使用方法：python ex02_数据管线.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.data_clean import clean_daily, parse_daily  # noqa: E402

# 原始 CSV（上一阶段产出）与清洗后的存储文件
RAW_CSV = PROJECT_ROOT / "data" / "stock_daily" / "hs300_daily.csv"
STORE_PATH = PROJECT_ROOT / "data" / "stock_daily" / "hs300_daily_clean.parquet"


# ------------------------------------------------------------------
# 存储工具：Parquet 优先，缺 pyarrow 自动回退 CSV
# ------------------------------------------------------------------
def save_store(df: pd.DataFrame, path: Path) -> Path:
    """把 DataFrame 存为 Parquet；没装 pyarrow 时回退到同名 CSV。

    Parquet 相比 CSV 的优势（《学习路线》2.2 推荐）：
      - 读写更快（列式存储 + 压缩）
      - 体积更小（自动压缩）
      - 保留列类型（CSV 每次读都要重新推断 dtype）
    """
    if path.suffix == ".parquet":
        try:
            df.to_parquet(path, index=False)
            print(f"已存为 Parquet：{path}")
            return path
        except ImportError:
            print("[提示] 未安装 pyarrow，回退到 CSV。安装：pip install pyarrow")
    csv_path = path.with_suffix(".csv")
    df.to_csv(csv_path, index=False)
    print(f"已存为 CSV：{csv_path}")
    return csv_path


def load_store(path: Path) -> pd.DataFrame:
    """从存储文件读回数据，兼容 parquet 和 csv 两种格式。"""
    if path.suffix == ".parquet" and path.exists():
        return pd.read_parquet(path)
    csv_path = path.with_suffix(".csv")
    return pd.read_csv(csv_path)


# ------------------------------------------------------------------
# 增量更新
# ------------------------------------------------------------------
def fetch_new_rows(codes: list[str], since_date: str) -> pd.DataFrame:
    """拉取 since_date 起（含当天）的日线数据，用于增量更新。

    用 Baostock（socket 连接，免费无注册，最稳）。逐只股票拉取，
    返回和原始数据相同结构的 DataFrame [code, date, open, ..., volume]。
    注意：Baostock 的 start_date 是"含当天"的，会和存量最后一天重叠，
    这个重叠交给增量更新的去重逻辑兜底（见 incremental_update）。
    网络异常时抛异常，由调用方决定如何兜底。
    """
    import baostock as bs

    lg = bs.login()
    try:
        frames = []
        for code in codes:
            code = str(code)  # 防止 code 列被读成整数导致 startswith 报错
            prefix = "sh" if code.startswith("6") else "sz"
            bs_code = f"{prefix}.{code}"
            rs = bs.query_history_k_data_plus(
                bs_code, "date,open,high,low,close,volume",
                start_date=since_date, end_date="",  # end 留空=到最新
                frequency="d", adjustflag="2",        # 2=前复权
            )
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            if rows:
                tmp = pd.DataFrame(rows, columns=["date", "open", "high",
                                                  "low", "close", "volume"])
                tmp.insert(0, "code", code)
                frames.append(tmp)
        if not frames:
            return pd.DataFrame()
        new = pd.concat(frames, ignore_index=True)
        new["date"] = pd.to_datetime(new["date"])
        for col in ["open", "high", "low", "close", "volume"]:
            new[col] = pd.to_numeric(new[col], errors="coerce")
        return new
    finally:
        bs.logout()


def incremental_update(store_path: Path, new_data: pd.DataFrame) -> int:
    """把新数据追加进存量数据：合并 → 去重 → 重存，返回被去重的重复行数。

    这是增量更新的核心原则：只追加新数据，而不是全量覆盖；合并后用
    drop_duplicates(keep="last") 保证即使新数据与存量有重叠，也只保留最新。
    """
    existing = load_store(store_path)
    merged = pd.concat([existing, new_data], ignore_index=True)
    merged = parse_daily(merged)  # 重新排序，保证时间顺序正确
    before = len(merged)
    merged = merged.drop_duplicates(subset=["code", "date"], keep="last")
    save_store(merged, store_path)
    return before - len(merged)


# ------------------------------------------------------------------
# Part A：全量管线 获取(读原始) → 清洗 → 存储
# ------------------------------------------------------------------
def pipeline():
    print("=" * 70)
    print("Part A · 全量数据管线：获取 → 清洗 → 存储为 Parquet")
    print("=" * 70)

    # 1. 获取：这里直接读上一阶段(01_数据获取)下载好的原始 CSV
    #    真实工程中这一步是调 AKShare/Baostock 拉数据（见 01_数据获取 的 ex01）
    raw = pd.read_csv(RAW_CSV)
    print(f"① 获取原始数据：{len(raw)} 行")

    # 2. 清洗
    clean, report = clean_daily(raw)
    print(f"② 清洗完成，报告：{report}")

    # 3. 清洗后重算派生字段（return / nav），因为清洗可能改变了数据
    #    （比如填充了缺失价、剔除了异常行），派生的收益率要基于干净价重算
    clean = clean.sort_values(["code", "date"]).reset_index(drop=True)
    clean["return"] = clean.groupby("code")["close"].pct_change()
    clean["nav"] = clean.groupby("code")["return"].transform(
        lambda r: (1 + r.fillna(0)).cumprod()
    )
    print(f"③ 重算派生字段 return / nav")

    # 4. 存储
    saved = save_store(clean, STORE_PATH)
    print(f"④ 已存储：{saved}（{len(clean)} 行）\n")
    return saved


# ------------------------------------------------------------------
# Part B：增量更新
# ------------------------------------------------------------------
def incremental():
    print("=" * 70)
    print("Part B · 增量更新：只拉最新交易日，追加而非全量覆盖")
    print("=" * 70)

    store = load_store(STORE_PATH)
    store = parse_daily(store)
    last_date = store["date"].max()
    print(f"存量数据最后交易日：{last_date.date()}")

    # since_date 传"最后交易日"：Baostock start_date 含当天，会重复拉到
    # 最后一天，正好靠后面的去重（keep="last"）覆盖掉，无需精确算下一个交易日
    since = last_date.strftime("%Y-%m-%d")
    sample_codes = store["code"].unique()[:3].tolist()  # 拿 3 只演示即可

    print(f"尝试用 Baostock 拉取 {since} 之后的新数据（{len(sample_codes)} 只）...")
    try:
        new = fetch_new_rows(sample_codes, since)
    except Exception as e:
        new = pd.DataFrame()
        print(f"[提示] 网络请求失败（{type(e).__name__}: {e}），改用模拟数据演示")

    if new.empty:
        # 网络不通时，构造一份"假设今天收盘后拉到的最新交易日"数据，
        # 用于演示追加 + 去重逻辑（日期推后一天，仅作教学演示）
        new_date = last_date + pd.Timedelta(days=1)
        new = pd.DataFrame({
            "code": sample_codes,
            "date": [new_date] * len(sample_codes),
            "open": [10.0] * len(sample_codes),
            "high": [10.3] * len(sample_codes),
            "low": [9.9] * len(sample_codes),
            "close": [10.2] * len(sample_codes),
            "volume": [100000] * len(sample_codes),
        })
        print(f"模拟新增 {len(new)} 行（日期 {new_date.date()}），演示追加逻辑")

    print(f"新数据 {len(new)} 行：")
    print(new[["code", "date", "close"]].to_string(index=False))

    dup_removed = incremental_update(STORE_PATH, new)
    final = load_store(STORE_PATH)
    print(f"\n追加完成：去重 {dup_removed} 行重复，存量现共 {len(final)} 行")
    print(f"最新交易日：{parse_daily(final)['date'].max().date()}")


def main():
    pipeline()
    incremental()

    print("\n" + "=" * 70)
    print("管线完成。字段含义和数据来源见同目录 数据字典.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
