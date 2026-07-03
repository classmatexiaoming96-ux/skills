# Skills

Four Hermes Agent skills:

| Skill | Description | Directory |
|-------|-------------|-----------|
| yt-to-doc | YouTube tech-talk → Feishu Cloud Doc + HTML | `yt-to-doc/` |
| youtube-to-html | YouTube video → GitHub Pages HTML (Chinese article) | `youtube-to-html/` |
| daily-digest | Daily AI news digest → GitHub Pages | `daily-digest/` |
| github-trending-monitor | Daily GitHub Trending source-level analysis | `github-trending-monitor/` |
| agent-learning-article | Anthropic Engineering blog → Chinese HTML article for Agent Learning site | `agent-learning-article/` |

## yt-to-doc

Turn YouTube tech-talk URLs into polished Feishu (Lark) Cloud Docs + standalone HTML pages, with optional Chinese restructured versions.

See [yt-to-doc/README.md](yt-to-doc/README.md) for full documentation, or [yt-to-doc/SKILL.md](yt-to-doc/SKILL.md) for the Claude Code skill definition.

## youtube-to-html

Daily cron: fetch a YouTube tech video, download subtitles, generate a detailed Chinese long-form HTML article, deploy to GitHub Pages.

## daily-digest

Daily cron: aggregate AI news from HN / Reddit / GitHub / product launches, render a dark-themed HTML digest, deploy to GitHub Pages.

## github-trending-monitor

Daily cron: scan GitHub Trending for new AI/coding repos, clone and analyze source code, generate architecture deep-dive HTML pages, deploy to GitHub Pages.
