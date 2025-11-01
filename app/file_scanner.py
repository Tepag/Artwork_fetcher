"""
File scanning utilities for finding music files.
"""

from pathlib import Path
from typing import List


def scan_folder_for_music_files(folder_path: str, recursive: bool = True) -> List[str]:
    """
    Scan a folder for music files.
    
    Args:
        folder_path: Path to the folder to scan
        recursive: If True, scan subdirectories recursively
    
    Returns:
        List of paths to music files found
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

