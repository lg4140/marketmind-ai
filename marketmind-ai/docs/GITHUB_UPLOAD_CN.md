# MarketMind AI v1.2 — GitHub 上传操作指南（中文版）

## 你要上传什么？

使用 **`MarketMind_AI_GitHub_Ready_v1_2.zip` 解压后 `marketmind-ai/` 文件夹中的全部内容**，而不是把整个 ZIP 文件当成 GitHub 项目上传。仓库根目录应该能直接看到 `README.md`、`LICENSE`、`.gitignore`、`src/`、`agents/` 等。

这是经过公开版整理的 v1.2：保留了完整可运行源码、测试、100 条**待测** LLM 用例、产品案例文档、Notebook 和模拟图表；剔除了重复旧文档、历史 DOCX、旧 Notebook 和本地运行缓存。项目全部行情数据为 synthetic，不包含原始私有市场数据。**上传前仍请核查 LICENSE 的作者署名是否正确、未来新增文件是否涉及保密资料。**

### 方式 A：GitHub 网页上传（无需命令行）

1. 打开 https://github.com/new ，新建仓库。
2. Repository name 推荐：`marketmind-ai`；Description：`Task-verified AI research copilot for synthetic limit order book analytics | Python, typed tools, evidence-gated workflows`。
3. 建议先选 **Private**，上传检查后再转 Public；不要勾选 GitHub 自动新建 README / .gitignore / License，因为压缩包内已有。
4. 解压 ZIP，打开 `marketmind-ai` 文件夹。仓库新建后点击 `uploading an existing file`，或者在仓库页面选择 **Add file → Upload files**。
5. 将 `marketmind-ai` **内部的文件和子文件夹**拖入上传区域，保留相对目录结构。尤其检查 `.github/workflows/ci.yml`、`.gitignore`、`.env.example` 三个隐藏目录/文件（macOS Finder 可按 `Command + Shift + .` 显示隐藏项）。如网页无法正常保留目录或隐藏文件，用方式 B。
6. 点击 **Commit changes**，回到仓库首页，确认自动显示 README 与项目图表。
7. 去 **Actions** 查看测试工作流结果；若需要公开，在 Settings → General → Danger Zone → Change repository visibility 重新检查后操作。

注意：GitHub 网页一次最多上传 **100 个文件**；本公开版已控制在该限制之下。若出现网页上传问题，推荐使用 Git 命令或 GitHub Desktop。

### 方式 B：macOS / Windows Git 命令上传（推荐，目录最完整）

先登录 GitHub，创建一个**空仓库** `marketmind-ai`，不要勾选 README、License 或 .gitignore。

解压后在终端中进入 `marketmind-ai` 项目目录，然后运行：

```bash
git init -b main
git status
git add .
git status --short
git commit -m "Initial release: MarketMind AI v1.2"
git remote add origin https://github.com/YOUR_USERNAME/marketmind-ai.git
git push -u origin main
```

把 `YOUR_USERNAME` 换成你的 GitHub 用户名。第一行 `git init -b main` 需要 Git 2.28+，旧版 Git 可以使用 `git init` 和 `git branch -M main`。

**macOS 解压示例：** 将 ZIP 解压到 Downloads，然后打开 Terminal：

```bash
cd ~/Downloads/marketmind-ai
```

如果之前已有 origin：

```bash
git remote set-url origin https://github.com/YOUR_USERNAME/marketmind-ai.git
git push -u origin main
```

首次推送可能要求登录或使用个人访问令牌；GitHub 不支持使用账户密码直接进行 Git HTTPS 认证。也可以通过 GitHub Desktop 图形界面完成首次发布。

### 上传后检查

- 根目录存在 `README.md`、`LICENSE`、`.gitignore`、`.env.example`、`.github/workflows/ci.yml`。
- 点击 `src/`、`agents/`、`verification/`、`tools/`、`evaluation/`，都能看到实际源码。
- `figures/v1_2_synthetic_demo.png` 能在 README 中加载。
- GitHub Actions 完成之后查看测试结果，而不是预设必定通过。
- 没有 `OPENAI_API_KEY` 实际密钥、`.env`、`reports/generated` 运行内容、`.sqlite3` / `.db`、原始 CSV、含保密信息的文件。
- README 明确说明：**62 项本地自动测试通过；45 项离线评测通过；100 个 LLM 用例为待测计划，不是 100% Agent 准确率**。

### 如何在本地验证项目

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m evaluation.run_evals
python -m evaluation.validate_llm_cases
python run_demo.py --mode offline
```

可选 UI：`python -m pip install -r requirements-ui.txt`，然后 `streamlit run app/streamlit_app.py`。真实 LLM 调用必须由你自己安全配置 `OPENAI_API_KEY`，可能收费，不属于离线验证。

### 常见问题

**为什么不直接上传完整 v1.2 旧 ZIP？** 原包包含多版本重复说明、旧 Word 和 Notebook。对于招聘作品集，GitHub 公开版应突出最新源码、PRD、可复现测试和代表性结果，减少旧版文件和重复内容。

**GitHub 网页能直接自动解压 ZIP 吗？** 不能把 ZIP 作为源码仓库的代替品。请先在本地解压，再上传里面的文件；否则访客只会看到一个 ZIP 下载文件。

**需要付费 API 才能展示吗？** 不需要。离线 Demo、Notebook、测试、产品文档均可展示。实时 LLM 工具调用是可选能力，需要另外配置和验证。

**可以声称自己实现了实际交易或赚钱了吗？** 不可以。本项目只读且全为合成数据，未进行真实股票预测或交易。
