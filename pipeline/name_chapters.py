"""Auto-generate chapters.json for a transcript using Claude.

Requires ANTHROPIC_API_KEY. For single videos you can hand-write chapters.json
instead; this is the batch path.

Usage:
    python pipeline/name_chapters.py <video_id>
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path


PROMPT = """You are given a numbered list of transcript paragraphs from a tech talk, each with its start time (in seconds). Your task is to divide them into coherent chapters and give each chapter a concise descriptive title.

Rules:
- Produce 6-12 chapters depending on talk length and topic shifts.
- Each chapter's "start" must be the start time of the first paragraph in that chapter.
- Titles must be 3-10 words, declarative, and describe the content (not generic like "Part 2").
- Output ONLY valid JSON: a list of objects {"start": <int seconds>, "title": "<title>"}. No prose, no markdown fences.

Paragraphs:
"""


def build_user_message(clean_doc: dict) -> str:
    lines = [PROMPT]
    for i, p in enumerate(clean_doc["paragraphs"]):
        text = p["text"][:300].replace("\n", " ")
        lines.append(f"[{i:03d}] t={int(p['start'])}s: {text}")
    return "\n".join(lines)


def call_claude(prompt: str) -> str:
    from anthropic import Anthropic
    client = Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def parse_chapters(raw: str) -> list[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw)


def main(video_id: str) -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set. Hand-write raw/{vid}.chapters.json "
              "instead, or set the key and rerun.", file=sys.stderr)
        sys.exit(2)

    clean_path = Path("raw") / f"{video_id}.clean.json"
    out_path = Path("raw") / f"{video_id}.chapters.json"
    doc = json.loads(clean_path.read_text())

    raw = call_claude(build_user_message(doc))
    chapters = parse_chapters(raw)
    out_path.write_text(json.dumps(chapters, indent=2, ensure_ascii=False))
    print(f"written: {out_path}  ({len(chapters)} chapters)")
    for c in chapters:
        print(f"  {c['start']:>5}s  {c['title']}")


if __name__ == "__main__":
    main(sys.argv[1])
