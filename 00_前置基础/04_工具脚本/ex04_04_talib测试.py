# %% 导入库
import talib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

print("TA-Lib 版本：", talib.__version__)
print("TA-Lib 指标数量：", len(talib.get_functions()))

# %% 生成模拟行情数据
# 用随机游走模拟一段日线数据，方便在没有真实数据时跑通流程
np.random.seed(42)
n = 250
dates = pd.bdate_range("2023-01-01", periods=n)
close = 100 + np.cumsum(np.random.randn(n))
high = close + np.abs(np.random.randn(n))
low = close - np.abs(np.random.randn(n))
open_ = np.roll(close, 1)
open_[0] = close[0]

df = pd.DataFrame(
    {"open": open_, "high": high, "low": low, "close": close}, index=dates
)
print(df.head())

# %% 测试常用指标
# 均线 MA（5 / 20）
df["ma5"] = talib.SMA(df["close"], timeperiod=5)
df["ma20"] = talib.SMA(df["close"], timeperiod=20)

# RSI 相对强弱指标
df["rsi"] = talib.RSI(df["close"], timeperiod=14)

# MACD
df["macd"], df["macd_signal"], df["macd_hist"] = talib.MACD(
    df["close"], fastperiod=12, slowperiod=26, signalperiod=9
)

# 布林带 BOLL
df["boll_up"], df["boll_mid"], df["boll_low"] = talib.BBANDS(
    df["close"], timeperiod=20, nbdevup=2, nbdevdn=2
)

# ATR 平均真实波幅
df["atr"] = talib.ATR(df["high"], df["low"], df["close"], timeperiod=14)

print(df[["ma5", "ma20", "rsi", "macd", "atr"]].tail())

# %% 画图验证：收盘价 + MA20 + 布林带
plt.figure(figsize=(12, 6))
plt.plot(df.index, df["close"], label="close", color="black")
plt.plot(df.index, df["ma20"], label="MA20", color="orange")
plt.plot(df.index, df["boll_up"], label="BOLL up", color="blue", linestyle="--")
plt.plot(df.index, df["boll_low"], label="BOLL low", color="blue", linestyle="--")
plt.fill_between(df.index, df["boll_up"], df["boll_low"], alpha=0.1, color="blue")
plt.legend()
plt.title("Close / MA20 / Bollinger Bands")
plt.show()

# %% 输出 RSI 统计
print("RSI 最新值：", df["rsi"].iloc[-1])
print("RSI > 70（超买）天数：", (df["rsi"] > 70).sum())
print("RSI < 30（超卖）天数：", (df["rsi"] < 30).sum())
print("\nTA-Lib 测试通过！")
