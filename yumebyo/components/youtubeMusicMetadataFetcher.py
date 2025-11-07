"""
YouTube Music metadata utilities.

This module wraps `ytmusicapi` to provide a lightweight interface for
retrieving song metadata from YouTube Music. All functionality is optional
and gracefully degrades when the dependency is not installed.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

import requests


try:
    from ytmusicapi import YTMusic  # type: ignore
    YTMUSIC_AVAILABLE = True
except ImportError:
    YTMUSIC_AVAILABLE = False
    YTMusic = None  # type: ignore
    print("Warning: ytmusicapi not installed. Install it with: pip install ytmusicapi")


try:
    from PIL import Image  # type: ignore

    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency warning only
    Image = None  # type: ignore
    PIL_AVAILABLE = False
    print("Warning: Pillow not installed. Install it with: pip install pillow")


_client: Optional["YTMusic"] = None


def init_youtube_music_client(auth_headers_path: Optional[str] = None) -> "YTMusic":
    """Initialise a singleton YTMusic client instance."""

    if not YTMUSIC_AVAILABLE:
        raise ImportError(
            "ytmusicapi is required. Install it with: pip install ytmusicapi"
        )

    global _client

    if _client is not None:
        return _client

    if auth_headers_path:
        _client = YTMusic(auth_headers_path)
    else:
        _client = YTMusic()

    return _client


def get_youtube_music_client() -> "YTMusic":
    """Return the existing YTMusic client, initialising it if necessary."""

    if _client is None:
        return init_youtube_music_client()
    return _client


def _select_highest_quality_thumbnail_url(
    thumbnails: List[Dict[str, Any]]
) -> Optional[str]:
    """Return the URL for the thumbnail with the largest pixel area."""

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


def _download_thumbnail(url: str) -> bytes:
    """Download raw image bytes for a thumbnail URL."""

    if not url:
        raise ValueError("No thumbnail URL provided for download.")

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.content


def _crop_image_bytes_to_square(image_bytes: bytes) -> bytes:
    """Return the supplied image bytes centre-cropped to a square."""

    if not PIL_AVAILABLE or Image is None:
        return image_bytes

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        width, height = img.size

        if width == height:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=95)
            return buffer.getvalue()

        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        right = left + side
        bottom = top + side
        cropped = img.crop((left, top, right, bottom))

        buffer = io.BytesIO()
        cropped.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()


def _maybe_downscale_to_480(image_bytes: bytes, downscale: bool) -> bytes:
    """Downscale the supplied (square) image bytes to 480x480 when requested."""

    if not downscale:
        return image_bytes

    if not PIL_AVAILABLE or Image is None:
        raise ImportError(
            "Pillow is required to downscale the downloaded artwork. Install it with: pip install pillow"
        )

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        if img.size == (480, 480):
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=95)
            return buffer.getvalue()

        resized = img.resize((480, 480), Image.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()


def download_best_thumbnail_image(
    metadata: Dict[str, Any],
    downscale_to_480: bool = False,
) -> Optional[bytes]:
    """Download and process the best thumbnail for the supplied metadata."""

    if not isinstance(metadata, dict):
        return None

    best_url = metadata.get("bestThumbnailUrl")
    thumbnails = metadata.get("thumbnails")
    if not best_url and isinstance(thumbnails, list):
        best_url = _select_highest_quality_thumbnail_url(thumbnails)

    if not best_url:
        return None

    print(f"Best thumbnail URL: {best_url}")

    image_bytes = _download_thumbnail(best_url)
    image_bytes = _crop_image_bytes_to_square(image_bytes)
    # image_bytes = _maybe_downscale_to_480(image_bytes, downscale_to_480)

    return image_bytes


def search_youtube_music_metadata(
    artist: Optional[str] = None,
    title: Optional[str] = None,
    limit: int = 5,
    ensure_client: bool = True
) -> List[Dict[str, Any]]:
    """Search YouTube Music for tracks matching the provided metadata."""

    if not YTMUSIC_AVAILABLE:
        raise ImportError(
            "ytmusicapi is required. Install it with: pip install ytmusicapi"
        )

    if artist is None and title is None:
        raise ValueError("At least one of artist or title must be provided.")

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    query_parts: List[str] = []
    if artist:
        query_parts.append(artist)
    if title:
        query_parts.append(title)

    query = " ".join(query_parts)

    client = get_youtube_music_client() if ensure_client else None
    if client is None:
        client = init_youtube_music_client()

    # INSERT_YOUR_CODE
    # Choose the search filter based on whether artist appears to be "nightcore"
    search_filter = "songs"

    if artist is not None and "nightcore" in artist.lower() or title is not None and "nightcore" in title.lower():
        search_filter = "videos"
        print(f"search in videos")
    search_results = client.search(query, filter=search_filter, limit=limit)

    normalised_results: List[Dict[str, Any]] = []
    for item in search_results:
        if not isinstance(item, dict):
            continue

        artists = []
        for artist_entry in item.get("artists", []):
            if isinstance(artist_entry, dict) and artist_entry.get("name"):
                artists.append(artist_entry["name"])

        album_name: Optional[str] = None
        album_entry = item.get("album")
        if isinstance(album_entry, dict):
            album_name = album_entry.get("name")

        thumbnails = item.get("thumbnails", [])
        best_thumbnail_url = _select_highest_quality_thumbnail_url(thumbnails)
        sorted_thumbnails = sorted(
            [thumb for thumb in thumbnails if isinstance(thumb, dict)],
            key=lambda thumb: int(thumb.get("width", 0) or 0)
            * int(thumb.get("height", 0) or 0),
            reverse=True,
        )

        normalised_results.append(
            {
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": artists,
                "album": album_name,
                "duration": item.get("duration"),
                "category": item.get("category"),
                "thumbnails": sorted_thumbnails,
                "bestThumbnailUrl": best_thumbnail_url,
                "isExplicit": item.get("isExplicit", False),
            }
        )

    return normalised_results


def fetch_primary_youtube_music_metadata(
    artist: Optional[str] = None,
    title: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Convenience helper to retrieve the first matching search result."""

    results = search_youtube_music_metadata(artist=artist, title=title, limit=1)
    if results:
        return results[0]
    return None


