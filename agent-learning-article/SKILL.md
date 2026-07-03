---
name: agent-learning-article
description: 将 /tmp/anthro_engineering/ 下的一篇 Anthropic Engineering 原文 Markdown 翻译为中文 HTML 文章，更新 Agent Learning 索引页的卡片和计数（X/24），git commit 到 /tmp/usersite。自执行 skill — 被加载后直接按步骤做。
triggers:
  - "翻译 Anthropic Engineering 文章到 Agent Learning"
  - "上线下一篇 Agent Learning 中文解读"
  - "agent learning 文章翻译"
  - "写 Agent Learning 文章"
  - "agent-learning-article"
---

# Agent Learning · 文章翻译上线（自执行）

你加载了这个 skill。请按下面的步骤完成一篇 Anthropic Engineering 文章的翻译和上线。

---

## 0. 先确认目标文章

查看 `/tmp/anthro_engineering/` 里有哪些 `.md` 文件，然后读 `/tmp/usersite/agent_learning/index.html` 看当前已发布到第几篇。选一篇还没翻译的，记下：

- **slug**：文件名（如 `claude-code-sandboxing`，不含 `.md`）
- **原文标题**：从 `.md` 的 first heading 取
- **原文 URL**：`https://www.anthropic.com/engineering/{slug}`
- **当前计数 N**：当前 header 区的 `<p class="meta">24 篇文章 · 持续更新中 · X / 24 已发布</p>` 中的数字 X
- **发布日期**：从原文 `.md` 的文件时间或内容取

---

## 1. Read 原文

Read `/tmp/anthro_engineering/{slug}.md` 一次性读完。评估文章长度和结构。

---

## 2. 生成中文 HTML

Write 工具写到 `/tmp/usersite/agent_learning/articles/{slug}.html`。结构如下：

