from yumebyo.components.youtube_music.get_thumbnail_url import get_thumbnail_url
from yumebyo.components.images.download_and_embed_using_url import download_and_embed_artwork_using_url

thumbnail_url = get_thumbnail_url(
    artist="Nightcore",
    title="forever young",
    filter="videos"
)


print(f"Thumbnail URL: {thumbnail_url}")

success = download_and_embed_artwork_using_url(
    file_path="/Volumes/HUB/Github/Artwork_fetcher/Artwork_fetcher/test/My Stupid Heart (Kids Version).mp3",
    image_url=thumbnail_url,
    square=True,
    downscale_to_480=True
)

print(f"Success: {success}")