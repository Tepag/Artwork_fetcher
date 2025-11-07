"""
YouTube Music metadata utilities.

This module wraps `ytmusicapi` to provide a lightweight interface for
retrieving song metadata from YouTube Music. All functionality is optional
and gracefully degrades when the dependency is not installed.
"""

from typing import Any, Dict, List, Optional


try:
    from ytmusicapi import YTMusic  # type: ignore
    YTMUSIC_AVAILABLE = True
except ImportError:
    YTMUSIC_AVAILABLE = False
    YTMusic = None  # type: ignore
    print("Warning: ytmusicapi not installed. Install it with: pip install ytmusicapi")


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

    search_results = client.search(query, filter="videos", limit=limit)

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

        normalised_results.append(
            {
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": artists,
                "album": album_name,
                "duration": item.get("duration"),
                "category": item.get("category"),
                "thumbnails": item.get("thumbnails", []),
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


