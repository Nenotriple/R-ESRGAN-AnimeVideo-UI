import os
import shutil
import threading
from pathlib import Path
from typing import Optional, Callable

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main

from .file_downloader import download_file
from .zip_utils import extract_zip


class FFmpegManager:
    """Manager class for FFmpeg operations and installation."""

    def __init__(self, app: "Main"):
        self.app = app
        self.app_path = self.app.app_path
        self.ffmpeg_dir = os.path.join(self.app.app_path, "bin", "ffmpeg")
        self.ffmpeg_exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
        self.ffprobe_exe = os.path.join(self.ffmpeg_dir, "ffprobe.exe")
        self.is_available = self._check_availability()
        self._download_thread = None


    def _check_availability(self) -> bool:
        """Check if FFmpeg is available in the bin directory or system PATH."""
        # Check local installation first
        if os.path.exists(self.ffmpeg_exe) and os.path.exists(self.ffprobe_exe):
            return True
        # Check system PATH
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


    def download_and_install_ffmpeg(self, progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Download and install FFmpeg to the bin/ffmpeg directory in a separate thread.

        Args:
            progress_callback: Optional callback for progress updates

        Note:
            This method starts a background thread and returns immediately.
            Use the progress_callback to receive status updates.
        """
        if self._download_thread and self._download_thread.is_alive():
            if progress_callback:
                progress_callback("Download already in progress...")
            return

        self._download_thread = threading.Thread(
            target=self._download_and_install_worker,
            args=(progress_callback,),
            daemon=True
        )
        self._download_thread.start()


    def _download_and_install_worker(self, progress_callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Worker method that runs in a separate thread to download and install FFmpeg.
        """
        url = "https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip"
        temp_zip_path = os.path.join(self.app_path, "bin/ffmpeg/ffmpeg-6.0-essentials_build.zip")

        def safe_callback(message: str):
            """Thread-safe wrapper for progress callback"""
            if progress_callback:
                # Schedule the callback on the main thread
                self.app.after(0, lambda: progress_callback(message))

        def download_progress_callback(downloaded: int, total_size: int):
            """Thread-safe wrapper for download progress"""
            # Schedule the progress update on the main thread
            self.app.after(0, lambda: self.app.ui_manager.status_bar.update_progress(downloaded, total_size))
            percent = downloaded * 100 // total_size if total_size else 0
            self.app.after(0, lambda: self.app.ui_manager.status_bar.update_status(f"Downloading FFmpeg... {percent}%"))

        try:
            # Create directories if they don't exist
            os.makedirs(self.ffmpeg_dir, exist_ok=True)
            safe_callback("Downloading FFmpeg...")
            # Download the zip file
            download_success = download_file(url, temp_zip_path, progress_callback=download_progress_callback)
            if not download_success:
                safe_callback("Failed to download FFmpeg")
                return
            safe_callback("Download complete. Extracting files...")
            # Extract specific files we need
            files_to_extract = [
                "ffmpeg-6.0-essentials_build/bin/ffmpeg.exe",
                "ffmpeg-6.0-essentials_build/bin/ffprobe.exe",
                "ffmpeg-6.0-essentials_build/bin/ffplay.exe",
                "ffmpeg-6.0-essentials_build/LICENSE"
            ]
            extract_success = extract_zip(
                temp_zip_path,
                self.ffmpeg_dir,
                files_to_extract,
                delete_after_extract=True,
                progress_callback=lambda f: safe_callback(f"Extracting: {Path(f).name}")
            )
            if not extract_success:
                safe_callback("Failed to extract FFmpeg")
                return
            # Update availability status
            self.is_available = self._check_availability()
            if self.is_available:
                safe_callback("FFmpeg installation completed successfully!")
            else:
                safe_callback("FFmpeg installation completed but verification failed")
        except Exception as e:
            safe_callback(f"Error during FFmpeg installation: {e}")
        finally:
            # Clean up temp file if it still exists
            if os.path.exists(temp_zip_path):
                try:
                    os.remove(temp_zip_path)
                except:
                    pass
            # Reset progress bar on main thread
            self.app.after(0, lambda: self.app.ui_manager.status_bar.update_progress(0, 100))


    def get_ffmpeg_path(self) -> Optional[str]:
        """Get the path to the FFmpeg executable."""
        if os.path.exists(self.ffmpeg_exe):
            return self.ffmpeg_exe
        return shutil.which("ffmpeg")


    def get_ffprobe_path(self) -> Optional[str]:
        """Get the path to the FFprobe executable."""
        if os.path.exists(self.ffprobe_exe):
            return self.ffprobe_exe
        return shutil.which("ffprobe")
