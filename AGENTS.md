# AGENTS.md

## 项目性质

量化交易自学仓库，**不是可构建/测试的软件项目**。没有 package.json、setup.py、CI 等工程化配置。

## 关键文件

- `学习路线.md` — 完整学习路线总纲，用户提问时优先参考
- `README.md` — 目录结构和使用说明

## 目录约定

- 学习阶段按 `00~05` 编号，内部子目录按 `01~0N` 编号
- 代码放在对应阶段的子目录下，用 `.py` 脚本（非 `.ipynb`，notebook 已被 `.gitignore` 排除）
- `utils/` — 跨阶段复用的公共工具模块（已有 `__init__.py`）
- `data/` — 所有行情数据，内容被 `.gitignore` 完全排除
- `notebooks/` — 探索性分析用（需用户明确要求 notebook 格式时才放置 `.ipynb`）

## 环境

- 平台：Windows（PowerShell 5.1）
- Python 生态为主，核心依赖见 `README.md`
