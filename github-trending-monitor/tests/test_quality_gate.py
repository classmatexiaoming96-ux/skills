from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "quality_gate.py"
PAGES_ROOT = Path("/root/repos/github-trending")

spec = importlib.util.spec_from_file_location("quality_gate", SCRIPT)
quality_gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = quality_gate
spec.loader.exec_module(quality_gate)


def page_metric(**overrides):
    data = {
        "name": "project.html",
        "path": "project.html",
        "page_type": "main",
        "size_kb": 10,
        "line_refs": 80,
        "code_wraps": 6,
        "min_code_wraps": 6,
        "bulk_line_piles": 0,
        "code_refs": 80,
        "low_explanation_refs": 0,
        "explanation_ratio": 1.0,
        "explanation_paragraphs": 6,
        "h3_count": 10,
        "layout_missing": [],
        "banned_design": [],
    }
    data.update(overrides)
    return quality_gate.PageMetrics(**data)


def test_opentag_antipattern_scores_below_60():
    result = quality_gate.evaluate_project(PAGES_ROOT, "opentag")

    assert result.score["average"] < 60
    assert result.score["grade"] == "F"


def test_qwen_agentworld_scores_at_least_90():
    result = quality_gate.evaluate_project(PAGES_ROOT, "qwen-agentworld")

    assert result.score["average"] >= 90
    assert result.score["grade"] == "A"


def test_compute_score_clamps_to_zero_for_bulk_piles():
    metrics = page_metric(
        code_wraps=0,
        explanation_paragraphs=0,
        explanation_ratio=0.0,
        h3_count=0,
        layout_missing=["--ink:"],
        bulk_line_piles=10,
    )

    score = quality_gate.compute_score(metrics, deep_links=0, index_card_ok=False)

    assert score["score"] == 0
    assert score["grade"] == "F"


def test_compute_score_caps_at_100_for_full_quality_main_page():
    metrics = page_metric(
        code_wraps=12,
        explanation_paragraphs=12,
        explanation_ratio=1.0,
        h3_count=20,
    )

    score = quality_gate.compute_score(metrics, deep_links=4, index_card_ok=True)

    assert score["score"] == 100
    assert score["grade"] == "A"
