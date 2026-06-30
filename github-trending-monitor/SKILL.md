---
name: github-trending-monitor
description: Daily GitHub Trending source-level deep-dive analysis. Scans trending AI/coding repos, generates architecture HTML pages, and deploys to GitHub Pages.
triggers:
  - "每日 GitHub Trending 监控"
  - "扫描 GitHub 热门仓库"
  - "github trending 深度分析"
---

# GitHub Trending 每日监控与源码级深度分析

每日从 GitHub 搜索热门 AI / 编码相关仓库，克隆源码，分析架构，生成深色主题的源码级深度分析 HTML 页面，部署到 GitHub Pages。

## 数据获取
- GitHub API: `q=created:>=5_days_ago+stars:>250+(agent+OR+AI+LLM+coding+copilot)`
- 过滤已有项目，评估标准：coding agent/LLM 相关、架构有亮点、Stars>250、活跃

## 生成流程
每个项目 30-60 分钟：clone → 读源码 → 主页面 → 2-4 子页面 → 质量校验 → 部署

## 本地模板
- 主页面模板：`templates/main-page.html`
- 子页面模板：`templates/sub-page.html`
- 共用样式骨架：`templates/layout-shell.css`

生成新页面时只引用本 skill 目录内的 `templates/` 文件，不依赖外部模板 skill 路径。

## 质量硬约束
- 主页面：源码引用≥8、行号引用≥50、H3≥10、深度阅读入口≥2
- 子页面：≥2个，每个≥20行号+≥3 H3
- 每个代码块用 `<span class="ln">` 标注真实行号
- 每个主页面≥1个 mermaid 图
- quality_gate 实测项目全部命中才算通过
