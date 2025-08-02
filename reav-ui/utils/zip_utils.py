# Standard library imports
import zipfile
from pathlib import Path

# Type hinting
from typing import Optional, Callable, List


#region Utility


def _get_extraction_files(archive: zipfile.ZipFile, files: Optional[List[str]]) -> List[str]:
    """Get list of files to extract from the archive."""
    if files is not None:
        return [f for f in files if f in archive.namelist()]
    return archive.namelist()


def _extract_file(archive: zipfile.ZipFile, file: str, extract_to: str) -> None:
    """Extract a single file from the archive to target directory."""
    with archive.open(file) as source:
        target_path = Path(extract_to) / Path(file).name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, 'wb') as target:
            target.write(source.read())


def _delete_zip_file(zip_path: str) -> None:
    """Safely delete the zip file."""
    try:
        Path(zip_path).unlink()
    except Exception as e:
        print(f"Failed to delete zip file {zip_path}: {e}")


#endregion
#region Process


def extract_zip(zip_path: str, extract_to: str, files: Optional[List[str]] = None, delete_after_extract: bool = False, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
    """Extract a zip file to the specified directory.
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
            extraction_files = _get_extraction_files(archive, files)

            for file in extraction_files:
                _extract_file(archive, file, extract_to)
                if progress_callback:
                    progress_callback(file)
        return True
    except Exception as e:
        print(f"Zip extraction failed: {e}")
        return False
    finally:
        if delete_after_extract:
            _delete_zip_file(zip_path)
