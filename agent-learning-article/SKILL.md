---
name: agent-learning-article
description: 翻译 Anthropic Engineering 文章 → 中文 HTML 上线到 Agent Learning。用 Codex tmux session 翻译原文、生成文章页、更新索引计数，Hermes 负责推送。独立 session 一次一篇。
triggers:
  - "翻译 Anthropic Engineering 文章到 Agent Learning"
  - "上线下一篇 Agent Learning 中文解读"
  - "agent learning 文章翻译"
  - "写 Agent Learning 文章"
---

# Agent Learning · 文章翻译上线流程

## 1. What this skill does

将一篇 Anthropic Engineering 博客原文 Markdown（放在 `/tmp/anthro_engineering/` 下）逐段翻译为中文，生成独立 dark-themed HTML 文章页，更新 Agent Learning 索引页的卡片列表和计数（X / 24），git commit 并输出 sentinel 给 Hermes 推送。

**一次任务 = 1 篇翻译 + 索引更新 + commit，Hermes 推送到 GitHub Pages。** 不修改首页 hero 卡片。

**输出目标**：`/tmp/usersite/agent_learning/articles/{slug}.html`
**索引**：`/tmp/usersite/agent_learning/index.html`
**原文源**：`/tmp/anthro_engineering/{slug}.md`
**上线地址**：`https://classmatexiaoming96-ux.github.io/agent_learning/`

## 2. 前置条件

| 项目 | 目录 |
|------|------|
| Git 仓库 | `/tmp/usersite`（origin: `classmatexiaoming96-ux/classmatexiaoming96-ux.github.io`）|
| 原文 Markdown | `/tmp/anthro_engineering/*.md` |
| Codex session | `/tmp/tmux-codex` socket |
| 首页（不动） | `/tmp/usersite/index.html` |

## 3. 完整流程

### Step 1: 写 prompt 文件

每个 prompt 命名：`/tmp/usersite/.codex-p{N}-{slug}-prompt.md`

模板文件见 `templates/prompt.md`。关键参数：
- `{slug}`：原文文件名（不含 .md，如 `claude-code-sandboxing`）
- `{原文标题}`：从原文 .md 的 first heading 提取
- `{原文链接}`：`https://www.anthropic.com/engineering/{slug}`
- `{当前计数}`：索引页当前显示的数（如 3→4）

### Step 2: 起 Codex tmux session

```bash
SOCKET=/tmp/tmux-codex
SESSION=codex-p{N}-{slug}
tmux -S $SOCKET new-session -d -s $SESSION -c /tmp/usersite 'script -q -c codex /dev/null'
sleep 6
# 确认 pane dead=0 且看到 prompt screen
```

### Step 3: 发送任务

```bash
SOCKET=/tmp/tmux-codex
SESSION=codex-p{N}-{slug}
PROMPT='先读 .codex-p{N}-{slug}-prompt.md 理解任务，然后按里面的要求执行。开始。'
tmux -S $SOCKET send-keys -t $SESSION -l "$PROMPT"
sleep 1
tmux -S $SOCKET send-keys -t $SESSION Enter
sleep 4
# 确认显示 "Working (Ns • esc to interrupt)"
```

### Step 4: 起 watcher（后台）

脚本见 `scripts/monitor.sh`。按需替换 SESSION / ARTIFACT / SENTINEL。

### Step 5: watcher 命中后验证并推送

```bash
cd /tmp/usersite
git log -2 --oneline          # 确认 commit 存在
git push origin main          # 推送上线
```

## 4. 关键约束

- **一次只做一篇**：不跑批处理，每篇独立 session
- **不改首页**：不修改 `/tmp/usersite/index.html` 的 hero 4 张卡片
- **不改已有文章**：不修改 articles/ 里的其他 .html
- **sentinel 防误判**：见 pitfalls 的「sentinel 自匹配」
- **写工具强制**：prompt 里必须写「用 Write 工具直接写到文件」，避免 echo task 模式

## 5. 文章结构

每篇 HTML 包含 5 个 section：

| Section | 内容 |
|---------|------|
| 导读 | 50-100 字中文导读，提炼本文核心价值 |
| 核心观点 | 5-10 条 bullet，原文独有见解 |
| 正文 | 逐段中文翻译，保留 H2/H3/列表/关键数字/代码块 |
| 深度解读 | 200-400 字中文解读，非翻译，是译者分析 |
| 落地启示 | 3-5 条 actionable 建议，面向工程团队 |

## 6. Pitfalls

### Sentinel 自匹配
prompt 里的 sentinel 文本会出现在 pane 中，导致 watcher 过早触发。解决：使用 `Standalone line` 或 `• sentinel` 严格 regex + 交叉验证 artifact 文件存在且非空。

### 索引页计数
索引页 meta 是 `已发布 X / 24`。patch 时先确认当前 X 的值再 +1。

### Codex 读文件限制
prompt 文件要放在 `/tmp/usersite/`（Codex workdir）内，否则 Read 工具拒读 `/tmp/`。

### Echo task 模式
翻译任务容易触发 Codex 的 echo behavior（只输出文件内容不执行）。prompt 里必须写「用 Write 工具直接写到文件路径」。

### Codex 5h 用法限制
撞 limit 时 session 仍在但不出结果。此时切 Coco（Trae CLI）作为 fallback。Coco session 用 `/tmp/tmux-coco/socket`。

## 7. Verification

```bash
# 检查 HTML 存在且非空
ls -la /tmp/usersite/agent_learning/articles/{slug}.html
# 检查索引计数
grep -c "已发布" /tmp/usersite/agent_learning/index.html
grep "{slug}" /tmp/usersite/agent_learning/index.html
# 检查 commit
cd /tmp/usersite && git log -1 --oneline
# 验证线上（push 后）
curl -sI https://classmatexiaoming96-ux.github.io/agent_learning/articles/{slug}.html | head -3
```
