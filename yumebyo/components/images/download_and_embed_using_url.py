"""
Artwork fetching, downloading, and embedding utilities.
"""

import base64
from typing import Optional
import requests

from mutagen import File
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
import io
from ..localMusicScanner import MUTAGEN_AVAILABLE

try:
    from PIL import Image  # type: ignore
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not installed. Install it with: pip install pillow")

def download_and_embed_artwork_using_url(
    file_path: str, 
    image_url: str, 
    mime_type: str = 'image/jpeg',
    square: bool = True,
    downscale_to_480: bool = False,
) -> bool:
    """
    Download an artwork image from a URL and embed it into a music file.
    
    Args:
        file_path: Path to the music file
        image_url: URL of the artwork image to download
        mime_type: MIME type of the image (default: 'image/jpeg')
        square: If True, crop the image to a square
        downscale_to_480: If True, downscale the image to 480x480
    
    Returns:
        True if successful, False otherwise
    """

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('Content-Type', '')

        if 'image' in content_type.lower():
            image_data = response.content
            if square:
                print("Cropping image to square")
                image_data = _crop_center_square(image_data)
            if downscale_to_480:
                image_data = _downscale_to_480(image_data)
            
            success = _embed_artwork(file_path, image_data, mime_type)

            return success
        else:
            print(f"Warning: URL does not appear to be an image (Content-Type: {content_type})")
            return None
    
    except Exception as e:
        print(f"Error downloading artwork image: {e}")
        return None
    


def _embed_artwork(
    file_path: str, 
    image_data: bytes, 
    mime_type: str = 'image/jpeg'
) -> bool:
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


def _crop_center_square(image_data: bytes) -> bytes:
    """
    Crop the image to a square.
    
    Args:
        image_data: Image data as bytes
    
    Returns:
        Image data as bytes
    """
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    
    width, height = image.size
    if width == height:
        return image_data
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    right = left + side
    bottom = top + side
    cropped = image.crop((left, top, right, bottom))

    buffer = io.BytesIO()
    cropped.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def _downscale_to_480(image_data: bytes) -> bytes:
    """
    Downscale the image to 480x480.
    
    Args:
        image_data: Image data as bytes
    
    Returns:
        Image data as bytes
    """

    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    image = image.resize((480, 480), Image.LANCZOS)


    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()