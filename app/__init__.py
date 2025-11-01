"""
Artwork Fetcher - A tool for fetching and embedding artwork into music files.
"""

__version__ = "1.0.0"

from app.processor import process_folder_for_artwork
from app.metadata import get_music_metadata, has_embedded_artwork
from app.url_builder import build_url_with_params, get_artwork_url_from_music_file

__all__ = [
    'process_folder_for_artwork',
    'get_music_metadata',
    'has_embedded_artwork',
    'build_url_with_params',
    'get_artwork_url_from_music_file',
]

