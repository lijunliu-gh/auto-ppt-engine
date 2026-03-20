from __future__ import annotations

from pathlib import Path

import pytest

import auto_ppt_cli


class TestParseArgs:
    def test_init_does_not_require_prompt(self):
        args = auto_ppt_cli.parse_args(["init", "--provider", "openai", "--api-key", "sk-test"])
        assert args.command == "init"

    def test_generate_requires_prompt(self):
        with pytest.raises(SystemExit):
            auto_ppt_cli.parse_args(["generate"])

    def test_generate_accepts_prompt(self):
        args = auto_ppt_cli.parse_args(["generate", "--prompt", "Create a deck"])
        assert args.command == "generate"
        assert args.prompt == "Create a deck"

    def test_prompt_file_populates_prompt(self, tmp_path):
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("Build a market update deck", encoding="utf-8")
        args = auto_ppt_cli.parse_args(["generate", "--prompt-file", str(prompt_file)])
        assert args.prompt == "Build a market update deck"


class TestBuildRequest:
    def test_generate_request_uses_output_dir(self):
        args = auto_ppt_cli.parse_args(
            [
                "generate",
                "--prompt",
                "Create a deck",
                "--source",
                "brief.md",
                "--output-dir",
                "custom-output",
            ]
        )
        request = auto_ppt_cli.build_request(args)
        assert request["action"] == "create"
        assert request["sources"] == [{"path": "brief.md"}]
        assert request["outputJson"].endswith("custom-output/py-generated-deck.json")
        assert request["outputPptx"].endswith("custom-output/py-generated-deck.pptx")

    def test_revise_request_sets_deck_path(self):
        args = auto_ppt_cli.parse_args(
            ["revise", "--prompt", "Tighten the flow", "--deck", "output/base.json"]
        )
        request = auto_ppt_cli.build_request(args)
        assert request["action"] == "revise"
        assert request["deckPath"] == "output/base.json"
        assert request["outputJson"].endswith("output/py-revised-deck.json")


class TestMain:
    def test_load_local_env_sets_defaults(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_MODEL=gpt-4.1-mini\nAUTO_PPT_OUTPUT_DIR=custom-output\n", encoding="utf-8")
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("AUTO_PPT_OUTPUT_DIR", raising=False)

        auto_ppt_cli.load_local_env(env_file)

        assert auto_ppt_cli.os.environ["OPENAI_MODEL"] == "gpt-4.1-mini"
        assert auto_ppt_cli.os.environ["AUTO_PPT_OUTPUT_DIR"] == "custom-output"

    def test_run_init_writes_env_file_non_interactive(self, tmp_path):
        env_file = tmp_path / ".env"
        args = auto_ppt_cli.parse_args(
            [
                "init",
                "--provider",
                "openai",
                "--api-key",
                "sk-test",
                "--model",
                "gpt-4.1-mini",
                "--output-dir",
                "build-output",
                "--env-file",
                str(env_file),
                "--non-interactive",
            ]
        )

        exit_code = auto_ppt_cli.run_init(args)
        contents = env_file.read_text(encoding="utf-8")

        assert exit_code == 0
        assert "OPENAI_API_KEY=sk-test" in contents
        assert "OPENAI_MODEL=gpt-4.1-mini" in contents
        assert "AUTO_PPT_OUTPUT_DIR=build-output" in contents

    def test_output_dir_env_is_used_by_generate_defaults(self, monkeypatch):
        monkeypatch.setenv("AUTO_PPT_OUTPUT_DIR", "configured-output")
        args = auto_ppt_cli.parse_args(["generate", "--prompt", "Create a deck"])
        request = auto_ppt_cli.build_request(args)
        assert request["outputJson"].endswith("configured-output/py-generated-deck.json")

    def test_main_calls_handle_skill_request(self, monkeypatch, capsys, tmp_path):
        captured = {}

        def fake_handle_skill_request(request, response_path=None):
            captured["request"] = request
            return {
                "action": "create",
                "deckJsonPath": str(tmp_path / "deck.json"),
                "pptxPath": str(tmp_path / "deck.pptx"),
                "renderer": "pptxgenjs",
                "slideCount": 6,
                "sourcesUsed": [],
            }

        monkeypatch.setattr(auto_ppt_cli, "handle_skill_request", fake_handle_skill_request)
        exit_code = auto_ppt_cli.main(["generate", "--prompt", "Create a deck"])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert captured["request"]["action"] == "create"
        assert "Generated deck JSON" in output

    def test_main_returns_error_code_on_exception(self, monkeypatch, capsys):
        def raise_error(request, response_path=None):
            raise RuntimeError("boom")

        monkeypatch.setattr(auto_ppt_cli, "handle_skill_request", raise_error)
        exit_code = auto_ppt_cli.main(["generate", "--prompt", "Create a deck"])
        error = capsys.readouterr().err
        assert exit_code == 1
        assert "auto-ppt: error: boom" in error

    def test_missing_api_key_error_is_actionable(self, monkeypatch, capsys):
        def raise_error(request, response_path=None):
            raise RuntimeError("OPENAI_API_KEY is not set. Use mock mode for offline testing or configure the API key.")

        monkeypatch.setattr(auto_ppt_cli, "handle_skill_request", raise_error)
        exit_code = auto_ppt_cli.main(["generate", "--prompt", "Create a deck"])
        error = capsys.readouterr().err

        assert exit_code == 1
        assert "run ./auto-ppt init" in error
        assert "--mock" in error

    def test_missing_deck_path_is_actionable(self, capsys):
        exit_code = auto_ppt_cli.main(["revise", "--prompt", "Tighten the flow", "--deck", "missing.json"])
        error = capsys.readouterr().err

        assert exit_code == 1
        assert "Deck file not found" in error
        assert "Run ./auto-ppt generate first" in error

    def test_missing_source_path_is_actionable(self, capsys):
        exit_code = auto_ppt_cli.main(["generate", "--prompt", "Create a deck", "--source", "missing-source.md"])
        error = capsys.readouterr().err

        assert exit_code == 1
        assert "Source file not found" in error
        assert "Check --source" in error

    def test_renderer_error_is_actionable(self, monkeypatch, capsys):
        def raise_error(request, response_path=None):
            raise RuntimeError("Node renderer failed: command not found: node")

        monkeypatch.setattr(auto_ppt_cli, "handle_skill_request", raise_error)
        exit_code = auto_ppt_cli.main(["generate", "--prompt", "Create a deck"])
        error = capsys.readouterr().err

        assert exit_code == 1
        assert "run npm install" in error.lower()
        assert "Node.js 18+" in error