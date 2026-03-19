"""Tests for the MCP server tools (create_deck, revise_deck)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp_server import create_deck, revise_deck


class TestMCPCreateDeck:
    def test_create_mock_returns_valid_json(self):
        result = create_deck(prompt="Test presentation about AI", mock=True)
        data = json.loads(result)
        assert data["ok"] is True
        assert data["action"] == "create"
        assert isinstance(data["slideCount"], int)
        assert data["slideCount"] > 0

    def test_create_mock_produces_pptx(self):
        result = create_deck(prompt="Quick test deck", mock=True)
        data = json.loads(result)
        assert Path(data["pptxPath"]).exists()
        assert Path(data["deckJsonPath"]).exists()

    def test_create_mock_with_output_dir(self, tmp_path):
        result = create_deck(
            prompt="Test with custom output",
            mock=True,
            output_dir=str(tmp_path),
        )
        data = json.loads(result)
        assert data["ok"] is True
        assert str(tmp_path) in data["pptxPath"]
        assert Path(data["pptxPath"]).exists()

    def test_create_mock_with_source(self):
        src = str(ROOT / "sample-source-brief.md")
        result = create_deck(
            prompt="Deck based on brief",
            mock=True,
            sources=[src],
        )
        data = json.loads(result)
        assert data["ok"] is True
        assert len(data["sourcesUsed"]) == 1

    def test_create_returns_assumptions(self):
        result = create_deck(prompt="Test deck", mock=True)
        data = json.loads(result)
        assert isinstance(data["assumptions"], list)
        assert len(data["assumptions"]) > 0


class TestMCPReviseDeck:
    def _create_base_deck(self) -> str:
        """Create a base deck and return the JSON path."""
        result = create_deck(prompt="Base deck for revision", mock=True)
        return json.loads(result)["deckJsonPath"]

    def test_revise_mock_returns_valid_json(self):
        deck_path = self._create_base_deck()
        result = revise_deck(
            prompt="Make it more concise",
            deck_path=deck_path,
            mock=True,
        )
        data = json.loads(result)
        assert data["ok"] is True
        assert data["action"] == "revise"

    def test_revise_compress(self):
        deck_path = self._create_base_deck()
        result = revise_deck(
            prompt="Compress to 5 slides",
            deck_path=deck_path,
            mock=True,
        )
        data = json.loads(result)
        assert data["slideCount"] <= 5

    def test_revise_produces_pptx(self):
        deck_path = self._create_base_deck()
        result = revise_deck(
            prompt="Add more detail",
            deck_path=deck_path,
            mock=True,
        )
        data = json.loads(result)
        assert Path(data["pptxPath"]).exists()

    def test_revise_with_output_dir(self, tmp_path):
        deck_path = self._create_base_deck()
        result = revise_deck(
            prompt="Improve structure",
            deck_path=deck_path,
            mock=True,
            output_dir=str(tmp_path),
        )
        data = json.loads(result)
        assert str(tmp_path) in data["pptxPath"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
