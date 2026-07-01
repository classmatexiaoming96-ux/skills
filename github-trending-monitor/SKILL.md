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

## 任务完成定义

**One task 完整定义 = 创建 `{project}.html` + 创建 `{project}/...` 子页面 + 追加 `index.html` 卡片 + `quality_gate.py` 通过 + commit/push + 验证线上主页含新入口。**

缺任何一步都视为任务失败。仅项目页面可访问但主页没有入口，用户感知不到，按失败处理。

允许修改白名单：

- 新增 `{project}.html`
- 新增 `{project}/...` 子页面
- 对 `index.html` 做 append-only 卡片追加
- 可选新增 `<workdir>/sources/{project}/` 源码快照

禁止重写历史页面、批量格式化现有 HTML、删除历史卡片，或把生成好的项目页先 push 再“有空补 index”。

## When to invoke this skill

在以下场景使用本 skill：

- 需要每天筛选 GitHub 新增热门 AI / LLM / coding-agent / developer-tool 项目。
- 需要对候选项目做源码级深度阅读，而不是只基于 README 写摘要。
- 需要把项目分析生成 GitHub Pages HTML 页面，并追加到聚合入口页。
- 需要严格复用本 skill 自带模板、占位符和质量门禁。

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
- `curl`：用于 GitHub Search API 查询和线上部署验证。
- `GITHUB_PAT`：必须来自环境变量 `$GITHUB_PAT`，不要假设任何固定 `.env` 路径。需要时让用户先在当前 shell 中导出。
- 网络代理：如果运行环境访问 GitHub 不稳定，先配置 `https_proxy` / `http_proxy`，并用 `curl https://api.github.com/rate_limit` 验证。

## 引用依赖

严格依赖并优先读取本 skill 目录内的模板、脚本和文档；不要依赖外部 `github-trending-page-template` skill：

- `templates/main-page.html`：主页面模板
- `templates/sub-page.html`：子页面模板
- `templates/layout-shell.css`：CSS shell
- `scripts/quality_gate.py`：质量门禁
- `docs/placeholder-map.md`：占位符说明

执行时把本 skill 安装目录记为 `<skill-dir>`，把 GitHub Pages 仓库记为 `<repo-path>`，把临时源码目录记为 `<workdir>/sources/<project>`，把线上站点根 URL 记为 `<site-base-url>`。

## 任务流程

### Step 1: 拉取候选仓库

查询最近 5 天创建、stars 大于 250、主题与 AI / LLM / coding agent / developer tools 相关的候选仓库：

```bash
DATE=$(date -ud '5 days ago' +%Y-%m-%d)
curl -sS -H "Authorization: token $GITHUB_PAT" \
  "https://api.github.com/search/repositories?q=created:>=$DATE+stars:>250+(agent+OR+coding+OR+code+assistant+OR+AI+agent+OR+copilot+OR+autonomous+agent+OR+LLM+OR+codellm)&sort=stars&order=desc&per_page=8"
```

记录每个候选项目的 `full_name`、stars、created_at、updated_at、description、language、html_url。

如果 API 返回 401/403，先检查 `$GITHUB_PAT` 和 rate limit；不要改用未认证请求反复重试。

### Step 2: 过滤已有项目

进入 `<repo-path>`，读取 `index.html` 中已有项目入口，排除已经收录的项目：

```bash
cd <repo-path>
grep -o 'href="[^"]*\.html"' index.html | sort -u
```

只允许追加新项目卡片；不要重写或格式化历史卡片。

对候选项目生成 `{project}` ID 时使用小写连字符，和最终文件名保持一致：`{project}.html`、`{project}/{project}-{topic}.html`。

### Step 3: 评估候选项目

每个候选项目最多快速评估 30 秒。以下 4 项全部为 yes 才继续：

1. 与 coding agent、LLM 应用开发、AI developer tooling 或自动化开发工作流相关。
2. 架构有可讲解亮点，例如多 agent、工具调用、RAG、WASM、MCP、sandbox、代码索引或工作流编排。
3. Stars > 250。
4. 最近 5 天仍活跃，或创建后有持续提交、issue、release、discussion。

不满足条件的项目记录跳过原因。不要为了凑数硬选低质量项目；只靠 README、demo 截图或营销文案能讲清的项目，按“源码层亮点不足”跳过。

### Step 4: 生成页面

每个合格项目按 4 步生成：

1. 克隆源码：

   ```bash
   mkdir -p <workdir>/sources
   git clone https://github.com/{owner}/{repo}.git <workdir>/sources/{project}/ --depth 1
   ```

2. 读取源码：优先查看 `.py`、`.ts`、`.tsx`、`.go`、`.rs`、`.java` 等关键实现文件。必须引用真实源码和真实行号，不要只读 README。

