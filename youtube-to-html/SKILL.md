---
name: youtube-to-html
description: YouTube 技术视频 → GitHub Pages HTML 单次任务 pipeline。从视频发现、字幕下载、内容生成到 GitHub Pages 部署的完整闭环。专为 dark ghost-button 主题设计，包含防踩坑护栏。
triggers:
  - "YouTube 视频生成 HTML 页面"
  - "youtube 转 github pages"
  - "生成油管视频课程页面"
---

# YouTube 技术视频 → GitHub Pages HTML Pipeline

## 1. What this skill does

为 YouTube 技术视频生成一个独立 dark-themed HTML 页面，保存到 GitHub Pages 仓库并推送到线上去。

**One task 完整定义 = 创建 VIDEO_ID.html + 追加 index.html 卡片 + push + 验证线上主页含新入口。** 缺任何一步都视为任务失败（仅子页面推送成功但主页没入口 = 用户感知不到 = 失败）。

**允许的修改白名单**：仅允许在 `index.html` 中追加新视频卡片。其它所有已存在的 .html 文件禁止修改（详见 §6 与 §10）。

GitHub Pages: `https://classmatexiaoming96-ux.github.io/youtube_course/`
仓库: `https://github.com/classmatexiaoming96-ux/classmatexiaoming96-ux.github.io`

---

## 2. Video discovery

### Search YouTube

```bash
# 代理访问（开发机直连 YouTube 会超时）
https_proxy=http://127.0.0.1:7890 curl -s \
  "https://www.youtube.com/results?search_query=AI+agent+programming+tutorial" \
  | grep -o 'watch?v=[a-zA-Z0-9_-]*' | sort -u | head -10
```

### Quality criteria

- **时长**：5-60min 最佳；<3min 太短；>90min 需要分段
- **字幕**：必须有英文自动字幕（可下载）
- **频道**：优先 @HenryAILabs、@connor-shorten（Weaviate）、@SimonHoiberg、@Matt Wolfe、@Fireship

---

## 3. Subtitle download

### Download VTT with yt-dlp + cookies

```bash
~/.hermes/skills/youtube-to-html/scripts/download_subtitles.sh VIDEO_ID
```

> **Cookies 维护**：youtube_cookies.txt 位于 `/tmp/yt-to-doc-research/youtube_cookies.txt`，有效期约 30 天。

### VTT cleaning and chunking

VTT 原始文件含大量 `<v Speaker>` 时间戳标签，直接喂给 Codex 会导致内容混乱。用清洗脚本处理：

```bash
~/.hermes/skills/youtube-to-html/scripts/vtt_cleaner.py VIDEO_ID
ls /tmp/yt-to-doc-research/raw/VIDEO_ID_chunk_*.txt
```

---

## 4. GitHub Pages repository

```bash
# ✅ 正确：克隆 user-site 仓库（classmatexiaoming96-ux.github.io）
git clone https://github.com/classmatexiaoming96-ux/classmatexiaoming96-ux.github.io.git <workdir>/usersite

# ❌ 错误：youtube_course 是内容仓库，不是 GitHub Pages 站点（会 404）
git clone https://github.com/classmatexiaoming96-ux/youtube_course.git /tmp/pages-clone
```

GitHub Pages 只从 `username.github.io` 仓库提供服务。

---

## 5. HTML generation prompt template

把以下 prompt 发给 Codex（去掉中文注释，只保留给 Codex 看的内容）：

```
请为以下 YouTube 视频生成一个独立的 HTML 页面，保存到 <workdir>/usersite/youtube_course/VIDEO_ID.html

## 强制输出语言

**所有输出内容必须使用简体中文（包括页面正文、表格、按钮文字、导航链接、章节标题和说明文字）。视频标题保留英文原文作为副标题或括号内原文，不要把整页写成英文。**

## 设计参考

**布局/结构/排版必须参考以下已有页面（视为唯一可信的设计样本）：`https://classmatexiaoming96-ux.github.io/youtube_course/mWvtOHlZM-I.html`。重点参考其分段式叙事、表格组织、引用块、决策矩阵和中文文章式讲解密度。**

## 视频信息
- Video ID: VIDEO_ID
- 标题: [视频标题]
- 频道: [频道名]
- 时长: X分XX秒
- Views: [播放量，如可获取]

## 内容概要（从字幕提取的核心要点，贴入 1-3 段摘要）
[字幕内容摘要]

## 必须遵循的 Dark Ghost-Button 主题 CSS
```css
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #16161f;
  --text-primary: #e2e8f0;
  --accent: #63b3ed;
  --accent-hover: #4299e1;
  --card-bg: rgba(255,255,255,0.05);
  --card-border: rgba(255,255,255,0.08);
}
body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: Inter, -apple-system, sans-serif;
}
button, .btn {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
button:hover, .btn:hover {
  background: var(--accent);
  color: var(--bg-primary);
}
.hero {
  background: var(--bg-secondary);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(12px);
  margin-bottom: 2rem;
}
.content-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  backdrop-filter: blur(12px);
}
```

