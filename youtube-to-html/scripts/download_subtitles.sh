#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: download_subtitles.sh VIDEO_ID" >&2
  exit 2
fi

VIDEO_ID="$1"
RESEARCH_DIR="/tmp/yt-to-doc-research"
RAW_DIR="${RESEARCH_DIR}/raw"
COOKIES_FILE="${RESEARCH_DIR}/youtube_cookies.txt"

mkdir -p "${RAW_DIR}"

yt-dlp --cookies "${COOKIES_FILE}" \
  --write-auto-sub --sub-lang en --skip-download \
  --output "${RAW_DIR}/%(video_id)s.%(ext)s" \
  "https://www.youtube.com/watch?v=${VIDEO_ID}"
