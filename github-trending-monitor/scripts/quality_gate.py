#!/usr/bin/env python3
"""github-trending-monitor quality gate.

Validate generated project pages against the legacy layout/content guardrails
and the newer source-depth checks that prevent citation-only pages.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


LAYOUT_ANCHORS = ("--ink:", "--panel:", "--star:", "--ease:", ".shell{", ".nav{", ".bg-stars")
KEY_CSS_VARS = {"ink", "panel", "star", "ease", "mono", "sans", "serif"}
MIN_MAIN_CODE_WRAPS = 4
MIN_CHILD_CODE_WRAPS = 3
SOURCE_REF_RE = re.compile(
    r"(?:src|lib|packages?|cmd|internal)/[a-zA-Z0-9_/.\-]+\."
    r"(?:ts|js|tsx|jsx|py|go|rs|java|kt|swift)"
)
LINE_REF_RE = re.compile(r"(?<![\d/]):(\d{2,4})(?![\d])")
CODE_REF_RE = re.compile(r"<code>[^<]+:\d+</code>")
BULK_LINE_PILE_RE = re.compile(r"(?:<code>[^<]+:[0-9]+</code>[·、,\s]+){15,}")
CODE_WRAP_BLOCK_RE = re.compile(r'<div class="code-wrap".*?</div>', re.DOTALL)
SOURCE_INDEX_PARA_RE = re.compile(r"<p[^>]*>[^<]*(?:源码索引|源文件地图).*?</p>", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
REF_TEXT_RE = re.compile(r"[\w./-]+:\d+")
EXPLANATION_CHAR_RE = re.compile(r"[A-Za-z\u4e00-\u9fff]")


@dataclass
class PageMetrics:
    name: str
    path: str
    page_type: str
    size_kb: int
    line_refs: int
    code_wraps: int
    min_code_wraps: int
    bulk_line_piles: int
    code_refs: int
    low_explanation_refs: int
    h3_count: int
    layout_missing: list[str]
    banned_design: list[str]


@dataclass
class GateResult:
    project: str
    passed: bool
    main_page: dict
    sub_pages: dict
    index: dict
    pages: list[PageMetrics]
    all_errors: list[str]
    warnings: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def layout_missing(content: str) -> list[str]:
    checks: tuple[tuple[str, str | re.Pattern[str]], ...] = (
        ("--ink:", "--ink:"),
        ("--panel:", "--panel:"),
        ("--star:", "--star:"),
        ("--ease:", "--ease:"),
        (".shell{", re.compile(r"\.shell\s*\{")),
        (".nav{", re.compile(r"\.nav\s*\{")),
        (".bg-stars", ".bg-stars"),
    )
    missing: list[str] = []
    for label, needle in checks:
        if isinstance(needle, str):
            if needle not in content:
                missing.append(label)
        elif not needle.search(content):
            missing.append(label)
    return missing


def old_design_system(content: str) -> list[str]:
    banned: list[str] = []
    if "--bg-card" in content and "--bg-elev" in content and "--ink" not in content:
        banned.append("--bg-card/--bg-elev system (B 系)")
    if "--glow-amber" in content and "--ink:" not in content:
        banned.append("--glow-amber system (A 系)")
    return banned


def css_vars(content: str) -> set[str]:
    return set(re.findall(r"--([a-z0-9-]+)\s*:", content))


def deep_link_count(content: str, project: str) -> int:
    links = re.findall(r'<a[^>]+class="[^"]*deep-link[^"]*"[^>]+href="([^"]+)"', content)
    return len([href for href in links if href.startswith(f"{project}/")])


def strip_html_for_explanation(fragment: str) -> str:
    text = TAG_RE.sub(" ", fragment)
    return REF_TEXT_RE.sub(" ", text)


def low_explanation_count(content: str) -> int:
    low = 0
    for match in CODE_REF_RE.finditer(content):
        start = max(0, match.start() - 200)
        end = min(len(content), match.end() + 200)
        nearby_text = strip_html_for_explanation(content[start:end])
        if len(EXPLANATION_CHAR_RE.findall(nearby_text)) < 30:
            low += 1
    return low


def bulk_line_pile_count(content: str) -> int:
    scan = CODE_WRAP_BLOCK_RE.sub(" ", content)
    scan = SOURCE_INDEX_PARA_RE.sub(" ", scan)
    return len(BULK_LINE_PILE_RE.findall(scan))


def page_metrics(root: Path, project: str, path: Path) -> PageMetrics:
    content = read_text(path)
    rel = path.relative_to(root).as_posix()
    page_type = "main" if path.name == f"{project}.html" else "child"
    min_code_wraps = MIN_MAIN_CODE_WRAPS if page_type == "main" else MIN_CHILD_CODE_WRAPS
    return PageMetrics(
        name=path.name,
        path=rel,
        page_type=page_type,
        size_kb=len(content) // 1024,
        line_refs=len(LINE_REF_RE.findall(content)),
        code_wraps=content.count('<div class="code-wrap"'),
        min_code_wraps=min_code_wraps,
        bulk_line_piles=bulk_line_pile_count(content),
        code_refs=len(CODE_REF_RE.findall(content)),
        low_explanation_refs=low_explanation_count(content),
        h3_count=len(re.findall(r"<h3[^>]*>", content)),
        layout_missing=layout_missing(content),
        banned_design=old_design_system(content),
    )


def apply_page_depth_checks(metrics: PageMetrics) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    min_line_refs = 50 if metrics.page_type == "main" else 20
    if metrics.line_refs < min_line_refs:
        errors.append(f"{metrics.path} 行号引用数 {metrics.line_refs} < {min_line_refs}")
    if metrics.code_wraps < metrics.min_code_wraps:
        errors.append(f"{metrics.path} 真实代码块数 {metrics.code_wraps} < {metrics.min_code_wraps}")
    if metrics.bulk_line_piles:
        errors.append(f"{metrics.path} 命中批量行号堆砌段 {metrics.bulk_line_piles} 处")
    if metrics.low_explanation_refs:
        warnings.append(
            f"{metrics.path} 讲解密度不足的 path:NN 引用 "
            f"{metrics.low_explanation_refs}/{metrics.code_refs}"
        )

    return errors, warnings


def check_main_page(root: Path, project: str) -> tuple[dict, PageMetrics | None, list[str]]:
    main = root / f"{project}.html"
    if not main.exists():
        return {"exists": False, "errors": [f"主页面不存在: {main}"]}, None, []

    content = read_text(main)
    metrics = page_metrics(root, project, main)
    errors: list[str] = []
    warnings: list[str] = []

    if metrics.layout_missing:
        errors.append(f"layout shell 缺失锚点: {metrics.layout_missing}")
    if metrics.banned_design:
        errors.append(f"检测到旧设计系统: {metrics.banned_design}")

    src_count = len(set(SOURCE_REF_RE.findall(content)))

    if metrics.h3_count < 10:
        errors.append(f"H3 章节数 {metrics.h3_count} < 10")

    deep_count = deep_link_count(content, project)
    if deep_count < 2:
        errors.append(f"深度阅读入口 {deep_count} < 2")

    depth_errors, depth_warnings = apply_page_depth_checks(metrics)
    errors.extend(depth_errors)
    warnings.extend(depth_warnings)

    has_mermaid = "mermaid" in content.lower()
    has_flow = ".flow" in content
    if not has_mermaid and not has_flow:
        warnings.append("没有 mermaid 或 ASCII flow 块（架构图缺失）")

    return (
        {
            "exists": True,
            "size_kb": metrics.size_kb,
            "src_refs": src_count,
            "line_refs": metrics.line_refs,
            "code_wraps": metrics.code_wraps,
            "min_code_wraps": metrics.min_code_wraps,
            "bulk_line_piles": metrics.bulk_line_piles,
            "code_refs": metrics.code_refs,
            "low_explanation_refs": metrics.low_explanation_refs,
            "h3_count": metrics.h3_count,
            "deep_links": deep_count,
            "has_mermaid": has_mermaid,
            "has_flow": has_flow,
            "errors": errors,
            "warnings": warnings,
        },
        metrics,
        warnings,
    )


def check_sub_pages(root: Path, project: str) -> tuple[dict, list[PageMetrics], list[str]]:
    sub_dir = root / project
    if not sub_dir.exists():
        return {"exists": False, "errors": [f"子页面目录不存在: {sub_dir}"]}, [], []

    sub_pages = sorted(sub_dir.glob("*.html"))
    if len(sub_pages) < 2:
        return {"exists": True, "count": len(sub_pages), "errors": [f"子页面数 {len(sub_pages)} < 2"]}, [], []

    errors: list[str] = []
    warnings: list[str] = []
    pages: list[dict] = []
    metrics_list: list[PageMetrics] = []
    main_path = root / f"{project}.html"
    main_vars = css_vars(read_text(main_path)) if main_path.exists() else set()

    for sub_page in sub_pages:
        content = read_text(sub_page)
        metrics = page_metrics(root, project, sub_page)
        metrics_list.append(metrics)

        if metrics.layout_missing:
            errors.append(f"{sub_page.name}: layout shell 缺失 {metrics.layout_missing}")
        if metrics.banned_design:
            errors.append(f"{sub_page.name}: 检测到旧设计系统 {metrics.banned_design}")
        if metrics.h3_count < 3:
            errors.append(f"{sub_page.name}: H3 数 {metrics.h3_count} < 3")

        sub_vars = css_vars(content)
        if main_vars and not main_vars.issubset(sub_vars):
            key_missing = (main_vars - sub_vars) & KEY_CSS_VARS
            if key_missing:
                errors.append(f"{sub_page.name}: 与主页 CSS vars 不一致, 缺 {key_missing}")

        depth_errors, depth_warnings = apply_page_depth_checks(metrics)
        errors.extend([e.replace(f"{metrics.path} ", f"{sub_page.name}: ") for e in depth_errors])
        warnings.extend(depth_warnings)

        pages.append(
            {
                "name": metrics.name,
                "size_kb": metrics.size_kb,
                "line_refs": metrics.line_refs,
                "code_wraps": metrics.code_wraps,
                "min_code_wraps": metrics.min_code_wraps,
                "bulk_line_piles": metrics.bulk_line_piles,
                "code_refs": metrics.code_refs,
                "low_explanation_refs": metrics.low_explanation_refs,
                "h3_count": metrics.h3_count,
            }
        )

    return {"exists": True, "count": len(sub_pages), "pages": pages, "errors": errors, "warnings": warnings}, metrics_list, warnings


def check_index(root: Path, project: str) -> dict:
    index = root / "index.html"
    if not index.exists():
        return {"exists": False, "errors": [], "warnings": ["index.html 不存在"]}

    content = read_text(index)
    has_card = f'href="{project}.html"' in content or f"#{project}" in content
    return {
        "exists": True,
        "has_card": has_card,
        "errors": [],
        "warnings": [] if has_card else [f'index.html 未包含项目卡片（href="{project}.html" 或 #{project} 锚点）'],
    }


def evaluate_project(root: Path, project: str) -> GateResult:
    main_result, main_metrics, main_warnings = check_main_page(root, project)
    sub_result, sub_metrics, sub_warnings = check_sub_pages(root, project)
    index_result = check_index(root, project)

    all_errors = main_result.get("errors", []) + sub_result.get("errors", []) + index_result.get("errors", [])
    warnings = main_warnings + sub_warnings + index_result.get("warnings", [])
    pages = ([main_metrics] if main_metrics else []) + sub_metrics

    return GateResult(
        project=project,
        passed=not all_errors,
        main_page=main_result,
        sub_pages=sub_result,
        index=index_result,
        pages=pages,
        all_errors=all_errors,
        warnings=warnings,
    )


def print_text(result: GateResult) -> None:
    print(f"=== Quality Gate · {result.project} ===\n")

    main = result.main_page
    if main.get("exists"):
        print(f"主页面 · {result.project}.html ({main['size_kb']}KB)")
        print(f"  源码引用: {main.get('src_refs', '?')}  行号引用: {main.get('line_refs', '?')}")
        print(f"  真实代码块: {main.get('code_wraps', '?')}/{main.get('min_code_wraps', '?')}")
        print(f"  H3 章节: {main.get('h3_count', '?')}  深度阅读: {main.get('deep_links', '?')}")
        print(f"  架构图: mermaid={main.get('has_mermaid', False)}, flow={main.get('has_flow', False)}")

    sub = result.sub_pages
    print(f"\n子页面 · {result.project}/ ({'存在' if sub.get('exists') else '缺失'})")
    for page in sub.get("pages", []):
        print(
            f"  {page['name']:50s} {page['size_kb']:3d}KB  "
            f"L_refs={page['line_refs']:3d}  code={page['code_wraps']:2d}/{page['min_code_wraps']}  "
            f"H3={page['h3_count']}"
        )

    print(f"\nindex.html · {'包含卡片' if result.index.get('has_card') else '缺卡片'}")

    if result.all_errors:
        print(f"\nFAIL · {len(result.all_errors)} 个错误:")
        for error in result.all_errors:
            print(f"  - {error}")
        return

    if result.warnings:
        print(f"\nWARN · {len(result.warnings)} 个警告:")
        for warning in result.warnings:
            print(f"  - {warning}")
    print("\nPASS · 所有质量门通过")


def result_to_json(result: GateResult) -> str:
    data = asdict(result)
    data["ok"] = result.passed
    return json.dumps(data, ensure_ascii=False, indent=2)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated github-trending project pages.")
    parser.add_argument("project", help="项目名（小写连字符，如 opentag）")
    parser.add_argument("--root", "--page-dir", dest="root", default=".", help="页面所在目录，默认当前目录")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = evaluate_project(Path(args.root).resolve(), args.project)
    if args.json:
        print(result_to_json(result))
    else:
        print_text(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