### HTML 完整结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{中文标题} - Agent Learning</title>
  <link rel="stylesheet" href="../../style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
  body.article-page { background: #0a0a0f; color: #e0e0e8; font-family: 'Inter', system-ui, sans-serif; }
  .article-nav { max-width: 980px; margin: 0 auto; padding: 28px 24px 0; }
  .back-link { color: #63b3ed; text-decoration: none; font-family: 'JetBrains Mono', monospace; font-size: 13px; }
  .article-content { max-width: 980px; margin: 0 auto; padding: 32px 24px 80px; line-height: 1.85; }
  .article-header { border-bottom: 1px solid rgba(99,179,237,.22); padding-bottom: 26px; margin-bottom: 32px; }
  .article-meta { display: flex; gap: 16px; color: #888; font-family: 'JetBrains Mono', monospace; font-size: 13px; margin-bottom: 14px; flex-wrap: wrap; }
  .article-title { font-size: clamp(32px, 5vw, 58px); line-height: 1.12; margin: 0 0 14px; }
  .article-original-title { color: #999; margin: 0; font-size: 16px; }
  .article-content section { margin: 34px 0; }
  .article-content h2 { color: #63b3ed; margin: 30px 0 16px; font-size: 26px; }
  .article-content h3 { color: #e0e0e8; margin: 26px 0 12px; font-size: 20px; }
  .article-content p, .article-content li { color: #c0c0c8; }
  .article-content ul { padding-left: 22px; }
  .article-content li { margin: 8px 0; }
  pre { overflow-x: auto; padding: 18px; border: 1px solid rgba(99,179,237,.18); border-radius: 8px; background: rgba(255,255,255,.04); }
  code { font-family: 'JetBrains Mono', monospace; }
  blockquote { border-left: 3px solid #63b3ed; margin: 20px 0; padding: 12px 18px; color: #aaa; background: rgba(255,255,255,.03); }
  .article-footer { border-top: 1px solid rgba(99,179,237,.22); margin-top: 46px; padding-top: 24px; }
  .article-footer a { color: #63b3ed; overflow-wrap: anywhere; }
  </style>
</head>
<body class="article-page">
  <nav class="article-nav">
    <a href="../index.html" class="back-link">← Agent Learning 索引</a>
  </nav>
  <article class="article-content">
    <header class="article-header">
      <div class="article-meta">
        <span class="article-date">{发布日期}</span>
        <span class="article-author">Anthropic Engineering</span>
      </div>
      <h1 class="article-title">{中文标题}</h1>
      <p class="article-original-title">原文：{原文标题}</p>
    </header>
    <section>
      <h2>导读</h2>
      <p>{50-100 字中文导读，提炼本文核心价值}</p>
    </section>
    <section>
      <h2>核心观点</h2>
      <ul>{5-10 条本文独有 bullet}</ul>
    </section>
    <section>
      <h2>正文</h2>
      {逐段中文翻译，保留 H2/H3 层级、列表、关键数字、代码块等内容}
    </section>
    <section>
      <h2>深度解读</h2>
      <p>{200-400 字中文深度分析，非翻译，而是译者对技术的理解和延伸}</p>
    </section>
    <section>
      <h2>落地启示</h2>
      <ul>{3-5 条 actionable 建议，面向工程师团队}</ul>
    </section>
    <footer class="article-footer">
      <p><strong>原文链接：</strong><a href="https://www.anthropic.com/engineering/{slug}" target="_blank" rel="noopener">https://www.anthropic.com/engineering/{slug}</a></p>
      <p><a href="../index.html" class="back-link">← 返回 Agent Learning 索引</a></p>
    </footer>
  </article>
</body>
</html>
```

### 翻译规则

- 逐段翻译，保留 H2/H3 层级、有序/无序列表、关键数字、benchmark 名称
- agent、harness、sandbox、permission、context window、eval、prompt、token 等术语保留英文
- 代码块原样保留（不翻译注释、变量名等）
- 关键数字、benchmark 名称、URL 必须保留
- 中文要自然流畅，不要机器翻译腔

---

## 3. 更新索引页

Read `/tmp/usersite/agent_learning/index.html`。做两件事：

### 3a. 加 article-card

在 article-grid 区域的最后一个 `</a>`（现有卡片）后面追加。**注意：卡片使用 .date / .zh-title / .en-title / .summary / .status 类名，不是自定义的类名。**

```html
      <a class="article-card" href="articles/{slug}.html">
        <div class="date">{发布日期}</div>
        <h3 class="zh-title">{中文标题}</h3>
        <p class="en-title">{英文原标题}</p>
        <p class="summary">{50-80 字中文摘要，从原文实际内容提炼}</p>
        <span class="status done">✓ 已发布</span>
      </a>
```

### 3b. 改计数

把 header 区的 `<p class="meta">24 篇文章 · 持续更新中 · X / 24 已发布</p>` 改为 `<p class="meta">24 篇文章 · 持续更新中 · {X+1} / 24 已发布</p>`。Read 文件确认当前 X 的值。

---

## 4. Git commit

```bash
cd /tmp/usersite
git add agent_learning/articles/{slug}.html agent_learning/index.html
git commit -m "feat(agent-learning): translate {slug} to Chinese + 索引页更新为 {X+1}/24"
```

---

## 5. 完成后输出

在终端输出一行：`DONE {slug}`

---

## 约束（必须遵守）

- ❌ 不改 `/tmp/usersite/index.html`（首页 hero 4 张卡片不动）
- ❌ 不改 articles/ 里其他已存在的 .html 文件
- ❌ 不 git push（Hermes 来推）
- ❌ 不写通用模板内容替换真实翻译
- ✅ 索引卡片的摘要必须从原文实际内容提炼

---

## Verification

完成后你应当验证：
1. `/tmp/usersite/agent_learning/articles/{slug}.html` 存在且非空，内容是中文翻译（不是原文）
2. 索引页有新的 article-card
3. 索引页计数已 +1
4. `git log -1` 显示 commit 存在
5. 工作树只有 prompt 文件是 untracked，没有其他杂音
