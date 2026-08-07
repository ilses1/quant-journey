# 03: Git 版本管理

---

## 为什么量化需要 Git？

量化交易的一个关键操作是**调参**。你今天把均线周期从 20 改成 21，明天改回 18，后天忘了三天前用的是 20 还是 22——没有版本管理，策略代码会变成一坨"不知道改了什么"的烂摊子。

```powershell
# 没有 Git 的日常：
策略_v1.py
策略_v1_改均线.py
策略_v1_改均线_修复bug.py
策略_v1_改均线_修复bug_最终版.py
策略_v1_改均线_修复bug_最终版_真的最终.py
```

> Git 让你每次改完都能保存一个"快照"，随时穿越回之前的任意版本。

---

## 安装

下载地址：[https://git-scm.com/download/win](https://git-scm.com/download/win)

安装过程一路默认即可。关键选择：
- 默认编辑器选 VS Code（不用 Vim——对新手不友好）
- "Adjusting your PATH environment" 选 **Git from the command line and also from 3rd-party software**

验证安装：
```powershell
git --version
```

### 首次配置

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

这两个信息会记录在每次提交里，方便后续追溯"谁改了什么"。

---

## 核心概念

```
工作区（Working Directory）    ← 你现在正在编辑的文件
    ↓ git add
暂存区（Staging Area）        ← 准备提交的文件"购物车"
    ↓ git commit
本地仓库（Local Repository）   ← 你的版本历史
    ↓ git push
远程仓库（Remote Repository）  ← GitHub / GitLab 上的备份
```

> 四个区域是 Git 的灵魂。`git add` 和 `git commit` 是两个独立步骤——这让你可以"挑哪些文件要提交、哪些先留着"。

---

## 日常操作

### 初始化仓库
```powershell
cd my_quant_project
git init                    # 把当前文件夹变成 Git 仓库
```

### 查看状态
```powershell
git status                  # 最常用的命令：看看改了什么
```

`git status` 的输出分三类：
- 红色（Untracked/Modified）：改了但还没 `git add`
- 绿色（Staged）：已 `git add`，准备提交
- 没有输出 = 工作区干净，和上次提交一样

### 三步提交流程
```powershell
git add my_strategy.py      # 第一步：把文件加入暂存区
git add .                   # 或一次性添加所有修改
git commit -m "修改均线参数为 (5, 20)"  # 第二步：提交并附上说明
git push origin main        # 第三步：推送到远程（如果有远程仓库）
```

### 查看历史
```powershell
git log --oneline -10       # 最近 10 条提交（一行一条，简洁）
git log --graph --oneline   # 带分支图的提交历史
git diff                    # 查看"改了但还没 add"的具体内容
git diff --staged           # 查看"已 add 但还没 commit"的内容
```

---

## 量化场景的 Git 操作

### 场景1：参数实验——新建分支

均线交叉策略，想试两组参数：(5, 20) 和 (10, 60)。不要在同一个文件里来回改！

```powershell
git checkout -b exp_ma5_20    # 新建并切换到分支
# 修改代码 → 测试回测 → 记录结果
git add .
git commit -m "实验: MA(5,20) 夏普=1.2"

git checkout main              # 回到主干
git checkout -b exp_ma10_60   # 新建另一个分支
# 修改代码 → 测试回测 → 记录结果
git add .
git commit -m "实验: MA(10,60) 夏普=0.9"

git checkout main              # 回到主干
```

每个分支独立记录一次实验，互不干扰。最后找到最好的参数，切回 `main` 合并：

```powershell
git merge exp_ma5_20           # 把 exp_ma5_20 的修改合并到 main
```

### 场景2：回测出 bug——回退版本
```powershell
git log --oneline              # 找到之前正常的版本号（如 abc1234）
git checkout abc1234 -- my_strategy.py   # 只回退这一个文件
# 或
git checkout abc1234           # 整个项目回退到那个版本（临时）
```

### 场景3：忘了改了什么
```powershell
git diff HEAD~1                # 对比"上一次提交"和"当前修改"
git show HEAD                  # 看最近一次提交改了哪些行
```

---

## .gitignore 文件

量化项目有些文件**绝对不能**提交到 Git：

```gitignore
# 行情数据（体积大、可重新下载、可能有版权问题）
data/
*.csv
*.parquet
*.h5
*.feather

# Jupyter Notebook 输出（每运行一次就变，污染 diff）
*.ipynb

# Python 缓存
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# 环境配置（敏感信息：API key、数据库密码等）
.env
*.token
secrets.yaml

# IDE 配置
.vscode/
.idea/

# Conda
envs/
```

> `.gitignore` 放在项目根目录。Git 会自动忽略其中列出的文件——它们不会出现在 `git status` 里，也不会被 `git add .` 误提交。

---

## 量化项目的分支策略

```
main                          # 稳定版本：经过充分回测的策略代码
  ├── dev                     # 开发分支：日常修改
  │   ├── exp_new_factor      # 实验：试新因子
  │   └── exp_parameter       # 实验：调参数
  └── release_v1.0            # 发布版本快照
```

日常开发在 `dev` 分支，具体实验再分叉。确认有效后才合回 `main`。

---

## 远程仓库（GitHub）

### 创建并关联远程仓库
```powershell
# 在 GitHub 上新建仓库（如 my_quant），然后：
git remote add origin https://github.com/你的用户名/my_quant.git
git push -u origin main
```

### 日常同步
```powershell
git pull origin main          # 拉取远程更新（先用这个，防止冲突）
git push origin main          # 推送本地更新
```

---

## 常见问题

### "我 commit 信息写错了"
```powershell
git commit --amend -m "正确的新信息"
```

### "我 git add 了一个不该 add 的文件"
```powershell
git reset HEAD 文件名          # 从暂存区移除，但保留本地修改
```

### "我改坏了一个文件，想回到最近一次提交的状态"
```powershell
git checkout -- 文件名          # 丢弃本地修改，恢复到最后一次提交的状态
```

### "merge 冲突了怎么办"
1. VS Code 会高亮冲突部分
2. 手动选择保留哪个版本的代码
3. `git add .` → `git commit` 完成合并

---

## 推荐学习资源

- [Pro Git 中文版](https://git-scm.com/book/zh/v2) — 最权威的免费 Git 教程
- [Learn Git Branching](https://learngitbranching.js.org/) — 交互式 Git 分支练习（强烈推荐）
- VS Code 内置 Git 图形界面（左侧 `Source Control` 面板）——可视化操作，降低学习曲线