## 页面内容结构

请生成“文章式”中文课程页，不要只做简单 bullet 摘要。页面至少包含以下结构：

1. **顶部返回链接**：页面最上方放置 `← 返回课程列表`，链接到 `index.html`
2. **Hero header**：中文主标题 + 英文视频标题副标题 + 频道 + 时长 + views
3. **视频嵌入**：`<iframe src="https://www.youtube.com/embed/VIDEO_ID" ...></iframe>`
4. **一、问题引入 / 背景**：用叙事段落开头，解释这个视频解决什么问题、为什么值得看，不要直接进入 bullet
5. **二、核心概念解释**：从 0 教学，帮助没看过视频的人理解关键术语、上下文和前置知识
6. **三、关键论点 / 实操步骤**：按视频脉络分段展开，每段配小标题，既讲“是什么”也讲“怎么做”
7. **四、对比表格 / 决策矩阵**：必须使用真实 `<table>` 元素组织信息，不要用 markdown 表格文本；表格要包含适用场景、优点、风险或决策建议
8. **五、引用块**：必须使用 `<blockquote>` 强调视频中的关键观点、金句或可转述的核心判断
9. **六、时间戳目录**：根据字幕整理章节列表，使用可扫描的时间点 + 中文说明
10. **七、相关推荐**：链接回 `index.html`，并链接到其他 `youtube_course/` 下的课程页

## 🚨 FORBIDDEN_FILES（最核心的约束）🚨

**只创建 <workdir>/usersite/youtube_course/VIDEO_ID.html，禁止修改任何其他文件。**

开始生成前，先动态获取已有文件列表（这些文件全部禁止修改）：

```bash
ls <workdir>/youtube_course/*.html   # 替换为用户实际的 GitHub Pages 仓库路径
```

DO NOT modify, touch, overwrite, or rewrite any file except <workdir>/usersite/youtube_course/VIDEO_ID.html

## 完成后验证

1. 确认文件已创建：`ls -la <workdir>/usersite/youtube_course/VIDEO_ID.html`
2. 确认深色主题：`grep -c "0a0a0f" <workdir>/usersite/youtube_course/VIDEO_ID.html`（应返回 ≥1）
3. 中文内容检查：`grep -c '[\xe4-\xe9][\x80-\xbf][\x80-\xbf]' <workdir>/usersite/youtube_course/VIDEO_ID.html`（应返回 ≥50）
4. 表格存在检查：`grep -c '<table' <workdir>/usersite/youtube_course/VIDEO_ID.html`（应返回 ≥1）
5. 引用块检查：`grep -c '<blockquote' <workdir>/usersite/youtube_course/VIDEO_ID.html`（应返回 ≥1）
6. 页面大小检查：`wc -c <workdir>/usersite/youtube_course/VIDEO_ID.html`（应 ≥ 15000；如果小于 15KB，说明内容不够深入，需要扩写）
7. 确认没有误改其他文件：`git diff --stat <workdir>/usersite/youtube_course/`
8. 如果 `git diff` 显示多个文件被修改 → 回滚并只保留新文件：

```bash
cd <workdir>/usersite
git stash
git checkout main -- youtube_course/  # 恢复所有旧文件
git stash pop  # 拿回新文件（只有 VIDEO_ID.html）
git diff --stat youtube_course/  # 验证只有 VIDEO_ID.html
```
```

---

## 6. Update index.html (add new video card) — ⚠️ 必做步骤

**这一步是硬约束，不是可选项。** 历史上多次 cron 任务跑完子页面 + commit + push 后，session 因为达到工具调用上限而中断，**漏掉 index.html 卡片 append** —— 后果是子页面在线上能访问，但用户在主页 `https://classmatexiaoming96-ux.github.io/youtube_course/` 看不到入口，等于任务失败。

**执行顺序**：§5（生成 VIDEO_ID.html）→ **本节（append index.html）**→ §7（commit push）。中间不要插入其他无关操作。

在 `git diff` 验证通过后，把新视频卡片追加到 index.html 的 video-cards 区域：

> ⚠️ **`sed` 模板里的 `VIDEO_ID` 必须替换为真实的 11 位 ID**（如 `BaXTos7B1vY`），不要把字面量 `VIDEO_ID` 写进 index.html。

```bash
# 用 sed 在 </section> 闭合标签前插入新卡片
sed -i '/<section class="video-cards">/!b;:a;n;/<\/section>/!ba;a\<!-- NEW VIDEO CARD -->\n<div class="video-card">\n  <a href="VIDEO_ID.html">\n    <div class="card-content">\n      <h3>[视频标题]</h3>\n      <p class="meta">[频道名] · [时长]</p>\n      <p class="description">[一句话描述]</p>\n    </div>\n  </a>\n</div>\n' <workdir>/usersite/youtube_course/index.html
```

