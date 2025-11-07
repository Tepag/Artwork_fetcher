from pathlib import Path
from typing import List, Dict, Optional, Iterable, Tuple
import os
import base64
import io

# Check if mutagen is installed
try:
    from mutagen import File
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC, Picture
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen not installed. Install it with: pip install mutagen")


try:
    from PIL import Image  # type: ignore

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False



def get_local_music_file_paths(
    folder_path: str,
    recursive: bool = True,
    verbose: bool = True
) -> List[str]:
    """
    Get the paths of all music files in a folder.
    
    Args:
        folder_path: Path to the folder to scan
        recursive: If True, scan subdirectories recursively
    
    Returns:
        List of paths to music files in the folder
    """
    music_extensions = {'.mp3', '.flac', '.m4a', '.mp4', '.ogg', '.oga', '.opus', '.wav', '.aac'}
    music_files = []
    
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        return music_files
    
    if recursive:
        for file_path in folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in music_extensions:
                music_files.append(str(file_path))
    else:
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in music_extensions:
                music_files.append(str(file_path))
    
    return sorted(music_files)



def _iter_embedded_artwork(
    audio_file: "File"
) -> Iterable[Tuple[bytes, Optional[int], Optional[int]]]:
    """Yield tuples of (image_data, width, height) for embedded artwork."""

    if isinstance(audio_file, MP3):
        tags = getattr(audio_file, "tags", None)
        if tags:
            for frame in list(tags.values()):
                frame_id = getattr(frame, "FrameID", "")
                if isinstance(frame_id, str) and frame_id.startswith("APIC"):
                    data = getattr(frame, "data", None)
                    if data:
                        yield data, None, None

    elif isinstance(audio_file, FLAC):
        for picture in getattr(audio_file, "pictures", []) or []:
            data = getattr(picture, "data", None)
            if data:
                width = getattr(picture, "width", None)
                height = getattr(picture, "height", None)
                yield data, width, height

    elif isinstance(audio_file, MP4):
        tags = getattr(audio_file, "tags", None)
        if tags:
            covers = tags.get("covr")
            if covers:
                for cover in covers:
                    try:
                        data = bytes(cover)
                    except Exception:
                        data = None
                    if data:
                        yield data, None, None

    elif isinstance(audio_file, OggVorbis):
        tags = getattr(audio_file, "tags", None)
        if tags:
            for key in ("METADATA_BLOCK_PICTURE", "metadata_block_picture"):
                entries = tags.get(key)
                if not entries:
                    continue
                for entry in entries:
                    try:
                        picture_bytes = base64.b64decode(entry)
                        picture = Picture(picture_bytes)
                        data = picture.data
                        width = getattr(picture, "width", None)
                        height = getattr(picture, "height", None)
                    except Exception:
                        continue
                    if data:
                        yield data, width, height

    else:
        tags = getattr(audio_file, "tags", None)
        if tags:
            for key, value in list(tags.items()):
                key_str = str(key)
                if "PICTURE" in key_str.upper() or key_str.startswith("APIC"):
                    if isinstance(value, bytes):
                        yield value, None, None


def _is_square_image(image_data: bytes, width: Optional[int], height: Optional[int]) -> Optional[bool]:
    """Return True if image is square, False if not, None if unknown."""

    if width and height:
        return width == height

    if not image_data:
        return None

    if not PIL_AVAILABLE:
        return None

    try:
        with Image.open(io.BytesIO(image_data)) as img:
            img.load()
            return img.width == img.height
    except Exception:
        return None


def remove_embedded_artwork(file_path: str, audio_file: Optional["File"] = None) -> bool:
    """Remove all embedded artwork from the file."""

    if not MUTAGEN_AVAILABLE:
        return False

    if not os.path.exists(file_path):
        return False

    close_file = False
    if audio_file is None:
        audio_file = File(file_path)
        close_file = True

    if audio_file is None:
        return False

    removed = False

    try:
        if isinstance(audio_file, MP3):
            tags = getattr(audio_file, "tags", None)
            if tags:
                keys_to_delete = [key for key in tags.keys() if str(key).startswith("APIC")]
                for key in keys_to_delete:
                    del tags[key]
                    removed = True
                if removed:
                    audio_file.save()

        elif isinstance(audio_file, FLAC):
            if getattr(audio_file, "pictures", None):
                audio_file.clear_pictures()
                audio_file.save()
                removed = True

        elif isinstance(audio_file, MP4):
            tags = getattr(audio_file, "tags", None)
            if tags and "covr" in tags:
                tags.pop("covr", None)
                audio_file.save()
                removed = True

        elif isinstance(audio_file, OggVorbis):
            tags = getattr(audio_file, "tags", None)
            if tags:
                deleted = False
                for key in ("METADATA_BLOCK_PICTURE", "metadata_block_picture"):
                    if key in tags:
                        del tags[key]
                        deleted = True
                if deleted:
                    audio_file.save()
                    removed = True

        else:
            tags = getattr(audio_file, "tags", None)
            if tags:
                keys_to_delete = [key for key in tags.keys() if "PICTURE" in str(key).upper()]
                for key in keys_to_delete:
                    del tags[key]
                    removed = True
                if removed:
                    audio_file.save()

    except Exception as exc:
        print(f"Warning: failed to remove artwork from {file_path}: {exc}")
        return False
    finally:
        if close_file and hasattr(audio_file, "close"):
            try:
                audio_file.close()  # type: ignore[attr-defined]
            except Exception:
                pass

    return removed


