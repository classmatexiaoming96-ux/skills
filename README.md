# yt-to-doc

A Claude Code skill that turns YouTube tech-talk URLs into polished Feishu (Lark) Cloud Docs + standalone HTML pages, with optional Chinese restructured versions (mermaid diagrams, tables, reorganized content — not a literal translation).

The mechanical pipeline is Python; the Chinese restructuring step is driven by Claude reading the English transcript and writing a fresh Chinese version, with this skill providing the style guide and Feishu-specific syntax rules.

## What you get

- **English path**: YouTube URL → cleaned transcript → chaptered HTML + Feishu doc
- **Chinese path**: English transcript → Claude-restructured Chinese markdown → Chinese HTML + Feishu doc overwrite
- Idempotent batch orchestrator with concurrency
- Index page for all rendered talks (for GitHub Pages / internal site)

## Install as a Claude Code skill

```bash
git clone https://github.com/<owner>/<repo>.git
cp -r <repo>/skills/yt-to-doc ~/.claude/skills/
cd ~/.claude/skills/yt-to-doc
pip install -r requirements.txt
```

Claude Code will pick up `SKILL.md` automatically. Trigger by asking Claude something like:

- "Turn this YouTube URL into a Feishu doc"
- "把这个 YouTube 视频做成中文飞书文档"
- "Refresh the Feishu doc for VID with a Chinese restructured version"

## Use the pipeline directly (no Claude needed)

```bash
# English HTML + Feishu in one shot
python run.py --url https://www.youtube.com/watch?v=VID --target both

# Batch from a URL list, concurrency 3
python run.py --urls-file urls.txt --target both --concurrency 3

# Only HTML, force re-render
python run.py --urls-file urls.txt --target html --force

# Chinese HTML (assumes you've written out/md_zh/<vid>.md already)
python -m pipeline.render_zh VID
```

## External requirements

| Requirement | Purpose | Setup |
|---|---|---|
| Python 3.10+ | runtime | — |
| `yt-dlp` | YouTube subtitle/metadata fetch | `pip install yt-dlp` (in requirements.txt) |
| `bytedcli` | push markdown to Feishu via MCP bridge | install per ByteDance internal docs |
| `ANTHROPIC_API_KEY` | only if running batch chapter naming | env var |
| `youtube_cookies.txt` (optional) | bypass YouTube bot checks on cloud/dev VMs | Netscape-format cookies at project root |

## Directory contract

When the skill runs, the working directory should look like:

```
<workdir>/
├── urls.txt              # one URL per line, # comments OK
├── raw/                  # fetcher output (vtt, info.json, clean.json, chapters.json)
└── out/
    ├── html/             # English HTML
    ├── html_zh/          # Chinese HTML
    ├── md/               # English markdown (Feishu doc body)
    ├── md_zh/            # Chinese restructured markdown
    └── feishu_urls.json  # video_id ↔ Feishu doc_id, auto-maintained
```

`out/feishu_urls.json` is the single source of truth for which Feishu doc corresponds to which video. Don't edit by hand unless you want to re-create a doc — `run.py` reads it on start and writes back after every Feishu push.

## Pipeline modules

| Module | What it does |
|---|---|
| `pipeline/fetch.py` | yt-dlp wrapper: VTT + info.json |
| `pipeline/clean.py` | VTT → paragraphs JSON (rolling-line dedup, filler strip, sentence split) |
| `pipeline/name_chapters.py` | Optional Claude-driven chapter title generation |
| `pipeline/render_html.py` | English HTML via Jinja2 templates |
| `pipeline/render_markdown.py` | English markdown for Feishu body |
| `pipeline/render_zh.py` | Chinese markdown → standalone HTML with mermaid + TOC |
| `pipeline/push_feishu.py` | `bytedcli feishu docs create-doc` wrapper |
| `run.py` | Orchestrator: fetch → clean → render → push |

## Chinese restructuring style

See `SKILL.md` for the full style guide and `examples/example_zh.md` for a reference output (a real Chinese version of an Anthropic talk on agent decomposition).

Key conventions:

- Reorganize argument structure, don't translate paragraph-by-paragraph
- 6–10 `##` sections, with `###` sub-points
- 2–4 mermaid diagrams visualizing flows or comparisons
- Tables for any "compare options" content
- Preserve timestamp links to YouTube
- End with a 一句话外带 takeaway

## Feishu mermaid gotchas

Feishu's mermaid renderer is stricter than the spec. The skill's SKILL.md
documents these in detail, but the short version:

- ❌ `rect rgb(...)` blocks — use `classDef` instead
- ❌ Parens inside `<br/>` inside node labels
- ❌ Double-quotes inside `[node]` labels
- ❌ Semicolons inside `sequenceDiagram`

`bytedcli ... update-doc --mode overwrite` returns `success=true` even when
mermaid boards fail to write. After any push, **eyeball the Feishu doc** for
empty board placeholders.

## License

MIT (or whatever the host repo declares).
