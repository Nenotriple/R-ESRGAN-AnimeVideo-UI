# Standard library imports
import os
import shutil
import threading
from pathlib import Path

# Local imports
from .file_downloader import download_file
from .zip_utils import extract_zip

# Type hinting
from typing import TYPE_CHECKING, Optional, Callable, List
if TYPE_CHECKING:
    from app import Main


#endregion
#region FFMPEGManager


class FFmpegManager:
    """Manager class for FFmpeg operations and installation."""


    # Class constants for better maintainability
    FFMPEG_DOWNLOAD_URL = "https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip"
    FFMPEG_ZIP_NAME = "ffmpeg-6.0-essentials_build.zip"
    FFMPEG_BUILD_PREFIX = "ffmpeg-6.0-essentials_build"


    def __init__(self, app: "Main"):
        self.app = app
        self.app_path = self.app.app_path
        self._init_paths()
        self.is_available = self._check_availability()
        self._download_thread = None


    def _init_paths(self) -> None:
        """Initialize all file paths used by FFmpeg."""
        self.ffmpeg_dir = os.path.join(self.app_path, "bin", "ffmpeg")
        self.ffmpeg_exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
        self.ffprobe_exe = os.path.join(self.ffmpeg_dir, "ffprobe.exe")
        self.ffplay_exe = os.path.join(self.ffmpeg_dir, "ffplay.exe")
        self.license_file = os.path.join(self.ffmpeg_dir, "LICENSE")


    def _check_local_installation(self) -> bool:
        """Check if FFmpeg files exist locally."""
        return os.path.exists(self.ffmpeg_exe) and os.path.exists(self.ffprobe_exe)


    def _check_system_installation(self) -> bool:
        """Check if FFmpeg is available in system PATH."""
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


    def _check_availability(self) -> bool:
        """Check if FFmpeg is available in the bin directory or system PATH."""
        return self._check_local_installation() or self._check_system_installation()


#region Download Utility


    def _get_file_mapping(self) -> dict[str, str]:
        """Get mapping of zip paths to local paths for FFmpeg files."""
        return {
            f"{self.FFMPEG_BUILD_PREFIX}/bin/ffmpeg.exe": self.ffmpeg_exe,
            f"{self.FFMPEG_BUILD_PREFIX}/bin/ffprobe.exe": self.ffprobe_exe,
            f"{self.FFMPEG_BUILD_PREFIX}/bin/ffplay.exe": self.ffplay_exe,
            f"{self.FFMPEG_BUILD_PREFIX}/LICENSE": self.license_file
        }


    def _get_missing_files(self) -> List[str]:
        """Get list of missing FFmpeg files that need to be installed."""
        file_mapping = self._get_file_mapping()
        return [zip_path for zip_path, local_path in file_mapping.items()
                if not os.path.exists(local_path)]


    def _is_download_in_progress(self) -> bool:
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
            self.ffmpeg_dir,
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
        temp_zip_path = os.path.join(self.app_path, f"bin/ffmpeg/{self.FFMPEG_ZIP_NAME}")
        safe_callback = self._create_thread_safe_callback(progress_callback)
        safe_completion_callback = self._create_thread_safe_callback(completion_callback)
        try:
            # Create directories and check for missing files
            os.makedirs(self.ffmpeg_dir, exist_ok=True)
            missing_files = self._get_missing_files()
            if not missing_files:
                self.is_available = True
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
            self.is_available = self._check_availability()
            completion_message = "FFmpeg installation completed successfully!"
            if self.is_available:
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
#region Download Process


    def download_and_install_ffmpeg(self, progress_callback: Optional[Callable[[str], None]] = None, completion_callback: Optional[Callable[[str], None]] = None) -> None:
        """Download and install FFmpeg to the bin/ffmpeg directory.
        Args:
            progress_callback: Optional callback for progress updates
            completion_callback: Optional callback called when download/extract is finished
        Note:
            This method starts a background thread and returns immediately.
            Use the progress_callback to receive status updates.
        """
        if self._is_download_in_progress():
            if progress_callback:
                progress_callback("Download already in progress...")
            return
        self._download_thread = threading.Thread(target=self._download_and_install_thread, args=(progress_callback, completion_callback), daemon=True)
        self._download_thread.start()


#endregion
#region FFmpeg Utility


    def _get_executable_path(self, local_exe_path: str, exe_name: str) -> Optional[str]:
        """Get the path to an executable, checking local installation first."""
        if os.path.exists(local_exe_path):
            return local_exe_path
        return shutil.which(exe_name)


    def get_ffmpeg_path(self) -> Optional[str]:
        """Get the path to the FFmpeg executable."""
        return self._get_executable_path(self.ffmpeg_exe, "ffmpeg")


    def get_ffprobe_path(self) -> Optional[str]:
        """Get the path to the FFprobe executable."""
        return self._get_executable_path(self.ffprobe_exe, "ffprobe")
