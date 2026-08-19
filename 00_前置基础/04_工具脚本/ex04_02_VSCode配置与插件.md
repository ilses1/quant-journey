# 02: VS Code 配置与量化开发环境

---

## 为什么选 VS Code？

量化代码是"脚本为主 + 偶尔工程化"的模式——既要在 Jupyter 里探索数据，又要写可复用的 `.py` 模块。VS Code 在这两者之间切换最流畅。

| 场景       | PyCharm | VS Code            | Jupyter |
| ---------- | ------- | ------------------ | ------- |
| 大型工程   | 强      | 中                 | 弱      |
| 脚本/探索  | 重      | 轻量               | 极佳    |
| 交互式运行 | 一般    | 好（内置 Jupyter） | 原生    |
| 插件生态   | 丰富    | 极丰富             | 有限    |
| 启动速度   | 慢      | 快                 | 快      |

---

## 安装

下载地址：[https://code.visualstudio.com/](https://code.visualstudio.com/)

安装后建议勾选：

- "将 Code 操作添加到 Windows 资源管理器文件上下文菜单"
- "将 Code 操作添加到 Windows 资源管理器目录上下文菜单"

这样在任意文件夹右键 → "通过 Code 打开"，就能用 VS Code 打开该文件夹。

---

## 必装插件

按 `Ctrl+Shift+X` 打开插件市场，搜索安装以下插件：

### Python 核心

| 插件                                    | 功能                                      |
| --------------------------------------- | ----------------------------------------- |
| **Python** (ms-python.python)           | Python 语法高亮、调试、IntelliSense、测试 |
| **Pylance** (ms-python.vscode-pylance)  | 快速代码补全、类型检查（比默认快很多）    |
| **Jupyter** (ms-toolsai.jupyter)        | 在 VS Code 内运行 `.ipynb` Notebook       |
| **Python Debugger** (ms-python.debugpy) | Python 调试器                             |

### 效率工具

| 插件                 | 功能                             |
| -------------------- | -------------------------------- |
| **GitLens**          | Git 增强：行级 blame、历史可视化 |
| **Git Graph**        | Git 提交历史可视化图表           |
| **Rainbow CSV**      | CSV 数据彩色分列高亮             |
| **Even Better TOML** | .toml 文件语法支持               |
| **vscode-icons**     | 文件图标美化，一眼看出文件类型   |

---

## Python 解释器选择 重要

VS Code 安装 Python 插件后，需要告诉它用哪个 Python：

1. `Ctrl+Shift+P` → 输入 `Python: Select Interpreter`
2. 选择你创建的 conda 环境，例如 `Python 3.10.xx ('my_quant': conda)`

选对解释器后：

- 代码补全才会索引你环境里安装的库
- 运行脚本时才会用你环境里的 Python
- 终端自动激活对应的 conda 环境

---

## 量化工作流：.py 脚本 vs .ipynb Notebook

### .py 脚本（策略代码、回测引擎）

- 最终策略代码的存放格式
- 可版本管理（Git diff 友好）
- 可被 import 复用
- 用 `# %%` 标记代码块，可以在 VS Code 里像 Notebook 一样逐块运行 # %%

# %% 是 VS Code 中 Python 交互式编程的“魔法指令”。

它被称为 “单元格标记”（Cell Marker）。只要在 Python 脚本（.py 文件）中加入 # %%，VS Code 就会自动把它识别为一个 Jupyter Notebook 风格的代码块。

```python
# %% 导入库
import pandas as pd
import numpy as np

# %% 加载数据
df = pd.read_parquet("stock_daily.parquet")

# %% 计算信号
df["signal"] = df["close"].rolling(20).mean()
```

每个 `# %%` 上方会出现 `Run Cell` 按钮，点击即可运行该代码块——兼具脚本的可维护性和 Notebook 的交互性。

### .ipynb（数据探索、可视化分析）

- 适合快速试错、画图、看分布
- 不适合长期维护（cell 执行顺序混乱是常见问题）
- 用 VS Code 内置 Jupyter 打开即可，无需浏览器

---

## 快捷键速记

| 操作               | 快捷键           |
| ------------------ | ---------------- |
| 命令面板           | `Ctrl+Shift+P`   |
| 打开终端           | `` Ctrl+` ``     |
| 搜索文件           | `Ctrl+P`         |
| 全局搜索           | `Ctrl+Shift+F`   |
| 运行当前 .py 文件  | `F5`（调试模式） |
| 运行 Notebook cell | `Ctrl+Enter`     |
| 代码格式化         | `Shift+Alt+F`    |

---

## 推荐 settings.json 配置

打开 `Ctrl+Shift+P` → `Preferences: Open User Settings (JSON)`，添加：

```json
{
  "python.defaultInterpreterPath": "C:\\Users\\你的用户名\\Anaconda3\\envs\\my_quant\\python.exe",
  "python.terminal.activateEnvironment": true,
  "editor.rulers": [100],
  "files.autoSave": "onFocusChange",
  "jupyter.askForKernelRestart": false,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

说明：

- `python.terminal.activateEnvironment`: 打开终端时自动激活 conda 环境
- `editor.rulers`: 在 100 列处画一条竖线（代码行宽提醒）
- `files.autoSave`: 切换文件/窗口时自动保存
- `formatOnSave`: 保存时自动格式化 Python 代码

---

## 终端集成

VS Code 内置终端默认是 PowerShell。按 `` Ctrl+` `` 打开：

1. 终端下拉菜单 → "选择默认配置文件"
2. 选 PowerShell 或 Command Prompt
3. VS Code 会自动激活 Python 插件指定的 conda 环境

运行脚本：

```powershell
# 终端里直接跑
python scripts/my_strategy.py
```

---

## 调试断点

量化的 bug 往往不是"语法错误"而是"逻辑错误"——信号算错了、时间对齐偏了、数据选错了。这时候 `print` 调试效率太低。

1. 在行号左侧点击，添加断点（红点）
2. 按 `F5` 启动调试
3. 程序运行到断点处暂停，左侧面板可查看所有变量值
4. `F10` 逐行执行，`F11` 进入函数内部

对一个 500 行的回测脚本，在关键位置（信号生成、订单执行、收益计算）打三个断点，几分钟就能定位问题。
