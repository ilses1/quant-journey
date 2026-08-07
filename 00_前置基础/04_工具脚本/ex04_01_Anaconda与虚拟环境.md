# 01: Anaconda 与虚拟环境

---

## 为什么需要 Anaconda？

量化交易涉及大量第三方库（NumPy、Pandas、TA-Lib、Backtrader 等），不同项目可能需要不同版本的 Python 或依赖库。直接在系统 Python 里装，迟早版本冲突。

**Anaconda 解决两个问题：**

| 问题 | 解决方案 |
|------|----------|
| Python 版本管理 | conda 可以安装并切换不同 Python 版本 |
| 依赖包隔离 | 每个项目有独立的虚拟环境，互不干扰 |

> 类比：Anaconda 就像给每个项目分配一个独立的"工具箱"，项目 A 用 Python 3.10 + NumPy 1.x，项目 B 用 Python 3.12 + NumPy 2.x，各自安好。

---

## 安装

> 以下为教程说明，不执行实际安装命令。

**Windows 安装包下载**：[https://www.anaconda.com/download](https://www.anaconda.com/download)

安装时务必勾选两个选项：
- `Add Anaconda to my PATH environment variable`
- `Register Anaconda as my default Python`

如果不勾 PATH，后续终端里无法直接使用 `conda` 命令。

**验证安装**（安装后）：
```powershell
conda --version
python --version
```

---

## 核心概念

```
Anaconda（发行版）
 ├── conda（包管理器 + 环境管理器）
 ├── base 环境（默认环境，Python + 常用科学计算包）
 ├── my_quant 环境（自定义环境，可以指定 Python 版本和依赖）
 └── another_project 环境（另一个独立环境）
```

---

## 虚拟环境操作

### 创建环境
```powershell
# 创建名为 "my_quant" 的环境，指定 Python 3.10
conda create -n my_quant python=3.10
```

### 激活/进入环境
```powershell
# Windows
conda activate my_quant

# 成功后终端前缀会变成 (my_quant) >
```

### 查看所有环境
```powershell
conda env list
```

### 查看当前环境下已安装的包
```powershell
conda list
# 或
pip list
```

### 退出环境
```powershell
conda deactivate
```

### 删除环境
```powershell
conda remove -n my_quant --all
```

### 导出/复现环境（重要）
```powershell
# 导出当前环境的依赖清单
conda env export > environment.yml

# 在另一台机器上，用这个文件复现一模一样的环境
conda env create -f environment.yml
```

---

## conda vs pip

| 区别 | conda | pip |
|------|-------|-----|
| 包的来源 | Anaconda 仓库（预编译二进制） | PyPI（源码或 wheel） |
| 能管理什么 | Python 包 + 非 Python 依赖（如 C 库） | 只管理 Python 包 |
| 虚拟环境 | 内置 | 需要 virtualenv/venv |
| 安装速度 | 较慢（仓库在国外） | 较快（可换国内镜像） |

**使用建议：**

1. 用 `conda` 创建和管理环境
2. 环境内用 `pip` 安装包（配合国内镜像更快）
3. `conda` 装不了的包（如 TA-Lib 的某些版本），用 `pip` 补装

---

## 国内镜像加速

conda 和 pip 默认从国外服务器下载，速度很慢。配置国内镜像：

### pip 清华镜像
```powershell
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### conda 清华镜像
```powershell
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --set show_channel_urls yes
```

恢复默认：
```powershell
conda config --remove-key channels
```

---

## 量化项目推荐环境结构

```
my_quant/                      # 项目根目录
├── environment.yml            # 环境依赖清单（可复现）
├── data/                      # 行情数据（.gitignore）
├── notebooks/                 # Jupyter 探索笔记
├── scripts/                   # 策略脚本
├── backtest/                  # 回测代码
└── utils/                     # 公共工具模块
```

团队协作时，`environment.yml` 是必备文件——别人拿到你的代码，一条命令就能复现你的环境。
