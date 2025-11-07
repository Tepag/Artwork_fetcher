from yumebyo.components.youtube_music.get_thumbnail_url import get_thumbnail_url

thumbnail_url = get_thumbnail_url(
    artist="Nightcore",
    title="forever young",
    filter="videos"
)

print(f"Thumbnail URL: {thumbnail_url}")