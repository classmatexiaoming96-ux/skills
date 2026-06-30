#!/usr/bin/env python3
"""
prefetch.py — gather raw material for the daily AI digest from every source.

Sources (all keyless, stdlib-only):
  • Google News RSS  → AI headlines (en + zh)
  • Hacker News (Algolia API) → top AI stories + Show HN (products)
  • Reddit JSON      → r/MachineLearning, r/LocalLLaMA, r/artificial, r/OpenAI …
  • GitHub           → Trending HTML scrape + Search API (recent high-star AI repos)

Output:
  data/{date}.json   one bundle the curation step reads from.

Notes:
  • Many sources need an egress proxy on this box. Set HTTPS_PROXY / HTTP_PROXY
    (e.g. http://127.0.0.1:7890) or pass --proxy. Each source is wrapped in
    try/except so a single failure never aborts the run; the summary at the end
    reports which buckets came back empty.

Usage:
  python3 scripts/prefetch.py                       # writes data/<today>.json
  python3 scripts/prefetch.py --date 2025-06-18 --proxy http://127.0.0.1:7890
"""
import argparse
import datetime as dt
import json
import os
import re
import ssl
import sys
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

REDDIT_SUBS = ["MachineLearning", "LocalLLaMA", "artificial", "OpenAI", "singularity"]
AI_TERMS = re.compile(r"\b(ai|llm|gpt|claude|gemini|llama|agent|model|openai|"
                      r"anthropic|deepseek|mistral|diffusion|transformer|rag|"
                      r"neural|inference|reasoning|multimodal|fine-?tun)\w*",
                      re.I)

_opener = None


def setup_http(proxy):
    global _opener
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    handlers = [urllib.request.HTTPSHandler(context=ctx)]
    proxy = proxy or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
        print(f"  · using proxy {proxy}", file=sys.stderr)
    _opener = urllib.request.build_opener(*handlers)


