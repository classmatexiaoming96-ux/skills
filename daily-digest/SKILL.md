---
name: daily-digest
description: 每天自动汇编一期「AI 每日速递」深色主题日报 HTML，并部署到 GitHub Pages。内容源覆盖 Google News（AI 要闻）、Hacker News + Reddit（社区热议）、X/Twitter via Nitter（AI trending）、GitHub Trending（开源热门）。产出 ~/.hermes/daily-digest/{date}.html，自带纯前端日历翻阅历史刊期。
triggers:
  - "生成今天的 AI 日报"
  - "daily digest / 每日速递"
  - "AI 每日新闻汇编 HTML"
  - "更新 AI 日报并部署"
---

# AI 每日速递 · Daily Digest

每天一刊的 AI 情报日报。**一次任务 = 生成一期 `{date}.html` + 刷新 manifest + 部署**。
风格独立设计（深色「编辑部」主题，与 pulse / youtube-to-html 均不同），不发飞书、不走 Codex review。

---

## 0. 布局总览

```
~/.hermes/skills/daily-digest/
├── SKILL.md
├── scripts/
│   ├── prefetch.py          # 抓四类信源 → data/{date}.json
│   └── build.py             # content/{date}.json + 模板 → {date}.html + manifest.js
├── templates/
│   └── digest.template.html # 日报骨架（占位符由 build.py 填充）
└── web/                     # 部署脚手架（viewer / 日历 / 样式），随每期一起发布
    ├── index.html           # 阅读器外壳：默认最新一期 + 日历浮层
    ├── calendar.html        # 独立日历页（历史刊期）
    ├── manifest.js          # window.DIGESTS（build.py 自动维护）
    └── assets/{digest.css, calendar.css, calendar.js, viewer.js}

~/.hermes/daily-digest/      # 工作 + 产出目录
├── data/{date}.json         # prefetch 原料
├── content/{date}.json      # 人工策展后的结构化内容（build.py 的输入）
├── {date}.html              # 产出：当期日报
└── manifest.js / .meta/     # build.py 维护
```

部署目标是 **user-site 仓库** `classmatexiaoming96-ux.github.io` 下的新子目录 `daily-digest/`
（与 `youtube_course/` 平级），线上地址：`https://classmatexiaoming96-ux.github.io/daily-digest/`。

---

## 1. 抓取信源（prefetch）

```bash
cd ~/.hermes/skills/daily-digest
# 本机出网通常要走代理；prefetch 会读 HTTPS_PROXY，也可显式 --proxy
python3 scripts/prefetch.py --date "$(date +%F)" \
  --proxy http://127.0.0.1:7890 \
  --out ~/.hermes/daily-digest/data
```

四类信源（全部免密钥、纯标准库）：

| 桶 | 来源 | 对应栏目 |
|---|---|---|
| `google_news` | Google News RSS（en + zh-CN，`when:1d`） | ① 今日要闻 |
| `hacker_news` | HN Algolia API（近 36h、points>40，AI 关键词过滤） | ② 社区热议 |
| `reddit` | r/MachineLearning · LocalLLaMA · artificial · OpenAI · singularity 的 `top?t=day` | ② 社区热议 |
| `show_hn` | HN Show HN（近 3 天，AI 关键词） | ③ 产品 · 概念 |
| `x_twitter` | Nitter HTML 解析（`nitter.tiekoetter.com`，#AI 搜索） | ② 社区热议  |
| `github` | `github.com/trending` 抓取 +（AI 命中为空时）Search API 兜底 | ④ 开源热门 |

> **代理**：开发机直连 Google News / Reddit / GitHub / Nitter 常超时。优先 `--proxy http://127.0.0.1:7890`。
> 每个信源都包 try/except，单源失败不中断；结尾 summary 会标出哪个桶 `⚠ EMPTY`，据此决定是否补抓。
> X（Twitter）通过 Nitter tiekoetter.com 实例走 HTML 解析获取，不再依赖不稳定的 Nitter RSS 或 X API key（已内置 curl fallback 绕过 Cloudflare 验证）。

---

## 2. 策展 → 写 `content/{date}.json`

读 `data/{date}.json`，**人工判断 + 提炼**成四个栏目，落到 `~/.hermes/daily-digest/content/{date}.json`。

### 策展规则

- **要闻**：从 google_news 选 5–7 条「今天真正发生/迫近」的事，挑一条做 `lead`（最有分量的头条）。去掉纯营销稿、重复事件合并。中文优先，英文标题可保留原名词。
- **社区热议**：从 hacker_news + reddit 按热度（points/comments）选 4–6 条**有讨论价值**的，不是单纯新闻。能提炼出一句代表性观点就填 `quote`（让它像「言论」，替代 X 的角色）。
- **产品 · 概念**：从 show_hn + 要闻 + trending 里**综合**出 3–5 个，可以是具体新产品，也可以是当周反复出现的**概念/趋势**（名字前加「概念 · 」）。
- **开源热门**：从 github 选 5–7 个 AI 相关、当日上升快的仓库，保留真实 `stars` / `stars_today`。
- 全程**每条都要有可点链接**；摘要 1–2 句、可扫读；宁缺毋滥，没料的栏目可少放。
- `intro` 写一句「今日导读」，串起当天主线。`edition` 期号在上一期基础上 +1（看 manifest.js）。

### content schema

