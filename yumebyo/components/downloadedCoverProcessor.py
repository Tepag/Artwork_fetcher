"""
Artwork fetching, downloading, and embedding utilities.
"""

import base64
from typing import Optional
import requests
from .webMetadataFetcher import get_context
from .localMusicScanner import MUTAGEN_AVAILABLE

import time

def fetch_first_artwork_image(artwork_url: str) -> Optional[str]:
    """
    Fetch the artwork page and extract the URL of the first available artwork image.
    
    Args:
        artwork_url: URL to the artwork selection page
    
    Returns:
        URL of the first available artwork image, or None if not found
    """
    context = get_context()
    page = context.new_page()

    try:
        page.goto(artwork_url, wait_until="networkidle")
        try:
            page.wait_for_selector("img", timeout=10000)
        except Exception:
            print("Warning: timed out waiting for artwork images to load.")
        imgs = page.query_selector_all("img")
        image_urls = [img.get_attribute("src") for img in imgs if img.get_attribute("src")]
        print(f"image_urls: {image_urls}")
        if image_urls:
            return image_urls[0]
        return None
    finally:
        page.close()


def download_artwork_image(image_url: str) -> Optional[bytes]:
    """
    Download an artwork image from a URL.
    
    Args:
        image_url: URL of the artwork image to download
    
    Returns:
        Image data as bytes, or None if download fails
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('Content-Type', '')
        if 'image' in content_type.lower():
            return response.content
        else:
            print(f"Warning: URL does not appear to be an image (Content-Type: {content_type})")
            return None
    
    except Exception as e:
        print(f"Error downloading artwork image: {e}")
        return None


def embed_artwork(file_path: str, image_data: bytes, mime_type: str = 'image/jpeg') -> bool:
    """
    Embed artwork image into a music file.
    
    Args:
        file_path: Path to the music file
        image_data: Image data as bytes
        mime_type: MIME type of the image (default: 'image/jpeg')
    
    Returns:
        True if embedding was successful, False otherwise
    """
    if not MUTAGEN_AVAILABLE:
        raise ImportError("mutagen is required. Install it with: pip install mutagen")
    
    try:
        from mutagen import File
        from mutagen.mp3 import MP3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
        from mutagen.oggvorbis import OggVorbis
        
        audio_file = File(file_path)
        if audio_file is None:
            raise ValueError(f"Unsupported file format or corrupted file: {file_path}")
        
        # Embed artwork based on file type
        if isinstance(audio_file, MP3):
            # MP3 uses APIC (Attached Picture) frames
            from mutagen.id3 import ID3, APIC, error as ID3Error
            
            try:
                audio_file.add_tags()
            except ID3Error:
                pass
            
            # Remove existing APIC frames
            if audio_file.tags:
                apic_keys = [key for key in audio_file.tags.keys() if key.startswith('APIC')]
                for key in apic_keys:
                    del audio_file.tags[key]
            
            # Add new APIC frame
            audio_file.tags.add(APIC(
                encoding=3,  # UTF-8
                mime=mime_type,
                type=3,  # Cover (front)
                desc='Cover',
                data=image_data
            ))
            audio_file.save()
            return True
        
        elif isinstance(audio_file, FLAC):
            # FLAC uses picture metadata
            from mutagen.flac import Picture
            
            picture = Picture()
            picture.type = 3  # Cover (front)
            picture.mime = mime_type
            picture.desc = 'Cover'
            picture.data = image_data
            
            audio_file.add_picture(picture)
            audio_file.save()
            return True
        
        elif isinstance(audio_file, MP4):
            # MP4 uses 'covr' tag
            from mutagen.mp4 import MP4Cover
            
            cover = MP4Cover(image_data, imageformat=MP4Cover.FORMAT_JPEG if 'jpeg' in mime_type or 'jpg' in mime_type else MP4Cover.FORMAT_PNG)
            audio_file.tags['covr'] = [cover]
            audio_file.save()
            return True
        
        elif isinstance(audio_file, OggVorbis):
            # OGG uses METADATA_BLOCK_PICTURE
            from mutagen.flac import Picture
            
            picture = Picture()
            picture.type = 3  # Cover (front)
            picture.mime = mime_type
            picture.desc = 'Cover'
            picture.data = image_data
            
            data = picture.write()
            b64data = base64.b64encode(data).decode('ascii')
            audio_file['METADATA_BLOCK_PICTURE'] = [b64data]
            audio_file.save()
            return True
        
        else:
            # Generic fallback - try to add as a tag
            print(f"Warning: Unsupported file format for embedding artwork: {type(audio_file)}")
            return False
    
    except Exception as e:
        print(f"Error embedding artwork into {file_path}: {e}")
        return False


def download_and_embed_artwork(file_path: str, artwork_url: str, verbose: bool = True) -> bool:
    """
    Fetch artwork from URL, download it, and embed it into the music file.
    
    Args:
        file_path: Path to the music file
        artwork_url: URL to the artwork selection page
        verbose: If True, print progress information
    
    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"  Fetching artwork page...")
    
    # Fetch the first available artwork image URL
    image_url = fetch_first_artwork_image(artwork_url)
    
    if not image_url:
        if verbose:
            print(f"  ✗ Could not find artwork image on page")
        return False
    
    if verbose:
        print(f"  Found artwork image: {image_url}")
        print(f"  Downloading artwork...")
    
    # Download the image
    image_data = download_artwork_image(image_url)
    
    if not image_data:
        if verbose:
            print(f"  ✗ Failed to download artwork image")
        return False
    
    if verbose:
        print(f"  Downloaded {len(image_data)} bytes")
    
    # Determine MIME type from URL or content
    mime_type = 'image/jpeg'
    if image_url.lower().endswith('.png'):
        mime_type = 'image/png'
    elif image_url.lower().endswith('.webp'):
        mime_type = 'image/webp'
    elif image_url.lower().endswith('.gif'):
        mime_type = 'image/gif'
    
    # Embed the artwork
    if verbose:
        print(f"  Embedding artwork into file...")
    
    success = embed_artwork(file_path, image_data, mime_type)
    
    if success and verbose:
        print(f"  ✓ Successfully embedded artwork!")
    elif not success and verbose:
        print(f"  ✗ Failed to embed artwork")
    
    return success

