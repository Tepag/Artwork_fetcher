from pathlib import Path
from typing import List, Dict, Optional
import os

# Check if mutagen is installed
try:
    from mutagen import File
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen not installed. Install it with: pip install mutagen")



def get_local_music_file_paths(folder_path: str, recursive: bool = True) -> List[str]:
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
        
        # Check for embedded artwork based on file type
        if isinstance(audio_file, MP3):
            if audio_file.tags is not None:
                # MP3 uses APIC (Attached Picture) frames
                if 'APIC:' in audio_file.tags or 'APIC' in audio_file.tags:
                    return True
                # Also check for cover art tags
                for key in audio_file.tags.keys():
                    if key.startswith('APIC'):
                        return True
        
        elif isinstance(audio_file, FLAC):
            if audio_file.pictures:
                return len(audio_file.pictures) > 0
        
        elif isinstance(audio_file, MP4):
            if audio_file.tags is not None:
                # MP4 uses 'covr' tag for artwork
                if 'covr' in audio_file.tags:
                    return True
        
        elif isinstance(audio_file, OggVorbis):
            if audio_file.tags is not None:
                # OGG can have METADATA_BLOCK_PICTURE in tags
                if 'METADATA_BLOCK_PICTURE' in audio_file.tags:
                    return True
                if 'metadata_block_picture' in audio_file.tags:
                    return True
        
        # Generic fallback - check for common artwork tag names
        if hasattr(audio_file, 'tags') and audio_file.tags is not None:
            tags = audio_file.tags
            artwork_keys = ['APIC', 'covr', 'METADATA_BLOCK_PICTURE', 'metadata_block_picture']
            for key in tags.keys():
                if any(art_key in str(key) for art_key in artwork_keys):
                    return True
            # Also check if key starts with APIC
            for key in tags.keys():
                if str(key).startswith('APIC'):
                    return True
        
        return False
    
    except Exception:
        return False



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
                        metadata['artist'] = str(audio_file.tags[tag][0])
                        break
                
                for tag in album_tags:
                    if tag in audio_file.tags:
                        metadata['album'] = str(audio_file.tags[tag][0])
                        break
                
                for tag in title_tags:
                    if tag in audio_file.tags:
                        metadata['title'] = str(audio_file.tags[tag][0])
                        break
        
        elif isinstance(audio_file, FLAC):
            # FLAC files use Vorbis comments
            if audio_file.tags is not None:
                if 'artist' in audio_file.tags:
                    metadata['artist'] = str(audio_file.tags['artist'][0])
                if 'album' in audio_file.tags:
                    metadata['album'] = str(audio_file.tags['album'][0])
                if 'title' in audio_file.tags:
                    metadata['title'] = str(audio_file.tags['title'][0])
        
        elif isinstance(audio_file, MP4):
            # MP4/M4A files use iTunes tags
            if audio_file.tags is not None:
                # MP4 uses different tag names
                if '\xa9ART' in audio_file.tags:
                    metadata['artist'] = str(audio_file.tags['\xa9ART'][0])
                if '\xa9alb' in audio_file.tags:
                    metadata['album'] = str(audio_file.tags['\xa9alb'][0])
                if '\xa9nam' in audio_file.tags:
                    metadata['title'] = str(audio_file.tags['\xa9nam'][0])
        
        elif isinstance(audio_file, OggVorbis):
            # OGG files use Vorbis comments
            if audio_file.tags is not None:
                if 'artist' in audio_file.tags:
                    metadata['artist'] = str(audio_file.tags['artist'][0])
                if 'album' in audio_file.tags:
                    metadata['album'] = str(audio_file.tags['album'][0])
                if 'title' in audio_file.tags:
                    metadata['title'] = str(audio_file.tags['title'][0])
        
        else:
            # Generic fallback - try common tag names
            if hasattr(audio_file, 'tags') and audio_file.tags is not None:
                tags = audio_file.tags
                # Try various common tag formats
                for artist_key in ['artist', 'ARTIST', 'TPE1', '\xa9ART']:
                    if artist_key in tags:
                        metadata['artist'] = str(tags[artist_key][0] if isinstance(tags[artist_key], list) else tags[artist_key])
                        break
                
                for album_key in ['album', 'ALBUM', 'TALB', '\xa9alb']:
                    if album_key in tags:
                        metadata['album'] = str(tags[album_key][0] if isinstance(tags[album_key], list) else tags[album_key])
                        break
                
                for title_key in ['title', 'TITLE', 'TIT2', '\xa9nam']:
                    if title_key in tags:
                        metadata['title'] = str(tags[title_key][0] if isinstance(tags[title_key], list) else tags[title_key])
                        break
        
        return metadata
    
    except Exception as e:
        raise Exception(f"Error reading metadata from {file_path}: {str(e)}")

