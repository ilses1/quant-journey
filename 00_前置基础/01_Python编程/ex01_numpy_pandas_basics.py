"""
ex01: NumPy / Pandas / Matplotlib 基础练习
目标：用 Pandas 读取/生成一份股票日线数据，计算均线并可视化

使用方法: 进入当前目录，运行 python ex01_numpy_pandas_basics.py 即可
"""

# ------------------------------------------------------------------
# 0. 导入与后端设置
# ------------------------------------------------------------------
import matplotlib 
# Matplotlib 是 Python 最主流的绘图库，用来把数据变成图表。
# 设置 matplotlib 后端为 Agg（Anti-Grain Geometry）
# Agg 是一个非交互式渲染引擎，只在内存中画图然后保存到文件
# 好处：不需要 GUI 窗口，服务器/命令行环境下也能运行，plt.show() 不会阻塞
matplotlib.use("Agg")

import numpy as np
# NumPy：科学计算核心库，提供 ndarray（多维数组）和向量化运算
# 量化中用于批量计算收益率、生成随机数、矩阵运算等

import pandas as pd
# Pandas：数据分析核心库，提供 Series（一维）和 DataFrame（二维表格）
# 量化中几乎所有时序行情（OHLCV）的处理都靠它
# NumPy 是底层计算引擎，Pandas 是上层数据分析工具。
import matplotlib.pyplot as plt
# Matplotlib 的 pyplot 模块，提供类似 MATLAB 的绘图 API
# 用于画净值曲线、K 线图、分布图等

import matplotlib.dates as mdates
# mdates 专门处理日期坐标轴，比如设置刻度间隔、格式化日期显示

# ------------------------------------------------------------------
# 1. 生成模拟日线数据（等价于后来从 AKShare 拉取的真实数据）
#    真实场景中这部分换成 akshare.stock_zh_a_hist() 即可
# ------------------------------------------------------------------

# 固定随机种子，保证每次运行生成的"随机数"完全一样，方便复现和调试
np.random.seed(42)
# np.random.seed(42) 是给随机数生成器一个固定的起点。以后随机数保持一致。 为了可复现
# 理解一个反直觉的事实：计算机不会"随机"，它只是在用数学公式模拟随机。这个公式每次从同一个起点开始算，结果就一模一样。

# pd.date_range 生成一个日期序列
# "2024-01-01" ~ "2025-06-30" 按交易日历生成工作日（freq="B"，B = Business day）
# 这会自动跳过周六周日，大约 1 年半产生约 390 个交易日
# "B"	工作日（跳过周末）	~252
# "D"	日历日	365
dates = pd.date_range("2024-01-01", "2025-06-30", freq="B")

# 记录总共多少个交易日
n = len(dates)

# np.random.normal(loc, scale, size) 从正态分布中随机抽样
# loc=0.0003：日均收益率为 0.03%（约等于年化 7.5%）  loc = location（位置），统计学术语，指概率分布的中心位置。
# scale=0.015：日收益率的标准差为 1.5%（约等于年化波动率 24%）  scale = standard deviation（标准差），统计学术语，指概率分布的离散程度。  标准差 = √( 每个数据与均值的差的平方 的总和 ÷ 数据个数 )
# size=n：生成 n 个随机数，形状和日期数量一致
returns = np.random.normal(0.0003, 0.015, n)

# 价格 = 初始价格 × 每日复利累积
# 1 + returns 将收益率变成"增长因子"（如 1.02 表示涨了 2%）
# np.cumprod 是累积乘积：第 i 天的价格 = 初始价 10 × (1+r₁) × (1+r₂) × ... × (1+rᵢ)
# 这模拟了股价的随机游走过程
close_price = 10 * np.cumprod(1 + returns)  #返回的 一维数组

# 1 + returns NumPy 的广播机制——标量 1 自动应用到数组的每一个元素：
# 1 + returns 内部实际是：
# [1+0.005, 1+(-0.003), 1+0.02]
# = [1.005, 0.997, 1.02]


# 模拟最高价：在收盘价的基础上向上浮动
# np.abs 取绝对值，保证浮动量始终为正（最高价 > 收盘价）
# 浮动比例 ~ N(0, 1%)，最高价比收盘价高约 0~1%
high = close_price * (1 + np.abs(np.random.normal(0, 0.01, n)))

# 模拟最低价：在收盘价的基础上向下浮动（1 - 正值 = 低于收盘价）
low = close_price * (1 - np.abs(np.random.normal(0, 0.01, n)))

# 模拟开盘价：在最低价和最高价之间随机取值
# np.random.uniform(0, 1, n) 生成 n 个 [0,1) 之间的随机数
# low + ratio × (high - low) 将开盘价均匀分布在 [low, high] 区间内
open_price = low + np.random.uniform(0, 1, n) * (high - low)

# 模拟成交量：在 10 万到 200 万之间均匀随机取整数
# np.random.randint(low, high, size) 生成 [low, high) 区间的随机整数
volume = np.random.randint(100_000, 2_000_000, n)

