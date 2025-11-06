import os
from typing import Dict, List, Optional

from components.localMusicScanner import get_local_music_file_paths
from components.localMusicScanner import has_embedded_artwork, get_music_metadata, MUTAGEN_AVAILABLE
from components.webMetadataFetcher import build_musichoarders_url_with_params, build_youtube_url_with_params
from app.artwork import download_and_embed_artwork


def yumebyo(
    folder_path: str,
    musichoarders_base_url: Optional[str] = "https://covers.musichoarders.xyz",
    youtube_base_url: Optional[str] = "https://music.youtube.com/search?q=",
    theme: Optional[str] = None,
    resolution: Optional[str] = None,
    sources: Optional[List[str]] = None,
    country: Optional[str] = None,
    recursive: bool = True,
    verbose: bool = True
) -> Dict[str, List[str]]:
    """
    Scan a folder for music files and embedd artwork from musichoarders.xyz and youtube.com for files without embedded artwork.
    
    Args:
        folder_path: Path to the folder to scan
        musichoarders_base_url: Base URL for the artwork service from musichoarders.xyz
        youtube_base_url: Base URL for the artwork service from youtube.com
        theme: Optional theme ('light' or 'dark')
        resolution: Optional resolution value
        sources: Optional list of sources for the artwork service from musichoarders.xyz
        country: Optional country code
        recursive: If True, scan subdirectories recursively
        verbose: If True, print progress information
    
    Returns:
        Dictionary with:
        - 'with_artwork': List of file paths that already have embedded artwork
        - 'without_artwork': List of file paths without embedded artwork
        - 'artwork_urls_musichoarders': Dictionary mapping file paths to artwork URLs from MusicHoarders
        - 'artwork_urls_youtube': Dictionary mapping file paths to artwork URLs from YouTube
    """

    if not MUTAGEN_AVAILABLE:
        raise ImportError("mutagen is required. Install it with: pip install mutagen")
    
    local_music_file_paths_list = get_local_music_file_paths(folder_path, recursive)
    
    results = {
        'with_artwork': [],
        'without_artwork': [],
        'artwork_urls_musichoarders': {},
        'artwork_urls_youtube': {}
    }
    
    if verbose:
        print(f"Found {len(local_music_file_paths_list)} music file(s). Scanning for embedded artwork...")
        print()
    
    for file_path in local_music_file_paths_list:
        try:
            if has_embedded_artwork(file_path):
                results['with_artwork'].append(file_path)
                if verbose:
                    print(f"✓ {os.path.basename(file_path)} - Already has embedded artwork")
            else:
                results['without_artwork'].append(file_path)
                
                # Extract metadata and build artwork URL for musichoarders.xyz
                try:
                    metadata = get_music_metadata(file_path)
                    if metadata['artist'] or metadata['album']:

                        musichoarders_artwork_url = build_musichoarders_url_with_params(
                            base_url=musichoarders_base_url,
                            sources=['spotify', 'applemusic'],
                            artist=metadata['artist'],
                            album=metadata['title']
                        )
                        
                        results['artwork_urls'][file_path] = musichoarders_artwork_url
                        if verbose:
                            print(f"✗ {os.path.basename(file_path)} - No artwork")
                            print(f"  Artist: {metadata['artist'] or 'N/A'}, Title: {metadata['title'] or 'N/A'}")
                            print(f"  Artwork URL: {musichoarders_artwork_url}")
                        
                        if(musichoarders_artwork_url is None):
                            youtube_artwork_url = build_youtube_url_with_params(
                                base_url=musichoarders_base_url,
                                sources=['spotify', 'applemusic'],
                                artist=metadata['artist'],
                                album=metadata['title']
                            )

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