def get(url, accept=None, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": accept or "*/*",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    })
    with _opener.open(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def get_json(url, **kw):
    return json.loads(get(url, accept="application/json", **kw))


def clean(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text or "")).strip()


# ---------------------------------------------------------------- Google News
def fetch_google_news():
    """Two queries: broad AI (en) + 中文 AI 新闻; merged, deduped by title."""
    queries = [
        ("https://news.google.com/rss/search?q=artificial+intelligence+when:1d"
         "&hl=en-US&gl=US&ceid=US:en", "en"),
        ("https://news.google.com/rss/search?q=AI+%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD+when:1d"
         "&hl=zh-CN&gl=CN&ceid=CN:zh-Hans", "zh"),
    ]
    items, seen = [], set()
    for url, lang in queries:
        try:
            root = ET.fromstring(get(url, accept="application/rss+xml"))
        except Exception as e:
            print(f"    ! google news ({lang}) failed: {e}", file=sys.stderr)
            continue
        for it in root.iter("item"):
            title = clean(it.findtext("title"))
            if not title or title.lower() in seen:
                continue
            seen.add(title.lower())
            # Google News titles end with " - Source"
            source = ""
            src_el = it.find("source")
            if src_el is not None:
                source = clean(src_el.text)
            elif " - " in title:
                source = title.rsplit(" - ", 1)[1]
            items.append({
                "title": title.rsplit(" - ", 1)[0] if " - " in title else title,
                "url": clean(it.findtext("link")),
                "source": source,
                "time": clean(it.findtext("pubDate")),
                "summary": clean(it.findtext("description"))[:280],
                "lang": lang,
            })
    return items[:40]


# ---------------------------------------------------------------- Hacker News
def fetch_hn():
    """Front-page-weighted AI stories from the last ~36h via Algolia."""
    cutoff = int((dt.datetime.utcnow() - dt.timedelta(hours=36)).timestamp())
    # Algolia rejects comma-joined numericFilters in one param — repeat the param instead.
    base = ("https://hn.algolia.com/api/v1/search?tags=story"
            f"&numericFilters=created_at_i>{cutoff}&numericFilters=points>40&hitsPerPage=60")
    out = []
    try:
        for q in ("AI", "LLM", "GPT", "agent", "model"):
            data = get_json(base + "&query=" + urllib.parse.quote(q))
            for h in data.get("hits", []):
                title = h.get("title") or ""
                if not AI_TERMS.search(title):
                    continue
                out.append({
                    "title": title,
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                    "hn_url": f"https://news.ycombinator.com/item?id={h['objectID']}",
                    "points": h.get("points", 0),
                    "comments": h.get("num_comments", 0),
                    "platform": "Hacker News",
                })
    except Exception as e:
        print(f"    ! hacker news failed: {e}", file=sys.stderr)
    # dedupe by objectID-ish (title) and sort by points
    seen, dedup = set(), []
    for h in sorted(out, key=lambda x: x["points"], reverse=True):
        if h["title"].lower() in seen:
            continue
        seen.add(h["title"].lower())
        dedup.append(h)
    return dedup[:25]


def fetch_show_hn():
    """Show HN launches in the last 3 days — raw material for products/concepts."""
    cutoff = int((dt.datetime.utcnow() - dt.timedelta(days=3)).timestamp())
    url = ("https://hn.algolia.com/api/v1/search?tags=show_hn"
           f"&numericFilters=created_at_i>{cutoff}&numericFilters=points>20&hitsPerPage=40")
    out = []
    try:
        for h in get_json(url).get("hits", []):
            title = h.get("title") or ""
            if not AI_TERMS.search(title):
                continue
            out.append({
                "title": re.sub(r"^Show HN:\s*", "", title),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                "points": h.get("points", 0),
                "comments": h.get("num_comments", 0),
            })
    except Exception as e:
        print(f"    ! show hn failed: {e}", file=sys.stderr)
    return sorted(out, key=lambda x: x["points"], reverse=True)[:15]


# ---------------------------------------------------------------- Reddit
def fetch_reddit():
    out = []
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit=12"
        try:
            data = get_json(url)
        except Exception as e:
            print(f"    ! reddit r/{sub} failed: {e}", file=sys.stderr)
            continue
        for c in data.get("data", {}).get("children", []):
            d = c.get("data", {})
            if d.get("stickied") or d.get("score", 0) < 30:
                continue
            out.append({
                "title": clean(d.get("title")),
                "url": "https://www.reddit.com" + d.get("permalink", ""),
                "link_url": d.get("url_overridden_by_dest") or "",
                "points": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "platform": f"Reddit r/{sub}",
                "selftext": clean(d.get("selftext", ""))[:300],
            })
    return sorted(out, key=lambda x: x["points"], reverse=True)[:25]


# ---------------------------------------------------------------- GitHub
def fetch_github_trending():
    """Scrape github.com/trending?since=daily and keep AI-flavoured repos."""
    out = []
    try:
        htmltext = get("https://github.com/trending?since=daily",
                       accept="text/html")
    except Exception as e:
        print(f"    ! github trending scrape failed: {e}", file=sys.stderr)
        return out
    # each repo row: <h2 ...><a href="/owner/name" ...>
    rows = re.findall(r'<article class="Box-row">(.*?)</article>', htmltext, re.S)
    for row in rows:
        # repo identity lives in the <h2> heading link: /owner/name (exactly 2 path segments)
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", row, re.S)
        m = re.search(r'href="/([^"/]+)/([^"/]+)"', h2.group(1)) if h2 else None
        if not m:
            continue
        owner, name = m.group(1), m.group(2)
        desc_m = re.search(r'<p class="col-9[^"]*">(.*?)</p>', row, re.S)
        desc = clean(desc_m.group(1)) if desc_m else ""
        lang_m = re.search(r'itemprop="programmingLanguage">([^<]+)<', row)
        lang = clean(lang_m.group(1)) if lang_m else ""
        # total stars: the digits inside the …/stargazers" anchor
        stars_m = re.search(r'stargazers"[^>]*>(.*?)</a>', row, re.S)
        stars = ""
        if stars_m:
            dm = re.search(r"[\d,]+", clean(stars_m.group(1)))
            stars = dm.group(0) if dm else ""
        today_m = re.search(r'([\d,]+)\s+stars today', row)
        today = today_m.group(1) if today_m else ""
        blob = f"{owner}/{name} {desc}"
        out.append({
            "owner": owner, "name": name,
            "url": f"https://github.com/{owner}/{name}",
            "desc": desc, "lang": lang, "stars": stars, "stars_today": today,
            "ai_match": bool(AI_TERMS.search(blob)),
        })
    return out


def fetch_github_search():
    """Recently-created, fast-rising AI repos via the Search API (fallback)."""
    since = (dt.date.today() - dt.timedelta(days=14)).isoformat()
    q = urllib.parse.quote(f"topic:ai topic:llm created:>{since}")
    url = (f"https://api.github.com/search/repositories?q={q}"
           "&sort=stars&order=desc&per_page=15")
    out = []
    try:
        for r in get_json(url).get("items", []):
            out.append({
                "owner": r["owner"]["login"], "name": r["name"],
                "url": r["html_url"], "desc": r.get("description") or "",
                "lang": r.get("language") or "", "stars": f"{r['stargazers_count']:,}",
                "stars_today": "", "ai_match": True,
            })
    except Exception as e:
        print(f"    ! github search failed: {e}", file=sys.stderr)
    return out


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data"))
    ap.add_argument("--proxy", default=None)
    args = ap.parse_args()

    setup_http(args.proxy)
    print(f"⟳ prefetching daily-digest sources for {args.date} …", file=sys.stderr)

    bundle = {"date": args.date, "fetched_at": dt.datetime.now().isoformat(timespec="seconds")}

    print("  → google news", file=sys.stderr)
    bundle["google_news"] = fetch_google_news()
    print("  → hacker news", file=sys.stderr)
    bundle["hacker_news"] = fetch_hn()
    print("  → show hn (products)", file=sys.stderr)
    bundle["show_hn"] = fetch_show_hn()
    print("  → reddit", file=sys.stderr)
    bundle["reddit"] = fetch_reddit()
    print("  → github trending", file=sys.stderr)
    trending = fetch_github_trending()
    if not any(r["ai_match"] for r in trending):
        trending += fetch_github_search()
    bundle["github"] = trending

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"{args.date}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    counts = {k: len(v) for k, v in bundle.items() if isinstance(v, list)}
    print("\n──────── prefetch summary ────────", file=sys.stderr)
    for k, n in counts.items():
        flag = "" if n else "   ⚠ EMPTY (check proxy / source)"
        print(f"  {k:<16} {n:>3} items{flag}", file=sys.stderr)
    print(f"\n✓ wrote {out_path}", file=sys.stderr)
    print(out_path)  # stdout = path, for scripting


if __name__ == "__main__":
    main()
