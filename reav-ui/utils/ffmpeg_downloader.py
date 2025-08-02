# Standard library imports
import os
import threading
from pathlib import Path
from typing import Optional, Callable, List

# Local imports
from .file_downloader import download_file
from .zip_utils import extract_zip

# Type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main
    from .ffmpeg_setup import FFmpegSetup


#region FFmpegDownloader


class FFmpegDownloader:
    """Handles FFmpeg download and extraction operations."""


    FFMPEG_DOWNLOAD_URL = "https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip"
    FFMPEG_ZIP_NAME = "ffmpeg-6.0-essentials_build.zip"


    def __init__(self, app: "Main", ffmpeg_setup: "FFmpegSetup"):
        self.app = app
        self.ffmpeg_setup = ffmpeg_setup
        self._download_thread = None


#endregion
#region Utility


    def is_download_in_progress(self) -> bool:
        """Check if a download is already in progress."""
        return self._download_thread and self._download_thread.is_alive()


    def _create_thread_safe_callback(self, callback: Optional[Callable[[str], None]]) -> Callable[[str], None]:
        """Create thread-safe wrapper for callbacks."""
        def safe_callback(message: str):
            if callback:
                self.app.after(0, lambda: callback(message))
        return safe_callback


    def _create_download_progress_callback(self) -> Callable[[int, int], None]:
        """Create thread-safe callback for download progress updates."""
        def download_progress_callback(downloaded: int, total_size: int):
            percent = downloaded * 100 // total_size if total_size else 0
            self.app.after(0, lambda: self.app.ui_manager.status_bar.update_progress(downloaded, total_size))
            self.app.after(0, lambda: self.app.ui_manager.status_bar.update_status(f"Downloading '{self.FFMPEG_ZIP_NAME}'... {percent}%"))
        return download_progress_callback


    def _perform_download(self, temp_zip_path: str, safe_callback: Callable[[str], None]) -> bool:
        """Perform the actual download operation."""
        download_progress_callback = self._create_download_progress_callback()
        return download_file(self.FFMPEG_DOWNLOAD_URL, temp_zip_path, progress_callback=download_progress_callback)


    def _perform_extraction(self, temp_zip_path: str, missing_files: List[str], safe_callback: Callable[[str], None]) -> bool:
        """Perform the extraction operation."""
        return extract_zip(
            temp_zip_path,
            self.ffmpeg_setup.ffmpeg_dir,
            missing_files,
            delete_after_extract=True,
            progress_callback=lambda f: safe_callback(f"Extracting: {Path(f).name}")
        )


    def _cleanup_temp_file(self, temp_zip_path: str) -> None:
        """Clean up temporary zip file if it exists."""
        if os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except Exception:
                pass


    def _reset_progress_bar(self) -> None:
        """Reset the progress bar on the main thread."""
        self.app.after(0, lambda: self.app.ui_manager.status_bar.update_progress(0, 100))


    def _download_and_install_thread(self, progress_callback: Optional[Callable[[str], None]] = None, completion_callback: Optional[Callable[[str], None]] = None) -> None:
        """Method to download and install FFmpeg."""
        temp_zip_path = os.path.join(self.ffmpeg_setup.ffmpeg_dir, self.FFMPEG_ZIP_NAME)
        safe_callback = self._create_thread_safe_callback(progress_callback)
        safe_completion_callback = self._create_thread_safe_callback(completion_callback)
        try:
            # Create directories and check for missing files
            self.ffmpeg_setup.ensure_ffmpeg_directory()
            missing_files = self.ffmpeg_setup.get_missing_files()
            if not missing_files:
                safe_callback("All FFmpeg files are already present")
                safe_completion_callback("FFmpeg installation already complete")
                return
            # Download
            safe_callback(f"Missing {len(missing_files)} FFmpeg files. Downloading...")
            if not self._perform_download(temp_zip_path, safe_callback):
                safe_callback("Failed to download FFmpeg")
                return
            # Extraction
            safe_callback("Download complete. Extracting missing files...")
            if not self._perform_extraction(temp_zip_path, missing_files, safe_callback):
                safe_callback("Failed to extract FFmpeg")
                return
            # Verification
            completion_message = "FFmpeg installation completed successfully!"
            if self.ffmpeg_setup.is_available():
                safe_callback(completion_message)
                safe_completion_callback(completion_message)
            else:
                safe_callback("FFmpeg installation completed but verification failed")
        except Exception as e:
            safe_callback(f"Error during FFmpeg installation: {e}")
        finally:
            self._cleanup_temp_file(temp_zip_path)
            self._reset_progress_bar()


#endregion
#region Process


    def download_and_install(self, progress_callback: Optional[Callable[[str], None]] = None, completion_callback: Optional[Callable[[str], None]] = None) -> None:
        """Download and install FFmpeg to the bin/ffmpeg directory.

        Args:
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback called when download/extract is finished

        Note:
            This method starts a background thread and returns immediately.
            Use the progress_callback to receive status updates.
        """
        if self.is_download_in_progress():
            if progress_callback:
                progress_callback("Download already in progress...")
            return

        self._download_thread = threading.Thread(target=self._download_and_install_thread, args=(progress_callback, completion_callback), daemon=True)
        self._download_thread.start()
