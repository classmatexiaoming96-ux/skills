"""Batch orchestrator: YouTube URLs → HTML docs + index page.

Usage:
    python run.py --url "https://youtu.be/XXXX"
    python run.py --urls-file urls.txt --concurrency 3
    python run.py --urls-file urls.txt --force      # re-process even if html exists

Per-video pipeline:
    fetch (yt-dlp) → clean (VTT→paragraphs) → render_html (with chapters.json if present)

Idempotency:
    - fetch skips if raw/<vid>.en.vtt + raw/<vid>.info.json exist
    - the orchestrator skips entire video if out/html/<vid>.html exists (unless --force)
    - chapters.json is read if present, otherwise heuristic fallback
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pipeline import clean, fetch, render_html, render_markdown, push_feishu

ROOT = Path(__file__).parent
RAW = ROOT / "raw"
OUT_HTML = ROOT / "out" / "html"
OUT_MD = ROOT / "out" / "md"
FEISHU_URLS_JSON = ROOT / "out" / "feishu_urls.json"


def load_feishu_urls() -> dict:
    if FEISHU_URLS_JSON.exists():
        return json.loads(FEISHU_URLS_JSON.read_text())
    return {}


def save_feishu_urls(d: dict) -> None:
    FEISHU_URLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    FEISHU_URLS_JSON.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def process_one(url_or_id: str, force_html: bool, force_feishu: bool,
                targets: set[str], feishu_pushed: dict,
                folder_token: str | None) -> dict:
    """Run the pipeline for one video. Returns a record for the index page."""
    vid = fetch.extract_video_id(url_or_id)
    html_path = OUT_HTML / f"{vid}.html"
    md_path = OUT_MD / f"{vid}.md"
    clean_path = RAW / f"{vid}.clean.json"
    chapters_path = RAW / f"{vid}.chapters.json"

    # Always need the cleaned transcript before rendering anything.
    html_needed = "html" in targets and (force_html or not html_path.exists())
    feishu_needed = "feishu" in targets and (force_feishu or vid not in feishu_pushed)

    if not html_needed and not feishu_needed:
        info = json.loads((RAW / f"{vid}.info.json").read_text())
        return {"video_id": vid, "status": "skipped",
                "title": info.get("title", ""),
                "uploader": info.get("uploader", ""),
                "duration": info.get("duration") or 0,
                "upload_date": info.get("upload_date", ""),
                "feishu_url": feishu_pushed.get(vid, {}).get("doc_url")}

    f = fetch.fetch(url_or_id, RAW)
    doc = clean.build(f["video_id"], f["info"], f["vtt"])
    clean_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))

    if html_needed:
        render_html.render(clean_path, html_path,
                           chapters_path if chapters_path.exists() else None)

    feishu_url = feishu_pushed.get(vid, {}).get("doc_url")
    if feishu_needed:
        if not chapters_path.exists():
            raise RuntimeError(f"missing {chapters_path} — feishu push needs "
                               "a chapters file (hand-write or run name_chapters.py)")
        render_markdown.render(clean_path, chapters_path, md_path)
        if force_feishu and vid in feishu_pushed:
            print(f"[warn] --force-feishu will create a duplicate doc for "
                  f"{vid}; old: {feishu_pushed[vid]['doc_url']}")
        pushed = push_feishu.push(doc["title"], md_path, folder_token)
        feishu_url = pushed["doc_url"]
        # mutation is safe here: each worker writes to a distinct key
        feishu_pushed[vid] = {**pushed, "title": doc["title"]}

    return {"video_id": vid, "status": "ok",
            "title": doc["title"], "uploader": doc["uploader"],
            "duration": doc["duration"], "upload_date": doc["upload_date"],
            "is_auto_subs": f["is_auto"],
            "feishu_url": feishu_url}


def load_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = []
    if args.url:
        urls.extend(args.url)
    if args.urls_file:
        for line in Path(args.urls_file).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def render_index(records: list[dict]) -> None:
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "pipeline" / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    tmpl = env.get_template("index.html.j2")
    talks = []
    for r in records:
        upload = r.get("upload_date") or ""
        upload_fmt = (f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}"
                      if len(upload) == 8 else upload)
        talks.append({
            "title": r["title"], "uploader": r["uploader"],
            "duration_hms": render_html.hms(r["duration"]),
            "upload_date_fmt": upload_fmt,
            "html_path": f"{r['video_id']}.html",
            "yt_url": f"https://www.youtube.com/watch?v={r['video_id']}",
        })
    talks.sort(key=lambda t: t["upload_date_fmt"], reverse=True)
    html = tmpl.render(talks=talks,
                       generated_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
    (OUT_HTML / "index.html").write_text(html)
    print(f"index: {OUT_HTML / 'index.html'}  ({len(talks)} talks)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", help="repeatable")
    ap.add_argument("--urls-file", type=Path)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--force", action="store_true",
                    help="re-render HTML even if it exists (does NOT trigger "
                         "feishu re-push; use --force-feishu for that)")
    ap.add_argument("--force-feishu", action="store_true",
                    help="re-push to feishu (CREATES A DUPLICATE doc — only "
                         "use when you've explicitly deleted the old one)")
    ap.add_argument("--target", choices=["html", "feishu", "both"],
                    default="html",
                    help="what to produce per video (default: html)")
    ap.add_argument("--folder-token", default=None,
                    help="feishu folder token; default: drive root")
    args = ap.parse_args(argv)

    urls = load_urls(args)
    if not urls:
        ap.error("provide --url or --urls-file")

    targets = {"html"} if args.target == "html" else (
        {"feishu"} if args.target == "feishu" else {"html", "feishu"})

    OUT_HTML.mkdir(parents=True, exist_ok=True)
    feishu_pushed = load_feishu_urls()
    records: list[dict] = []
    failures: list[tuple[str, str]] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(process_one, u, args.force, args.force_feishu,
                          targets, feishu_pushed, args.folder_token): u
                for u in urls}
        for fut in as_completed(futs):
            url = futs[fut]
            try:
                rec = fut.result()
                records.append(rec)
                fu = f" → {rec['feishu_url']}" if rec.get("feishu_url") else ""
                print(f"[{rec['status']:>7}] {rec['video_id']}  "
                      f"{rec['title'][:60]}{fu}")
            except Exception as e:
                failures.append((url, str(e)))
                print(f"[ FAIL ] {url}: {e}", file=sys.stderr)
                traceback.print_exc(limit=2)

    if "feishu" in targets:
        save_feishu_urls(feishu_pushed)
    if "html" in targets and records:
        render_index(records)
    print(f"\nDone. ok={sum(1 for r in records if r['status']=='ok')} "
          f"skipped={sum(1 for r in records if r['status']=='skipped')} "
          f"failed={len(failures)}")
    return 1 if failures and not records else 0


if __name__ == "__main__":
    sys.exit(main())
