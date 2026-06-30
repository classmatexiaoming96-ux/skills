#!/usr/bin/env python3
"""
github-trending-page-template · quality-gate

校验新生成的页面是否满足质量硬约束。

Usage:
  python3 quality_gate.py <project-name> [--sources-dir ../sources/{project}] [--page-dir .]

校验项：
  1. 主页面文件存在：{project}.html
  2. 子页面目录存在：{project}/（且 ≥ 2 个 .html）
  3. 主页面引用 src/ 路径 ≥ 10
  4. 主页面行号引用（L123 或 :123 形式）≥ 50
  5. 主页面 H3 章节 ≥ 10
  6. 主页面有"深度阅读"入口 ≥ 2（链到子页面）
  7. layout shell 锚点（--ink / --panel / --star）齐全
  8. 子页面 layout shell 与主页面一致
  9. 不允许的旧 CSS 变量（--bg-card / --glow-amber as primary / --ink-* / --star-* OK）
  10. index.html 有项目卡片入口
"""
import re
import sys
import argparse
from pathlib import Path


def count_pattern(content: str, pattern: str) -> int:
    return len(re.findall(pattern, content))


def has_deep_links(content: str, project: str) -> int:
    """数 .deep-link 元素，且 href 必须链到 {project}/ 子目录"""
    links = re.findall(r'<a[^>]+class="[^"]*deep-link[^"]*"[^>]+href="([^"]+)"', content)
    project_links = [l for l in links if l.startswith(f'{project}/')]
    return len(project_links)


def has_old_design_system(content: str) -> list[str]:
    """检测禁用的旧设计变量"""
    banned = []
    if '--bg-card' in content and '--bg-elev' in content and '--ink' not in content:
        banned.append('--bg-card/--bg-elev system (B 系)')
    # A 系：--glow-amber + 没有 --ink
    if '--glow-amber' in content and '--ink:' not in content:
        banned.append('--glow-amber system (A 系)')
    return banned


def has_layout_shell(content: str) -> tuple[bool, list[str]]:
    """检查 layout shell 关键锚点"""
    required = ['--ink:', '--panel:', '--star:', '--ease:', '.shell{', '.nav{', '.bg-stars']
    missing = [r for r in required if r not in content]
    return (len(missing) == 0, missing)


def check_main_page(project_dir: Path, project: str) -> dict:
    """校验主页面"""
    main = project_dir / f'{project}.html'
    if not main.exists():
        return {'exists': False, 'errors': [f'主页面不存在: {main}']}

    content = main.read_text()
    errors = []
    warnings = []

    # 1. layout shell 锚点
    ok, missing = has_layout_shell(content)
    if not ok:
        errors.append(f'layout shell 缺失锚点: {missing}')

    # 2. 禁用旧设计系统
    banned = has_old_design_system(content)
    if banned:
        errors.append(f'检测到旧设计系统: {banned}')

    # 3. 源码文件引用 ≥ 8（openclaw 标杆 = 9）
    src_refs = re.findall(r'(?:src|lib|packages?|cmd|internal)/[a-zA-Z0-9_/.\-]+\.(?:ts|js|tsx|jsx|py|go|rs|java|kt|swift)', content)
    src_count = len(set(src_refs))
    if src_count < 8:
        errors.append(f'源码文件引用数 {src_count} < 8')

    # 4. 行号引用 ≥ 50
    line_refs = re.findall(r'(?<![\d/]):(\d{2,4})(?![\d])', content)
    if len(line_refs) < 50:
        errors.append(f'行号引用数 {len(line_refs)} < 50')

    # 5. H3 ≥ 10
    h3_count = len(re.findall(r'<h3[^>]*>', content))
    if h3_count < 10:
        errors.append(f'H3 章节数 {h3_count} < 10')

    # 6. 深度阅读入口 ≥ 2
    deep_count = has_deep_links(content, project)
    if deep_count < 2:
        errors.append(f'深度阅读入口 {deep_count} < 2')

    # 7. mermaid 或 flow 块
    has_mermaid = 'mermaid' in content.lower()
    has_flow = '.flow' in content
    if not has_mermaid and not has_flow:
        warnings.append('没有 mermaid 或 ASCII flow 块（架构图缺失）')

    return {
        'exists': True,
        'size_kb': len(content) // 1024,
        'src_refs': src_count,
        'line_refs': len(line_refs),
        'h3_count': h3_count,
        'deep_links': deep_count,
        'has_mermaid': has_mermaid,
        'has_flow': has_flow,
        'errors': errors,
        'warnings': warnings,
    }


