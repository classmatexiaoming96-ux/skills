---
name: github-trending-monitor
description: Use when running a daily GitHub Trending monitor for newly created AI, LLM, coding-agent, or developer-tool repositories that need source-level analysis and GitHub Pages publication.
triggers:
  - "GitHub Trending 每日监控"
  - "daily github trending monitor"
  - "source-level GitHub repo analysis"
  - "AI agent trending 项目分析"
---

# GitHub Trending 每日监控

## When to invoke this skill

在以下场景使用本 skill：

- 需要每天筛选 GitHub 新增热门 AI / LLM / coding-agent / developer-tool 项目。
- 需要对候选项目做源码级深度阅读，而不是只基于 README 写摘要。
- 需要把项目分析生成 GitHub Pages HTML 页面，并追加到聚合入口页。
- 需要严格复用 `github-trending-page-template` 的模板、占位符和质量门禁。

不要在只需要简单仓库列表、stars 排名截图、README 摘要或一次性人工选题时使用。

## 前置依赖检查

每次执行前先检查：

```bash
git --version
curl --version
test -n "$GITHUB_PAT" && echo "GITHUB_PAT ok" || echo "GITHUB_PAT missing"
curl -sS --max-time 10 https://api.github.com/rate_limit >/dev/null
```

- `git`：用于克隆候选项目、提交生成页面、推送 GitHub Pages 仓库。
- `curl`：用于 GitHub Search API 查询。
- `GITHUB_PAT`：必须来自环境变量 `$GITHUB_PAT`，不要假设任何固定 `.env` 路径。需要时让用户先在当前 shell 中导出。
- 网络代理：如果运行环境访问 GitHub 不稳定，先配置 `https_proxy` / `http_proxy`，并用 `curl https://api.github.com/rate_limit` 验证。

## 引用依赖

严格依赖并优先读取 skill `github-trending-page-template`：

- `templates/main-page.html`：主页面模板
- `templates/sub-page.html`：子页面模板
- `templates/layout-shell.css`：CSS shell
- `scripts/quality_gate.py`：质量门禁
- `docs/placeholder-map.md`：占位符说明

执行时把该 skill 安装目录记为 `<template-skill-dir>`，把 GitHub Pages 仓库记为 `<repo-path>`，把临时源码目录记为 `<workdir>/sources/<project>`，把线上站点根 URL 记为 `<site-base-url>`。

## 任务流程

### Step 1: 拉取候选仓库

查询最近 5 天创建、stars 大于 250、主题与 AI / LLM / coding agent / developer tools 相关的候选仓库：

```bash
DATE=$(date -ud '5 days ago' +%Y-%m-%d)
curl -sS -H "Authorization: token $GITHUB_PAT" \
  "https://api.github.com/search/repositories?q=created:>=$DATE+stars:>250+(agent+OR+coding+OR+code+assistant+OR+AI+agent+OR+copilot+OR+autonomous+agent+OR+LLM+OR+codellm)&sort=stars&order=desc&per_page=8"
```

记录每个候选项目的 `full_name`、stars、created_at、updated_at、description、language、html_url。

### Step 2: 过滤已有项目

进入 `<repo-path>`，读取 `index.html` 中已有项目入口，排除已经收录的项目：

```bash
cd <repo-path>
grep -o 'href="[^"]*\.html"' index.html | sort -u
```

只允许追加新项目卡片；不要重写或格式化历史卡片。

### Step 3: 评估候选项目

每个候选项目最多快速评估 30 秒。以下 4 项全部为 yes 才继续：

1. 与 coding agent、LLM 应用开发、AI developer tooling 或自动化开发工作流相关。
2. 架构有可讲解亮点，例如多 agent、工具调用、RAG、WASM、MCP、sandbox、代码索引或工作流编排。
3. Stars > 250。
4. 最近 5 天仍活跃，或创建后有持续提交、issue、release、discussion。

不满足条件的项目记录跳过原因。不要为了凑数硬选低质量项目。

### Step 4: 生成页面

每个合格项目按 4 步生成：

1. 克隆源码：

   ```bash
   mkdir -p <workdir>/sources
   git clone https://github.com/{owner}/{repo}.git <workdir>/sources/{project}/ --depth 1
   ```

2. 读取源码：优先查看 `.py`、`.ts`、`.tsx`、`.go`、`.rs`、`.java` 等关键实现文件。必须引用真实源码和真实行号，不要只读 README。

3. 生成主页面：复制 `<template-skill-dir>/templates/main-page.html`，按 `placeholder-map.md` 填充。

   - 把 `layout-shell.css` 注入 `__LAYOUT_SHELL_CSS__`。
   - 把 `--star / --star-soft / --star-deep` 改为项目 accent 色。
   - 6 个章节依次填充，H3 总数不少于 10。
   - 代码块从源码复制，保留真实行号。
   - 必须包含 mermaid 架构图。
   - H3 末尾至少 2 个“深度阅读”入口。

