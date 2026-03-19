from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from python_backend.skill_api import handle_skill_request

PORT = int(os.getenv("PORT", "3010"))


class SkillRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "auto-ppt-python-skill-server"})
            return
        self._send_json(
            404,
            {
                "ok": False,
                "error": "Not found",
                "routes": {"health": "GET /health", "skill": "POST /skill"},
            },
        )

    def do_POST(self) -> None:
        if self.path != "/skill":
            self._send_json(404, {"ok": False, "error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1024 * 1024:
                raise RuntimeError("Request body too large.")
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise RuntimeError("Request body must be a JSON object.")
            payload["_baseDir"] = str(Path.cwd())
            result = handle_skill_request(payload, None)
            self._send_json(200, result)
        except Exception as error:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(error)})


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), SkillRequestHandler)
    print(f"Python skill server listening on http://127.0.0.1:{PORT}")
    print(f"Health: http://127.0.0.1:{PORT}/health")
    print(f"Skill endpoint: POST http://127.0.0.1:{PORT}/skill")
    server.serve_forever()


if __name__ == "__main__":
    main()
