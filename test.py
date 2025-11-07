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


def _select_highest_quality_thumbnail(thumbnails: Iterable[Dict[str, Any]]) -> Optional[str]:
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


def _resolve_video_id(ytmusic: YTMusic, query: Optional[str], video_id: Optional[str]) -> str:
    """Locate a YouTube Music video ID from either a direct ID or a search query."""

    if video_id:
        return video_id

    if not query:
        raise ValueError("Either --query or --video-id must be provided.")

    search_results = ytmusic.search(query, filter="videos", limit=1)
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


def _download_image(url: str, output_path: Path) -> Path:
    """Download the image at *url* into *output_path* and return the path."""

    if not url:
        raise ValueError("No thumbnail URL provided for download.")

    response = requests.get(url, timeout=15)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        handle.write(response.content)

    return output_path


def _crop_image_to_square(image_path: Path) -> Path:
    """Center-crop the image at *image_path* to a square, in-place."""

    if not PIL_AVAILABLE or Image is None:
        raise ImportError(
            "Pillow is required to crop the downloaded artwork. Install it with: pip install pillow"
        )

    with Image.open(image_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        if width == height:
            img.save(image_path)
            return image_path

        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        right = left + side
        bottom = top + side
        cropped = img.crop((left, top, right, bottom))
        cropped.save(image_path)

    return image_path


def fetch_highest_quality_cover(
    query: Optional[str] = None,
    video_id: Optional[str] = None,
    output: Optional[os.PathLike[str]] = None,
    downscale_to_480: bool = False,
) -> Path:
    """Fetch and save the highest quality cover image for the specified song/video.

    When ``downscale_to_480`` is True, the cropped artwork is resized to 480x480.
    """

    ytmusic = YTMusic()
    resolved_video_id = _resolve_video_id(ytmusic, query=query, video_id=video_id)

    song_payload = ytmusic.get_song(resolved_video_id)
    thumbnail_url = _select_highest_quality_thumbnail(_iter_thumbnails(song_payload))

    if not thumbnail_url:
        raise LookupError(
            f"Failed to locate any thumbnails for video ID: {resolved_video_id}"
        )

    if output is None:
        output = Path(f"{resolved_video_id}.jpg")
    else:
        output = Path(output)

    image_path = _download_image(thumbnail_url, output)
    image_path = _crop_image_to_square(image_path)

    if downscale_to_480:
        if not PIL_AVAILABLE or Image is None:
            raise ImportError(
                "Pillow is required to downscale the downloaded artwork. Install it with: pip install pillow"
            )
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            if img.size != (480, 480):
                img = img.resize((480, 480), Image.LANCZOS)
                img.save(image_path)

    return image_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Search query to locate the song/album", default=None)
    parser.add_argument(
        "--video-id",
        help="Direct YouTube video ID to fetch artwork from",
        default=None,
    )
    parser.add_argument(
        "--output",
        help="Path where the downloaded cover should be saved (defaults to <videoId>.jpg)",
        default=None,
    )
    parser.add_argument(
        "--downscale-480",
        help="Downscale the final artwork to 480x480 after cropping",
        action="store_true",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    try:
        output_path = fetch_highest_quality_cover(
            query=args.query,
            video_id=args.video_id,
            output=args.output,
            downscale_to_480=args.downscale_480,
        )
    except Exception as exc:  # pragma: no cover - script execution feedback
        print(f"Error: {exc}")
        raise SystemExit(1)

    print(f"Downloaded artwork to: {output_path}")


if __name__ == "__main__":
    main()

