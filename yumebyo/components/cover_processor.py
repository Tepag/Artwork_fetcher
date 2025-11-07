"""Utilities for processing cover images sourced from YouTube Music metadata."""

from __future__ import annotations

import io
from typing import Any, Dict, Iterable, Optional, Tuple

import requests

from .youtubeMusicMetadataFetcher import (
    fetch_primary_youtube_music_metadata,
)


try:
    from PIL import Image  # type: ignore

    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency warning only
    Image = None  # type: ignore
    PIL_AVAILABLE = False
    print("Warning: Pillow not installed. Install it with: pip install pillow")


DEFAULT_BACKGROUND_COLOR: Tuple[int, int, int] = (0, 0, 0)


def _select_best_thumbnail(thumbnails: Iterable[Dict[str, Any]]) -> Optional[str]:
    """Return the URL for the highest-area thumbnail."""

    best_url: Optional[str] = None
    best_area = -1

    for thumb in thumbnails:
        if not isinstance(thumb, dict):
            continue
        url = thumb.get("url")
        width = int(thumb.get("width", 0) or 0)
        height = int(thumb.get("height", 0) or 0)
        if not url or width <= 0 or height <= 0:
            continue
        area = width * height
        if area > best_area:
            best_area = area
            best_url = url

    return best_url


def _download_image_data(url: str, timeout: int = 10) -> Optional[bytes]:
    """Download binary image data from a URL."""

    if not url:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network failure reporting only
        print(f"Error downloading thumbnail from {url}: {exc}")
        return None

    content_type = response.headers.get("Content-Type", "").lower()
    if "image" not in content_type:
        print(
            f"Warning: URL {url} returned unexpected content type: {content_type or 'unknown'}"
        )
        return None

    return response.content


def _crop_center_square(image: "Image.Image") -> "Image.Image":
    """Crop the image to a centred square using the shortest dimension."""

    width, height = image.size
    if width == height:
        return image

    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    right = left + side
    bottom = top + side
    return image.crop((left, top, right, bottom))


def download_and_process_youtube_cover(
    metadata: Dict[str, Any],
    force_480: bool = False,
    background_color: Tuple[int, int, int] = DEFAULT_BACKGROUND_COLOR,
) -> Optional[bytes]:
    """
    Download the best thumbnail for the supplied metadata and process it.

    Args:
        metadata: A metadata dictionary as returned by
            `youtubeMusicMetadataFetcher`.
        force_480: When True, ensure the final artwork is exactly 480x480.
            When False, images with any dimension below 480px are cropped to a
            square and then upscaled to 480px, while larger images are cropped
            to a centred square but keep their native resolution.
        background_color: Retained for backwards compatibility; currently
            unused because images are cropped instead of padded.

    Returns:
        Processed image bytes (JPEG) or None if the operation fails.
    """

    thumbnails = metadata.get("thumbnails") if isinstance(metadata, dict) else None
    if not thumbnails:
        print("No thumbnails present in metadata; skipping download.")
        return None

    thumbnail_url = _select_best_thumbnail(thumbnails)
    if not thumbnail_url:
        print("Could not determine a valid thumbnail URL from metadata.")
        return None

    image_data = _download_image_data(thumbnail_url)
    if image_data is None:
        return None

    if not PIL_AVAILABLE:
        if force_480:
            raise ImportError(
                "Pillow is required to resize the thumbnail. Install it with: pip install pillow"
            )
        return image_data

    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    image = _crop_center_square(image)

    if force_480 or image.width < 480:
        image = image.resize((480, 480), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def fetch_and_process_primary_cover(
    artist: Optional[str] = None,
    title: Optional[str] = None,
    force_480: bool = False,
    background_color: Tuple[int, int, int] = DEFAULT_BACKGROUND_COLOR,
) -> Optional[bytes]:
    """Fetch primary metadata using the YouTube component and process its cover."""

    metadata = fetch_primary_youtube_music_metadata(artist=artist, title=title)
    if not metadata:
        print("No matching YouTube Music metadata found.")
        return None

    return download_and_process_youtube_cover(
        metadata,
        force_480=force_480,
        background_color=background_color,
    )


