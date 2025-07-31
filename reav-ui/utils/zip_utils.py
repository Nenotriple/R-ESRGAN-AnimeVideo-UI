import zipfile
from pathlib import Path
from typing import Optional, Callable, List


def extract_zip(
    zip_path: str,
    extract_to: str,
    files: Optional[List[str]] = None,
    delete_after_extract: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None
) -> bool:
    """
    Extract a zip file to the specified directory.

    Args:
        zip_path: Path to the zip file.
        extract_to: Directory to extract files to.
        files: Optional list of file names to extract. If None, extract all.
        delete_after_extract: Whether to delete the zip file after extraction.
        progress_callback: Optional callback called with each file name.

    Returns:
        bool: True if extraction succeeds, False otherwise.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as archive:
            if files is not None:
                members = [f for f in files if f in archive.namelist()]
            else:
                members = archive.namelist()
            for member in members:
                # Extract file content and write to target directory with just the filename
                with archive.open(member) as source:
                    target_path = Path(extract_to) / Path(member).name
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'wb') as target:
                        target.write(source.read())
                if progress_callback:
                    progress_callback(member)
        return True
    except Exception as e:
        print(f"Zip extraction failed: {e}")
        return False
    finally:
        if delete_after_extract:
            try:
                Path(zip_path).unlink()
            except Exception as e:
                print(f"Failed to delete zip file {zip_path}: {e}")


# Example usage
#if __name__ == "__main__":
#    zip_file = "downloads/ffmpeg-6.0-essentials_build.zip"
#    extract_dir = "bin/ffmpeg"
#    # Extract all files
#    #success = extract_zip(zip_file, extract_dir, progress_callback=lambda f: print(f"Extracted: {f}"))
#    # Extract specific files
#    files = ["ffmpeg-6.0-essentials_build/bin/ffmpeg.exe", "ffmpeg-6.0-essentials_build/bin/ffprobe.exe", "ffmpeg-6.0-essentials_build/bin/ffplay.exe", "ffmpeg-6.0-essentials_build/LICENSE"]
#    success = extract_zip(zip_file, extract_dir, files, delete_after_extract=True, progress_callback=lambda f: print(f"Extracted: {f}"))
