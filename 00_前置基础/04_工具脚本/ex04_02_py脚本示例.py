# %% 导入库
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# %% 生成模拟行情数据
# 用随机游走模拟一段日线收盘价，方便在没有真实数据时跑通流程
np.random.seed(42)
n = 250
dates = pd.bdate_range("2023-01-01", periods=n)
close = 100 + np.cumsum(np.random.randn(n))

df = pd.DataFrame({"close": close}, index=dates)
print(df.head())

# %% 计算信号：20 日均线
df["ma20"] = df["close"].rolling(20).mean()
df["signal"] = (df["close"] > df["ma20"]).astype(int)

# %% 画图：收盘价 + 均线
plt.figure(figsize=(10, 4))
plt.plot(df.index, df["close"], label="close")
plt.plot(df.index, df["ma20"], label="MA20")
plt.legend()
plt.title("Close vs MA20")
plt.show()

# %% 输出信号统计
print("信号为 1（收盘价在均线上方）的天数：", df["signal"].sum())