3. 生成主页面：复制 `<skill-dir>/templates/main-page.html`，按 `<skill-dir>/docs/placeholder-map.md` 填充。

   - 把 `<skill-dir>/templates/layout-shell.css` 注入 `__LAYOUT_SHELL_CSS__`。
   - 把 `--star / --star-soft / --star-deep` 改为项目 accent 色。
   - 6 个章节依次填充，H3 总数不少于 10。
   - 代码块从源码复制，保留真实行号。
   - 必须包含 mermaid 架构图或等价 architecture flow。
   - H3 末尾至少 2 个“深度阅读”入口。
   - 主页面必须链接到所有子页面，例如 `href="{project}/{project}-{topic}.html"`。

4. 生成 2-4 个子页面：复制 `<skill-dir>/templates/sub-page.html`，每个页面深入一个模块。

   - 路径：`{project}/{project}-{topic}.html`
   - 主页面 H3 末尾链接到子页面，例如 `href="{project}/{project}-{topic}.html"`。
   - 每个子页面至少 20 个真实行号引用、至少 3 个 H3。
   - 子页面使用与主页面一致的 layout shell 和 CSS vars。

### Step 5: 校验 + index append + 推送 + fail-fast 验证

这一步是硬约束，不是可选项。执行顺序必须是：

```text
quality_gate 初检 -> append index.html -> 本地 grep -> diff 范围检查 -> commit/push -> 线上主页 grep -> 新页面 curl
```

#### 5.1 质量门禁初检

质量门禁必须 exit 0；失败时修复后重跑，不要绕过。如果此时 `index.html` 还没追加卡片，quality gate 会因为第 10 项失败。先完成卡片 append，再重跑。

```bash
cd <repo-path>
python3 <skill-dir>/scripts/quality_gate.py {project} --json
```

#### 5.2 append `index.html` 卡片

在 `index.html` 的既有项目卡片区域追加新卡片，保持现有结构，只 append 新卡片。卡片链接必须包含 `href="{project}.html"`；不要把字面量 `{project}`、`PROJECT_ID`、`VIDEO_ID` 写入页面；不要重排历史卡片。

追加后立即验证：

```bash
cd <repo-path>
grep -n "{project}.html" index.html
grep -n "{project}" index.html
```

第一条 grep 必须有输出；没有输出就停止，不允许 commit/push。

#### 5.3 quality gate 复检

`index.html` append 后重跑质量门禁：

```bash
cd <repo-path>
python3 <skill-dir>/scripts/quality_gate.py {project} --json
```

`--json` 模式返回非 0 时必须修复；不要在 `passed: false` 时继续提交。

#### 5.4 diff 范围检查

提交前确认只包含本次新增项目和 `index.html`：

```bash
cd <repo-path>
git diff --stat
git diff --name-only | sort
```

只允许出现 `{project}.html`、`{project}/...`、`index.html`、可选 `<workdir>/sources/{project}/...`；不允许出现历史 HTML、无关配置、token、cookies、`.env` 或临时日志。

#### 5.5 commit + push

```bash
cd <repo-path>
git add {project}.html {project}/ index.html <workdir>/sources/{project}/
git commit -m "feat({project}): source-level deep-dive + N nested detail pages"
git push https://x-access-token:$GITHUB_PAT@github.com/<owner>/<pages-repo>.git main
```

如果远端有新提交，先 fetch/rebase；不要 force push。

#### 5.6 线上 fail-fast 验证

推送成功后等待 CDN 生效，再验证线上主页和新页面：

```bash
sleep 120

# 1. 线上主页必须包含新项目入口。这条不通过 = 任务失败。
curl -fsSL "<site-base-url>/" | grep -o "{project}.html" | head -3

# 2. 新主页面必须可访问。
curl -fsSI "<site-base-url>/{project}.html" | grep -E "HTTP/[0-9.]+ 200"

# 3. 子页面必须可访问。对每个 topic 各跑一次。
curl -fsSI "<site-base-url>/{project}/{project}-{topic}.html" | grep -E "HTTP/[0-9.]+ 200"

# 4. 本地 index.html 仍必须包含新入口。
grep -n "{project}.html" index.html
```

以上任一失败，都不要汇报“部署成功”。最终消息必须写明失败步骤、错误摘要和下一步需要的输入。

### Step 6: 无新项目处理

如果没有符合条件的新项目，输出“今日无符合条件的新项目”，并列出每个跳过项目及原因。不要提交空 commit，不要硬选质量差的项目，不改 `index.html`，不运行部署步骤。

## 工具调用预算

进入页面生成前先预留至少 8-10 次工具调用给收尾：append `index.html`、本地 grep、quality_gate 复检、git diff/stat、git add/commit、git push、线上主页 curl + grep、新主页面 curl、子页面 curl、最终汇报。

如果预算不足，优先停止新增子页面，先完成 `index.html` append、commit、push、线上主页 grep。

不允许先 push 项目页、再“有空时”补 index 卡片。昨天凌晨 `browser-bc` 缺主页入口就是这个失败模式。

## 输出格式

最终消息使用以下结构：

