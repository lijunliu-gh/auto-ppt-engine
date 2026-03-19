"""Tests for image_handler module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from python_backend.image_handler import (
    SUPPORTED_IMAGE_EXTENSIONS,
    MAX_IMAGE_SIZE,
    POSITION_PRESETS,
    DEFAULT_POSITION,
    classify_visual,
    partition_visuals,
    resolve_image,
    get_position,
    _looks_like_image_path,
    _load_local_image,
    _detect_image_ext,
)


# ── classify_visual ──────────────────────────────────────────────────


class TestClassifyVisual:
    def test_plain_string_description(self):
        result = classify_visual("Add a market chart")
        assert result["kind"] == "description"
        assert result["text"] == "Add a market chart"

    def test_string_image_path_png(self):
        result = classify_visual("images/logo.png")
        assert result["kind"] == "image"
        assert result["path"] == "images/logo.png"
        assert result["position"] == DEFAULT_POSITION

    def test_string_image_path_jpg(self):
        result = classify_visual("photo.JPG")
        assert result["kind"] == "image"

    def test_string_not_image_path(self):
        result = classify_visual("some-file.txt")
        assert result["kind"] == "description"

    def test_dict_image_with_path(self):
        result = classify_visual({"type": "image", "path": "assets/chart.png", "alt": "chart"})
        assert result["kind"] == "image"
        assert result["path"] == "assets/chart.png"
        assert result["alt"] == "chart"
        assert result["position"] == DEFAULT_POSITION

    def test_dict_image_with_url(self):
        result = classify_visual({"type": "image", "url": "https://example.com/img.png", "position": "center"})
        assert result["kind"] == "image"
        assert result["url"] == "https://example.com/img.png"
        assert result["position"] == "center"

    def test_dict_placeholder(self):
        result = classify_visual({"type": "placeholder", "prompt": "A workflow diagram", "position": "left"})
        assert result["kind"] == "placeholder"
        assert result["prompt"] == "A workflow diagram"
        assert result["position"] == "left"

    def test_dict_unknown_type_fallback(self):
        result = classify_visual({"type": "unknown", "data": "stuff"})
        assert result["kind"] == "description"

    def test_non_string_non_dict_fallback(self):
        result = classify_visual(42)
        assert result["kind"] == "description"
        assert result["text"] == "42"


# ── _looks_like_image_path ───────────────────────────────────────────


class TestLooksLikeImagePath:
    @pytest.mark.parametrize("path_str", [
        "logo.png", "img.JPG", "photo.jpeg", "anim.gif", "icon.bmp",
        "scan.tiff", "scan.tif", "graphic.svg", "banner.webp",
    ])
    def test_supported_extensions(self, path_str):
        assert _looks_like_image_path(path_str) is True

    @pytest.mark.parametrize("path_str", [
        "doc.pdf", "readme.md", "data.csv", "script.py", "archive.zip",
    ])
    def test_unsupported_extensions(self, path_str):
        assert _looks_like_image_path(path_str) is False

    def test_with_spaces(self):
        assert _looks_like_image_path("  photo.png  ") is True


# ── partition_visuals ────────────────────────────────────────────────


class TestPartitionVisuals:
    def test_empty_list(self):
        d, i, p = partition_visuals([])
        assert d == [] and i == [] and p == []

    def test_none_input(self):
        d, i, p = partition_visuals(None)
        assert d == [] and i == [] and p == []

    def test_mixed_visuals(self):
        visuals = [
            "Add a diagram",
            "logo.png",
            {"type": "image", "path": "chart.jpg"},
            {"type": "placeholder", "prompt": "team photo"},
        ]
        descs, imgs, phs = partition_visuals(visuals)
        assert len(descs) == 1
        assert descs[0]["text"] == "Add a diagram"
        assert len(imgs) == 2  # "logo.png" + dict image
        assert len(phs) == 1
        assert phs[0]["prompt"] == "team photo"

    def test_all_descriptions(self):
        visuals = ["Idea A", "Idea B"]
        d, i, p = partition_visuals(visuals)
        assert len(d) == 2 and len(i) == 0 and len(p) == 0


# ── get_position ─────────────────────────────────────────────────────


class TestGetPosition:
    def test_default_position(self):
        pos = get_position({"position": "right"})
        assert pos == POSITION_PRESETS["right"]

    def test_center(self):
        pos = get_position({"position": "center"})
        assert pos == POSITION_PRESETS["center"]

    def test_missing_position_uses_default(self):
        pos = get_position({})
        assert pos == POSITION_PRESETS[DEFAULT_POSITION]

    def test_invalid_position_uses_default(self):
        pos = get_position({"position": "top-left"})
        assert pos == POSITION_PRESETS[DEFAULT_POSITION]


# ── resolve_image / _load_local_image ────────────────────────────────


class TestResolveImage:
    def test_non_image_kind_returns_none(self):
        result = resolve_image({"kind": "description", "text": "hi"}, Path("/tmp"))
        assert result is None

    def test_load_local_image_success(self, tmp_path):
        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)  # minimal PNG header

        result = _load_local_image("test.png", tmp_path)
        assert result is not None
        data, ext = result
        assert ext == ".png"
        assert data.startswith(b"\x89PNG")

    def test_load_local_image_path_traversal_blocked(self, tmp_path):
        """Paths that escape base_dir must be rejected."""
        evil = tmp_path / "sub"
        evil.mkdir()
        target = tmp_path / "secret.png"
        target.write_bytes(b"\x89PNG" + b"\x00" * 100)

        result = _load_local_image("../secret.png", evil)
        assert result is None

    def test_load_local_image_not_found(self, tmp_path):
        result = _load_local_image("missing.png", tmp_path)
        assert result is None

    def test_load_local_image_unsupported_ext(self, tmp_path):
        txt = tmp_path / "file.txt"
        txt.write_bytes(b"not an image")
        result = _load_local_image("file.txt", tmp_path)
        assert result is None

    def test_load_local_image_too_large(self, tmp_path):
        big = tmp_path / "huge.png"
        big.write_bytes(b"\x00" * (MAX_IMAGE_SIZE + 1))
        result = _load_local_image("huge.png", tmp_path)
        assert result is None

    def test_resolve_image_with_path(self, tmp_path):
        img = tmp_path / "icon.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)
        visual = {"kind": "image", "path": "icon.jpg"}
        result = resolve_image(visual, tmp_path)
        assert result is not None
        data, ext = result
        assert ext == ".jpg"

    def test_resolve_image_no_path_no_url(self):
        result = resolve_image({"kind": "image"}, Path("/tmp"))
        assert result is None


# ── _detect_image_ext ────────────────────────────────────────────────


class TestDetectImageExt:
    def test_from_url_extension(self):
        assert _detect_image_ext("https://example.com/photo.jpg", "") == ".jpg"

    def test_from_content_type(self):
        assert _detect_image_ext("https://example.com/img", "image/png") == ".png"

    def test_fallback_to_png(self):
        assert _detect_image_ext("https://example.com/img", "application/octet-stream") == ".png"

    def test_content_type_with_charset(self):
        assert _detect_image_ext("https://example.com/x", "image/jpeg; charset=utf-8") == ".jpg"


# ── Schema integration ───────────────────────────────────────────────


class TestVisualObjectSchema:
    """Verify that visual objects validate against deck-schema.json."""

    @pytest.fixture
    def schema(self):
        import json
        schema_path = Path(__file__).resolve().parent.parent / "deck-schema.json"
        return json.loads(schema_path.read_text(encoding="utf-8"))

    @pytest.fixture
    def visual_validator(self, schema):
        from jsonschema import Draft202012Validator
        visual_items_schema = schema["$defs"]["slide"]["properties"]["visuals"]["items"]
        # Build a self-contained schema by inlining the $defs
        full = dict(visual_items_schema)
        full["$defs"] = schema.get("$defs", {})
        return Draft202012Validator(full)

    def test_visual_object_def_exists(self, schema):
        assert "visualObject" in schema.get("$defs", {})

    def test_string_visuals_still_valid(self, visual_validator):
        visual_validator.validate("Add a diagram")

    def test_image_object_valid(self, visual_validator):
        visual_validator.validate({"type": "image", "path": "logo.png", "position": "right"})

    def test_placeholder_object_valid(self, visual_validator):
        visual_validator.validate({"type": "placeholder", "prompt": "A workflow", "position": "center"})
