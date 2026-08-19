# 01: Miniconda 与虚拟环境

---

## 为什么选 Miniconda？

**核心原则：不修改系统 PATH，两套 Python 共存互不干扰，旧 Python 完全保留，不会被删除或覆盖。**

| 对比       |          完整 Anaconda           |     Miniconda     |
| ---------- | :------------------------------: | :---------------: |
| 安装包大小 |             ~600 MB              |      ~80 MB       |
| 预装包数量 |         250+ 科学计算包          | 仅 conda + Python |
| 占用磁盘   |              3 GB+               |      ~500 MB      |
| 启动速度   |                慢                |        快         |
| 功能       | 完全一样（conda 命令、环境管理） |     完全一样      |

> Miniconda = conda 包管理器 + 一个最小 Python。需要什么库自己按需 `conda install`，不浪费磁盘，不预装用不到的包。

---

## 1. 下载 Miniconda（Windows 64 位）

- **清华镜像（国内下载快，推荐）：**
  `https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Windows-x86_64.exe`

- **官网（备用）：**
  `https://docs.conda.io/en/latest/miniconda.html`

> 文件名：`Miniconda3-latest-Windows-x86_64.exe`

---

## 2. 安装步骤（关键选项！决定会不会和旧 Python 冲突）

### 1. 双击 exe → Next → I Agree

### 2. Install for 选择

```
Just Me (recommended)  ✅  — 仅当前用户，不要选 All Users
```

### 3. 安装路径

默认：`C:\Users\你的用户名\miniconda3`

> 路径**不要有中文、空格**。可以改到 D 盘，例如 `D:\miniconda3`。不要放到 `Program Files`。

### 4. Advanced Installation Options【最重要】

```
✅ Create shortcuts (supported packages only)      勾选（开始菜单出快捷方式）
❌ Add Miniconda3 to my PATH environment variable  【绝对不要勾选！】
❌ Register Miniconda3 as my default Python 3.x    【绝对不要勾选！】
✅ Clear the package cache upon completion          勾选
```

> **为什么不能勾选那两项？**
>
> 不勾选 PATH → 普通 cmd/PowerShell 依旧调用你原来的 Python
> 不勾选默认 Python → 系统不会把 `.py` 文件关联改到 Miniconda
> conda 只能通过开始菜单的专用 Prompt 启动 → 两套完全隔离

### 5. 点 Install 等待安装完成 → Finish

---

## 3. 如何启动 Miniconda

安装完后，Windows 开始菜单找到：

**`Anaconda Prompt (miniconda3)`**

> 以后所有 conda 命令，**全部在这里输入**。不要用普通 cmd、不要用 PowerShell。

### 验证安装成功

在 Anaconda Prompt 中输入：

```bash
conda --version
```

输出版本号即成功。

> 在普通 cmd 敲 `conda` 会提示"不是内部命令"——**这是正常现象，不是故障**，因为我们没有把它加到系统 PATH。

### 验证两套 Python 独立共存

**普通 cmd：**

```cmd
where python
```

→ 显示你原来安装的原生 Python 路径。

**Anaconda Prompt (miniconda3)：**

```bash
where python
```

→ 显示 `miniconda3` 内部的 `python.exe`，和上面路径不一样。

> 两条路径不同 = 两套隔离成功，旧 Python 毫发无损。

---

## 4. 配置国内镜像源（必做） 国内源 坏了 使用默认源 开科学上网

在 **Anaconda Prompt (miniconda3)** 中执行以下全部命令：

```bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge
conda config --set show_channel_urls yes
conda clean -i
```

验证是否配置成功：

```bash
conda config --show channels
```

> 清华镜像源能让 conda 下载速度从几 KB/s 提升到几 MB/s。量化后期装 TA-Lib 等需要编译 C 扩展的库时，镜像源是必备。

---

## 5. 创建量化专属环境

```bash
conda create -n quant python=3.10
```

创建失败 记得清理缓存

```bash
conda clean --tarballs --packages
```

输入 `y` 确认安装。Python 3.10 是当前量化生态兼容性最好的版本。

激活进入量化环境：

```bash
conda activate quant
```

> 提示符前面出现 `(quant)` 代表已进入量化独立环境。

### 安装量化核心库

```bash
# 难编译的库优先 conda 安装（TA-Lib 在 Windows 上用 conda 最省事）
conda install ta-lib numpy pandas matplotlib

# pip 安装其余量化库
pip install akshare backtrader pandas-ta yfinance scipy statsmodels
```

### 查看当前环境已安装的包

```bash
conda list
```

---

## 6. 日常使用规则（牢记）

| 场景                     | 操作                                                           |
| ------------------------ | -------------------------------------------------------------- |
| 用 Miniconda / 量化环境  | 打开「Anaconda Prompt (miniconda3)」→ `conda activate quant`   |
| 用原来旧的 Python        | 打开普通 cmd / PowerShell → 直接 `python`                      |
| VS Code 选解释器         | 手动选择 `miniconda3/envs/quant/python.exe`，不要选系统 Python |
| Jupyter 里 import 不到包 | 必须在激活 `quant` 环境的 Prompt 里启动 Jupyter                |

---

## 7. 虚拟环境操作速查

| 操作         | 命令                                  |
| ------------ | ------------------------------------- |
| 创建环境     | `conda create -n 环境名 python=3.10`  |
| 激活环境     | `conda activate 环境名`               |
| 退出环境     | `conda deactivate`                    |
| 查看所有环境 | `conda env list`                      |
| 删除环境     | `conda remove -n 环境名 --all`        |
| 查看已安装包 | `conda list`                          |
| 导出环境     | `conda env export > environment.yml`  |
| 复现环境     | `conda env create -f environment.yml` |

---

## 8. conda vs pip 使用原则

| 区别     | conda                              | pip                                 |
| -------- | ---------------------------------- | ----------------------------------- |
| 包来源   | conda 仓库（预编译二进制）         | PyPI（源码或 wheel）                |
| 能管什么 | Python 包 + 非 Python 依赖（C 库） | 只管理 Python 包                    |
| 典型场景 | TA-Lib、NumPy 等含 C 扩展的包      | 纯 Python 包（akshare、backtrader） |

> **原则：能用 conda 装的优先 conda，conda 装不了的再用 pip。**

---

## 常见问题排查

| 问题                                   | 原因                      | 解决                                                      |
| -------------------------------------- | ------------------------- | --------------------------------------------------------- |
| 普通 cmd 输入 `conda` 提示不是内部命令 | 没有加到 PATH（故意的）   | 必须用 Anaconda Prompt (miniconda3)                       |
| `import talib` 报错 DLL 找不到         | TA-Lib 的 C 库未正确安装  | 用 `conda install ta-lib` 重装（conda 会自动处理 C 依赖） |
| VS Code 终端里 `conda activate` 失败   | VS Code 默认用 PowerShell | 在 VS Code 设置里把终端 shell 路径指向 Anaconda Prompt    |
| 环境装坏了想重来                       | —                         | `conda remove -n quant --all` 删除重建                    |

> 如果你后续不想用 Miniconda，直接在 Windows 设置里卸载 Miniconda3——**不会碰你原来的 Python 半分**。

---

## 量化项目推荐目录结构

```
D:\my_quant_project\            # 项目根目录
├── environment.yml             # 环境依赖清单（可复现）
├── data\                       # 行情数据（.gitignore）
├── notebooks\                  # Jupyter 探索笔记
├── scripts\                    # 策略脚本
├── backtest\                   # 回测代码
└── utils\                      # 公共工具模块
```