def has_embedded_artwork(file_path: str) -> bool:
    """
    Check if a music file has embedded artwork/cover art using mutagen.
    
    Args:
        file_path: Path to the music file
    
    Returns:
        True if artwork is embedded, False otherwise
    """

    if not MUTAGEN_AVAILABLE:
        return False
    
    if not os.path.exists(file_path):
        return False
    
    try:
        audio_file = File(file_path)
        if audio_file is None:
            return False
        
        artwork_found = False
        square_artwork_found = False

        for artwork_data, width, height in _iter_embedded_artwork(audio_file):
            artwork_found = True
            is_square = _is_square_image(artwork_data, width, height)

            if is_square is False:
                remove_embedded_artwork(file_path, audio_file)
                return False

            if is_square is True:
                square_artwork_found = True

        if square_artwork_found:
            return True

        return artwork_found
    
    except Exception:
        return False



def _extract_tag_value(tag_value):
    """
    Safely extract and convert a tag value to string.
    Handles lists, bytes, strings, and empty values.
    """
    if tag_value is None:
        return None
    if isinstance(tag_value, list):
        if len(tag_value) == 0:
            return None
        tag_value = tag_value[0]
    if isinstance(tag_value, bytes):
        try:
            return tag_value.decode('utf-8')
        except UnicodeDecodeError:
            return tag_value.decode('utf-8', errors='replace')
    return str(tag_value)


def get_music_metadata(file_path: str) -> Dict[str, Optional[str]]:
    """
    Extract artist and album/title from a music file.
    
    Supports multiple formats:
    - MP3 (ID3 tags)
    - FLAC (Vorbis comments)
    - MP4/M4A (iTunes tags)
    - OGG (Vorbis comments)
    
    Args:
        file_path: Path to the music file
    
    Returns:
        Dictionary with 'artist' and 'album'/'title' keys
    """
    if not MUTAGEN_AVAILABLE:
        raise ImportError("mutagen is required. Install it with: pip install mutagen")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        audio_file = File(file_path)
        if audio_file is None:
            raise ValueError(f"Unsupported file format or corrupted file: {file_path}")
        
        metadata = {
            'artist': None,
            'album': None,
            'title': None
        }
        
        # Extract metadata based on file type
        if isinstance(audio_file, MP3):
            # MP3 files use ID3 tags
            if audio_file.tags is not None:
                # Try common tag names
                artist_tags = ['TPE1', 'TPE2', 'TCOM']
                album_tags = ['TALB']
                title_tags = ['TIT2', 'TIT1']
                
                for tag in artist_tags:
                    if tag in audio_file.tags:
                        metadata['artist'] = _extract_tag_value(audio_file.tags[tag])
                        if metadata['artist']:
                            break
                
                for tag in album_tags:
                    if tag in audio_file.tags:
                        metadata['album'] = _extract_tag_value(audio_file.tags[tag])
                        if metadata['album']:
                            break
                
                for tag in title_tags:
                    if tag in audio_file.tags:
                        metadata['title'] = _extract_tag_value(audio_file.tags[tag])
                        if metadata['title']:
                            break
        
        elif isinstance(audio_file, FLAC):
            # FLAC files use Vorbis comments
            if audio_file.tags is not None:
                if 'artist' in audio_file.tags:
                    metadata['artist'] = _extract_tag_value(audio_file.tags['artist'])
                if 'album' in audio_file.tags:
                    metadata['album'] = _extract_tag_value(audio_file.tags['album'])
                if 'title' in audio_file.tags:
                    metadata['title'] = _extract_tag_value(audio_file.tags['title'])
        
        elif isinstance(audio_file, MP4):
            # MP4/M4A files use iTunes tags
            if audio_file.tags is not None:
                # MP4 uses different tag names
                if '\xa9ART' in audio_file.tags:
                    metadata['artist'] = _extract_tag_value(audio_file.tags['\xa9ART'])
                if '\xa9alb' in audio_file.tags:
                    metadata['album'] = _extract_tag_value(audio_file.tags['\xa9alb'])
                if '\xa9nam' in audio_file.tags:
                    metadata['title'] = _extract_tag_value(audio_file.tags['\xa9nam'])
        
        elif isinstance(audio_file, OggVorbis):
            # OGG files use Vorbis comments
            if audio_file.tags is not None:
                if 'artist' in audio_file.tags:
                    metadata['artist'] = _extract_tag_value(audio_file.tags['artist'])
                if 'album' in audio_file.tags:
                    metadata['album'] = _extract_tag_value(audio_file.tags['album'])
                if 'title' in audio_file.tags:
                    metadata['title'] = _extract_tag_value(audio_file.tags['title'])
        
        else:
            # Generic fallback - try common tag names
            if hasattr(audio_file, 'tags') and audio_file.tags is not None:
                tags = audio_file.tags
                # Try various common tag formats
                for artist_key in ['artist', 'ARTIST', 'TPE1', '\xa9ART']:
                    if artist_key in tags:
                        metadata['artist'] = _extract_tag_value(tags[artist_key])
                        if metadata['artist']:
                            break
                
                for album_key in ['album', 'ALBUM', 'TALB', '\xa9alb']:
                    if album_key in tags:
                        metadata['album'] = _extract_tag_value(tags[album_key])
                        if metadata['album']:
                            break
                
                for title_key in ['title', 'TITLE', 'TIT2', '\xa9nam']:
                    if title_key in tags:
                        metadata['title'] = _extract_tag_value(tags[title_key])
                        if metadata['title']:
                            break
        
        return metadata
    
    except Exception as e:
        raise Exception(f"Error reading metadata from {file_path}: {str(e)}")