```jsonc
{
  "date": "2025-06-18", "weekday": "星期三", "edition": 42,
  "intro": "一句话导读…",
  "headline_title": "用于 manifest/日历的当期标题（可省，默认取 lead.title）",
  "sections": {
    "headlines": {
      "lead":  { "tag":"头条", "title":"", "summary":"", "source":"", "url":"", "time":"2 小时前" },
      "items": [ { "title":"","summary":"","source":"","url":"","time":"","tag":"政策" } ]
    },
    "community": {
      "items": [ { "title":"","summary":"","quote":"可选","platform":"Hacker News",
                   "points":1284,"comments":612,"url":"" } ]
    },
    "products": {
      "items": [ { "icon":"🧩","name":"","tagline":"","summary":"","tag":"新产品","url":"可选" } ]
    },
    "repos": {
      "items": [ { "owner":"","name":"","desc":"","lang":"Python",
                   "stars":"18,420","stars_today":"2,140","url":"","tag":"Agent" } ]
    }
  }
}
```

> 栏目可缺省（缺哪个少哪个），但顺序固定：headlines → community → products → repos。
> 每栏 `--accent` 配色已在 build.py 固定：要闻金、社区青、产品紫、开源绿。

---

## 3. 渲染（build）

```bash
cd ~/.hermes/skills/daily-digest
python3 scripts/build.py ~/.hermes/daily-digest/content/$(date +%F).json \
  --template templates/digest.template.html \
  --out ~/.hermes/daily-digest
```

产出 `~/.hermes/daily-digest/{date}.html`，并**自动重建 `manifest.js`**（扫描目录下所有 `YYYY-MM-DD.html` + `.meta/` 元数据）。每页都是**自包含**的（只依赖同目录 `assets/digest.css`），可单独打开，也能被 viewer 用 iframe 嵌入。

校验：

```bash
grep -c "assets/digest.css" ~/.hermes/daily-digest/$(date +%F).html   # =1 → 主题样式已挂
grep -o 'sec-no">[0-9]*' ~/.hermes/daily-digest/$(date +%F).html       # 应见 01 02 03 04
```

---

## 4. 部署（GitHub Pages，user-site 仓库）

```bash
# 4.1 克隆 user-site 仓库（不是内容仓库！）
git clone https://github.com/classmatexiaoming96-ux/classmatexiaoming96-ux.github.io.git /tmp/usersite
mkdir -p /tmp/usersite/daily-digest

# 4.2 首次：铺设脚手架（viewer / 日历 / 样式）；以后只在脚手架改动时重铺
\cp -rf web/assets /tmp/usersite/daily-digest/
\cp -f  web/index.html web/calendar.html /tmp/usersite/daily-digest/

# 4.3 每期：拷新日报 + manifest
\cp -f ~/.hermes/daily-digest/$(date +%F).html /tmp/usersite/daily-digest/
\cp -f ~/.hermes/daily-digest/manifest.js       /tmp/usersite/daily-digest/

# 4.4 提交（只动 daily-digest/ ）
cd /tmp/usersite
git add daily-digest/
git diff --cached --stat        # 确认只改了 daily-digest/ 下的文件
git commit -m "digest: add $(date +%F) edition"
git pull origin main --rebase
git push origin main
```

> 用 `\cp -f` 绕开交互式 overwrite 提示（见 youtube-to-html 同类坑）。
> 验证：`sleep 120 && curl -sI https://classmatexiaoming96-ux.github.io/daily-digest/$(date +%F).html`

---

## 5. 入口（GitHub Trending + YouTube 页面）

详见 `docs/entry-points.md`。要点：

- **YouTube 课程页**（user-site `youtube_course/index.html`）：在 hero 下方加一条 ghost-button「📰 AI 每日速递」指向 `../daily-digest/`。改 1 个文件、纯加法。
- **GitHub Trending 页**（独立仓库 `classmatexiaoming96-ux/github-trending`）：日报不是「源码拆解 tab」，**不要**塞进 `.tab-panel`/`VALID`/`TITLES` 那套（那是按 5 触点加 tab 的规则，见记忆 github-trending-tab-checklist）。正确做法是在 `site-index` 顶部导航里加一条**外链卡片** `🗞 AI 每日速递` 指向日报站，单文件、最低风险。

两个入口都是**外链**到 `daily-digest/`，互不耦合，挂了也不影响主站。

---

## 6. 阅读器行为（纯前端，无后端）

- `index.html`：读 `manifest.js`（`window.DIGESTS`），**无 hash 时默认最新一期**，用 iframe 载入 `{date}.html`；顶栏 ‹ › 翻前后一天，`📅 日历` 开浮层选任意日期；状态存在 `location.hash`（`#YYYY-MM-DD`），可分享深链；← → 方向键翻页。
- `calendar.html`：独立整页月历，有日报的日期高亮可点，跳 `index.html#日期`。
- 月历/翻页全部基于 `manifest.js`，**不发 fetch**（GitHub Pages 与 file:// 都能跑）；新增一期只需 build 重写 manifest.js。

---

## 7. 已知坑

| 坑 | 后果 | 规避 |
|---|---|---|
| 直连抓 Google News/Reddit/GitHub 超时 | 信源 EMPTY | `--proxy http://127.0.0.1:7890`；看 prefetch summary 的 ⚠ |
| 推错仓库（推到内容仓而非 user-site） | 全站 404 | 只 clone `classmatexiaoming96-ux.github.io.git` |
| 把日报当 tab 塞进 trending index | 改动面大、易碰坏现有 tab | 入口走 site-index **外链卡片**，不动 VALID/TITLES |
| `cp` 交互卡在 overwrite | 文件没更新 | 一律 `\cp -f` |
| 浅色主题渗漏 | 日报不像深色刊 | 模板已硬挂 `assets/digest.css`；校验 `grep -c assets/digest.css` |
| manifest 手改 | viewer 找不到新刊 | 只让 build.py 维护 manifest.js，勿手改 |
| 期号不连续 | 刊期混乱 | `edition` = 上期（manifest 第一条）+1 |
| reddit 返回 403 | reddit 桶空 | 已带 UA；仍失败则靠 HN 补足社区栏 |
