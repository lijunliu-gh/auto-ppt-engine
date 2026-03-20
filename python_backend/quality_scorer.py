"""Quality scorecard for generated and revised deck JSON.

Provides programmatic pass/fail and soft-quality scoring that can be run
against any deck JSON — during CI, manual review, or regression checks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .smart_layer import (
    SUPPORTED_LAYOUTS,
    VALID_CHART_TYPES,
    create_validator,
    load_schema,
)

# ---------------------------------------------------------------------------
# Hard-fail criteria  –  any of these → deck is REJECTED
# ---------------------------------------------------------------------------

def check_schema_compliance(deck: Dict[str, Any]) -> List[str]:
    """Return schema validation errors (empty = pass)."""
    validator = create_validator()
    errors = sorted(validator.iter_errors(deck), key=lambda e: list(e.path))
    return [
        f"{'/' + '/'.join(str(p) for p in e.path) if list(e.path) else '/'}: {e.message}"
        for e in errors
    ]


def check_slide_numbering(deck: Dict[str, Any]) -> List[str]:
    """Pages must be consecutive 1..N and match slideCount."""
    slides = deck.get("slides", [])
    issues: List[str] = []
    for i, s in enumerate(slides):
        expected = i + 1
        actual = s.get("page")
        if actual != expected:
            issues.append(f"Slide {i+1}: page={actual}, expected={expected}")
    declared = deck.get("slideCount")
    if declared is not None and declared != len(slides):
        issues.append(f"slideCount={declared} but {len(slides)} slides present")
    return issues


def check_layout_validity(deck: Dict[str, Any]) -> List[str]:
    """Every slide layout must be in SUPPORTED_LAYOUTS."""
    issues: List[str] = []
    for s in deck.get("slides", []):
        layout = s.get("layout", "")
        if layout not in SUPPORTED_LAYOUTS:
            issues.append(f"Slide {s.get('page')}: invalid layout '{layout}'")
    return issues


def check_chart_integrity(deck: Dict[str, Any]) -> List[str]:
    """Charts must have valid type, non-empty categories, and matching series lengths."""
    issues: List[str] = []
    for s in deck.get("slides", []):
        chart = s.get("chart", {})
        ctype = chart.get("type", "")
        if not ctype:
            continue
        page = s.get("page")
        if ctype not in VALID_CHART_TYPES:
            issues.append(f"Slide {page}: chart type '{ctype}' not in {sorted(VALID_CHART_TYPES)}")
        cats = chart.get("categories", [])
        if not cats:
            issues.append(f"Slide {page}: chart has no categories")
            continue
        for si, series in enumerate(chart.get("series", [])):
            data = series.get("data", [])
            if len(data) != len(cats):
                issues.append(
                    f"Slide {page}: series[{si}] data length {len(data)} != categories length {len(cats)}"
                )
            for di, val in enumerate(data):
                if not isinstance(val, (int, float)):
                    issues.append(f"Slide {page}: series[{si}].data[{di}] is not numeric ({val!r})")
    return issues


# ---------------------------------------------------------------------------
# Soft-quality criteria  –  warnings that degrade the score, not hard fails
# ---------------------------------------------------------------------------

def check_slide_density(deck: Dict[str, Any], max_bullets: int = 8) -> List[str]:
    """Flag slides that are too dense (too many bullets)."""
    warnings: List[str] = []
    for s in deck.get("slides", []):
        for field in ("bullets", "left", "right"):
            items = s.get(field, [])
            if len(items) > max_bullets:
                warnings.append(
                    f"Slide {s.get('page')}: {field} has {len(items)} items (max recommended {max_bullets})"
                )
    return warnings


def check_empty_content_slides(deck: Dict[str, Any]) -> List[str]:
    """Flag non-structural slides that have no meaningful content."""
    structural = {"title", "agenda", "section", "closing"}
    warnings: List[str] = []
    for s in deck.get("slides", []):
        if s.get("layout") in structural:
            continue
        has_bullets = bool(s.get("bullets"))
        has_columns = bool(s.get("left")) or bool(s.get("right"))
        has_table = bool(s.get("table", {}).get("rows"))
        has_chart = bool(s.get("chart", {}).get("type"))
        if not (has_bullets or has_columns or has_table or has_chart):
            warnings.append(f"Slide {s.get('page')} ({s.get('layout')}): no substantive content")
    return warnings


def check_title_quality(deck: Dict[str, Any]) -> List[str]:
    """Flag slides with missing or very short titles."""
    warnings: List[str] = []
    for s in deck.get("slides", []):
        title = (s.get("title") or "").strip()
        if not title:
            warnings.append(f"Slide {s.get('page')}: missing title")
        elif len(title) < 4:
            warnings.append(f"Slide {s.get('page')}: very short title '{title}'")
    return warnings


def check_speaker_notes(deck: Dict[str, Any]) -> List[str]:
    """Flag decks that request speaker notes but have none."""
    if not deck.get("needsSpeakerNotes"):
        return []
    missing = []
    for s in deck.get("slides", []):
        notes = s.get("speakerNotes", [])
        if not notes or all(not n.strip() for n in notes):
            missing.append(f"Slide {s.get('page')}: speaker notes requested but empty")
    if len(missing) > len(deck.get("slides", [])) // 2:
        return [f"{len(missing)} slides missing speaker notes despite needsSpeakerNotes=true"]
    return []


def check_layout_variety(deck: Dict[str, Any]) -> List[str]:
    """Flag decks that use only one layout type for content slides."""
    structural = {"title", "agenda", "section", "closing"}
    content_layouts = [
        s.get("layout") for s in deck.get("slides", []) if s.get("layout") not in structural
    ]
    if len(content_layouts) < 3:
        return []
    unique = set(content_layouts)
    if len(unique) == 1:
        return [f"All {len(content_layouts)} content slides use '{content_layouts[0]}' — consider more variety"]
    return []


def check_source_attribution(deck: Dict[str, Any]) -> List[str]:
    """Flag decks with sourceDisplayMode != hidden but no sources on any slide."""
    mode = deck.get("sourceDisplayMode", "hidden")
    if mode == "hidden":
        return []
    has_any = any(s.get("sources") for s in deck.get("slides", []))
    if not has_any:
        return [f"sourceDisplayMode='{mode}' but no slide has source references"]
    return []


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

HARD_CHECKS = [
    ("schema_compliance", check_schema_compliance),
    ("slide_numbering", check_slide_numbering),
    ("layout_validity", check_layout_validity),
    ("chart_integrity", check_chart_integrity),
]

SOFT_CHECKS = [
    ("slide_density", check_slide_density),
    ("empty_content", check_empty_content_slides),
    ("title_quality", check_title_quality),
    ("speaker_notes", check_speaker_notes),
    ("layout_variety", check_layout_variety),
    ("source_attribution", check_source_attribution),
]


def score_deck(deck: Dict[str, Any]) -> Dict[str, Any]:
    """Run all checks and return a structured scorecard.

    Returns:
        {
            "pass": bool,           # True if all hard checks pass
            "hard_failures": {...},  # category → [error strings]
            "soft_warnings": {...},  # category → [warning strings]
            "hard_score": float,     # 0.0–1.0 (fraction of hard checks passed)
            "soft_score": float,     # 0.0–1.0 (fraction of soft checks clean)
            "summary": str,          # human-readable one-liner
        }
    """
    hard_failures: Dict[str, List[str]] = {}
    soft_warnings: Dict[str, List[str]] = {}

    for name, fn in HARD_CHECKS:
        issues = fn(deck)
        if issues:
            hard_failures[name] = issues

    for name, fn in SOFT_CHECKS:
        issues = fn(deck)
        if issues:
            soft_warnings[name] = issues

    hard_passed = len(HARD_CHECKS) - len(hard_failures)
    soft_clean = len(SOFT_CHECKS) - len(soft_warnings)
    hard_score = hard_passed / len(HARD_CHECKS) if HARD_CHECKS else 1.0
    soft_score = soft_clean / len(SOFT_CHECKS) if SOFT_CHECKS else 1.0
    passed = len(hard_failures) == 0

    if passed and not soft_warnings:
        summary = f"PASS — {len(HARD_CHECKS)} hard checks clean, {len(SOFT_CHECKS)} soft checks clean"
    elif passed:
        summary = f"PASS with warnings — {len(soft_warnings)} soft issue(s)"
    else:
        summary = f"FAIL — {len(hard_failures)} hard failure(s): {', '.join(hard_failures.keys())}"

    return {
        "pass": passed,
        "hard_failures": hard_failures,
        "soft_warnings": soft_warnings,
        "hard_score": round(hard_score, 2),
        "soft_score": round(soft_score, 2),
        "summary": summary,
    }


def score_deck_file(path: str | Path) -> Dict[str, Any]:
    """Load a deck JSON file and score it."""
    deck = json.loads(Path(path).read_text(encoding="utf-8"))
    return score_deck(deck)
