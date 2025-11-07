"""
Browser management for Playwright-based artwork fetching.
"""

from playwright.sync_api import Browser, BrowserContext, Playwright, sync_playwright
from urllib.parse import urlencode, quote_plus
from typing import Optional, List


# Global references
_p: Playwright = None
_browser: Browser = None
_context: BrowserContext = None


def init_browser():
    """Initialize the Playwright browser and context."""
    global _p, _browser, _context
    _p = sync_playwright().start()
    _browser = _p.firefox.launch(headless=False)  # headless=True if you don't need to see it
    _context = _browser.new_context()
    print("Browser started!")


def get_context() -> BrowserContext:
    """Get the current browser context."""
    if _context is None:
        raise RuntimeError("Browser not initialized. Call init_browser() first.")
    return _context


def close_browser():
    """Close the browser and clean up."""
    global _p, _browser, _context
    if _browser:
        _browser.close()
    if _p:
        _p.stop()
    _p = None
    _browser = None
    _context = None

"""
URL building utilities for artwork fetching.
"""




def build_youtube_url_with_params(
    base_url: Optional[str] = "https://music.youtube.com/search?q=",
    artist: Optional[str] = None,
    title: Optional[str] = None
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
    # Build the search query by combining artist and title
    query_parts = []
    if artist:
        query_parts.append(artist)
    if title:
        query_parts.append(title)
    
    if query_parts:
        # Join with '+' and URL-encode the query
        query = ' '.join(query_parts)
        encoded_query = quote_plus(query)
        return f"{base_url}{encoded_query}"
    
    return base_url

def build_musichoarders_url_with_params(
    base_url: Optional[str] = "https://covers.musichoarders.xyz",
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
