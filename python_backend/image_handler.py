"""Image handler: resolve, validate, and load images for slide rendering.

Security: reuses path traversal and SSRF protections from source_loader.
"""

from __future__ import annotations

import io
import logging
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("auto-ppt")

# Supported image formats (by extension)
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".svg", ".webp"}

# Maximum image file size: 10 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# Position presets: (left, top, width, height) in inches
POSITION_PRESETS = {
    "right": (8.95, 1.65, 3.35, 4.0),
    "left": (0.6, 1.65, 4.5, 4.0),
    "center": (3.5, 1.8, 6.33, 4.5),
    "full": (0.5, 1.4, 12.33, 5.8),
}
# Default position when not specified
DEFAULT_POSITION = "right"


def classify_visual(item: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Classify a visual item and normalize to a standard dict format.

    Returns a dict with:
        - "kind": "description" | "image" | "placeholder"
        - Other fields depending on kind.
    """
    if isinstance(item, str):
        # Check if the string looks like a file path to an image
        if _looks_like_image_path(item):
            return {"kind": "image", "path": item, "position": DEFAULT_POSITION}
        return {"kind": "description", "text": item}

    if isinstance(item, dict):
        vtype = item.get("type", "")
        if vtype == "image":
            return {
                "kind": "image",
                "path": item.get("path"),
                "url": item.get("url"),
                "alt": item.get("alt", ""),
                "position": item.get("position", DEFAULT_POSITION),
            }
        elif vtype == "placeholder":
            return {
                "kind": "placeholder",
                "prompt": item.get("prompt", ""),
                "alt": item.get("alt", ""),
                "position": item.get("position", DEFAULT_POSITION),
            }

    # Fallback: treat as description
    return {"kind": "description", "text": str(item)}


def _looks_like_image_path(s: str) -> bool:
    """Check if a string looks like a local image file path."""
    s_lower = s.strip().lower()
    return any(s_lower.endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS)


def resolve_image(
    visual: Dict[str, Any],
    base_dir: Path,
) -> Optional[Tuple[bytes, str]]:
    """Resolve an image visual to bytes + format suffix.

    Args:
        visual: Classified visual dict with kind="image".
        base_dir: Base directory for resolving relative paths.

    Returns:
        (image_bytes, extension) or None if resolution fails.
    """
    if visual.get("kind") != "image":
        return None

    # Try local path first
    path_str = visual.get("path")
    if path_str:
        return _load_local_image(path_str, base_dir)

    # Try URL
    url_str = visual.get("url")
    if url_str:
        return _load_url_image(url_str)

    return None


def _load_local_image(path_str: str, base_dir: Path) -> Optional[Tuple[bytes, str]]:
    """Load an image from a local file path with security checks."""
    try:
        path = Path(path_str)
        if not path.is_absolute():
            path = (base_dir / path).resolve()
        else:
            path = path.resolve()

        # Security: ensure path stays within base_dir
        base_resolved = base_dir.resolve()
        if not str(path).startswith(str(base_resolved)):
            logger.warning("Image path traversal blocked: %s", path_str)
            return None

        if not path.exists():
            logger.warning("Image not found: %s", path)
            return None

        ext = path.suffix.lower()
        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            logger.warning("Unsupported image format: %s", ext)
            return None

        size = path.stat().st_size
        if size > MAX_IMAGE_SIZE:
            logger.warning("Image too large (%d bytes): %s", size, path)
            return None

        data = path.read_bytes()
        return (data, ext)

    except Exception as e:
        logger.warning("Failed to load image %s: %s", path_str, e)
        return None


def _load_url_image(url_str: str) -> Optional[Tuple[bytes, str]]:
    """Load an image from a URL with SSRF and size protections."""
    try:
        # Reuse SSRF protection from source_loader
        from .source_loader import _validate_url_target
        _validate_url_target(url_str)
    except Exception as e:
        logger.warning("Image URL blocked by SSRF protection: %s — %s", url_str, e)
        return None

    try:
        req = urllib.request.Request(
            url_str,
            headers={
                "User-Agent": "auto-ppt-engine/0.5.0",
                "Accept": "image/*",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_length = resp.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_IMAGE_SIZE:
                logger.warning("Remote image too large: %s bytes", content_length)
                return None

            data = resp.read(MAX_IMAGE_SIZE + 1)
            if len(data) > MAX_IMAGE_SIZE:
                logger.warning("Remote image exceeded size limit during download")
                return None

            # Detect extension from URL or content-type
            ext = _detect_image_ext(url_str, resp.headers.get("Content-Type", ""))
            return (data, ext)

    except Exception as e:
        logger.warning("Failed to load image from URL %s: %s", url_str, e)
        return None


def _detect_image_ext(url: str, content_type: str) -> str:
    """Detect image extension from URL or content-type header."""
    # Try URL extension
    from urllib.parse import urlparse
    path = urlparse(url).path.lower()
    for ext in SUPPORTED_IMAGE_EXTENSIONS:
        if path.endswith(ext):
            return ext

    # Try content-type
    ct_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
    }
    ct_lower = content_type.lower().split(";")[0].strip()
    return ct_map.get(ct_lower, ".png")


def get_position(visual: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """Get the position preset for a visual item.

    Returns (left, top, width, height) in inches.
    """
    pos = visual.get("position", DEFAULT_POSITION)
    return POSITION_PRESETS.get(pos, POSITION_PRESETS[DEFAULT_POSITION])


def partition_visuals(
    visuals: List[Any],
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Partition a visuals array into descriptions, images, and placeholders.

    Returns:
        (descriptions, images, placeholders) — each a list of classified dicts.
    """
    descriptions: List[Dict] = []
    images: List[Dict] = []
    placeholders: List[Dict] = []

    for item in visuals or []:
        classified = classify_visual(item)
        kind = classified["kind"]
        if kind == "description":
            descriptions.append(classified)
        elif kind == "image":
            images.append(classified)
        elif kind == "placeholder":
            placeholders.append(classified)

    return descriptions, images, placeholders
