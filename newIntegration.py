"""
This script is used to get the artwork URL from the covers.musichoarders.xyz website.
"""
# pip install playwright
# playwright install
from playwright.sync_api import sync_playwright

url = "https://covers.musichoarders.xyz?sources=spotify%2Capplemusic&artist=LBI%20%E5%88%A9%E6%AF%94&album=%E8%B7%B3%E6%A5%BC%E6%9C%BA"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    # adjust selector to whatever the site uses for result images

    imgs = page.query_selector_all("a")
    srcs = [img.get_attribute("href") for img in imgs if img.get_attribute("href")]
    print(srcs)

    # browser.close()
