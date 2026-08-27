# Skills

Reusable Agent Skills for Claude Code, Cursor, Codex, OpenCode, Hermes, and
other coding agents that support the `SKILL.md` convention.

| Skill | Description | Directory |
|-------|-------------|-----------|
| yt-to-doc | YouTube tech-talk → Feishu Cloud Doc + HTML | `yt-to-doc/` |
| youtube-to-html | YouTube video → GitHub Pages HTML (Chinese article) | `youtube-to-html/` |
| daily-digest | Daily AI news digest → GitHub Pages | `daily-digest/` |
| github-trending-monitor | Daily GitHub Trending source-level analysis | `github-trending-monitor/` |
| agent-learning-article | Anthropic Engineering blog → Chinese HTML article for Agent Learning site | `agent-learning-article/` |
| lark-beautiful-article | Source material → polished, native Feishu/Lark article | `lark-beautiful-article/` |
| lark-archify | Validated Archify diagram → editable Feishu/Lark whiteboard | `lark-archify/` |
| lark-kb-retriever | Progressive Feishu/Lark Drive and Wiki retrieval with citations | `lark-kb-retriever/` |

## yt-to-doc

Turn YouTube tech-talk URLs into polished Feishu (Lark) Cloud Docs + standalone HTML pages, with optional Chinese restructured versions.

See [yt-to-doc/README.md](yt-to-doc/README.md) for full documentation, or [yt-to-doc/SKILL.md](yt-to-doc/SKILL.md) for the Claude Code skill definition.

## youtube-to-html

Daily cron: fetch a YouTube tech video, download subtitles, generate a detailed Chinese long-form HTML article, deploy to GitHub Pages.

## daily-digest

Daily cron: aggregate AI news from HN / Reddit / GitHub / product launches, render a dark-themed HTML digest, deploy to GitHub Pages.

## github-trending-monitor

Daily cron: scan GitHub Trending for new AI/coding repos, clone and analyze source code, generate architecture deep-dive HTML pages, deploy to GitHub Pages.

## Lark document skills

The three `lark-*` skills are portable orchestration skills built on the
official [`larksuite/cli`](https://github.com/larksuite/cli):

- `lark-beautiful-article` edits heterogeneous source material into a native
  Feishu/Lark document and uses safe, revision-aware updates.
- `lark-archify` keeps Archify's typed JSON and validation workflow, then
  publishes the trusted artifact as an editable whiteboard.
- `lark-kb-retriever` searches Drive and Wiki progressively, reads only the
  necessary sections, and returns document/block-level citations.

They intentionally do not contain Codex-only UI metadata, so the same folders
can be installed by any Agent Skills-compatible coding agent. Runtime use
requires `lark-cli`; `lark-archify` additionally requires the upstream
[`archify`](https://github.com/tt-a1i/archify) skill.
