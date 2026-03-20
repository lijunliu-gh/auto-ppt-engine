"""Tests for the quality scorecard system."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from python_backend.quality_scorer import (
    check_chart_integrity,
    check_empty_content_slides,
    check_layout_validity,
    check_layout_variety,
    check_schema_compliance,
    check_slide_density,
    check_slide_numbering,
    check_source_attribution,
    check_speaker_notes,
    check_title_quality,
    score_deck,
)
from python_backend.smart_layer import build_mock_deck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_deck(slides=None, **overrides):
    """Build a minimal valid deck for testing."""
    base = {
        "schemaVersion": "0.3.0",
        "deckTitle": "Test Deck",
        "language": "en-US",
        "audience": "Testers",
        "scenario": "Unit test",
        "tone": "Professional",
        "theme": "business-clean",
        "sourceDisplayMode": "hidden",
        "slideCount": 1,
        "needsSpeakerNotes": False,
        "assumptions": [],
        "slides": slides or [_minimal_slide(1, "title", "Test Title")],
    }
    base.update(overrides)
    if "slideCount" not in overrides:
        base["slideCount"] = len(base["slides"])
    return base


def _minimal_slide(page, layout, title, **overrides):
    """Build a minimal valid slide."""
    slide = {
        "page": page,
        "layout": layout,
        "title": title,
        "subtitle": "",
        "objective": "",
        "bullets": [],
        "left": [],
        "right": [],
        "table": {"columns": [], "rows": []},
        "chart": {"type": "", "title": "", "categories": [], "series": []},
        "visuals": [],
        "sources": [],
        "speakerNotes": [],
    }
    slide.update(overrides)
    return slide


# ===========================================================================
# Hard check tests
# ===========================================================================


class TestSchemaCompliance:
    def test_valid_deck_passes(self):
        deck = _minimal_deck()
        assert check_schema_compliance(deck) == []

    def test_missing_required_field_fails(self):
        deck = _minimal_deck()
        del deck["deckTitle"]
        errors = check_schema_compliance(deck)
        assert any("deckTitle" in e for e in errors)

    def test_mock_deck_passes(self):
        deck = build_mock_deck("Test prompt", [], [], [])
        assert check_schema_compliance(deck) == []


class TestSlideNumbering:
    def test_consecutive_numbering_passes(self):
        slides = [_minimal_slide(i, "bullet", f"Slide {i}") for i in range(1, 4)]
        deck = _minimal_deck(slides=slides)
        assert check_slide_numbering(deck) == []

    def test_wrong_page_number_fails(self):
        slides = [
            _minimal_slide(1, "title", "First"),
            _minimal_slide(3, "bullet", "Skipped"),
        ]
        deck = _minimal_deck(slides=slides)
        issues = check_slide_numbering(deck)
        assert len(issues) >= 1
        assert "expected=2" in issues[0]

    def test_count_mismatch_fails(self):
        slides = [_minimal_slide(1, "title", "Only")]
        deck = _minimal_deck(slides=slides, slideCount=5)
        issues = check_slide_numbering(deck)
        assert any("slideCount=5" in i for i in issues)


class TestLayoutValidity:
    def test_supported_layouts_pass(self):
        slides = [_minimal_slide(1, "bullet", "OK")]
        deck = _minimal_deck(slides=slides)
        assert check_layout_validity(deck) == []

    def test_unknown_layout_fails(self):
        slides = [_minimal_slide(1, "fancy-grid", "Bad")]
        deck = _minimal_deck(slides=slides)
        issues = check_layout_validity(deck)
        assert len(issues) == 1
        assert "fancy-grid" in issues[0]


class TestChartIntegrity:
    def test_valid_chart_passes(self):
        chart = {
            "type": "bar",
            "title": "Revenue",
            "categories": ["Q1", "Q2", "Q3"],
            "series": [{"name": "Sales", "data": [100, 200, 300]}],
        }
        slides = [_minimal_slide(1, "chart", "Chart", chart=chart)]
        deck = _minimal_deck(slides=slides)
        assert check_chart_integrity(deck) == []

    def test_empty_chart_skipped(self):
        slides = [_minimal_slide(1, "bullet", "No chart")]
        deck = _minimal_deck(slides=slides)
        assert check_chart_integrity(deck) == []

    def test_bad_chart_type_fails(self):
        chart = {
            "type": "donut",
            "title": "Bad",
            "categories": ["A"],
            "series": [{"name": "X", "data": [1]}],
        }
        slides = [_minimal_slide(1, "chart", "Bad", chart=chart)]
        deck = _minimal_deck(slides=slides)
        issues = check_chart_integrity(deck)
        assert any("donut" in i for i in issues)

    def test_series_length_mismatch_fails(self):
        chart = {
            "type": "bar",
            "title": "Mismatch",
            "categories": ["Q1", "Q2"],
            "series": [{"name": "X", "data": [1, 2, 3]}],
        }
        slides = [_minimal_slide(1, "chart", "Mismatch", chart=chart)]
        deck = _minimal_deck(slides=slides)
        issues = check_chart_integrity(deck)
        assert any("length" in i for i in issues)

    def test_non_numeric_data_fails(self):
        chart = {
            "type": "bar",
            "title": "Non-num",
            "categories": ["A"],
            "series": [{"name": "X", "data": ["abc"]}],
        }
        slides = [_minimal_slide(1, "chart", "Non-num", chart=chart)]
        deck = _minimal_deck(slides=slides)
        issues = check_chart_integrity(deck)
        assert any("not numeric" in i for i in issues)


# ===========================================================================
# Soft check tests
# ===========================================================================


class TestSlideDensity:
    def test_normal_density_clean(self):
        slides = [_minimal_slide(1, "bullet", "OK", bullets=["a", "b", "c"])]
        deck = _minimal_deck(slides=slides)
        assert check_slide_density(deck) == []

    def test_overdense_warns(self):
        slides = [_minimal_slide(1, "bullet", "Dense", bullets=list("abcdefghij"))]
        deck = _minimal_deck(slides=slides)
        warnings = check_slide_density(deck)
        assert len(warnings) == 1


class TestEmptyContent:
    def test_structural_slide_ok_empty(self):
        slides = [_minimal_slide(1, "title", "Welcome")]
        deck = _minimal_deck(slides=slides)
        assert check_empty_content_slides(deck) == []

    def test_content_slide_needs_content(self):
        slides = [_minimal_slide(1, "bullet", "Empty body")]
        deck = _minimal_deck(slides=slides)
        warnings = check_empty_content_slides(deck)
        assert len(warnings) == 1

    def test_chart_counts_as_content(self):
        chart = {
            "type": "bar",
            "title": "Revenue",
            "categories": ["Q1"],
            "series": [{"name": "X", "data": [1]}],
        }
        slides = [_minimal_slide(1, "chart", "Chart", chart=chart)]
        deck = _minimal_deck(slides=slides)
        assert check_empty_content_slides(deck) == []


class TestTitleQuality:
    def test_good_title_passes(self):
        slides = [_minimal_slide(1, "bullet", "Market Overview")]
        deck = _minimal_deck(slides=slides)
        assert check_title_quality(deck) == []

    def test_missing_title_warns(self):
        slides = [_minimal_slide(1, "bullet", "")]
        deck = _minimal_deck(slides=slides)
        assert len(check_title_quality(deck)) == 1

    def test_very_short_title_warns(self):
        slides = [_minimal_slide(1, "bullet", "Hi")]
        deck = _minimal_deck(slides=slides)
        assert len(check_title_quality(deck)) == 1


class TestSpeakerNotes:
    def test_not_requested_clean(self):
        deck = _minimal_deck(needsSpeakerNotes=False)
        assert check_speaker_notes(deck) == []

    def test_requested_and_present_clean(self):
        slides = [_minimal_slide(1, "bullet", "OK", speakerNotes=["Talk about this"])]
        deck = _minimal_deck(slides=slides, needsSpeakerNotes=True)
        assert check_speaker_notes(deck) == []

    def test_requested_but_mostly_missing_warns(self):
        slides = [
            _minimal_slide(i, "bullet", f"S{i}", speakerNotes=[])
            for i in range(1, 6)
        ]
        deck = _minimal_deck(slides=slides, needsSpeakerNotes=True)
        warnings = check_speaker_notes(deck)
        assert len(warnings) >= 1


class TestLayoutVariety:
    def test_varied_layouts_clean(self):
        slides = [
            _minimal_slide(1, "title", "Title"),
            _minimal_slide(2, "bullet", "A", bullets=["x"]),
            _minimal_slide(3, "two-column", "B", left=["l"], right=["r"]),
            _minimal_slide(4, "chart", "C", chart={"type": "bar", "title": "T", "categories": ["Q1"], "series": [{"name": "X", "data": [1]}]}),
        ]
        deck = _minimal_deck(slides=slides)
        assert check_layout_variety(deck) == []

    def test_monotone_layout_warns(self):
        slides = [
            _minimal_slide(1, "title", "Title"),
            _minimal_slide(2, "bullet", "A", bullets=["x"]),
            _minimal_slide(3, "bullet", "B", bullets=["y"]),
            _minimal_slide(4, "bullet", "C", bullets=["z"]),
            _minimal_slide(5, "bullet", "D", bullets=["w"]),
        ]
        deck = _minimal_deck(slides=slides)
        warnings = check_layout_variety(deck)
        assert len(warnings) == 1


class TestSourceAttribution:
    def test_hidden_mode_always_clean(self):
        deck = _minimal_deck(sourceDisplayMode="hidden")
        assert check_source_attribution(deck) == []

    def test_notes_mode_with_sources_clean(self):
        slides = [_minimal_slide(1, "bullet", "A", bullets=["x"], sources=[{"label": "Test", "ref": "test.md"}])]
        deck = _minimal_deck(slides=slides, sourceDisplayMode="notes")
        assert check_source_attribution(deck) == []

    def test_notes_mode_without_sources_warns(self):
        slides = [_minimal_slide(1, "bullet", "A", bullets=["x"])]
        deck = _minimal_deck(slides=slides, sourceDisplayMode="notes")
        warnings = check_source_attribution(deck)
        assert len(warnings) == 1


# ===========================================================================
# Composite scorer tests
# ===========================================================================


class TestScoreDeck:
    def test_valid_deck_passes(self):
        deck = _minimal_deck()
        result = score_deck(deck)
        assert result["pass"] is True
        assert result["hard_score"] == 1.0

    def test_mock_deck_passes(self):
        deck = build_mock_deck("Create an 8-slide strategy deck", [], [], [])
        result = score_deck(deck)
        assert result["pass"] is True
        assert result["hard_score"] == 1.0

    def test_broken_deck_fails(self):
        deck = _minimal_deck()
        del deck["deckTitle"]
        result = score_deck(deck)
        assert result["pass"] is False
        assert "schema_compliance" in result["hard_failures"]

    def test_summary_reflects_status(self):
        deck = _minimal_deck()
        result = score_deck(deck)
        assert "PASS" in result["summary"]

    def test_soft_warnings_do_not_fail(self):
        slides = [_minimal_slide(1, "bullet", "Dense", bullets=list("abcdefghij"))]
        deck = _minimal_deck(slides=slides)
        result = score_deck(deck)
        assert result["pass"] is True
        assert result["soft_score"] < 1.0
        assert "warnings" in result["summary"]
