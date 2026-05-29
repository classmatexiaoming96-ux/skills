"""yt-dlp wrapper: download English subs + info.json for a video.

Idempotent: skips download if both files already exist locally.
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path


_YT_ID = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|v/|shorts/))([A-Za-z0-9_-]{11})"
)


def extract_video_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = _YT_ID.search(s)
    if not m:
        raise ValueError(f"could not extract video id from: {url_or_id!r}")
    return m.group(1)


def fetch(url_or_id: str, raw_dir: Path) -> dict:
    """Returns {'video_id', 'vtt', 'info', 'is_auto'} or raises CalledProcessError.

    `is_auto` is True if only auto-generated subs were available (used later
    to decide whether to run punctuation repair).
    """
    vid = extract_video_id(url_or_id)
    raw_dir.mkdir(parents=True, exist_ok=True)
    vtt = raw_dir / f"{vid}.en.vtt"
    info = raw_dir / f"{vid}.info.json"

    if vtt.exists() and info.exists():
        return {"video_id": vid, "vtt": vtt, "info": info,
                "is_auto": _looks_auto(vtt), "skipped": True}

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--js-runtimes", "node",
        "--skip-download",
        "--write-subs", "--write-auto-subs",
        "--sub-lang", "en", "--sub-format", "vtt",
        "--write-info-json",
        "--no-progress",
        "-o", "%(id)s.%(ext)s",
    ]
    # Auto-pick up cookies.txt when present — needed when YouTube bot-checks
    # the IP (common on cloud/dev VPS). Put a Netscape-format file at the
    # project root and yt-dlp will use it.
    cookies = Path(__file__).resolve().parent.parent / "youtube_cookies.txt"
    if cookies.exists():
        cmd += ["--cookies", str(cookies)]
    cmd.append(f"https://www.youtube.com/watch?v={vid}")
    subprocess.run(cmd, cwd=str(raw_dir), check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if not vtt.exists():
        raise RuntimeError(f"no English subtitle found for {vid}")
    return {"video_id": vid, "vtt": vtt, "info": info,
            "is_auto": _looks_auto(vtt), "skipped": False}


def _looks_auto(vtt: Path) -> bool:
    """Heuristic: auto-generated VTT contains 'Kind: captions' AND text is
    typically lowercase / unpunctuated. Cheap check: presence of 'Kind: auto'
    OR header missing punctuation in first cue."""
    head = vtt.read_text()[:2000]
    if "Kind: auto" in head:
        return True
    # Manual subs almost always have capital letters + periods within first 500
    # chars of body. Auto-generated YouTube ASR is all-lowercase, no periods.
    body = head.split("\n\n", 1)[-1] if "\n\n" in head else head
    return ("." not in body[:500]) and not any(c.isupper() for c in body[:200])


if __name__ == "__main__":
    out = fetch(sys.argv[1], Path("raw"))
    print(out)