验证卡片已插入：
```bash
grep -c "VIDEO_ID" <workdir>/usersite/youtube_course/index.html
```

---

## 7. Commit and push

```bash
cd <workdir>/usersite

git add youtube_course/
git commit -m "feat: add VIDEO_ID youtube video page"

# 如果有 remote 新提交，先 rebase
git fetch origin
git pull origin main --rebase
git push origin main
```

---

## 8. Deployment verification

**Fail-fast 验证**：以下 4 项全部必须通过，任何一项失败都视为任务未完成，必须补完再回报。

```bash
# 等待 ~2 分钟 CDN 生效
sleep 120

# ✅ 1. 主页包含新视频（最关键 — 这条不通过 = 任务失败）
curl -s "https://classmatexiaoming96-ux.github.io/youtube_course/" | grep -o "VIDEO_ID" | head -3
# 期望：至少 1 个匹配

# ✅ 2. 新页面本身可访问
curl -sI "https://classmatexiaoming96-ux.github.io/youtube_course/VIDEO_ID.html"
# 期望：HTTP 200

# ✅ 3. 新页面深色主题
curl -s "https://classmatexiaoming96-ux.github.io/youtube_course/VIDEO_ID.html" | grep -c "0a0a0f"
# 期望：≥ 1

# ✅ 4. 本地 index.html 已包含新 ID（推送前就应验证）
grep -c "VIDEO_ID" <workdir>/usersite/youtube_course/index.html
# 期望：≥ 1
```

**如果验证 1 不通过**（主页不含新 ID），立即执行补救：
```bash
# 在 index.html 末尾追加卡片（参考 §6 的 sed 模板）
cd <workdir>/usersite
git add youtube_course/index.html
git commit -m "fix(youtube): append VIDEO_ID card to index"
git push origin main
# 再次 sleep 120 + 重新跑验证 1
```

---

## 9. Directory structure

```
<workdir>/usersite/                     # GitHub Pages user-site 仓库
└── youtube_course/
    ├── index.html                      # 主页（禁止重写，只能追加卡片）
    ├── mWvtOHlZM-I.html               # 已有（禁止修改）
    ├── gv0WHhKelSE.html
    ├── HNzH5Us1Rvg.html
    ├── fHWFF_pnqDk.html
    ├── 96jN2OCOfLs.html
    ├── 3Y8aq_ofEVs.html
    ├── QJG2nA2_Xko.html
    ├── EAeUiipzCTE.html
    ├── LNkAW4SSgdY.html
    └── VIDEO_ID.html                   # ← 只创建这一个新文件

/tmp/yt-to-doc-research/
└── raw/
    ├── VIDEO_ID.en.vtt                # 原始字幕
    └── VIDEO_ID_chunk_*.txt           # 清洗后字幕块

~/.hermes/skills/youtube-to-html/       # 本 skill
```

---

## 10. Known pitfalls

| 坑 | 影响 | 预防 |
|----|------|------|
| **Codex 重写已有文件** — 没列 FORBIDDEN_FILES | Git 历史污染，已有页面损坏 | 始终在 prompt 中列全所有已有 .html 文件名 |
| **浅色主题渗透** — Codex 用浅色背景代替 #0a0a0f | 深色主题破版，页面不可读 | 始终在 prompt 中附完整 CSS block；生成后 `grep -c "0a0a0f"` 验证 |
| **推错仓库** — 推到 youtube_course 内容仓库 | 所有页面 404 | 始终克隆 `classmatexiaoming96-ux.github.io.git` |
| **cp 交互确认** — `cp` 无 `\` 前缀卡在覆盖确认 | index.html 未更新 | 始终使用 `\cp -f` |
| **VTT 时间戳未清洗** — `<v Speaker>` 标签未移除 | Codex 理解混乱，内容质量下降 | 始终用 `scripts/vtt_cleaner.py` 处理后再喂给 Codex |
| **Cookies 过期** — youtube_cookies.txt 超过 30 天 | 字幕下载失败 | 从浏览器重新导出 cookies 文件 |
| **长视频 VTT** — 单文件 > 8000 chars 导致 CodeGen 混乱 | 内容截断或乱码 | 始终用 chunk 脚本分块 |
| **index.html 卡片 append 跳过** — cron 跑完子页面 + commit 后 session 工具调用达上限 | 主页没入口，用户感知不到新视频；汇报里说"部署成功"误导 | 把"index.html append"列为必做步骤写在 prompt 顶部；verification 阶段 grep 主页含新 ID 作为 fail-fast 检查 |
