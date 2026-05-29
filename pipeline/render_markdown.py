"""Render clean.json + chapters.json into Feishu-friendly markdown.

Output structure:
    # <title>
    > Speaker · duration · upload_date · [YouTube ↗](url)
    ---
    ## 01 · <chapter title>
    [0:05](url&t=5s) <paragraph text>

    [0:24](url&t=24s) <next paragraph>
    ...

Feishu docx renders standard markdown headings, inline links, paragraphs, and
blockquotes, so we keep the format minimal and portable.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def hms(seconds: float) -> str:
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def _group(paragraphs: list[dict], chapter_starts: list[dict]) -> list[dict]:
    starts = sorted(chapter_starts, key=lambda c: c["start"])
    chapters = [{"title": c["title"], "start": c["start"], "paragraphs": []}
                for c in starts]
    for p in paragraphs:
        idx = 0
        for i, c in enumerate(starts):
            if p["start"] >= c["start"]:
                idx = i
            else:
                break
        chapters[idx]["paragraphs"].append(p)
    return [c for c in chapters if c["paragraphs"]]


def render(clean_json: Path, chapters_json: Path, out_md: Path) -> str:
    doc = json.loads(clean_json.read_text())
    chapter_starts = json.loads(chapters_json.read_text())
    chapters = _group(doc["paragraphs"], chapter_starts)

    yt = doc["yt_url"]
    upload = doc.get("upload_date") or ""
    upload_fmt = (f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}"
                  if len(upload) == 8 else upload)

    lines = []
    lines.append(f"# {doc['title']}")
    lines.append("")
    lines.append(f"> {doc['uploader']} · {hms(doc['duration'])} · {upload_fmt} · "
                 f"[YouTube ↗]({yt})")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, ch in enumerate(chapters, 1):
        lines.append(f"## {i:02d} · {ch['title']}")
        lines.append("")
        for p in ch["paragraphs"]:
            t = int(p["start"])
            lines.append(f"[{hms(p['start'])}]({yt}&t={t}s) {p['text']}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_字幕来源：YouTube · 段落由脚本自动分段 · 时间戳点击跳转 YouTube_")
    lines.append("")

    md = "\n".join(lines)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md)
    return md


if __name__ == "__main__":
    vid = sys.argv[1]
    md = render(Path("raw") / f"{vid}.clean.json",
                Path("raw") / f"{vid}.chapters.json",
                Path("out/md") / f"{vid}.md")
    print(f"written: out/md/{vid}.md  ({len(md):,} chars)")
