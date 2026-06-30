#!/usr/bin/env python3
"""
build.py — render a curated content JSON into a standalone dark-theme digest
HTML page, and refresh the site manifest used by the viewer / calendar.

Usage:
    python3 scripts/build.py content/2025-06-18.json \
        --template templates/digest.template.html \
        --out web/

Inputs:
    content/{date}.json   curated content (schema documented in SKILL.md)
Outputs:
    {out}/{date}.html     the rendered digest (links assets/digest.css)
    {out}/manifest.js     window.DIGESTS = [...]  (rebuilt from every *.html date)

The script has no third-party dependencies.
"""
import argparse
import datetime as dt
import glob
import html
import json
import os
import re
import sys

ACCENTS = {
    "headlines": "var(--gold)",
    "community": "var(--cyan)",
    "products":  "var(--violet)",
    "repos":     "var(--green)",
}
ACCENT_SOFT = {
    "headlines": "rgba(245,181,68,.12)",
    "community": "rgba(79,209,197,.12)",
    "products":  "rgba(169,139,255,.12)",
    "repos":     "rgba(93,217,113,.12)",
}
SECTION_TITLES = {
    "headlines": ("今日要闻", "Google News"),
    "community": ("社区热议", "Hacker News · Reddit"),
    "products":  ("产品 · 概念", "Products & Concepts"),
    "repos":     ("开源热门", "GitHub Trending"),
}
LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Rust": "#dea584", "Go": "#00ADD8", "C++": "#f34b7d", "C": "#555555",
    "Java": "#b07219", "Jupyter Notebook": "#DA5B0B", "Swift": "#F05138",
    "Kotlin": "#A97BFF", "Zig": "#ec915c", "Mojo": "#ff4c1f", "Shell": "#89e051",
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def style_attr(key):
    return f'--accent:{ACCENTS[key]};--accent-soft:{ACCENT_SOFT[key]}'


def tag(text, cls="tag"):
    return f'<span class="{cls}">{esc(text)}</span>' if text else ""


def src_line(name, extra=""):
    inner = f'<span class="src">◷ <b>{esc(name)}</b>{extra}</span>'
    return inner


# ---------- per-section renderers ----------
def render_headlines(data, key):
    out = [f'  <section class="sec reveal" style="{style_attr(key)}">']
    zh, meta = SECTION_TITLES[key]
    out.append(f'    <div class="sec-head"><span class="sec-no">01</span><h2>{zh}</h2>'
               f'<span class="sec-meta">{meta}</span></div>')
    lead = data.get("lead")
    if lead:
        extra = f' <span class="dotsep">·</span> {esc(lead.get("time",""))}' if lead.get("time") else ""
        out.append(f'    <a class="lead" href="{esc(lead["url"])}" target="_blank" rel="noopener">')
        out.append(f'      {tag(lead.get("tag"))}')
        out.append(f'      <h3>{esc(lead["title"])}</h3>')
        out.append(f'      <p>{esc(lead.get("summary",""))}</p>')
        out.append(f'      <div class="src">◷ <b>{esc(lead.get("source",""))}</b>{extra}</div>')
        out.append('    </a>')
    items = data.get("items", [])
    if items:
        out.append('    <div class="rows">')
        for i, it in enumerate(items, 1):
            metas = []
            if it.get("source"): metas.append(f'<b style="color:var(--ink-dim)">{esc(it["source"])}</b>')
            if it.get("time"): metas.append(esc(it["time"]))
            if it.get("tag"): metas.append(tag(it["tag"]))
            meta_html = ' <span class="dotsep">·</span> '.join(metas)
            out.append(f'      <a class="row" href="{esc(it["url"])}" target="_blank" rel="noopener">')
            out.append(f'        <div class="idx">{i:02d}</div>')
            out.append('        <div class="body">')
            out.append(f'          <h4>{esc(it["title"])}</h4>')
            if it.get("summary"):
                out.append(f'          <p>{esc(it["summary"])}</p>')
            if meta_html:
                out.append(f'          <div class="meta-line">{meta_html}</div>')
            out.append('        </div>')
            out.append('        <div class="arrow">↗</div>')
            out.append('      </a>')
        out.append('    </div>')
    out.append('  </section>')
    return "\n".join(out)


