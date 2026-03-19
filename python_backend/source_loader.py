from __future__ import annotations

import importlib
import ipaddress
import json
import logging
import mimetypes
import os
import re
import socket
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, TypedDict, cast
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

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

logger = logging.getLogger("auto-ppt")


class SourceLoadResult(TypedDict):
    loaded_sources: List[Dict[str, Any]]
    context_texts: List[str]
    truncated_sources: List[str]


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
    resolved = (base_dir / path).resolve() if not path.is_absolute() else path.resolve()
    # Prevent path traversal: resolved path must be inside base_dir
    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError:
        _fail(f"Path traversal blocked: {value!r} resolves outside base directory")
    return resolved


def _read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    _fail(f"Unable to decode text file: {path}")
    return ""  # unreachable, satisfies type checker


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


def _validate_url_target(url: str) -> None:
    """Block SSRF: reject private/loopback IPs and non-http(s) schemes."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        _fail(f"URL scheme not allowed: {parsed.scheme!r}")
    hostname = parsed.hostname
    if not hostname:
        _fail(f"Invalid URL: {url!r}")
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        _fail(f"Cannot resolve hostname: {hostname!r}")
    for _family, _type, _proto, _canonname, sockaddr in addr_info:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            _fail(f"URL target blocked (private/reserved IP): {hostname!r} -> {ip}")


def _check_file_size(path: Path) -> None:
    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        _fail(f"File too large ({size / 1024 / 1024:.1f} MB > 50 MB limit): {path}")


def _fetch_url(url: str) -> str:
    _validate_url_target(url)
    request = Request(
        url,
        headers={
            "User-Agent": "auto-ppt-prototype/0.5.0",
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
    _check_file_size(path)

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


def _build_context_text(spec: Dict[str, Any], source_text: str) -> tuple[str, bool]:
    """Return (context_text, was_truncated)."""
    excerpt = source_text.strip()
    truncated = False
    if len(excerpt) > 5000:
        excerpt = excerpt[:5000].rstrip() + "\n...[truncated]"
        truncated = True
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
    return "\n".join(metadata) + "\n\nContent:\n" + excerpt, truncated


def load_source_contexts(sources: Iterable[Any], base_dir: str | Path) -> SourceLoadResult:
    base_path = Path(base_dir)
    loaded_sources: List[Dict[str, Any]] = []
    context_texts: List[str] = []
    truncated_sources: List[str] = []

    for source in sources:
        spec = _normalize_source(source, base_path)
        logger.info("Loading source: %s (%s)", spec["label"], spec["location"])
        source_text = _read_source_text(spec)
        context_text, was_truncated = _build_context_text(spec, source_text)
        if was_truncated:
            truncated_sources.append(spec["label"])
            logger.warning("Source truncated to 5000 chars: %s", spec["label"])
        context_texts.append(context_text)
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
        "truncated_sources": truncated_sources,
    }
