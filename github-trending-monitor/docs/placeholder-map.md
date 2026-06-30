# 主页面占位符索引 (main-page.html)

按出现顺序列出 main-page.html 模板里所有 `{{占位符}}`，方便生成时填充。

## HTML <head> 区
| 占位符 | 说明 | 示例 |
|---|---|---|
| `{{PROJECT_NAME}}` | 项目名（kebab-case） | `opentag` |
| `{{TAGLINE}}` | 一句话标语 | `@agent 跨平台协议` |
| `{{META_DESCRIPTION}}` | meta description（用于 SEO） | `amplifthq/opentag 源码级深度解析` |
| `{{STAR}}` | accent 主色（hex） | `#e8825a` |
| `{{STAR_SOFT}}` | accent 浅色 | `#f0a585` |
| `{{STAR_DEEP}}` | accent 深色 | `#c0653f` |

## Side Nav
| 占位符 | 说明 | 示例 |
|---|---|---|
| `{{PROJECT_ACCENT}}` | nav 标题斜体高亮部分 | `Claw` |
| `{{LANG}}` | 主语言 | `TypeScript` |
| `{{ECOSYSTEM}}` | 生态/包管理器 | `pnpm monorepo` |
| `{{SEC1_TITLE}}` ~ `{{SEC6_TITLE}}` | 6 个章节标题 | 见 SKILL.md §6 |
| `{{STARS}}` | GitHub stars 数 | `1,234` |
| `{{CREATED_AT}}` | 创建时间 | `2026-04` |
| `{{REPO_URL}}` | 仓库 URL | `https://github.com/owner/repo` |
| `{{OWNER}}` | 仓库 owner | `amplifthq` |
| `{{REPO}}` | 仓库名 | `opentag` |

## Hero
| 占位符 | 说明 | 示例 |
|---|---|---|
| `{{HERO_DESCRIPTION}}` | hero 段正文（1-2 句） | `OpenTag 把 Slack/GitHub/Lark/Telegram 上的 @agent 提及统一调度到本地 Codex/Claude Code，git worktree 隔离 + 3-mode 安全。` |
| `{{LOC}}` | 代码行数（k/M） | `6.6K` |
| `{{FILE_COUNT}}` | 文件数 | `328` |
| `{{LAST_COMMIT}}` | 最近 commit 时间（相对） | `3d ago` |
| `{{HERO_ART}}` | 可选 SVG/图（默认空） | （留空即可） |

## Overview (§00)
| 占位符 | 说明 |
|---|---|
| `{{OVERVIEW_PARA_1}}` `{{OVERVIEW_PARA_2}}` | 概述正文 2 段 |
| `{{ARCH_PATTERN}}` | 架构模式 |
| `{{CORE_ABSTRACT}}` | 核心抽象 |
| `{{PERF_DATA}}` | 性能/精度数据 |
| `{{DOWNSTREAM}}` | 下游依赖 |

## Architecture (§01)
| 占位符 | 说明 |
|---|---|
| `{{SEC1_INTRO}}` | §01 引言 |
| `{{FLOW_DIAGRAM_1}}` | ASCII 流程图（见 SKILL.md §9） |
| `{{MODULES_DESC}}` | 模块清单说明 |
| `{{MODULE_CARDS}}` | 模块卡片 HTML（g3 grid） |
| `{{KEY_STRUCT_FILE}}` `{{KEY_STRUCT_LINE_START}}` `{{KEY_STRUCT_LINE_END}}` | 关键数据结构定位 |
| `{{KEY_STRUCT_CODE}}` | 关键数据结构代码（含行号 `<span class="ln">`） |
| `{{DEEP_LINK_1}}` `{{DEEP_LINK_1_TITLE}}` | 子页面 1 入口 |

## Core Modules (§02)
| 占位符 | 说明 |
|---|---|
| `{{MODULE_A_TITLE}}` `{{MODULE_A_DESC}}` | 模块 A 标题/描述 |
| `{{MODULE_A_FILE}}` `{{MODULE_A_LINE_START}}` `{{MODULE_A_LINE_END}}` | 模块 A 代码定位 |
| `{{MODULE_A_CODE}}` | 模块 A 代码（含行号） |
| `{{MODULE_B_*}}` | 模块 B 同上 |
| `{{DEEP_LINK_2}}` `{{DEEP_LINK_2_TITLE}}` | 子页面 2 入口 |

## Key Flow (§03)
| 占位符 | 说明 |
|---|---|
| `{{SEC3_INTRO}}` | §03 引言 |
| `{{FLOW_A_TITLE}}` `{{FLOW_A_DIAGRAM}}` | 流程 A |
| `{{FLOW_B_TITLE}}` `{{FLOW_B_DIAGRAM}}` | 流程 B |
| `{{DEEP_LINK_3}}` `{{DEEP_LINK_3_TITLE}}` | 子页面 3 入口 |

## Tests (§04)
| 占位符 | 说明 |
|---|---|
| `{{SEC4_INTRO}}` | §04 引言 |
| `{{TEST_COVERAGE_DESC}}` | 测试覆盖说明 |
| `{{TEST_FILE}}` `{{TEST_LINE_START}}` `{{TEST_LINE_END}}` | 测试代码定位 |
| `{{TEST_CODE}}` | 测试代码（含行号） |
| `{{EDGE_CASES}}` | 边界/失败模式（`<li>` 列表） |

## Highlights (§05) & Risks (§06)
| 占位符 | 说明 |
|---|---|
| `{{HIGHLIGHT_CARDS}}` | 亮点卡片 HTML（g2 grid） |
| `{{RISKS_INTRO}}` | 风险段引言 |
| `{{RISK_CARDS}}` | 风险卡片 HTML（g2 grid） |

## Footer
| 占位符 | 说明 |
|---|---|
| `{{DATE}}` | 生成日期 |
| （其他用 nav 已有值） | |

---

## 子页面 (sub-page.html) 关键占位符

| 占位符 | 说明 |
|---|---|
| `{{TOPIC}}` `{{TOPIC_TITLE}}` | 子页面主题（中英文均可） |
| `{{INTRO_FILE}}` `{{INTRO_LINE_START}}` `{{INTRO_LINE_END}}` `{{INTRO_CODE}}` | 导入链代码 |
| `{{SUB_TOPIC_A/B_*}}` | 子主题 A/B（各对应一段代码） |
| `{{KEY_FLOW_DIAGRAM}}` `{{FLOW_DESC}}` | 关键流程 |
| `{{EDGE_CASES}}` | 边界/失败模式列表 |
| `{{RELATED_CARDS}}` | 关联模块卡片 |