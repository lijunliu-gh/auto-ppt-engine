"""Unit tests for the Python smart layer and source loader."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

# Ensure repo root is importable
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from python_backend.smart_layer import (
    build_mock_deck,
    clamp_slide_count,
    compress_deck,
    create_validator,
    empty_slide,
    extract_json,
    extract_numerical_hints,
    format_validation_errors,
    infer_audience,
    infer_deck_title,
    infer_slide_count,
    infer_theme,
    load_schema,
    normalize_closing_slide,
    normalize_deck_source_metadata,
    renumber_slides,
    validate_chart_slides,
    _is_valid_chart,
    apply_heuristic_revision,
    execute_planning_flow,
)
from python_backend.source_loader import (
    load_source_contexts,
    _resolve_local_path,
    _is_url,
    _html_to_text,
)


# ── Schema & Validation ──────────────────────────────────────────────────────

class TestSchemaValidation:
    def test_load_schema_returns_dict(self):
        schema = load_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_schema_requires_schema_version(self):
        schema = load_schema()
        assert "schemaVersion" in schema["required"]

    def test_validator_accepts_valid_mock_deck(self):
        validator = create_validator()
        deck = build_mock_deck("Test presentation", [], [], [])
        errors = list(validator.iter_errors(deck))
        assert errors == [], f"Schema errors: {format_validation_errors(errors)}"

    def test_validator_rejects_missing_title(self):
        validator = create_validator()
        deck = build_mock_deck("Test", [], [], [])
        del deck["deckTitle"]
        errors = list(validator.iter_errors(deck))
        assert len(errors) > 0

    def test_format_validation_errors_empty(self):
        assert "Unknown" in format_validation_errors([])


# ── Inference Functions ───────────────────────────────────────────────────────

class TestInferenceFunctions:
    def test_infer_theme_tech(self):
        assert infer_theme("A tech startup pitch") == "tech-modern"

    def test_infer_theme_pitch(self):
        assert infer_theme("investor pitch deck") == "pitch-bold"

    def test_infer_theme_default(self):
        assert infer_theme("quarterly review") == "business-clean"

    def test_infer_slide_count_explicit(self):
        assert infer_slide_count("Create 10 slides about AI") == 10

    def test_infer_slide_count_default(self):
        assert infer_slide_count("Create a presentation") == 8

    def test_clamp_slide_count_low(self):
        assert clamp_slide_count(2) == 5

    def test_clamp_slide_count_high(self):
        assert clamp_slide_count(20) == 12

    def test_clamp_slide_count_invalid(self):
        assert clamp_slide_count("abc") == 8

    def test_infer_audience_executive(self):
        assert "Executive" in infer_audience("board presentation")

    def test_infer_deck_title_long(self):
        title = infer_deck_title("A" * 100)
        assert len(title) <= 36

    def test_infer_deck_title_empty(self):
        assert infer_deck_title("") == "Auto-generated Presentation"


# ── Slide Utilities ───────────────────────────────────────────────────────────

class TestSlideUtilities:
    def test_empty_slide_structure(self):
        slide = empty_slide(1, "bullet", "Test")
        assert slide["page"] == 1
        assert slide["layout"] == "bullet"
        assert slide["title"] == "Test"
        assert isinstance(slide["bullets"], list)
        assert isinstance(slide["sources"], list)

    def test_renumber_slides(self):
        deck = {"slides": [
            empty_slide(5, "bullet", "A"),
            empty_slide(9, "bullet", "B"),
        ]}
        renumber_slides(deck)
        assert deck["slides"][0]["page"] == 1
        assert deck["slides"][1]["page"] == 2
        assert deck["slideCount"] == 2

    def test_normalize_closing_slide_empty(self):
        deck = {"slides": []}
        normalize_closing_slide(deck)  # should not raise
        assert deck["slides"] == []

    def test_normalize_closing_slide_moves_to_end(self):
        deck = {"slides": [
            empty_slide(1, "title", "Intro"),
            empty_slide(2, "closing", "End"),
            empty_slide(3, "bullet", "Middle"),
        ]}
        normalize_closing_slide(deck)
        assert deck["slides"][-1]["layout"] == "closing"

    def test_compress_deck(self):
        deck = {"slides": [
            empty_slide(1, "title", "Intro"),
            empty_slide(2, "bullet", "A"),
            empty_slide(3, "bullet", "B"),
            empty_slide(4, "bullet", "C"),
            empty_slide(5, "closing", "End"),
        ]}
        compress_deck(deck, 3)
        assert len(deck["slides"]) == 3


# ── Mock Deck Generation ─────────────────────────────────────────────────────

class TestMockDeck:
    def test_build_mock_deck_valid(self):
        deck = build_mock_deck("AI strategy presentation", [], [], [])
        assert deck["schemaVersion"] == "0.3.0"
        assert isinstance(deck["slides"], list)
        assert len(deck["slides"]) > 0
        assert deck["slides"][0]["layout"] == "title"
        assert deck["slides"][-1]["layout"] == "closing"

    def test_build_mock_deck_with_context(self):
        deck = build_mock_deck("Test", [], ["context1"], [])
        found = any("context" in a.lower() for a in deck["assumptions"])
        assert found

    def test_normalize_deck_source_metadata_adds_version(self):
        deck = {"slides": [empty_slide(1, "bullet", "A")]}
        result = normalize_deck_source_metadata(deck)
        assert result["schemaVersion"] == "0.3.0"
        assert result["sourceDisplayMode"] == "notes"


# ── execute_planning_flow (mock mode) ─────────────────────────────────────────

class TestExecutePlanningFlow:
    def test_mock_create(self):
        deck = execute_planning_flow(prompt="Test deck", mock=True, mode="create")
        validator = create_validator()
        errors = list(validator.iter_errors(deck))
        assert errors == [], format_validation_errors(errors)
        assert deck["schemaVersion"] == "0.3.0"

    def test_mock_revise(self):
        original = execute_planning_flow(prompt="Original", mock=True, mode="create")
        revised = execute_planning_flow(
            prompt="Add more detail to slide 3",
            mock=True,
            mode="revise",
            existing_deck=original,
        )
        validator = create_validator()
        errors = list(validator.iter_errors(revised))
        assert errors == [], format_validation_errors(errors)

    def test_mock_revise_without_deck_fails(self):
        with pytest.raises(RuntimeError, match="existingDeck"):
            execute_planning_flow(prompt="Revise", mock=True, mode="revise")


# ── Heuristic Revision ───────────────────────────────────────────────────────

class TestHeuristicRevision:
    def _base_deck(self) -> dict:
        return execute_planning_flow(prompt="Base deck", mock=True, mode="create")

    def test_compress_revision(self):
        deck = self._base_deck()
        original_count = deck["slideCount"]
        revised = apply_heuristic_revision(deck, "compress to 5 slides", [])
        assert revised["slideCount"] <= 5

    def test_theme_revision(self):
        deck = self._base_deck()
        revised = apply_heuristic_revision(deck, "make it tech themed", [])
        assert revised["theme"] == "tech-modern"


# ── JSON Extraction ───────────────────────────────────────────────────────────

class TestExtractJson:
    def test_clean_json(self):
        result = extract_json('{"key": "value"}')
        assert json.loads(result) == {"key": "value"}

    def test_json_wrapped_in_text(self):
        result = extract_json('Here is the result: {"key": "value"} enjoy!')
        assert json.loads(result) == {"key": "value"}

    def test_no_json_raises(self):
        with pytest.raises(RuntimeError, match="JSON"):
            extract_json("no json here")


# ── LLM Provider ─────────────────────────────────────────────────────────────

class TestLLMProvider:
    def test_reasoning_model_detection(self):
        from python_backend.llm_provider import OpenAIProvider
        provider = object.__new__(OpenAIProvider)
        for model, expected in [
            ("o3", True),
            ("o3-mini", True),
            ("o4-mini", True),
            ("o1", True),
            ("o1-pro", True),
            ("codex-mini-latest", True),
            ("gpt-4.1-mini", False),
            ("gpt-4o", False),
            ("gpt-4.1", False),
        ]:
            provider._model = model
            assert provider._is_reasoning_model() == expected, f"{model} should be reasoning={expected}"

    def test_standard_model_uses_system_role(self):
        from python_backend.llm_provider import OpenAIProvider
        provider = object.__new__(OpenAIProvider)
        provider._model = "gpt-4.1-mini"
        assert not provider._is_reasoning_model()

    def test_reasoning_model_uses_developer_role(self):
        from python_backend.llm_provider import OpenAIProvider
        provider = object.__new__(OpenAIProvider)
        provider._model = "o3"
        assert provider._is_reasoning_model()

    def test_provider_auto_detection(self):
        from python_backend.llm_provider import (
            _detect_provider_class,
            OpenAIProvider,
            AnthropicProvider,
            GeminiProvider,
        )
        # OpenAI family
        assert _detect_provider_class("gpt-4.1-mini") is OpenAIProvider
        assert _detect_provider_class("gpt-4o") is OpenAIProvider
        assert _detect_provider_class("o3") is OpenAIProvider
        # Chinese models go through OpenAI-compatible
        assert _detect_provider_class("qwen-plus") is OpenAIProvider
        assert _detect_provider_class("deepseek-chat") is OpenAIProvider
        assert _detect_provider_class("glm-4-plus") is OpenAIProvider
        assert _detect_provider_class("MiniMax-Text-01") is OpenAIProvider
        # Anthropic
        assert _detect_provider_class("claude-sonnet-4-20250514") is AnthropicProvider
        assert _detect_provider_class("claude-3.5-sonnet") is AnthropicProvider
        assert _detect_provider_class("claude-3-opus") is AnthropicProvider
        # Gemini
        assert _detect_provider_class("gemini-2.5-pro") is GeminiProvider
        assert _detect_provider_class("gemini-2.0-flash") is GeminiProvider

    def test_anthropic_provider_class_exists(self):
        from python_backend.llm_provider import AnthropicProvider
        assert hasattr(AnthropicProvider, "chat")

    def test_gemini_provider_class_exists(self):
        from python_backend.llm_provider import GeminiProvider
        assert hasattr(GeminiProvider, "chat")


# ── Source Loader ─────────────────────────────────────────────────────────────

class TestSourceLoader:
    def test_is_url(self):
        assert _is_url("https://example.com")
        assert _is_url("http://example.com")
        assert not _is_url("/some/path")
        assert not _is_url("relative/path.txt")

    def test_html_to_text(self):
        html = "<h1>Title</h1><p>Body text</p>"
        text = _html_to_text(html)
        assert "Title" in text
        assert "Body" in text
        assert "<h1>" not in text

    def test_load_text_source(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello source content")
            f.flush()
            path = f.name
        try:
            result = load_source_contexts([path], str(Path(path).parent))
            assert len(result["loaded_sources"]) == 1
            assert "Hello source content" in result["context_texts"][0]
        finally:
            os.unlink(path)

    def test_load_json_source(self):
        data = {"key": "value", "number": 42}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            result = load_source_contexts([path], str(Path(path).parent))
            assert "key" in result["context_texts"][0]
        finally:
            os.unlink(path)

    def test_truncation_tracking(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("x" * 10000)
            path = f.name
        try:
            result = load_source_contexts([path], str(Path(path).parent))
            assert len(result["truncated_sources"]) == 1
            assert "[truncated]" in result["context_texts"][0]
        finally:
            os.unlink(path)


# ── Security: Path Traversal ─────────────────────────────────────────────────

class TestPathTraversal:
    def test_path_traversal_blocked(self):
        base = Path(tempfile.mkdtemp())
        with pytest.raises(RuntimeError, match="traversal"):
            _resolve_local_path("../../etc/passwd", base)

    def test_normal_path_allowed(self):
        base = Path(tempfile.mkdtemp())
        (base / "file.txt").write_text("ok")
        result = _resolve_local_path("file.txt", base)
        assert result == (base / "file.txt").resolve()


# ── Chart Validation & Fallback ──────────────────────────────────────────────

class TestChartValidation:
    def test_valid_chart(self):
        chart = {
            "type": "bar",
            "title": "Revenue",
            "categories": ["Q1", "Q2", "Q3"],
            "series": [{"name": "2025", "data": [100, 200, 300]}],
        }
        assert _is_valid_chart(chart) is True

    def test_empty_categories_invalid(self):
        chart = {"type": "bar", "title": "X", "categories": [], "series": [{"name": "A", "data": [1]}]}
        assert _is_valid_chart(chart) is False

    def test_empty_series_invalid(self):
        chart = {"type": "bar", "title": "X", "categories": ["Q1"], "series": []}
        assert _is_valid_chart(chart) is False

    def test_non_numeric_data_invalid(self):
        chart = {
            "type": "bar", "title": "X",
            "categories": ["A"], "series": [{"name": "S", "data": ["not-a-number"]}],
        }
        assert _is_valid_chart(chart) is False

    def test_empty_data_array_invalid(self):
        chart = {"type": "bar", "title": "X", "categories": ["A"], "series": [{"name": "S", "data": []}]}
        assert _is_valid_chart(chart) is False

    def test_fallback_converts_to_bullet(self):
        deck = {
            "slides": [
                {
                    "page": 1, "layout": "chart", "title": "Bad chart",
                    "chart": {"type": "bar", "title": "Empty", "categories": [], "series": []},
                    "bullets": [], "objective": "",
                },
            ],
        }
        notes = validate_chart_slides(deck)
        assert len(notes) == 1
        assert deck["slides"][0]["layout"] == "bullet"
        assert "converted to bullet" in notes[0].lower()

    def test_valid_chart_not_degraded(self):
        deck = {
            "slides": [
                {
                    "page": 1, "layout": "chart", "title": "Good chart",
                    "chart": {
                        "type": "bar", "title": "Revenue",
                        "categories": ["Q1", "Q2"], "series": [{"name": "A", "data": [10, 20]}],
                    },
                    "bullets": [], "objective": "",
                },
            ],
        }
        notes = validate_chart_slides(deck)
        assert len(notes) == 0
        assert deck["slides"][0]["layout"] == "chart"

    def test_mock_deck_includes_chart_slide(self):
        deck = build_mock_deck("Test chart deck", [], [], [])
        chart_slides = [s for s in deck["slides"] if s["layout"] == "chart"]
        assert len(chart_slides) >= 1
        chart = chart_slides[0]["chart"]
        assert _is_valid_chart(chart)


class TestNumericalExtraction:
    def test_extracts_percentages(self):
        text = "Revenue grew 25% in Q1, 30% in Q2, and 45% in Q3"
        result = extract_numerical_hints([text])
        assert "NUMERICAL DATA DETECTED" in result

    def test_extracts_dollar_amounts(self):
        text = "Total revenue: $1,200,000 in 2024, $1,500,000 in 2025, projected $2,000,000 in 2026"
        result = extract_numerical_hints([text])
        assert "NUMERICAL DATA DETECTED" in result

    def test_no_numbers_returns_empty(self):
        text = "This is a purely qualitative description without any numbers"
        result = extract_numerical_hints([text])
        assert result == ""

    def test_few_numbers_not_triggered(self):
        text = "Only 5% of users"
        result = extract_numerical_hints([text])
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
