import matplotlib

- Matplotlib 是 Python 最主流的绘图库，用来把数据变成图表。

import numpy as np
import pandas as pd

- NumPy 是底层计算引擎，Pandas 是上层数据分析工具。

np.random.seed(42)

- np.random.seed(42) 是给随机数生成器一个固定的起点。以后随机数保持一致。 为了可复现

returns = np.random.normal(0.0003, 0.015, n)

- np.random.normal(loc, scale, size) 从正态分布中随机抽样
- loc=0.0003：日均收益率为 0.03%（约等于年化 7.5%） loc = location（位置），统计学术语，指概率分布的中心位置。
- scale=0.015：日收益率的标准差为 1.5%（约等于年化波动率 24%） scale = standard deviation（标准差），统计学术语，指概率分布的离散程度。 标准差 = √( 每个数据与均值的差的平方 的总和 ÷ 数据个数 )
- size=n：生成 n 个随机数，形状和日期数量一致

close_price = 10 \* np.cumprod(1 + returns) #返回的 一维数组

- np.cumprod 是累积乘积：第 i 天的价格 = 初始价 10 × (1+r₁) × (1+r₂) × ... × (1+rᵢ)
- 1 + returns NumPy 的广播机制——标量 1 自动应用到数组的每一个元素：

- 1 + returns 内部实际是：

- [1+0.005, 1+(-0.003), 1+0.02]

- = [1.005, 0.997, 1.02]

df = pd.DataFrame({
"date": dates, # 日期列
"open": open_price, # 开盘价
"high": high, # 最高价
"low": low, # 最低价
"close": close_price, # 收盘价（量化中最核心的价格字段）
"volume": volume, # 成交量
})

- 这是 Pandas 创建 DataFrame 最常用的方式之一
- 二维表格 类似 excel 每一个字典字段是一列
- date open high low close volume
- 0 2024-01-01 10.064 10.125 9.975 10.078 1880488
- 1 2024-01-02 10.032 10.114 10.028 10.060 1565689
- 2 2024-01-03 10.153 10.207 10.068 10.160 168148

df.set_index("date", inplace=True)

- 将 date 列设为行索引（index），并原地修改 DataFrame（inplace=True）
- DataFrame（inplace=True）如果是 False（默认），需要写成 df2 = df.set_index("date") 来接收结果，原来的 df 不动。

print(df.head(10))

- df.head(10) 取 DataFrame 的前 10 行，默认不写参数是前 5 行。就是快速瞟一眼数据长什么样，不用打印全部 391 行。

- df.head(3) - 前 3 行

- df.head() - 前 5 行（默认）

- df.tail(10) - 后 10 行

df["ma_5"] = df["close"].rolling(5).mean() # 5 日均线（周线

- 前 4 天（n-1 天）因为没有足够的 5 天数据，结果为 NaN
- rolling 是一个通用的滑动窗口机制，算均线只是它的一个用法。

- 它分两步：rolling(n) 帮你把数据切成一个个窗口，然后你想对这些窗口做什么都可以：

- df["close"].rolling(5).mean() - 均值 → 均线

- df["close"].rolling(5).max() - 最大值 → 5日最高

- df["close"].rolling(5).min() - 最小值 → 5日最低

- df["close"].rolling(5).std() - 标准差 → 布林带

- df["close"].rolling(5).sum() - 求和

- df["close"].rolling(5).apply(lambda x: x[-1] - x[0]) - 自定义：最新-最早

print(df[["close", "ma_5", "ma_20", "ma_60"]].tail(10))

- df[["close", "ma_5", "ma_20", "ma_60"]] 从整张表里挑出 4 列，然后 .tail(10) 取最后 10 行，print 打印出来。

- 关键细节：双中括号 [[...]] vs 单中括号 [...]：

- df["close"] - 单括号 → 返回一列，类型是 Series

- df[["close", "ma_5"]]- 双括号 → 返回多列，类型是 DataFrame

print(f"\n平均日收益率: {df['return'].mean():.6f}")

- f"..." : — f-string（格式化字符串）
- 花括号 {} :Python 表达式执行，结果自动嵌入字符串。
- \n : — 换行符 打印一个空行，让输出和前面的内容分开，视觉上更清晰。
- :.6f — 格式化保留 6 位小数
- f 表示浮点数的定点格式，6 保留 6 位小数。类似的：
- x = 0.0005334421
- print(f"{x:.2f}") - 0.00
- print(f"{x:.4f}") - 0.0005
- print(f"{x:.6f}") - 0.000533

print(f"年化波动率: {df['return'].std() \* np.sqrt(252):.4f}")

- 年方差 = 日方差 × 252
- 年标准差 = √(日方差 × 252) = 日标准差 × √252
- 原理：独立日收益率的方差可加 → 年方差 = 日方差 × 252 → 年标准差 = 日标准差 × √252

plot_df = df.loc["2025-01-01":"2025-06-30"].copy()

- loc 是按标签名定位数据，不是按位置号。
- 基本语法：df.loc[行标签, 列标签]
- 按日期取一行
- df.loc["2025-03-14"] - 3月14日那天的全部列
- 按日期取特定列
- df.loc["2025-03-14", "close"] - 只看收盘价
- 日期切片（左右都包含，和普通 Python 切片不同）
- df.loc["2025-01":"2025-03"] - 1月到3月全部数据 左右边界都包含
- .copy() 显式复制一份，避免后续修改影响到原始的 df（虽然这里不修改，但是好习惯）

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8),
gridspec_kw={"height_ratios": [3, 1]},
sharex=True) # 两个返回值：

- fig — 整张画布，管保存、标题等全局操作
- (ax1, ax2) — 上下两个子图对象，各自独立画东西