4. 生成 2-4 个子页面：复制 `<template-skill-dir>/templates/sub-page.html`，每个页面深入一个模块。

   - 路径：`{project}/{project}-{topic}.html`
   - 主页面 H3 末尾链接到子页面，例如 `href="{project}/{project}-{topic}.html"`。
   - 每个子页面至少 20 个真实行号引用、至少 3 个 H3。

### Step 5: 校验 + 推送

质量门禁必须 exit 0；失败时修复后重跑，不要绕过：

```bash
cd <repo-path>
python3 <template-skill-dir>/scripts/quality_gate.py {project} --json
```

通过后追加 `index.html` 卡片，保持现有结构，只 append 新卡片。

```bash
git add {project}.html {project}/ index.html <workdir>/sources/{project}/
git commit -m "feat({project}): source-level deep-dive + N nested detail pages"
git push https://x-access-token:$GITHUB_PAT@github.com/<owner>/<pages-repo>.git main
```

推送成功后生成直链：

- 主页面：`<site-base-url>/{project}.html`
- 子页面：`<site-base-url>/{project}/{project}-{topic}.html`

### Step 6: 无新项目处理

如果没有符合条件的新项目，输出“今日无符合条件的新项目”，并列出每个跳过项目及原因。不要提交空 commit，不要硬选质量差的项目。

## 输出格式

最终消息使用以下结构：

- 新增项目：每个项目包含 Tab 锚点、stars、commit hash、子页面数量。
- 线上链接：主页面直链 + 每个子页面直链。
- 质量自检：源码引用数、行号引用数、子页面数、quality_gate 状态。
- 跳过项目：项目名 + 跳过原因。
- 失败步骤：如有失败，写明步骤、错误摘要和下一步需要的输入。

## 重要约束

- 禁止修改任何已有项目页面；只新增 `{project}.html`、`{project}/...`，并对 `index.html` 做 append-only 更新。
- 禁止重建历史页面或批量格式化现有 HTML。
- 禁止让 `--bg-card`、`--bg-elev` 或 `--glow-amber` 主导设计系统；模板色板以 `--ink / --panel / --star` 为准。
- 必须为每个代码块使用 `<span class="ln">` 标注真实行号，行号要能对上源码。
- 必须让每个主页面包含至少 1 个 mermaid 图和至少 2 个子页面入口。
- quality_gate 失败必须修复，不允许用“差一点就过了”作为完成标准。
- 不要在公开 skill 中硬编码个人路径、个人 GitHub Pages URL 或本机 `.env` 路径；使用 `<workdir>`、`<repo-path>`、`<site-base-url>` 和 `$GITHUB_PAT`。
- 不要提交 token、cookies、`.env`、本地缓存或临时日志。

## 失败处理

- `curl` 返回 401/403：检查 `$GITHUB_PAT` 是否存在、scope 是否足够、GitHub rate limit 是否耗尽。
- `curl` 超时或解析失败：检查代理和 DNS；必要时设置 `https_proxy` 后重试。
- `git clone` 失败：记录错误并跳过该 repo，不要阻塞整个批次。
- 源码分析不出亮点：跳过该 repo，并记录“源码层亮点不足”。
- 页面生成超过 90 分钟：优先完成主页面；子页面可在下一轮补，但必须在最终消息标明质量门禁是否通过。
- quality_gate 失败：读取 JSON 中的失败指标，针对源码引用、行号、H3、子页面、layout shell 锚点逐项修复后重跑。
- `git push` 失败：不要泄露 token；只报告 PAT 可能失效、权限不足或远端有新提交，并说明需要 rebase 或更新凭据。

## Known pitfalls

| 坑 | 影响 | 预防 |
|----|------|------|
| 只读 README | 页面变成浅层介绍，质量门禁和用户预期都不达标 | 必须 clone 并阅读关键源码文件 |
| 行号伪造 | 深度阅读入口不可验证 | 用 `nl -ba`、编辑器行号或源码片段真实行号填充 |
| 重写 index.html | 历史卡片结构和样式被污染 | 只定位现有卡片区域并 append 新卡片 |
| 误改历史 HTML | Git diff 噪声大，线上历史页可能破损 | `git diff --stat` 必须只出现新项目文件和 index.html |
| 忘记子页面回链 | 主页面“深度阅读”入口断开 | 生成后逐个 grep 子页面 href |
| 模板 shell 未注入完整 | quality_gate layout anchors 失败 | 先读取 layout-shell.css，再替换 `__LAYOUT_SHELL_CSS__` |
| 公开版写死个人路径 | clone 用户无法复用 | 文档中统一使用 `<workdir>`、`<repo-path>`、`<site-base-url>` |
