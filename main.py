#!/usr/bin/env python3
"""
Main entry point for the Artwork Fetcher CLI.
"""

import argparse
from app.browser import init_browser, close_browser
from app.processor import process_folder_for_artwork
import time


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Metadata Fetcher based on covers.musichoarders.xyz API."
    )
    parser.add_argument(
        '--dir', '-d',
        type=str,
        required=True,
        help="Path to your music folder"
    )
    args = parser.parse_args()

    base_url = "https://covers.musichoarders.xyz"
    
    # Initialize browser
    init_browser()

    try:
        results = process_folder_for_artwork(
            folder_path=args.dir,
            base_url=base_url,
            recursive=True,
            verbose=True
        )
        print("\nProcessing complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up browser
        time.sleep(10)
        close_browser()


if __name__ == "__main__":
    main()
