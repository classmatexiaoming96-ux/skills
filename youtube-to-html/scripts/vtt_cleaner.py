#!/usr/bin/env python3
import re
import sys
from pathlib import Path


RAW_DIR = Path("/tmp/yt-to-doc-research/raw")
CHUNK_SIZE = 8000


def parse_vtt_clean(path):
    content = path.read_text(encoding="utf-8")
    segments = []

    for line in content.splitlines():
        if re.match(r"(\d{2}:\d{2}:\d{2}\.\d{3}) -->", line):
            continue
        if line.strip() in ("", "WEBVTT", "Kind: captions", "Language: en"):
            continue

        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean:
            segments.append(clean)

    return " ".join(segments)


def main():
    if len(sys.argv) != 2:
        print("Usage: vtt_cleaner.py VIDEO_ID", file=sys.stderr)
        return 2

    video_id = sys.argv[1]
    text = parse_vtt_clean(RAW_DIR / f"{video_id}.en.vtt")

    for i in range(0, len(text), CHUNK_SIZE):
        chunk_num = i // CHUNK_SIZE
        chunk = text[i : i + CHUNK_SIZE]
        output_path = RAW_DIR / f"{video_id}_chunk_{chunk_num}.txt"
        output_path.write_text(chunk, encoding="utf-8")
        print(f"Chunk {chunk_num}: {len(chunk)} chars")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
