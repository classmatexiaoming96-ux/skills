你的任务：为 1 篇 Anthropic Engineering 文章生成完整中文 HTML，并同步更新 Agent Learning 索引页的计数。

**原文 markdown**（请先 Read）：/tmp/anthro_engineering/{slug}.md
**输出 HTML**：/tmp/usersite/agent_learning/articles/{slug}.html

## 步骤

1. **Read** /tmp/anthro_engineering/{slug}.md 一次性读完
2. **逐段翻译**整篇原文为中文，保留 H2/H3 层级、列表、关键数字
3. **生成完整 HTML**（用 Write 工具直接写到 /tmp/usersite/agent_learning/articles/{slug}.html）
4. **更新 Agent Learning 索引页** /tmp/usersite/agent_learning/index.html：在 article-grid 加入新的文章卡片，并更新 header 区的计数为 {new_count}
5. **git commit**：`cd /tmp/usersite && git add agent_learning/articles/{slug}.html agent_learning/index.html && git commit -m "feat(agent-learning): translate {slug} to Chinese + 索引页更新为 {new_count}"`
6. **输出 sentinel**：单独一行 `DONE {slug}`

## HTML 模板

用下面的 HTML 结构，**用实际翻译内容填充**（不要保留模板标记）：

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
  <!-- 内联 article-page 样式同已上线文章 -->
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
      <p class="article-original-title">原文：{原标题}</p>
    </header>
    <section><h2>导读</h2><p>50-100 字中文导读，提炼本文价值</p></section>
    <section><h2>核心观点</h2><ul>5-10 条本文独有 bullet</ul></section>
    <section><h2>正文</h2>逐段中文翻译，保留所有 H2/H3、列表、代码块</section>
    <section><h2>深度解读</h2><p>200-400 字中文分析，非翻译</p></section>
    <section><h2>落地启示</h2><ul>3-5 条 actionable 建议</ul></section>
    <footer class="article-footer">
      <p><strong>原文链接：</strong><a href="https://www.anthropic.com/engineering/{slug}" target="_blank">https://www.anthropic.com/engineering/{slug}</a></p>
      <p><a href="../index.html" class="back-link">← 返回 Agent Learning 索引</a></p>
    </footer>
  </article>
</body>
</html>
```

## 索引卡片模板

```html
<a class="article-card" href="articles/{slug}.html">
  <div class="article-card-meta">{发布日期} · Anthropic Engineering</div>
  <h3 class="article-card-title">{中文标题}</h3>
  <p class="article-card-desc">50-80 字中文摘要</p>
  <div class="article-card-link">阅读全文 →</div>
</a>
```

## 约束

- 必须 Read 原文实际内容翻译，不能写模板或泛化内容
- 禁止写与其他文章重复的正文
- 中文自然流畅，保留 agent、harness、sandbox、permission、context window、eval、prompt、token 等术语
- 关键数字、benchmark 名称、URL 必须保留

## 完成

1. Write 写出 /tmp/usersite/agent_learning/articles/{slug}.html
2. patch 更新 /tmp/usersite/agent_learning/index.html 加卡片 + 改计数
3. git add + git commit
4. 终端输出 `DONE {slug}`

**不要：** git push、修改首页 index.html 的 hero 卡片、修改其他文章。