def render_community(data, key, num):
    out = [f'  <section class="sec reveal" style="{style_attr(key)}">']
    zh, meta = SECTION_TITLES[key]
    out.append(f'    <div class="sec-head"><span class="sec-no">{num}</span><h2>{zh}</h2>'
               f'<span class="sec-meta">{meta}</span></div>')
    out.append('    <div class="rows">')
    for i, it in enumerate(data.get("items", []), 1):
        metas = []
        if it.get("platform"): metas.append(f'<b style="color:var(--ink-dim)">{esc(it["platform"])}</b>')
        if it.get("points") is not None: metas.append(f'▲ {esc(it["points"])}')
        if it.get("comments") is not None: metas.append(f'💬 {esc(it["comments"])}')
        meta_html = ' <span class="dotsep">·</span> '.join(metas)
        out.append(f'      <a class="row" href="{esc(it["url"])}" target="_blank" rel="noopener">')
        out.append(f'        <div class="idx">{i:02d}</div>')
        out.append('        <div class="body">')
        out.append(f'          <h4>{esc(it["title"])}</h4>')
        if it.get("summary"):
            out.append(f'          <p>{esc(it["summary"])}</p>')
        if it.get("quote"):
            out.append(f'          <div class="quote">“{esc(it["quote"])}”</div>')
        if meta_html:
            out.append(f'          <div class="meta-line">{meta_html}</div>')
        out.append('        </div>')
        out.append('        <div class="arrow">↗</div>')
        out.append('      </a>')
    out.append('    </div>')
    out.append('  </section>')
    return "\n".join(out)


def render_products(data, key, num):
    out = [f'  <section class="sec reveal" style="{style_attr(key)}">']
    zh, meta = SECTION_TITLES[key]
    out.append(f'    <div class="sec-head"><span class="sec-no">{num}</span><h2>{zh}</h2>'
               f'<span class="sec-meta">{meta}</span></div>')
    out.append('    <div class="cards">')
    for it in data.get("items", []):
        href = f' href="{esc(it["url"])}" target="_blank" rel="noopener"' if it.get("url") else ""
        elem = "a" if it.get("url") else "div"
        out.append(f'      <{elem} class="card"{href}>')
        out.append('        <div class="ct">')
        out.append(f'          <span class="ico">{esc(it.get("icon","✦"))}</span>')
        out.append(f'          <h4>{esc(it["name"])}</h4>')
        out.append('        </div>')
        if it.get("tagline"):
            out.append(f'        <p class="tagline">{esc(it["tagline"])}</p>')
        out.append(f'        <p>{esc(it.get("summary",""))}</p>')
        if it.get("tag"):
            out.append(f'        <div>{tag(it["tag"])}</div>')
        out.append(f'      </{elem}>')
    out.append('    </div>')
    out.append('  </section>')
    return "\n".join(out)


def render_repos(data, key, num):
    out = [f'  <section class="sec reveal" style="{style_attr(key)}">']
    zh, meta = SECTION_TITLES[key]
    out.append(f'    <div class="sec-head"><span class="sec-no">{num}</span><h2>{zh}</h2>'
               f'<span class="sec-meta">{meta}</span></div>')
    for it in data.get("items", []):
        lang = it.get("lang", "")
        dot = LANG_COLORS.get(lang, "#8b949e")
        metas = []
        if lang:
            metas.append(f'<span><span class="lang-dot" style="background:{dot}"></span>{esc(lang)}</span>')
        if it.get("tag"):
            metas.append(tag(it["tag"]))
        meta_html = ' <span class="dotsep">·</span> '.join(metas)
        owner = esc(it.get("owner", ""))
        name = esc(it.get("name", ""))
        today = f'<div class="today">▲ {esc(it["stars_today"])} today</div>' if it.get("stars_today") else ""
        out.append(f'    <a class="repo" href="{esc(it["url"])}" target="_blank" rel="noopener">')
        out.append('      <div>')
        out.append(f'        <div class="name">{owner} / <b>{name}</b></div>')
        out.append(f'        <div class="desc">{esc(it.get("desc",""))}</div>')
        if meta_html:
            out.append(f'        <div class="repo-meta">{meta_html}</div>')
        out.append('      </div>')
        out.append('      <div class="stars">')
        out.append(f'        <div class="total">★ {esc(it.get("stars",""))}</div>')
        out.append(f'        {today}')
        out.append('      </div>')
        out.append('    </a>')
    out.append('  </section>')
    return "\n".join(out)