- 新增项目：每个项目包含 Tab 锚点、stars、commit hash、子页面数量。
- 线上链接：主页面直链 + 每个子页面直链。
- 质量自检：源码引用数、行号引用数、子页面数、quality_gate 状态、线上主页 grep 状态。
- 跳过项目：项目名 + 跳过原因。
- 失败步骤：如有失败，写明步骤、错误摘要和下一步需要的输入。

## 重要约束

- 禁止修改任何已有项目页面；只新增 `{project}.html`、`{project}/...`，并对 `index.html` 做 append-only 更新。
- 禁止重建历史页面或批量格式化现有 HTML。
- 禁止让 `--bg-card`、`--bg-elev` 或 `--glow-amber` 主导设计系统；模板色板以 `--ink / --panel / --star` 为准。
- 必须为每个代码块使用 `<span class="ln">` 标注真实行号，行号要能对上源码。
- 必须让每个主页面包含至少 1 个 mermaid 图或等价 architecture flow，且至少 2 个子页面入口。
- quality_gate 失败必须修复，不允许用“差一点就过了”作为完成标准。
- `index.html` 新卡片必须在 commit/push 前追加并本地 grep 通过。
- 推送后线上主页必须 grep 到 `{project}.html`，否则视为任务失败。
- 不要在公开 skill 中硬编码个人路径、个人 GitHub Pages URL 或本机 `.env` 路径；使用 `<skill-dir>`、`<workdir>`、`<repo-path>`、`<site-base-url>` 和 `$GITHUB_PAT`。
- 不要提交 token、cookies、`.env`、本地缓存或临时日志；不要删除或依赖外部 `github-trending-page-template`。

## 失败处理

- `curl` 返回 401/403：检查 `$GITHUB_PAT` 是否存在、scope 是否足够、GitHub rate limit 是否耗尽。
- `curl` 超时或解析失败：检查代理和 DNS；必要时设置 `https_proxy` 后重试。
- `git clone` 失败：记录错误并跳过该 repo，不要阻塞整个批次。
- 源码分析不出亮点：跳过该 repo，并记录“源码层亮点不足”。
- 页面生成超过 90 分钟：优先完成主页面和至少 2 个子页面；如果收尾预算不足，先停内容扩展，完成 `index.html` append 与部署验证。
- quality_gate 失败：读取 JSON 中的失败指标，针对源码引用、行号、H3、子页面、layout shell 锚点、index 卡片逐项修复后重跑。
- `git push` 失败：不要泄露 token；只报告 PAT 可能失效、权限不足或远端有新提交，并说明需要 rebase 或更新凭据。
- 线上主页 grep 失败：按下面的失败补救流程处理，不要汇报成功。

## 失败补救流程

如果 push 后线上主页 grep 不到 `{project}.html`，先检查本地 `index.html`：

   ```bash
   cd <repo-path>
   grep -n "{project}.html" index.html
   ```

如果本地缺失，先 append 卡片，再本地 grep，并单独提交修复：

   ```bash
   cd <repo-path>
   git add index.html
   git commit -m "fix({project}): append project card to index"
   git push https://x-access-token:$GITHUB_PAT@github.com/<owner>/<pages-repo>.git main
   sleep 120
   curl -fsSL "<site-base-url>/" | grep -o "{project}.html" | head -3
   ```

如果本地存在但线上缺失，检查是否 push 到正确仓库、GitHub Pages 分支是否正确、CDN 是否尚未生效；等待后重试线上 grep。线上主页 grep 通过前，不要汇报“部署成功”。

## Known pitfalls

| 坑 | 影响 | 预防 |
|----|------|------|
| 只读 README | 页面变成浅层介绍，质量门禁和用户预期都不达标 | 必须 clone 并阅读关键源码文件 |
| 行号伪造 | 深度阅读入口不可验证 | 用 `nl -ba`、编辑器行号或源码片段真实行号填充 |
| 重写 index.html | 历史卡片结构和样式被污染 | 只定位现有卡片区域并 append 新卡片 |
| 误改历史 HTML | Git diff 噪声大，线上历史页可能破损 | `git diff --stat` 必须只出现新项目文件和 index.html |
| 忘记子页面回链 | 主页面“深度阅读”入口断开 | 生成后逐个 grep 子页面 href |
| 模板 shell 未注入完整 | quality_gate layout anchors 失败 | 先读取 layout-shell.css，再替换 `__LAYOUT_SHELL_CSS__` |
| 公开版写死个人路径 | clone 用户无法复用 | 文档中统一使用 `<skill-dir>`、`<workdir>`、`<repo-path>`、`<site-base-url>` |
| index.html 卡片 append 跳过 | 主页没入口，用户感知不到新项目；汇报“部署成功”会误导 | 把 `index.html` append 放在 commit/push 前；本地 `grep "{project}.html" index.html` 和线上 `curl <site-base-url>/ | grep "{project}.html"` 都必须通过 |
