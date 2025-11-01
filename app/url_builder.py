"""
URL building utilities for artwork fetching.
"""

from urllib.parse import urlencode
from typing import Optional, List


def build_url_with_params(
    base_url: str,
    theme: Optional[str] = None,
    resolution: Optional[str] = None,
    sources: Optional[List[str]] = None,
    country: Optional[str] = None,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    identifier: Optional[str] = None
) -> str:
    """
    Build a URL with query parameters for artwork fetching.
    
    All parameters are optional. A search is automatically initiated if at least 
    one of artist, album or identifier is provided.
    
    Args:
        base_url: The base URL of the site
        theme: 'light' or 'dark'
        resolution: Resolution value
        sources: List of sources (will be joined with commas, lowercase, no spaces/punctuation)
        country: Country code
        artist: Artist name
        album: Album name
        identifier: Identifier value
    
    Returns:
        Complete URL with query parameters
    """
    params = {}
    
    if theme and theme.lower() in ['light', 'dark']:
        params['theme'] = theme.lower()
    
    if resolution:
        params['resolution'] = resolution
    
    if sources:
        # All sources are lowercase and contain no spaces, punctuation or symbols
        sources_clean = [s.lower().strip() for s in sources if s]
        params['sources'] = ','.join(sources_clean)
    
    if country:
        params['country'] = country
    
    if artist:
        params['artist'] = artist
    
    if album:
        params['album'] = album
    
    if identifier:
        params['identifier'] = identifier
    
    # Build the URL
    if params:
        query_string = urlencode(params)
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}{query_string}"
    
    return base_url


def get_artwork_url_from_music_file(
    file_path: str,
    base_url: str = "https://covers.musichoarders.xyz",
    theme: Optional[str] = None,
    resolution: Optional[str] = None,
    sources: Optional[List[str]] = None,
    country: Optional[str] = None
) -> str:
    """
    Extract metadata from a music file and build an artwork URL.
    
    Args:
        file_path: Path to the music file
        base_url: Base URL for the artwork service
        theme: Optional theme ('light' or 'dark')
        resolution: Optional resolution value
        sources: Optional list of sources
        country: Optional country code
    
    Returns:
        Complete URL with query parameters based on extracted metadata
    """
    from app.metadata import get_music_metadata
    
    metadata = get_music_metadata(file_path)
    
    return build_url_with_params(
        base_url=base_url,
        theme=theme,
        resolution=resolution,
        sources=['spotify', 'applemusic'],
        country=country,
        artist=metadata['artist'],
        album=metadata['album']
    )

