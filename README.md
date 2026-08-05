# 量化交易学习仓库

## 目录结构

```
D:\testQunt\
│
├── 学习路线.md                   ← 学习路线总纲
├── README.md                     ← 本文件
├── .gitignore
│
├── 00_前置基础/
│   ├── 01_Python编程/            ← NumPy / Pandas / Matplotlib 练习
│   ├── 02_数学统计/              ← 线性代数、概率论、时间序列笔记
│   ├── 03_金融市场/              ← 交易机制、市场微观结构笔记
│   └── 04_工具脚本/              ← 环境配置、常用工具函数
│
├── 01_数据能力/
│   ├── 01_数据获取/              ← AKShare / Tushare / yfinance 接口封装
│   ├── 02_数据清洗/              ← 缺失值/异常值/复权处理脚本
│   └── 03_技术指标/              ← TA-Lib / 自定义指标计算
│
├── 02_策略入门/
│   ├── 01_择时策略/              ← 双均线、MACD、布林带、RSI 等策略
│   ├── 02_选股策略/              ← 多因子模型、因子 IC/IR 检验
│   └── 03_策略评价/              ← 夏普比、最大回撤、卡玛比等指标
│
├── 03_回测与风控/
│   ├── 01_回测框架/              ← Backtrader / VnPy / 自建回测引擎
│   ├── 02_仓位管理/              ← 凯利公式、风险平价、等权分配
│   └── 03_风险控制/              ← VaR、止损止盈、行业暴露监控
│
├── 04_进阶方向/
│   ├── 01_机器学习/              ← XGBoost / LSTM / 强化学习选股
│   ├── 02_组合优化/              ← Markowitz / Black-Litterman / HRP
│   ├── 03_期权衍生品/            ← B-S 模型、希腊字母、波动率交易
│   └── 04_另类数据/              ← 新闻舆情 / NLP / 卫星图像
│
├── 05_实战项目/
│   ├── 01_双均线策略/            ← 完整回测 + 参数优化 + 绩效分析
│   ├── 02_多因子选股/            ← 因子库 + IC 检验 + 组合构建 + 回测
│   └── 03_配对交易/              ← 协整检验 + 信号生成 + 回测
│
├── data/                         ← 本地行情数据（受 .gitignore 保护）
│   ├── stock_daily/              ← A 股日线
│   ├── stock_minute/             ← A 股分钟线
│   ├── fundamental/              ← 财务 / 估值数据
│   ├── futures/                  ← 期货数据
│   └── macro/                    ← 宏观经济数据
│
├── notebooks/                    ← Jupyter Notebook 探索笔记
│
└── utils/                        ← 公共工具函数（数据加载、图表等）
```

## 使用方式

1. 按 `00 -> 01 -> 02 -> 03 -> 04 -> 05` 的顺序学习
2. 每个子目录下新建 `.py` 脚本或 `.ipynb` notebook 做练习
3. 练习数据下载后统一存入 `data/` 目录
4. 每个阶段结束后，在 `05_实战项目/` 中完成一个完整项目作为检验

## 环境要求

```bash
# 核心依赖
pip install numpy pandas matplotlib seaborn scipy scikit-learn
# 金融数据
pip install akshare tushare yfinance baostock
# 回测 & 分析
pip install backtrader pyfolio statsmodels
# 技术指标（Windows 建议下载预编译 whl）
pip install ta-lib
# 机器学习
pip install xgboost lightgbm
```