# 用字典构建 DataFrame，每个 key 是一列，value 是对应的数组
# 这是 Pandas 创建 DataFrame 最常用的方式之一
# 二维表格  类似 excel 每一个字典字段是一列
#        date       open       high        low      close   volume
# 0  2024-01-01  10.064   10.125   9.975   10.078  1880488
# 1  2024-01-02  10.032   10.114   10.028  10.060  1565689
# 2  2024-01-03  10.153   10.207   10.068  10.160   168148

df = pd.DataFrame({
    "date":  dates,       # 日期列
    "open":  open_price,  # 开盘价
    "high":  high,        # 最高价
    "low":   low,         # 最低价
    "close": close_price, # 收盘价（量化中最核心的价格字段）
    "volume": volume,     # 成交量
})

# 将 date 列设为行索引（index），并原地修改 DataFrame（inplace=True）
#  DataFrame（inplace=True）如果是 False（默认），需要写成 df2 = df.set_index("date") 来接收结果，原来的 df 不动。
# 设置日期索引后，可以用 df.loc["2025-03"] 按日期切片，这对时序数据非常方便  设置索引
df.set_index("date", inplace=True)

# 打印前 10 行，快速查看数据长什么样
print("=== 数据概览 ===")
print(df.head(10))
# df.head(10) 取 DataFrame 的前 10 行，默认不写参数是前 5 行。就是快速瞟一眼数据长什么样，不用打印全部 391 行。
# df.head(3)   # 前 3 行
# df.head()    # 前 5 行（默认）
# df.tail(10)  # 后 10 行

# df.shape 返回 (行数, 列数)，是一个元组
# df.index[0] 和 df.index[-1] 分别是第一个和最后一个索引（即日期）
# .date() 把 Timestamp 截断到日期部分（去掉了时分秒）
# 数据形状: (391, 5), 日期范围: 2024-01-01 ~ 2025-06-30
print(f"\n数据形状: {df.shape}, 日期范围: {df.index[0].date()} ~ {df.index[-1].date()}")

# ------------------------------------------------------------------
# 2. 用 Pandas 计算移动均线（Moving Average）
# ------------------------------------------------------------------

# rolling(5) 创建一个长度为 5 的滑动窗口
# .mean() 对窗口内的数据取均值
# 前 4 天（n-1 天）因为没有足够的 5 天数据，结果为 NaN
# 这是量化中最基础的技术指标，用于平滑价格、识别趋势方向
# df["新列名"] = 值 这个语法，如果列名不存在就自动创建，存在就覆盖。Pandas 里直接按字符串起名赋值就行，不需要预先声明。
# 对 df 新增三列：5 日均线（周线）、20 日均线（月线）、60 日均线（季线）
# rolling 是一个通用的滑动窗口机制，算均线只是它的一个用法。
# 它分两步：rolling(n) 帮你把数据切成一个个窗口，然后你想对这些窗口做什么都可以：
# df["close"].rolling(5).mean()   # 均值 → 均线
# df["close"].rolling(5).max()    # 最大值 → 5日最高
# df["close"].rolling(5).min()    # 最小值 → 5日最低
# df["close"].rolling(5).std()    # 标准差 → 布林带
# df["close"].rolling(5).sum()    # 求和
# df["close"].rolling(5).apply(lambda x: x[-1] - x[0])  # 自定义：最新-最早
df["ma_5"] = df["close"].rolling(5).mean()    # 5 日均线（周线）
df["ma_20"] = df["close"].rolling(20).mean()  # 20 日均线（月线）
df["ma_60"] = df["close"].rolling(60).mean()  # 60 日均线（季线）

# 用双中括号 [[...]] 选出多列，.tail(10) 取最后 10 行
print("\n=== 带均线的数据 ===")
# df[["close", "ma_5", "ma_20", "ma_60"]] 从整张表里挑出 4 列，然后 .tail(10) 取最后 10 行，print 打印出来。
# 关键细节：双中括号 [[...]] vs 单中括号 [...]：
# df["close"]                          # 单括号 → 返回一列，类型是 Series
# df[["close", "ma_5"]]                # 双括号 → 返回多列，类型是 DataFrame
print(df[["close", "ma_5", "ma_20", "ma_60"]].tail(10))

# ------------------------------------------------------------------
# 3. 计算日收益率（关键指标）
# ------------------------------------------------------------------

# pct_change() 计算每行相对于前一行的百分比变化
# 公式：return_t = (close_t - close_{t-1}) / close_{t-1}
# 第一行因为没有前一天的数据，结果为 NaN
df["return"] = df["close"].pct_change()