# ---------- manifest ----------
def rebuild_manifest(out_dir):
    """Scan {out}/YYYY-MM-DD.html and rebuild manifest.js with metadata sidecars."""
    entries = []
    for path in sorted(glob.glob(os.path.join(out_dir, "[0-9]" * 4 + "-*.html"))):
        base = os.path.basename(path)
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.html$", base)
        if not m:
            continue
        date = m.group(1)
        meta = {"date": date}
        sidecar = os.path.join(out_dir, ".meta", date + ".json")
        if os.path.exists(sidecar):
            with open(sidecar) as f:
                meta.update(json.load(f))
        entries.append(meta)
    entries.sort(key=lambda e: e["date"], reverse=True)
    js = ("/* auto-generated by build.py — do not edit by hand */\n"
          "window.DIGESTS = " + json.dumps(entries, ensure_ascii=False, indent=2) + ";\n")
    with open(os.path.join(out_dir, "manifest.js"), "w") as f:
        f.write(js)
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content", help="path to content/{date}.json")
    ap.add_argument("--template", default=os.path.join(os.path.dirname(__file__), "..", "templates", "digest.template.html"))
    ap.add_argument("--out", default="web")
    ap.add_argument("--generated-at", default=None, help="override timestamp (else now, local)")
    args = ap.parse_args()

    with open(args.content, encoding="utf-8") as f:
        c = json.load(f)
    with open(args.template, encoding="utf-8") as f:
        tmpl = f.read()

    date = c["date"]
    secs = c.get("sections", {})
    parts = []
    if "headlines" in secs:
        parts.append(render_headlines(secs["headlines"], "headlines"))
    n = 2
    for key, fn in (("community", render_community), ("products", render_products), ("repos", render_repos)):
        if key in secs:
            parts.append(fn(secs[key], key, f"{n:02d}"))
            n += 1
    sections_html = "\n\n".join(parts)

    def count(key, sub="items"):
        s = secs.get(key, {})
        n = len(s.get(sub, []))
        if key == "headlines" and s.get("lead"):
            n += 1
        return n

    gen_at = args.generated_at or dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    intro = c.get("intro", "")
    repl = {
        "{{DATE}}": esc(date),
        "{{WEEKDAY}}": esc(c.get("weekday", "")),
        "{{EDITION}}": esc(c.get("edition", "1")),
        "{{INTRO}}": esc(intro),
        "{{INTRO_PLAIN}}": esc(re.sub(r"\s+", " ", intro)[:150]),
        "{{N_HEADLINES}}": str(count("headlines")),
        "{{N_COMMUNITY}}": str(count("community")),
        "{{N_PRODUCTS}}": str(count("products")),
        "{{N_REPOS}}": str(count("repos")),
        "{{GENERATED_AT}}": esc(gen_at),
        "{{SECTIONS}}": sections_html,
    }
    out_html = tmpl
    for k, v in repl.items():
        out_html = out_html.replace(k, v)

    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"{date}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out_html)

    # sidecar metadata for the manifest / calendar
    meta_dir = os.path.join(args.out, ".meta")
    os.makedirs(meta_dir, exist_ok=True)
    with open(os.path.join(meta_dir, f"{date}.json"), "w", encoding="utf-8") as f:
        json.dump({
            "date": date,
            "weekday": c.get("weekday", ""),
            "edition": c.get("edition", 1),
            "title": c.get("headline_title") or (secs.get("headlines", {}).get("lead", {}) or {}).get("title", ""),
            "intro": intro,
        }, f, ensure_ascii=False)

    entries = rebuild_manifest(args.out)
    print(f"✓ wrote {out_path}")
    print(f"✓ manifest.js now lists {len(entries)} digest(s): {', '.join(e['date'] for e in entries[:8])}")


if __name__ == "__main__":
    sys.exit(main())
