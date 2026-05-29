"""VTT → structured paragraphs.

Output schema:
{
  "video_id": str, "title": str, "uploader": str, "duration": int,
  "upload_date": str, "yt_url": str,
  "paragraphs": [{"start": float, "text": str, "sentences": [str, ...]}],
}
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import webvtt


@dataclass
class Cue:
    start: float
    end: float
    text: str


def _normalize(text: str) -> str:
    import html
    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Conservative filler patterns. Skipping "kind of" / "sort of" / "like" —
# too many legitimate uses in technical speech to strip safely.
_FILLERS = [
    (re.compile(r"\[(?:Applause|Music|Laughter)\]", re.IGNORECASE), ""),
    (re.compile(r"(?<=[.!?]\s)(?:Uh|Um|Ah),?\s+"), ""),  # leading fillers in a sentence
    (re.compile(r"^(?:Uh|Um|Ah),?\s+"), ""),             # at very start
    (re.compile(r",?\s+\b(?:uh|um|ah)\b,?(?=\s)", re.IGNORECASE), ""),  # interior
    (re.compile(r"\byou know,\s+"), ""),
    (re.compile(r"\bI mean,\s+"), ""),
]


def strip_fillers(text: str) -> str:
    for pat, repl in _FILLERS:
        text = pat.sub(repl, text)
    text = re.sub(r"\s+([,.!?])", r"\1", text)  # fix " ," / " ." left behind
    text = re.sub(r"\s{2,}", " ", text).strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


_WORD_TS = re.compile(r"<\d{2}:\d{2}:\d{2}\.\d{3}>")
_C_TAG = re.compile(r"</?c>")


def load_cues(vtt_path: Path) -> list[Cue]:
    """Detects YouTube's auto-sub rolling 2-line format (carryover line 1 +
    new content line 2, with per-word timestamps) and extracts only the new
    content. Manual subs (single coherent text) go through unchanged."""
    raw = vtt_path.read_text()
    is_rolling = bool(_WORD_TS.search(raw))

    cues: list[Cue] = []
    for c in webvtt.read(str(vtt_path)):
        if is_rolling:
            t = _extract_new_line(c.text)
        else:
            t = _normalize(c.text)
        if not t:
            continue
        cues.append(Cue(c.start_in_seconds, c.end_in_seconds, t))
    return cues


def _extract_new_line(cue_text: str) -> str:
    text = _WORD_TS.sub("", cue_text)
    text = _C_TAG.sub("", text)
    non_empty = [l.strip() for l in text.split("\n") if l.strip()]
    if not non_empty:
        return ""
    return _normalize(non_empty[-1])


def dedupe_rolling(cues: list[Cue]) -> list[Cue]:
    """Drop sequential duplicates. After load_cues handles the rolling-line
    case, marker cues (carryover-only) can still echo the previous cue's
    text — this strips those."""
    out: list[Cue] = []
    for c in cues:
        if out and c.text == out[-1].text:
            continue
        out.append(c)
    return out


_SENT_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'\(])")


def merge_into_sentences(cues: list[Cue]) -> list[tuple[float, str]]:
    """Concatenate cue text into one stream while remembering each sentence's
    earliest cue timestamp."""
    if not cues:
        return []
    big = []
    for c in cues:
        big.append((c.start, c.text))
    full = " ".join(t for _, t in big)
    parts = _SENT_END.split(full)
    sentences: list[tuple[float, str]] = []
    cursor = 0
    for s in parts:
        s = s.strip()
        if not s:
            continue
        idx = full.find(s, cursor)
        cursor = idx + len(s) if idx >= 0 else cursor
        sent_start = _ts_at_char(big, idx if idx >= 0 else 0)
        sentences.append((sent_start, s))
    return sentences


def _ts_at_char(big: list[tuple[float, str]], char_pos: int) -> float:
    """Find which cue char_pos falls into, return that cue's start."""
    pos = 0
    for start, text in big:
        nxt = pos + len(text) + 1
        if char_pos < nxt:
            return start
        pos = nxt
    return big[-1][0] if big else 0.0


def group_paragraphs(sentences: list[tuple[float, str]],
                     target_sents: int = 5) -> list[dict]:
    """Group sentences into paragraphs by count. Cue-derived timestamps don't
    expose real speaker pauses, so a gap heuristic mis-splits — count-based
    grouping is more reliable for spoken-tech transcripts."""
    paragraphs: list[dict] = []
    cur: list[tuple[float, str]] = []
    for sent in sentences:
        cur.append(sent)
        if len(cur) >= target_sents:
            paragraphs.append(_make_para(cur))
            cur = []
    if cur:
        paragraphs.append(_make_para(cur))
    return paragraphs


def _make_para(group: list[tuple[float, str]]) -> dict:
    cleaned = [strip_fillers(s) for s in (s for _, s in group)]
    cleaned = [s for s in cleaned if s]
    return {
        "start": group[0][0],
        "text": " ".join(cleaned),
        "sentences": cleaned,
    }


def build(video_id: str, info_path: Path, vtt_path: Path) -> dict:
    info = json.loads(info_path.read_text())
    cues = load_cues(vtt_path)
    cues = dedupe_rolling(cues)
    sentences = merge_into_sentences(cues)
    paragraphs = group_paragraphs(sentences)
    return {
        "video_id": video_id,
        "title": info.get("title", ""),
        "uploader": info.get("uploader", ""),
        "duration": info.get("duration") or 0,
        "upload_date": info.get("upload_date", ""),
        "yt_url": f"https://www.youtube.com/watch?v={video_id}",
        "description": (info.get("description") or "").strip(),
        "paragraphs": paragraphs,
    }


if __name__ == "__main__":
    import sys
    vid = sys.argv[1]
    base = Path("raw")
    doc = build(vid, base / f"{vid}.info.json", base / f"{vid}.en.vtt")
    print(f"paragraphs: {len(doc['paragraphs'])}")
    print(f"first para start={doc['paragraphs'][0]['start']:.1f}s")
    print(doc['paragraphs'][0]['text'][:200])
    out = Path("raw") / f"{vid}.clean.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"written: {out}")