# .mean() 计算全序列的平均日收益率
# .6f 格式化：保留 6 位小数
# f"..." : — f-string（格式化字符串）
# 花括号 {} :Python 表达式执行，结果自动嵌入字符串。
# \n : — 换行符 打印一个空行，让输出和前面的内容分开，视觉上更清晰。
# :.6f — 格式化保留 6 位小数
# f 表示浮点数的定点格式，6 保留 6 位小数。类似的：
# x = 0.0005334421
# print(f"{x:.2f}")   # 0.00
# print(f"{x:.4f}")   # 0.0005
# print(f"{x:.6f}")   # 0.000533
print(f"\n平均日收益率: {df['return'].mean():.6f}")

# .std() 计算日收益率的标准差（即日波动率）
# 乘以 √252 得到年化波动率（假设一年有 252 个交易日）
# 年方差 = 日方差 × 252
# 年标准差 = √(日方差 × 252) = 日标准差 × √252
# 原理：独立日收益率的方差可加 → 年方差 = 日方差 × 252 → 年标准差 = 日标准差 × √252
print(f"年化波动率: {df['return'].std() * np.sqrt(252):.4f}")

# ------------------------------------------------------------------
# 4. 可视化：价格曲线 + 均线 + 成交量副图
# ------------------------------------------------------------------

# df.loc["2025-01-01":"2025-06-30"] 按日期索引切片，只取 2025 年上半年的数据
# loc 是按标签名定位数据，不是按位置号。
# 基本语法：df.loc[行标签, 列标签]
# 按日期取一行
# df.loc["2025-03-14"]                    # 3月14日那天的全部列
# 按日期取特定列
# df.loc["2025-03-14", "close"]           # 只看收盘价
# 日期切片（左右都包含，和普通 Python 切片不同）
# df.loc["2025-01":"2025-03"]             # 1月到3月全部数据  左右边界都包含
# .copy() 显式复制一份，避免后续修改影响到原始的 df（虽然这里不修改，但是好习惯）
plot_df = df.loc["2025-01-01":"2025-06-30"].copy()

# plt.subplots(2, 1) 创建 2 行 1 列的子图网格
# ax1 上面的图（价格+均线），ax2 下面的图（成交量）
# figsize=(14, 8) 整张图的宽 14 英寸、高 8 英寸
# gridspec_kw={"height_ratios": [3, 1]} 设置上下子图高度比例为 3:1
# sharex=True 让上下两个子图共享 X 轴（放大/缩小时同步）
# 两个返回值：
# - fig — 整张画布，管保存、标题等全局操作
# - (ax1, ax2) — 上下两个子图对象，各自独立画东西
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8),
                                gridspec_kw={"height_ratios": [3, 1]},
                                sharex=True)

# --- 上图：收盘价 + 三条均线 ---
# ax1.plot(x, y, ...) 画折线图
# plot() 就是给一串 (x, y) 坐标点，按顺序连线。它不存数据，
# color 线条颜色, linewidth 线宽, label 图例标签
ax1.plot(plot_df.index, plot_df["close"], color="black", linewidth=0.8, label="Close")
ax1.plot(plot_df.index, plot_df["ma_5"],  color="red",   linewidth=0.8, label="MA5")
ax1.plot(plot_df.index, plot_df["ma_20"], color="blue",  linewidth=0.8, label="MA20")
ax1.plot(plot_df.index, plot_df["ma_60"], color="green", linewidth=0.8, label="MA60")

# 设置 Y 轴标签  只是显示文字
ax1.set_ylabel("Price")

# 显示图例，loc="upper left" 放到左上角
ax1.legend(loc="upper left")

# 设置标题
ax1.set_title("Stock Price & Moving Averages")

# 显示网格线，alpha=0.3 半透明，不喧宾夺主
#  True — 打开网格线
# - alpha=0.3 — 透明度 30%
ax1.grid(True, alpha=0.3)

# --- 下图：成交量柱状图 ---
# ax2.bar(x, y, ...) 画柱状图
# alpha=0.6 柱体半透明，width=0.8 柱子宽度
ax2.bar(plot_df.index, plot_df["volume"], color="gray", alpha=0.6, width=0.8)
ax2.set_ylabel("Volume")
ax2.set_xlabel("Date")
ax2.grid(True, alpha=0.3)

# --- X 轴日期格式化 ---
# MonthLocator() 每月显示一个刻度，避免日期太密挤在一起
ax1.xaxis.set_major_locator(mdates.MonthLocator())
# DateFormatter("%Y-%m") 把日期显示为 "2025-01" 这种年月格式
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
# autofmt_xdate() 自动旋转日期标签角度，防止长标签重叠
fig.autofmt_xdate()

# tight_layout() 自动调整子图之间的间距，避免标签被裁剪
plt.tight_layout()

# 保存图片到本地文件
# dpi=150 分辨率 150 像素/英寸，图片清晰且文件不太大
# plt.savefig() 保存的是当前活动的那张画布。当前代码里只有一张 fig，
plt.savefig("./ex01_output1.png", dpi=150)

# 关闭所有图形，释放内存
plt.close()

print("\n图片已保存到 ex01_output.png")
print("=== 练习完成 ===")
