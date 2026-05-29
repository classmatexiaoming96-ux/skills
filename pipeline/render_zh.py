"""Render the Chinese restructured markdown into a standalone HTML file with
mermaid support and Chinese-friendly typography."""
from __future__ import annotations
import re
import sys
from pathlib import Path

import markdown


HTML_SHELL = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root {{
    --bg: #fafaf7;
    --fg: #1a1a1a;
    --muted: #6b6b6b;
    --accent: #c96442;
    --accent-bg: #f6e8e0;
    --border: #e3e3df;
    --code-bg: #f3f1ec;
    --sidebar-w: 280px;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0; background: var(--bg); color: var(--fg);
    font: 16px/1.75 -apple-system, BlinkMacSystemFont, "PingFang SC",
          "Hiragino Sans GB", "Microsoft YaHei", "Segoe UI", sans-serif;
  }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  .layout {{ display: grid; grid-template-columns: var(--sidebar-w) 1fr; min-height: 100vh; }}
  aside.toc {{
    position: sticky; top: 0; align-self: start; max-height: 100vh; overflow-y: auto;
    padding: 28px 20px; border-right: 1px solid var(--border); background: #fff;
    font-size: 14px;
  }}
  aside.toc h2 {{
    font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--muted); margin: 0 0 12px;
  }}
  aside.toc ol {{ list-style: none; margin: 0; padding: 0; }}
  aside.toc li {{ margin: 0 0 10px; line-height: 1.4; }}
  aside.toc a {{ color: var(--fg); display: block; }}
  aside.toc a:hover {{ color: var(--accent); }}

  main {{ padding: 40px clamp(24px, 6vw, 80px); max-width: 920px; }}
  main > h1:first-child {{ font-size: 30px; line-height: 1.3; margin: 0 0 10px; }}

  h2 {{
    font-size: 22px; margin: 48px 0 16px; padding-bottom: 8px;
    border-bottom: 2px solid var(--border); scroll-margin-top: 20px;
  }}
  h3 {{ font-size: 17px; margin: 28px 0 12px; color: #333; }}

  p {{ margin: 0 0 18px; }}

  blockquote {{
    margin: 18px 0; padding: 12px 18px; border-left: 3px solid var(--accent);
    background: var(--accent-bg); color: #4a3320; font-size: 15px;
  }}
  blockquote p:last-child {{ margin-bottom: 0; }}

  ul, ol {{ margin: 0 0 18px; padding-left: 28px; }}
  li {{ margin: 0 0 8px; }}
  li > p {{ margin: 0 0 8px; }}

  code {{
    background: var(--code-bg); padding: 2px 6px; border-radius: 3px;
    font: 0.92em ui-monospace, SFMono-Regular, Menlo, monospace;
  }}
  pre {{
    background: var(--code-bg); padding: 14px 16px; border-radius: 6px;
    overflow-x: auto; font-size: 13px;
  }}
  pre code {{ background: transparent; padding: 0; }}

  /* Mermaid containers — let mermaid.js render inside, white bg */
  .mermaid {{
    background: #fff; padding: 18px; border: 1px solid var(--border);
    border-radius: 6px; margin: 20px 0; text-align: center;
  }}

  table {{
    border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 14.5px;
  }}
  th, td {{
    border: 1px solid var(--border); padding: 10px 12px; text-align: left;
    vertical-align: top; line-height: 1.55;
  }}
  th {{ background: #f1ede6; font-weight: 600; }}
  tr:nth-child(even) td {{ background: #fbf9f4; }}

  hr {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}

  em {{ color: var(--muted); }}

  footer.meta {{
    border-top: 1px solid var(--border); padding-top: 20px; margin-top: 48px;
    color: var(--muted); font-size: 13px;
  }}

  @media (max-width: 760px) {{
    .layout {{ grid-template-columns: 1fr; }}
    aside.toc {{
      position: static; max-height: none; border-right: none;
      border-bottom: 1px solid var(--border);
    }}
  }}
</style>
</head>
<body>
<div class="layout">
  <aside class="toc">
    <h2>目录</h2>
    <ol>{toc}</ol>
  </aside>
  <main>
{body}
  </main>
</div>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' }});
</script>
</body>
</html>
"""


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w一-鿿]+", "-", text.strip()).strip("-").lower()
    return s or "section"


def build_toc(md_text: str) -> tuple[str, str]:
    """Return (markdown with anchored h2s, toc_html)."""
    toc_items = []
    out_lines = []
    for line in md_text.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m and not line.startswith("###"):
            title = m.group(1).strip()
            slug = _slugify(title)
            toc_items.append(f'<li><a href="#{slug}">{title}</a></li>')
            out_lines.append(f'<h2 id="{slug}">{title}</h2>')
        else:
            out_lines.append(line)
    return "\n".join(out_lines), "\n".join(toc_items)


def render_mermaid_blocks(html: str) -> str:
    """python-markdown wraps fenced code in <pre><code class="language-mermaid">.
    Convert those to <div class="mermaid"> so mermaid.js picks them up."""
    pattern = re.compile(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        re.DOTALL,
    )
    def replace(m: re.Match) -> str:
        body = m.group(1)
        body = (body.replace("&lt;", "<").replace("&gt;", ">")
                    .replace("&amp;", "&").replace("&quot;", '"')
                    .replace("&#39;", "'"))
        return f'<div class="mermaid">{body}</div>'
    return pattern.sub(replace, html)


def render(md_path: Path, html_path: Path) -> None:
    md_text = md_path.read_text()
    title_match = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else md_path.stem

    md_with_ids, toc = build_toc(md_text)
    body = markdown.markdown(
        md_with_ids,
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    body = render_mermaid_blocks(body)

    html = HTML_SHELL.format(title=title, toc=toc, body=body)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html)
    print(f"written: {html_path}  ({len(html):,} bytes)")


if __name__ == "__main__":
    vid = sys.argv[1]
    render(Path("out/md_zh") / f"{vid}.md",
           Path("out/html_zh") / f"{vid}.html")
