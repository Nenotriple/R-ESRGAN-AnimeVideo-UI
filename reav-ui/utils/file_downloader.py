# Standard library imports
import urllib.request
from pathlib import Path

# Type hinting
from typing import Optional, Callable


def _print_progress(downloaded: int, total_size: int):
    percent = downloaded * 100 // total_size if total_size else 0
    print(f"\rDownloaded {percent}% - {downloaded} of {total_size} bytes", end="", flush=True)


def _download(url: str, output_path: str, chunk_size: int,
             progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    try:
        with urllib.request.urlopen(url) as response, open(output_path, 'wb') as out_file:
            total_size = int(response.getheader('Content-Length', 0))
            downloaded = 0
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
                else:
                    _print_progress(downloaded, total_size)
            return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


def download_file(url: str, output_path: str, chunk_size: int = 8192, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """
    Download a file from URL to specified path.

    Args:
        url: The URL to download from
        output_path: Local path where file will be saved
        chunk_size: Size of chunks to download
        progress_callback: Optional callback for progress (downloaded_bytes, total_bytes)

    Returns:
        bool: True if download successful, False otherwise
    """
    # Create output directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    # Download the file in chunks
    download_status = _download(url, output_path, chunk_size, progress_callback)
    return download_status
