from __future__ import annotations

import importlib
import json
import mimetypes
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, TypedDict, cast
from urllib.parse import urlparse
from urllib.request import Request, urlopen

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
}
HTML_EXTENSIONS = {".html", ".htm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}


class SourceLoadResult(TypedDict):
    loaded_sources: List[Dict[str, Any]]
    context_texts: List[str]


class _HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._parts)


def _fail(message: str) -> None:
    raise RuntimeError(message)


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def _resolve_local_path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    _fail(f"Unable to decode text file: {path}")
    raise RuntimeError(f"Unable to decode text file: {path}")


def _html_to_text(text: str) -> str:
    parser = _HtmlTextExtractor()
    parser.feed(text)
    extracted = parser.get_text()
    return extracted if extracted.strip() else text


def _read_pdf(path: Path) -> str:
    PdfReader = importlib.import_module("pypdf").PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        content = page.extract_text() or ""
        if content.strip():
            pages.append(content.strip())
    return "\n\n".join(pages)


def _read_docx(path: Path) -> str:
    Document = importlib.import_module("docx").Document

    document = Document(str(path))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def _fetch_url(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "auto-ppt-prototype/0.3.0",
            "Accept": "text/html,application/json,text/plain;q=0.9,*/*;q=0.5",
        },
    )
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")
        content_type = response.headers.get_content_type()
    if content_type == "text/html":
        return _html_to_text(body)
    return body


def _normalize_source(source: Any, base_dir: Path) -> Dict[str, Any]:
    if isinstance(source, str):
        source = {"path": source}
    if not isinstance(source, dict):
        _fail("Each source must be a string or object.")

    location = source.get("url") or source.get("path") or source.get("location")
    if not location or not isinstance(location, str):
        _fail("Each source must include a path, url, or location.")
    location_str = cast(str, location)

    is_url = _is_url(location_str)
    resolved_location = location_str if is_url else str(_resolve_local_path(location_str, base_dir))
    label = str(source.get("label") or Path(location_str).name or location_str)

    return {
        "id": source.get("id") or re.sub(r"[^a-zA-Z0-9]+", "-", label.lower()).strip("-") or "source",
        "label": label,
        "type": source.get("type") or ("url" if is_url else "file"),
        "location": resolved_location,
        "trustLevel": source.get("trustLevel") or "user-provided",
        "priority": source.get("priority") or "normal",
        "notes": source.get("notes") or "",
        "citation": source.get("citation") or "",
        "_is_url": is_url,
    }


def _read_source_text(spec: Dict[str, Any]) -> str:
    if spec["_is_url"]:
        return _fetch_url(spec["location"])

    path = Path(spec["location"])
    if not path.exists():
        _fail(f"Source file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        text = _read_text_file(path)
        if suffix in {".json"}:
            try:
                parsed = json.loads(text)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                return text
        return text
    if suffix in HTML_EXTENSIONS:
        return _html_to_text(_read_text_file(path))
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    if suffix in IMAGE_EXTENSIONS:
        return f"Image asset reference only: {path.name}"

    guessed_type, _ = mimetypes.guess_type(str(path))
    if guessed_type and guessed_type.startswith("text/"):
        return _read_text_file(path)

    return f"Binary or unsupported source reference: {path.name}"


def _build_context_text(spec: Dict[str, Any], source_text: str) -> str:
    excerpt = source_text.strip()
    if len(excerpt) > 5000:
        excerpt = excerpt[:5000].rstrip() + "\n...[truncated]"
    metadata = [
        f"Label: {spec['label']}",
        f"Type: {spec['type']}",
        f"Location: {spec['location']}",
        f"Trust level: {spec['trustLevel']}",
        f"Priority: {spec['priority']}",
    ]
    if spec["notes"]:
        metadata.append(f"Notes: {spec['notes']}")
    if spec["citation"]:
        metadata.append(f"Citation: {spec['citation']}")
    return "\n".join(metadata) + "\n\nContent:\n" + excerpt


def load_source_contexts(sources: Iterable[Any], base_dir: str | Path) -> SourceLoadResult:
    base_path = Path(base_dir)
    loaded_sources: List[Dict[str, Any]] = []
    context_texts: List[str] = []

    for source in sources:
        spec = _normalize_source(source, base_path)
        source_text = _read_source_text(spec)
        context_texts.append(_build_context_text(spec, source_text))
        loaded_sources.append(
            {
                key: value
                for key, value in spec.items()
                if not key.startswith("_")
            }
        )

    return {
        "loaded_sources": loaded_sources,
        "context_texts": context_texts,
    }
