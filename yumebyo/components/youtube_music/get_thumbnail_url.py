"""Utility script to fetch the highest quality YouTube Music cover image.

Usage examples:

    python test.py --query "Daft Punk Harder Better Faster" --output cover.jpg
    python test.py --video-id dQw4w9WgXcQ --downscale-480

The script uses `ytmusicapi` to locate the requested song/video and downloads
the highest resolution thumbnail that the API exposes.
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
import requests
from ytmusicapi import YTMusic
try:
    from PIL import Image  # type: ignore

    PIL_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency warning only
    Image = None  # type: ignore
    PIL_AVAILABLE = False
    print("Warning: Pillow not installed. Install it with: pip install pillow")



def get_thumbnail_url(
artist: str, 
title: str,
filter: str = "songs"
) -> str:
    """
    Get the thumbnail URL for a YouTube Music song/video.
    
    Args:
        artist: The artist name
        title: The song title
        filter: The filter to use to search for the songs/videos
    
    Returns:
        The thumbnail URL
    """

    ytmusic = YTMusic()
    query = f"{artist} {title}"
    resolved_video_id = _get_video_id(ytmusic, query=query, filter=filter)

    song_payload = ytmusic.get_song(resolved_video_id)
    thumbnail_url = _fetch_highest_quality_thumbnail_url(_iter_thumbnails(song_payload))

    if not thumbnail_url:
        raise LookupError(
            f"Failed to locate any thumbnails for video ID: {resolved_video_id}"
        )

    return thumbnail_url

    

def _iter_thumbnails(song_payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Yield all thumbnail dictionaries available for the supplied payload."""

    if not isinstance(song_payload, dict):
        return

    video_details = song_payload.get("videoDetails")
    if isinstance(video_details, dict):
        thumbnail_block = video_details.get("thumbnail")
        if isinstance(thumbnail_block, dict):
            thumbnails = thumbnail_block.get("thumbnails")
            if isinstance(thumbnails, list):
                for thumb in thumbnails:
                    if isinstance(thumb, dict):
                        yield thumb

    microformat = song_payload.get("microformat")
    if isinstance(microformat, dict):
        renderer = microformat.get("microformatDataRenderer")
        if isinstance(renderer, dict):
            thumbnail_block = renderer.get("thumbnail")
            if isinstance(thumbnail_block, dict):
                thumbnails = thumbnail_block.get("thumbnails")
                if isinstance(thumbnails, list):
                    for thumb in thumbnails:
                        if isinstance(thumb, dict):
                            yield thumb


def _fetch_highest_quality_thumbnail_url(thumbnails: Iterable[Dict[str, Any]]) -> Optional[str]:
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


def _get_video_id(
ytmusic: YTMusic, 
query: Optional[str], 
filter: str = "songs"
) -> str:
    """Locate a YouTube Music video ID from either a direct ID or a search query."""

    if not query:
        raise ValueError("Either --query or --video-id must be provided.")

    search_results = ytmusic.search(query, filter=filter, limit=1)
    if not search_results:
        search_results = ytmusic.search(query, limit=1)

    if not search_results:
        raise LookupError(f"No results found on YouTube Music for query: {query!r}")

    result = search_results[0]
    video_id = result.get("videoId")
    if not video_id:
        raise LookupError(
            f"The top search result for query {query!r} did not contain a videoId."
        )

    return video_id



