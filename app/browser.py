"""
Browser management for Playwright-based artwork fetching.
"""

from playwright.sync_api import Browser, BrowserContext, Playwright, sync_playwright

# Global references
_p: Playwright = None
_browser: Browser = None
_context: BrowserContext = None


def init_browser():
    """Initialize the Playwright browser and context."""
    global _p, _browser, _context
    _p = sync_playwright().start()
    _browser = _p.firefox.launch(headless=True)  # headless=True if you don't need to see it
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

