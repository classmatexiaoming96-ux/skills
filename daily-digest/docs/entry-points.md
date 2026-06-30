# 入口方案：GitHub Trending 页 + YouTube 页 → AI 每日速递

目标：在两个已上线的站点各加一个**外链入口**，点进去到达
`https://classmatexiaoming96-ux.github.io/daily-digest/`（默认显示最新一期，可用日历翻历史）。

两处都坚持三条原则：**纯加法**（不改现有逻辑）、**外链**（解耦，日报站挂了不影响主站）、**最低触点**。

---

## A. YouTube 课程页（user-site `youtube_course/index.html`）

该页是一个 hero + 卡片网格的静态页。入口做成 hero 下方的一条 ghost-button 横幅即可。

**位置**：`<div class="stats-bar">…</div>` 之后、第一个 `<section class="category-section">` 之前。

**插入片段**（已贴合该页 dark ghost-button 主题）：

```html
<!-- ▼ daily-digest 入口（新增，纯加法） -->
<a class="digest-entry" href="../daily-digest/">
  <span class="de-ico">🗞</span>
  <span class="de-text">
    <strong>AI 每日速递 · Daily Digest</strong>
    <span>每天一刊：要闻 · 社区热议 · 产品概念 · 开源热门 → 默认最新，附日历翻历史</span>
  </span>
  <span class="de-arrow">→</span>
</a>
<style>
  .digest-entry{
    display:flex;align-items:center;gap:16px;margin:28px 0 8px;padding:18px 22px;
    border:1px solid rgba(255,255,255,.12);border-radius:14px;
    background:linear-gradient(180deg,rgba(245,181,68,.10),transparent 60%),rgba(255,255,255,.03);
    color:#e2e8f0;transition:border-color .2s,transform .2s;
  }
  .digest-entry:hover{border-color:#F5B544;transform:translateY(-2px);}
  .digest-entry .de-ico{font-size:26px;}
  .digest-entry .de-text{display:flex;flex-direction:column;gap:4px;flex:1;}
  .digest-entry .de-text strong{font-size:16px;}
  .digest-entry .de-text span{font-size:13px;color:#9aa0ac;}
  .digest-entry .de-arrow{color:#F5B544;font-size:20px;}
</style>
<!-- ▲ daily-digest 入口 -->
```

部署同 youtube-to-html：clone user-site → 改 `youtube_course/index.html` →
`git diff --stat` 确认只动这一文件 → commit/push。**列其余 html 为 FORBIDDEN，勿碰**。

---

## B. GitHub Trending 拆解站（独立仓库 `classmatexiaoming96-ux/github-trending`）

⚠️ **不要**把日报当成一个「源码拆解 tab」。该站加 tab 需 5 个触点
（standalone html、tablist button、site-index、`assets/main.js` 的 `VALID` 数组、`TITLES` 映射，
见记忆 *github-trending-tab-checklist*）——日报不是源码拆解，套这套既费事又易碰坏现有 tab。

**正确做法**：日报是**外部栏目**，挂在顶部 `site-index` 导航里做一条外链卡片。只改 `index.html` 一个文件，
不动 `main.js`、不进 `VALID`/`TITLES`、不加 `.tab-panel`。

**位置**：`index.html` 的 `<div class="site-index-links">` 里，作为**第一条**（最显眼）。

**插入片段**（贴合该站 site-index 链接样式，额外加金色高亮区分「外部栏目」）：

```html
<!-- ▼ 外部栏目：AI 每日速递（新增，外链，不参与 tab 切换） -->
<a class="ext-digest" href="https://classmatexiaoming96-ux.github.io/daily-digest/" target="_blank" rel="noopener">
  🗞 AI 每日速递<br><span>每日刊 · 要闻/社区/产品/开源</span>
</a>
<style>
  .site-index-links a.ext-digest{
    border:1px solid rgba(245,181,68,.45);
    background:linear-gradient(180deg,rgba(245,181,68,.12),transparent);
  }
  .site-index-links a.ext-digest:hover{border-color:#F5B544;}
  .site-index-links a.ext-digest span{color:#F5B544;}
</style>
<!-- ▲ 外部栏目 -->
```

> 因为是外链且不带 `index.html#xx` 形式的 hash，`main.js` 的 tab 路由完全不会接管它，
> 也就**绕开了「tab id 不在 VALID 里会静默回落默认 tab」那个坑**。

部署：
```bash
git clone https://classmatexiaoming96-ux:<token>@github.com/classmatexiaoming96-ux/github-trending /tmp/gh-trending
# 编辑 /tmp/gh-trending/index.html，仅插入上面片段
cd /tmp/gh-trending
git add index.html && git commit -m "feat: add AI Daily Digest external entry to site-index"
git pull origin main --rebase && git push origin main
```

---

## C. 反向回链（可选）

日报站 `index.html` 顶栏 brand 可加两个小链接回 GitHub Trending 拆解站与 YouTube 课程站，
形成三站互链。非必须，按需添加：

```html
<!-- 放进 web/index.html 的 .vbar，brand 之后 -->
<a class="vbtn" href="https://classmatexiaoming96-ux.github.io/youtube_course/">🎬 视频</a>
<a class="vbtn" href="https://classmatexiaoming96-ux.github.io/github-trending/">🗂 拆解</a>
```

---

## 触点汇总

| 站点 | 改动文件 | 触点数 | 是否动 JS |
|---|---|---|---|
| YouTube 课程页 | `youtube_course/index.html` | 1 | 否 |
| GitHub Trending 站 | `index.html`（site-index） | 1 | **否**（关键：不进 VALID/TITLES） |
| 日报站本体 | `daily-digest/`（新子目录） | 新增 | 自带 viewer.js |
