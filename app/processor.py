"""
Folder processing utilities for batch artwork operations.
"""

import os
from typing import Dict, List, Optional

from app.file_scanner import scan_folder_for_music_files
from app.metadata import has_embedded_artwork, get_music_metadata, MUTAGEN_AVAILABLE
from app.url_builder import build_url_with_params
from app.artwork import download_and_embed_artwork


def process_folder_for_artwork(
    folder_path: str,
    base_url: str = "https://covers.musichoarders.xyz",
    theme: Optional[str] = None,
    resolution: Optional[str] = None,
    sources: Optional[List[str]] = None,
    country: Optional[str] = None,
    recursive: bool = True,
    verbose: bool = True
) -> Dict[str, List[str]]:
    """
    Scan a folder for music files and generate artwork URLs for files without embedded artwork.
    
    Args:
        folder_path: Path to the folder to scan
        base_url: Base URL for the artwork service
        theme: Optional theme ('light' or 'dark')
        resolution: Optional resolution value
        sources: Optional list of sources
        country: Optional country code
        recursive: If True, scan subdirectories recursively
        verbose: If True, print progress information
    
    Returns:
        Dictionary with:
        - 'with_artwork': List of file paths that already have embedded artwork
        - 'without_artwork': List of file paths without embedded artwork
        - 'artwork_urls': Dictionary mapping file paths to artwork URLs
    """
    if not MUTAGEN_AVAILABLE:
        raise ImportError("mutagen is required. Install it with: pip install mutagen")
    
    music_files = scan_folder_for_music_files(folder_path, recursive)
    
    results = {
        'with_artwork': [],
        'without_artwork': [],
        'artwork_urls': {}
    }
    
    if verbose:
        print(f"Found {len(music_files)} music file(s). Scanning for embedded artwork...")
        print()
    
    for file_path in music_files:
        try:
            if has_embedded_artwork(file_path):
                results['with_artwork'].append(file_path)
                if verbose:
                    print(f"✓ {os.path.basename(file_path)} - Already has embedded artwork")
            else:
                results['without_artwork'].append(file_path)
                
                # Extract metadata and build artwork URL
                try:
                    metadata = get_music_metadata(file_path)
                    if metadata['artist'] or metadata['album']:
                        artwork_url = build_url_with_params(
                            base_url=base_url,
                            sources=['spotify', 'applemusic'],
                            artist=metadata['artist'],
                            album=metadata['title']
                        )
                        results['artwork_urls'][file_path] = artwork_url
                        if verbose:
                            print(f"✗ {os.path.basename(file_path)} - No artwork")
                            print(f"  Artist: {metadata['artist'] or 'N/A'}, Title: {metadata['title'] or 'N/A'}")
                            print(f"  Artwork URL: {artwork_url}")
                        
                        # Download and embed the artwork
                        if verbose:
                            print()
                        success = download_and_embed_artwork(file_path, artwork_url, verbose=verbose)
                        
                        if success:
                            results['with_artwork'].append(file_path)  # Move to with_artwork after embedding
                            if file_path in results['without_artwork']:
                                results['without_artwork'].remove(file_path)
                        if verbose:
                            print()
                    else:
                        if verbose:
                            print(f"✗ {os.path.basename(file_path)} - No artwork (missing metadata)")
                except Exception as e:
                    if verbose:
                        print(f"✗ {os.path.basename(file_path)} - Error extracting metadata: {e}")
        
        except Exception as e:
            if verbose:
                print(f"✗ {os.path.basename(file_path)} - Error processing: {e}")
    
    if verbose:
        print()
        print(f"Summary:")
        print(f"  Files with artwork: {len(results['with_artwork'])}")
        print(f"  Files without artwork: {len(results['without_artwork'])}")
        print(f"  Artwork URLs generated: {len(results['artwork_urls'])}")
    
    return results