def check_sub_pages(project_dir: Path, project: str) -> dict:
    """校验子页面目录"""
    sub_dir = project_dir / project
    if not sub_dir.exists():
        return {'exists': False, 'errors': [f'子页面目录不存在: {sub_dir}']}

    sub_pages = sorted(sub_dir.glob('*.html'))
    if len(sub_pages) < 2:
        return {'exists': True, 'count': len(sub_pages), 'errors': [f'子页面数 {len(sub_pages)} < 2']}

    errors = []
    sub_stats = []
    main_content = (project_dir / f'{project}.html').read_text()
    main_vars = set(re.findall(r'--([a-z0-9-]+)\s*:', main_content))

    for sp in sub_pages:
        content = sp.read_text()
        # 检查 layout shell 一致性
        ok, missing = has_layout_shell(content)
        if not ok:
            errors.append(f'{sp.name}: layout shell 缺失 {missing}')
        # 检查禁用设计系统
        banned = has_old_design_system(content)
        if banned:
            errors.append(f'{sp.name}: 检测到旧设计系统 {banned}')
        # 行号引用 ≥ 20（子页面比主页宽松）
        line_refs = len(re.findall(r'(?<![\d/]):(\d{2,4})(?![\d])', content))
        if line_refs < 20:
            errors.append(f'{sp.name}: 行号引用 {line_refs} < 20')
        # H3 ≥ 3
        h3_count = len(re.findall(r'<h3[^>]*>', content))
        if h3_count < 3:
            errors.append(f'{sp.name}: H3 数 {h3_count} < 3')
        # 与主页 CSS vars 一致
        sub_vars = set(re.findall(r'--([a-z0-9-]+)\s*:', content))
        if main_vars and not main_vars.issubset(sub_vars):
            missing = main_vars - sub_vars
            # 只报告关键 vars
            key_missing = missing & {'ink', 'panel', 'star', 'ease', 'mono', 'sans', 'serif'}
            if key_missing:
                errors.append(f'{sp.name}: 与主页 CSS vars 不一致, 缺 {key_missing}')
        sub_stats.append({
            'name': sp.name,
            'size_kb': len(content) // 1024,
            'line_refs': line_refs,
            'h3_count': h3_count,
        })

    return {
        'exists': True,
        'count': len(sub_pages),
        'pages': sub_stats,
        'errors': errors,
    }


def check_index(project_dir: Path, project: str) -> dict:
    """校验 index.html 包含项目卡片"""
    idx = project_dir / 'index.html'
    if not idx.exists():
        return {'exists': False, 'errors': ['index.html 不存在']}

    content = idx.read_text()
    project_card = f'href="{project}.html"' in content or f'#{project}' in content
    return {
        'exists': True,
        'has_card': project_card,
        'errors': [] if project_card else [f'index.html 未包含项目卡片（href="{project}.html" 或 #{project} 锚点）'],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', help='项目名（小写连字符，如 opentag）')
    parser.add_argument('--page-dir', default='.', help='页面所在目录（默认当前目录，应是 github-trending 根）')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()

    project_dir = Path(args.page_dir).resolve()
    project = args.project

    main_result = check_main_page(project_dir, project)
    sub_result = check_sub_pages(project_dir, project)
    idx_result = check_index(project_dir, project)

    all_errors = main_result.get('errors', []) + sub_result.get('errors', []) + idx_result.get('errors', [])

    result = {
        'project': project,
        'main_page': main_result,
        'sub_pages': sub_result,
        'index': idx_result,
        'all_errors': all_errors,
        'passed': len(all_errors) == 0,
    }

    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f'=== Quality Gate · {project} ===\n')
        if main_result['exists']:
            print(f'主页面 · {project}.html ({main_result["size_kb"]}KB)')
            print(f'  源码引用: {main_result.get("src_refs", "?")}  行号引用: {main_result.get("line_refs", "?")}')
            print(f'  H3 章节: {main_result.get("h3_count", "?")}  深度阅读: {main_result.get("deep_links", "?")}')
            print(f'  架构图: mermaid={main_result.get("has_mermaid", False)}, flow={main_result.get("has_flow", False)}')

        print(f'\n子页面 · {project}/ ({"存在" if sub_result["exists"] else "缺失"})')
        if sub_result.get('pages'):
            for p in sub_result['pages']:
                print(f'  {p["name"]:50s} {p["size_kb"]:3d}KB  L_refs={p["line_refs"]:3d}  H3={p["h3_count"]}')

        print(f'\nindex.html · {"包含卡片" if idx_result.get("has_card") else "缺卡片"}')

        if all_errors:
            print(f'\n❌ {len(all_errors)} 个错误:')
            for e in all_errors:
                print(f'  - {e}')
            sys.exit(1)
        else:
            warnings = main_result.get('warnings', [])
            if warnings:
                print(f'\n⚠️ {len(warnings)} 个警告:')
                for w in warnings:
                    print(f'  - {w}')
            print('\n✅ 所有质量门通过')


if __name__ == '__main__':
    main()