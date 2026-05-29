"""Render a cleaned transcript JSON into a self-contained HTML file."""
from __future__ import annotations
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def hms(seconds: float) -> str:
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def chapter_title(first_text: str, max_words: int = 8) -> str:
    """Fallback: first N words of the chapter's opening paragraph.
    Used only when no chapters.json is available."""
    words = first_text.split()
    title = " ".join(words[:max_words]).rstrip(".,;:")
    return title + ("…" if len(words) > max_words else "")


def group_into_chapters(paragraphs: list[dict],
                        chapter_starts: list[dict] | None = None,
                        paras_per_chapter: int = 5) -> list[dict]:
    """If chapter_starts is provided (list of {start, title}), assign each
    paragraph to the chapter whose start <= paragraph.start. Otherwise fall
    back to naive N-paragraphs-per-chapter grouping."""
    if not chapter_starts:
        chapters = []
        for i in range(0, len(paragraphs), paras_per_chapter):
            group = paragraphs[i:i + paras_per_chapter]
            chapters.append({"title": chapter_title(group[0]["text"]),
                             "paragraphs": group})
        return chapters

    sorted_starts = sorted(chapter_starts, key=lambda c: c["start"])
    chapters = [{"title": c["title"], "start": c["start"], "paragraphs": []}
                for c in sorted_starts]
    for p in paragraphs:
        idx = 0
        for i, c in enumerate(sorted_starts):
            if p["start"] >= c["start"]:
                idx = i
            else:
                break
        chapters[idx]["paragraphs"].append(p)
    return [c for c in chapters if c["paragraphs"]]


def render(clean_json: Path, out_html: Path,
           chapters_json: Path | None = None) -> None:
    doc = json.loads(clean_json.read_text())
    env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["hms"] = hms
    tmpl = env.get_template("talk.html.j2")

    chapter_starts = None
    if chapters_json and chapters_json.exists():
        chapter_starts = json.loads(chapters_json.read_text())
    chapters = group_into_chapters(doc["paragraphs"], chapter_starts)
    upload = doc.get("upload_date") or ""
    upload_fmt = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if len(upload) == 8 else upload

    html = tmpl.render(
        title=doc["title"],
        uploader=doc["uploader"],
        yt_url=doc["yt_url"],
        duration_hms=hms(doc["duration"]),
        upload_date_fmt=upload_fmt,
        chapters=chapters,
    )
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html)
    print(f"written: {out_html}  ({len(html):,} bytes, {len(chapters)} chapters)")


if __name__ == "__main__":
    vid = sys.argv[1]
    render(Path("raw") / f"{vid}.clean.json",
           Path("out/html") / f"{vid}.html",
           Path("raw") / f"{vid}.chapters.json")
