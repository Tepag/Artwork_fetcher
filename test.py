"""Simple harness to exercise the YouTube Music metadata component."""

from yumebyo.components.youtubeMusicMetadataFetcher import (
    fetch_primary_youtube_music_metadata,
    search_youtube_music_metadata,
)


def main() -> None:
    try:
        top_result = fetch_primary_youtube_music_metadata(
            artist="Nightcore",
            title="Forever young",
        )
        print("Top result:")
        print(top_result or "No result found.")

        results = search_youtube_music_metadata(
            artist="Daft Punk",
            title="Harder Better Faster Stronger",
            limit=3,
        )
        # print("\nTop 3 normalised results:")
        # for idx, entry in enumerate(results, start=1):
            # artist_names = ", ".join(entry.get("artists", [])) or "Unknown artist"
            # print(f"{idx}. {entry.get('title', 'Unknown title')} - {artist_names}")
    except ImportError as exc:
        print(exc)


if __name__ == "__main__":
    main()

