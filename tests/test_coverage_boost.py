"""Tests to boost coverage for llm_provider, source_loader, skill_api, and smart_layer."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent


# ══════════════════════════════════════════════════════════════════════
# llm_provider.py
# ══════════════════════════════════════════════════════════════════════

from python_backend.llm_provider import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    _detect_provider_class,
    get_default_provider,
)


class TestOpenAIProvider:
    def test_init_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENAI_API_KEY", None)
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                OpenAIProvider()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("importlib.import_module")
    def test_init_uses_env_key(self, mock_import):
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        provider = OpenAIProvider()
        assert provider._model == "gpt-4.1-mini"
        mock_openai.OpenAI.assert_called_once()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("importlib.import_module")
    def test_init_custom_model_and_base_url(self, mock_import):
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        provider = OpenAIProvider(api_key="k", base_url="http://custom", model="qwen-plus")
        assert provider._model == "qwen-plus"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("importlib.import_module")
    def test_is_reasoning_model(self, mock_import):
        mock_import.return_value = MagicMock()
        for model in ("o1-preview", "o3-mini", "o4-mini", "codex-mini-latest"):
            p = OpenAIProvider(api_key="k", model=model)
            assert p._is_reasoning_model() is True
        for model in ("gpt-4.1-mini", "gpt-4o", "qwen-plus"):
            p = OpenAIProvider(api_key="k", model=model)
            assert p._is_reasoning_model() is False

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("importlib.import_module")
    def test_chat_standard_model(self, mock_import):
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        mock_client = mock_openai.OpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"deckTitle":"Test"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="k", model="gpt-4.1-mini")
        result = provider.chat("system", "user")
        assert result == '{"deckTitle":"Test"}'
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["messages"][0]["role"] == "system"
        assert "temperature" in call_kwargs

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_REASONING_EFFORT": "high"})
    @patch("importlib.import_module")
    def test_chat_reasoning_model(self, mock_import):
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        mock_client = mock_openai.OpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"ok":true}'))]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="k", model="o3-mini")
        result = provider.chat("system", "user")
        assert result == '{"ok":true}'
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["messages"][0]["role"] == "developer"
        assert call_kwargs["reasoning_effort"] == "high"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("importlib.import_module")
    def test_chat_no_content_raises(self, mock_import):
        mock_openai = MagicMock()
        mock_import.return_value = mock_openai
        mock_client = mock_openai.OpenAI.return_value
        mock_response = MagicMock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="k")
        with pytest.raises(RuntimeError, match="no content"):
            provider.chat("s", "u")


class TestAnthropicProvider:
    @patch("importlib.import_module")
    def test_init_requires_api_key(self, mock_import):
        mock_import.return_value = MagicMock()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                AnthropicProvider()

    @patch("importlib.import_module")
    def test_init_with_key(self, mock_import):
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-20250514")
        assert provider._model == "claude-sonnet-4-20250514"

    @patch("importlib.import_module")
    def test_chat_success(self, mock_import):
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        mock_client = mock_anthropic.Anthropic.return_value
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"deckTitle":"Test"}')]
        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="k", model="claude-sonnet-4-20250514")
        result = provider.chat("system", "user")
        assert result == '{"deckTitle":"Test"}'

    @patch("importlib.import_module")
    def test_chat_no_content_raises(self, mock_import):
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        mock_client = mock_anthropic.Anthropic.return_value
        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="k")
        with pytest.raises(RuntimeError, match="no content"):
            provider.chat("s", "u")


class TestGeminiProvider:
    @patch("importlib.import_module")
    def test_init_requires_api_key(self, mock_import):
        mock_import.return_value = MagicMock()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_API_KEY", None)
            with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
                GeminiProvider()

    @patch("importlib.import_module")
    def test_init_with_key(self, mock_import):
        mock_genai = MagicMock()
        mock_import.return_value = mock_genai
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-pro")
        assert provider._model_name == "gemini-2.5-pro"
        mock_genai.configure.assert_called_once_with(api_key="test-key")

    @patch("importlib.import_module")
    def test_chat_success(self, mock_import):
        mock_genai = MagicMock()
        mock_import.return_value = mock_genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = '{"deckTitle":"Test"}'
        mock_model.generate_content.return_value = mock_response

        provider = GeminiProvider(api_key="k", model="gemini-2.5-pro")
        result = provider.chat("system", "user")
        assert result == '{"deckTitle":"Test"}'

    @patch("importlib.import_module")
    def test_chat_no_content_raises(self, mock_import):
        mock_genai = MagicMock()
        mock_import.return_value = mock_genai
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model.generate_content.return_value = mock_response

        provider = GeminiProvider(api_key="k")
        with pytest.raises(RuntimeError, match="no content"):
            provider.chat("s", "u")


class TestProviderFactory:
    def test_detect_anthropic(self):
        assert _detect_provider_class("claude-sonnet-4-20250514") is AnthropicProvider

    def test_detect_gemini(self):
        assert _detect_provider_class("gemini-2.5-pro") is GeminiProvider

    def test_detect_openai_default(self):
        assert _detect_provider_class("gpt-4.1-mini") is OpenAIProvider

    def test_detect_openai_for_custom(self):
        assert _detect_provider_class("qwen-plus") is OpenAIProvider

    @patch.dict(os.environ, {"OPENAI_MODEL": "claude-sonnet-4-20250514", "ANTHROPIC_API_KEY": "test"})
    @patch("importlib.import_module")
    def test_get_default_provider_anthropic(self, mock_import):
        mock_anthropic = MagicMock()
        mock_import.return_value = mock_anthropic
        provider = get_default_provider()
        assert isinstance(provider, AnthropicProvider)

    @patch.dict(os.environ, {"OPENAI_MODEL": "gemini-2.5-pro", "GOOGLE_API_KEY": "test"})
    @patch("importlib.import_module")
    def test_get_default_provider_gemini(self, mock_import):
        mock_genai = MagicMock()
        mock_import.return_value = mock_genai
        provider = get_default_provider()
        assert isinstance(provider, GeminiProvider)


# ══════════════════════════════════════════════════════════════════════
# source_loader.py
# ══════════════════════════════════════════════════════════════════════

from python_backend.source_loader import (
    _is_url,
    _html_to_text,
    _resolve_local_path,
    _read_text_file,
    _normalize_source,
    _read_source_text,
    _build_context_text,
    _check_file_size,
    _validate_url_target,
    load_source_contexts,
    MAX_FILE_SIZE_BYTES,
)


class TestSourceLoaderHelpers:
    def test_read_text_file_utf8(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        assert _read_text_file(f) == "hello world"

    def test_read_text_file_latin1(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes("café".encode("latin-1"))
        result = _read_text_file(f)
        assert "caf" in result

    def test_resolve_local_path_traversal_blocked(self, tmp_path):
        with pytest.raises(RuntimeError, match="traversal"):
            _resolve_local_path("../../etc/passwd", tmp_path)

    def test_resolve_local_path_valid(self, tmp_path):
        f = tmp_path / "data.txt"
        f.touch()
        resolved = _resolve_local_path("data.txt", tmp_path)
        assert resolved == f

    def test_html_to_text_extracts(self):
        html = "<html><body><p>Hello</p><p>World</p></body></html>"
        result = _html_to_text(html)
        assert "Hello" in result
        assert "World" in result

    def test_html_to_text_empty_returns_original(self):
        html = "<html><body></body></html>"
        result = _html_to_text(html)
        assert result == html

    def test_check_file_size_ok(self, tmp_path):
        f = tmp_path / "small.txt"
        f.write_bytes(b"x" * 100)
        _check_file_size(f)  # should not raise

    def test_check_file_size_too_large(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_bytes(b"x" * (MAX_FILE_SIZE_BYTES + 1))
        with pytest.raises(RuntimeError, match="too large"):
            _check_file_size(f)

    def test_validate_url_target_non_http_blocked(self):
        with pytest.raises(RuntimeError, match="scheme"):
            _validate_url_target("ftp://example.com/file")

    def test_validate_url_target_no_hostname_blocked(self):
        with pytest.raises(RuntimeError, match="Invalid URL"):
            _validate_url_target("http:///no-host")

    @patch("socket.getaddrinfo", return_value=[
        (2, 1, 6, "", ("127.0.0.1", 0))
    ])
    def test_validate_url_target_loopback_blocked(self, _mock_dns):
        with pytest.raises(RuntimeError, match="blocked"):
            _validate_url_target("http://evil.local/test")


class TestNormalizeSource:
    def test_string_source(self, tmp_path):
        f = tmp_path / "readme.md"
        f.touch()
        result = _normalize_source(str(f), tmp_path)
        assert result["label"] == f.name
        assert result["type"] == "file"

    def test_url_source(self, tmp_path):
        result = _normalize_source({"url": "https://example.com/api"}, tmp_path)
        assert result["type"] == "url"
        assert result["_is_url"] is True
        assert result["label"] == "api"

    def test_dict_source_with_label(self, tmp_path):
        f = tmp_path / "data.json"
        f.touch()
        result = _normalize_source({"path": str(f), "label": "My Data"}, tmp_path)
        assert result["label"] == "My Data"

    def test_invalid_source_type(self, tmp_path):
        with pytest.raises(RuntimeError, match="string or object"):
            _normalize_source(42, tmp_path)

    def test_missing_location(self, tmp_path):
        with pytest.raises(RuntimeError, match="path, url, or location"):
            _normalize_source({"label": "no path"}, tmp_path)


class TestReadSourceText:
    def test_read_text_file(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# Notes\nHello")
        spec = _normalize_source(str(f), tmp_path)
        text = _read_source_text(spec)
        assert "Hello" in text

    def test_read_json_file(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}')
        spec = _normalize_source(str(f), tmp_path)
        text = _read_source_text(spec)
        assert '"key"' in text

    def test_read_html_file(self, tmp_path):
        f = tmp_path / "page.html"
        f.write_text("<html><body><p>Content</p></body></html>")
        spec = _normalize_source(str(f), tmp_path)
        text = _read_source_text(spec)
        assert "Content" in text

    def test_read_image_file(self, tmp_path):
        f = tmp_path / "logo.png"
        f.write_bytes(b"\x89PNG")
        spec = _normalize_source(str(f), tmp_path)
        text = _read_source_text(spec)
        assert "Image asset reference" in text

    def test_read_binary_file(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        spec = _normalize_source(str(f), tmp_path)
        text = _read_source_text(spec)
        assert "Binary or unsupported" in text

    def test_file_not_found(self, tmp_path):
        spec = {
            "label": "missing",
            "type": "file",
            "location": str(tmp_path / "nope.txt"),
            "trustLevel": "user-provided",
            "priority": "normal",
            "notes": "",
            "citation": "",
            "_is_url": False,
        }
        with pytest.raises(RuntimeError, match="not found"):
            _read_source_text(spec)


class TestBuildContextText:
    def test_short_text_not_truncated(self):
        spec = {"label": "test", "type": "file", "location": "/tmp/t", "trustLevel": "user-provided", "priority": "normal", "notes": "", "citation": ""}
        text, truncated = _build_context_text(spec, "short content")
        assert not truncated
        assert "short content" in text

    def test_long_text_truncated(self):
        spec = {"label": "big", "type": "file", "location": "/tmp/b", "trustLevel": "user-provided", "priority": "high", "notes": "important", "citation": "cite me"}
        text, truncated = _build_context_text(spec, "x" * 6000)
        assert truncated
        assert "[truncated]" in text
        assert "Notes: important" in text
        assert "Citation: cite me" in text


class TestLoadSourceContexts:
    def test_load_multiple_sources(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f1.write_text("content A")
        f2 = tmp_path / "b.md"
        f2.write_text("content B")
        result = load_source_contexts([str(f1), str(f2)], tmp_path)
        assert len(result["loaded_sources"]) == 2
        assert len(result["context_texts"]) == 2
        assert "_is_url" not in result["loaded_sources"][0]

    def test_load_truncated_tracking(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("x" * 6000)
        result = load_source_contexts([str(f)], tmp_path)
        assert len(result["truncated_sources"]) == 1


# ══════════════════════════════════════════════════════════════════════
# skill_api.py
# ══════════════════════════════════════════════════════════════════════

from python_backend.skill_api import (
    load_request,
    resolve_from_base,
    handle_skill_request,
)


class TestSkillAPILoadRequest:
    def test_valid_create_request(self, tmp_path):
        req = tmp_path / "req.json"
        req.write_text(json.dumps({"action": "create", "prompt": "make a deck"}))
        result = load_request(req)
        assert result["action"] == "create"
        assert result["prompt"] == "make a deck"
        assert "_baseDir" in result

    def test_valid_revise_request(self, tmp_path):
        req = tmp_path / "req.json"
        req.write_text(json.dumps({"action": "revise", "prompt": "compress to 5 slides"}))
        result = load_request(req)
        assert result["action"] == "revise"

    def test_invalid_action(self, tmp_path):
        req = tmp_path / "req.json"
        req.write_text(json.dumps({"action": "delete", "prompt": "test"}))
        with pytest.raises(RuntimeError, match="create.*revise"):
            load_request(req)

    def test_missing_prompt(self, tmp_path):
        req = tmp_path / "req.json"
        req.write_text(json.dumps({"action": "create"}))
        with pytest.raises(RuntimeError, match="prompt"):
            load_request(req)

    def test_non_dict_payload(self, tmp_path):
        req = tmp_path / "req.json"
        req.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(RuntimeError, match="object"):
            load_request(req)


class TestResolveFromBase:
    def test_relative_path(self, tmp_path):
        result = resolve_from_base(tmp_path, "sub/file.json")
        assert result == (tmp_path / "sub" / "file.json").resolve()

    def test_absolute_path(self, tmp_path):
        result = resolve_from_base(tmp_path, "/absolute/path.json")
        assert result == Path("/absolute/path.json")


class TestHandleSkillRequest:
    def test_mock_create(self, tmp_path):
        request = {
            "action": "create",
            "prompt": "Test deck about testing",
            "mock": True,
            "_baseDir": str(tmp_path),
        }
        with patch("python_backend.skill_api.render_deck_via_node") as mock_render:
            response = handle_skill_request(request)
        assert response["ok"] is True
        assert response["action"] == "create"
        assert response["renderer"] == "pptxgenjs"
        assert response["slideCount"] > 0
        mock_render.assert_called_once()

    def test_mock_create_saves_response(self, tmp_path):
        request = {
            "action": "create",
            "prompt": "Test deck",
            "mock": True,
            "_baseDir": str(tmp_path),
        }
        resp_path = tmp_path / "output" / "resp.json"
        with patch("python_backend.skill_api.render_deck_via_node"):
            response = handle_skill_request(request, response_path=resp_path)
        assert resp_path.exists()
        saved = json.loads(resp_path.read_text())
        assert saved["ok"] is True

    def test_mock_create_with_sources(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("Source content here")
        request = {
            "action": "create",
            "prompt": "Deck with sources",
            "mock": True,
            "sources": [str(src)],
            "_baseDir": str(tmp_path),
        }
        with patch("python_backend.skill_api.render_deck_via_node"):
            response = handle_skill_request(request)
        assert len(response["sourcesUsed"]) == 1

    def test_mock_create_with_context_files(self, tmp_path):
        ctx = tmp_path / "context.md"
        ctx.write_text("Context material")
        request = {
            "action": "create",
            "prompt": "Deck with context",
            "mock": True,
            "contextFiles": ["context.md"],
            "_baseDir": str(tmp_path),
        }
        with patch("python_backend.skill_api.render_deck_via_node"):
            response = handle_skill_request(request)
        assert response["ok"] is True


# ══════════════════════════════════════════════════════════════════════
# smart_layer.py — additional coverage
# ══════════════════════════════════════════════════════════════════════

from python_backend.smart_layer import (
    apply_heuristic_revision,
    apply_page_specific_revision,
    apply_requested_theme,
    build_create_prompt,
    build_mock_deck,
    build_repair_prompt,
    build_revise_prompt,
    build_system_prompt,
    compress_deck,
    emphasize_execution_plan,
    empty_slide,
    execute_planning_flow,
    extract_json,
    infer_audience,
    infer_scenario,
    infer_tone,
    infer_theme,
    make_more_conclusion_driven,
    normalize_closing_slide,
    normalize_deck_source_metadata,
    renumber_slides,
    requested_page_index,
    requested_slide_count,
    revise_requested_layout,
)


class TestSmartLayerInference:
    def test_infer_audience_executive(self):
        assert "xecutive" in infer_audience("board meeting for executives")

    def test_infer_audience_investor(self):
        assert "nvestor" in infer_audience("investor pitch")

    def test_infer_audience_client(self):
        assert "ustomer" in infer_audience("client review")

    def test_infer_audience_default(self):
        result = infer_audience("general meeting")
        assert "stakeholder" in result.lower()

    def test_infer_scenario_training(self):
        assert "raining" in infer_scenario("training session")

    def test_infer_scenario_investor(self):
        assert "nvestor" in infer_scenario("investor pitch")

    def test_infer_scenario_review(self):
        assert "review" in infer_scenario("quarterly review").lower()

    def test_infer_scenario_default(self):
        result = infer_scenario("something")
        assert "resentation" in result.lower()

    def test_infer_tone_tech(self):
        assert "echnical" in infer_tone("tech stack overview")

    def test_infer_tone_professional(self):
        assert "rofessional" in infer_tone("professional briefing")

    def test_infer_tone_default(self):
        result = infer_tone("general topic")
        assert "rofessional" in result

    def test_infer_theme_tech(self):
        assert infer_theme("tech review") == "tech-modern"

    def test_infer_theme_pitch(self):
        assert infer_theme("investor pitch") == "pitch-bold"

    def test_infer_theme_training(self):
        assert infer_theme("training session") == "education-bright"

    def test_infer_theme_internal(self):
        assert infer_theme("internal review") == "internal-minimal"

    def test_infer_theme_default(self):
        assert infer_theme("general") == "business-clean"


class TestSmartLayerPrompts:
    def test_build_system_prompt_contains_layouts(self):
        prompt = build_system_prompt("skill text", {"type": "object"})
        assert "bullet" in prompt
        assert "CHART DATA RULES" in prompt
        assert "VISUAL RULES" in prompt

    def test_build_create_prompt_basic(self):
        prompt = build_create_prompt("make a deck", [], [])
        assert "make a deck" in prompt

    def test_build_create_prompt_with_context(self):
        prompt = build_create_prompt("deck", ["context A", "context B"], [])
        assert "Context 1" in prompt
        assert "Context 2" in prompt

    def test_build_create_prompt_with_research(self):
        prompt = build_create_prompt("deck", [], ["Research note 1"])
        assert "Research note 1" in prompt

    def test_build_revise_prompt(self):
        deck = {"deckTitle": "Test", "slides": []}
        prompt = build_revise_prompt(deck, "compress to 5 slides", [], [])
        assert "compress to 5 slides" in prompt
        assert "Test" in prompt

    def test_build_repair_prompt(self):
        prompt = build_repair_prompt("original", '{"bad": true}', "slideCount mismatch")
        assert "slideCount mismatch" in prompt
        assert '{"bad": true}' in prompt


class TestSmartLayerRevisionHelpers:
    @pytest.fixture
    def base_deck(self):
        return {
            "deckTitle": "Test",
            "slides": [
                empty_slide(1, "title", "Title"),
                empty_slide(2, "bullet", "Content"),
                empty_slide(3, "bullet", "More"),
                empty_slide(4, "closing", "End"),
            ],
            "slideCount": 4,
        }

    def test_apply_requested_theme_tech(self, base_deck):
        apply_requested_theme(base_deck, "make it tech-modern")
        assert base_deck["theme"] == "tech-modern"

    def test_apply_requested_theme_professional(self, base_deck):
        apply_requested_theme(base_deck, "professional look")
        assert base_deck["theme"] == "business-clean"

    def test_apply_page_specific_revision_timeline(self, base_deck):
        result = apply_page_specific_revision(base_deck, "change slide 2 to timeline")
        assert result is True
        assert base_deck["slides"][1]["layout"] == "timeline"

    def test_apply_page_specific_revision_comparison(self, base_deck):
        result = apply_page_specific_revision(base_deck, "change slide 3 to comparison")
        assert result is True
        assert base_deck["slides"][2]["layout"] == "comparison"

    def test_apply_page_specific_revision_process(self, base_deck):
        apply_page_specific_revision(base_deck, "change slide 2 to process")
        assert base_deck["slides"][1]["layout"] == "process"

    def test_apply_page_specific_revision_two_column(self, base_deck):
        apply_page_specific_revision(base_deck, "change slide 2 to two-column")
        assert base_deck["slides"][1]["layout"] == "two-column"

    def test_apply_page_specific_revision_summary(self, base_deck):
        apply_page_specific_revision(base_deck, "change slide 2 to summary")
        assert base_deck["slides"][1]["layout"] == "summary"

    def test_apply_page_specific_revision_no_match(self, base_deck):
        result = apply_page_specific_revision(base_deck, "make it better")
        assert result is False

    def test_compress_deck(self, base_deck):
        compress_deck(base_deck, 3)
        assert len(base_deck["slides"]) == 3

    def test_compress_deck_no_change_if_under_target(self, base_deck):
        compress_deck(base_deck, 10)
        assert len(base_deck["slides"]) == 4

    def test_emphasize_execution_plan(self, base_deck):
        emphasize_execution_plan(base_deck)
        layouts = [s["layout"] for s in base_deck["slides"]]
        assert "process" in layouts or "timeline" in layouts

    def test_make_more_conclusion_driven(self, base_deck):
        make_more_conclusion_driven(base_deck)
        assert base_deck["slides"][1]["layout"] == "summary"
        assert base_deck["slides"][1]["title"] == "Key conclusions"

    def test_normalize_closing_slide_moves_to_end(self):
        deck = {
            "slides": [
                empty_slide(1, "title", "Title"),
                empty_slide(2, "closing", "End"),
                empty_slide(3, "bullet", "Content"),
            ]
        }
        normalize_closing_slide(deck)
        assert deck["slides"][-1]["layout"] == "closing"

    def test_renumber_slides(self):
        deck = {
            "slides": [
                {"page": 99, "layout": "title"},
                {"page": 1, "layout": "bullet"},
            ]
        }
        renumber_slides(deck)
        assert deck["slides"][0]["page"] == 1
        assert deck["slides"][1]["page"] == 2
        assert deck["slideCount"] == 2


class TestSmartLayerHeuristicRevision:
    def test_heuristic_revision_basic(self):
        deck = {
            "deckTitle": "Test",
            "slides": [
                empty_slide(1, "title", "Title"),
                empty_slide(2, "bullet", "Content"),
                empty_slide(3, "closing", "End"),
            ],
            "slideCount": 3,
        }
        result = apply_heuristic_revision(deck, "add more detail", [])
        assert result["slides"][-1]["layout"] == "closing"
        assert any("add more detail" in a for a in result.get("assumptions", []))

    def test_heuristic_revision_conclusion(self):
        deck = {
            "deckTitle": "Test",
            "slides": [
                empty_slide(1, "title", "Title"),
                empty_slide(2, "bullet", "Content"),
                empty_slide(3, "closing", "End"),
            ],
            "slideCount": 3,
        }
        result = apply_heuristic_revision(deck, "make it more conclusion driven", [])
        assert result["slides"][1]["layout"] == "summary"

    def test_heuristic_revision_execution_plan(self):
        deck = {
            "deckTitle": "Test",
            "slides": [
                empty_slide(1, "title", "Title"),
                empty_slide(2, "bullet", "Content"),
                empty_slide(3, "closing", "End"),
            ],
            "slideCount": 3,
        }
        result = apply_heuristic_revision(deck, "add execution plan", [])
        layouts = [s["layout"] for s in result["slides"]]
        assert "process" in layouts or "timeline" in layouts

    def test_heuristic_revision_compress(self):
        deck = {
            "deckTitle": "Test",
            "slides": [
                empty_slide(1, "title", "Title"),
                empty_slide(2, "bullet", "A"),
                empty_slide(3, "bullet", "B"),
                empty_slide(4, "bullet", "C"),
                empty_slide(5, "bullet", "D"),
                empty_slide(6, "bullet", "E"),
                empty_slide(7, "bullet", "F"),
                empty_slide(8, "bullet", "G"),
                empty_slide(9, "bullet", "H"),
                empty_slide(10, "closing", "End"),
            ],
            "slideCount": 10,
        }
        result = apply_heuristic_revision(deck, "compress to 5 slides", [])
        assert len(result["slides"]) == 5


class TestSmartLayerExecuteFlow:
    def test_execute_mock_create(self):
        deck = execute_planning_flow(
            prompt="Test deck about AI",
            mock=True,
            mode="create",
        )
        assert deck["deckTitle"]
        assert len(deck["slides"]) > 0

    def test_execute_mock_revise(self):
        original = execute_planning_flow(prompt="original deck", mock=True, mode="create")
        revised = execute_planning_flow(
            prompt="compress to 5 slides",
            mock=True,
            mode="revise",
            existing_deck=original,
        )
        assert revised["slides"][-1]["layout"] == "closing"

    def test_execute_mock_revise_no_deck_fails(self):
        with pytest.raises(RuntimeError, match="existingDeck"):
            execute_planning_flow(
                prompt="revise it",
                mock=True,
                mode="revise",
                existing_deck=None,
            )


class TestRequestedPageIndex:
    def test_extracts_slide_number(self):
        assert requested_page_index("change slide 3 to timeline") == 2

    def test_extracts_page_number(self):
        assert requested_page_index("update slide 1") == 0

    def test_no_match(self):
        assert requested_page_index("make it better") is None


class TestRequestedSlideCount:
    def test_extracts_count(self):
        assert requested_slide_count("compress to 5 slides") == 5

    def test_no_match(self):
        assert requested_slide_count("make it shorter") is None


class TestReviseRequestedLayout:
    def test_timeline(self):
        assert revise_requested_layout("change to timeline") == "timeline"

    def test_process(self):
        assert revise_requested_layout("make it a process layout") == "process"

    def test_chart(self):
        assert revise_requested_layout("convert to chart") == "chart"

    def test_no_match(self):
        assert revise_requested_layout("improve content") is None


class TestExtractJsonAdditional:
    def test_json_with_surrounding_text(self):
        text = 'Here is the result: {"key": "value"} done.'
        result = extract_json(text)
        assert result == '{"key": "value"}'
