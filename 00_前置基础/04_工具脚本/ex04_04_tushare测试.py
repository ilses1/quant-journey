# %% 导入 tushare 并初始化
import tushare as ts

# 把下面的字符串替换成你在 tushare.pro 个人主页复制的 token
ts.set_token("9429160674e99dc10175cdbe4649f7c7e7b509eaf6ffe5321967c73b")
pro = ts.pro_api()

# %% 测试：拉取贵州茅台（600519.SH）最近 5 个交易日日线行情
df = pro.daily(ts_code="600519.SH", start_date="20240101", end_date="20240131")
print("数据行数：", len(df))
print(df.head())
