# Standard library imports
import os
import shutil

from tkinter import messagebox

# Type hinting
from typing import TYPE_CHECKING, List, Dict
if TYPE_CHECKING:
    from app import Main


#region FFmpegSetup


class FFmpegSetup:
    """Handles FFmpeg setup, verification, and file existence checks."""

    # Class constants for better maintainability
    FFMPEG_BUILD_PREFIX = "ffmpeg-6.0-essentials_build"


    def __init__(self, app: "Main"):
        self.app = app
        self.app_path = self.app.app_path
        self._init_paths()


    def _init_paths(self) -> None:
        """Initialize all file paths used by FFmpeg."""
        self.ffmpeg_dir = os.path.join(self.app_path, "bin", "ffmpeg")
        self.ffmpeg_exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
        self.ffprobe_exe = os.path.join(self.ffmpeg_dir, "ffprobe.exe")
        self.ffplay_exe = os.path.join(self.ffmpeg_dir, "ffplay.exe")
        self.license_file = os.path.join(self.ffmpeg_dir, "LICENSE")


#endregion
#region Utility


    def check_local_installation(self) -> bool:
        """Check if FFmpeg files exist locally."""
        return os.path.exists(self.ffmpeg_exe) and os.path.exists(self.ffprobe_exe)


    def check_system_installation(self) -> bool:
        """Check if FFmpeg is available in system PATH."""
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


    def is_available(self) -> bool:
        """Check if FFmpeg is available in the bin directory or system PATH."""
        return self.check_local_installation() or self.check_system_installation()


    def get_file_mapping(self) -> Dict[str, str]:
        """Get mapping of zip paths to local paths for FFmpeg files."""
        return {
            f"{self.FFMPEG_BUILD_PREFIX}/bin/ffmpeg.exe": self.ffmpeg_exe,
            f"{self.FFMPEG_BUILD_PREFIX}/bin/ffprobe.exe": self.ffprobe_exe,
            f"{self.FFMPEG_BUILD_PREFIX}/bin/ffplay.exe": self.ffplay_exe,
            f"{self.FFMPEG_BUILD_PREFIX}/LICENSE": self.license_file
        }


    def get_missing_files(self) -> List[str]:
        """Get list of missing FFmpeg files that need to be installed."""
        file_mapping = self.get_file_mapping()
        return [zip_path for zip_path, local_path in file_mapping.items()
                if not os.path.exists(local_path)]


    def get_missing_filenames(self) -> List[str]:
        """Get list of missing FFmpeg filenames (basename only)."""
        missing_files = self.get_missing_files()
        return [os.path.basename(file_path) for file_path in missing_files]


    def ensure_ffmpeg_directory(self) -> None:
        """Ensure the FFmpeg directory exists."""
        os.makedirs(self.ffmpeg_dir, exist_ok=True)


    def show_ffmpeg_download_dialog(self, missing_files: list) -> bool:
        """
        Show a dialog asking user if they want to download FFmpeg.

        Returns:
            bool: True if user confirms download, False if they cancel
        """
        files_list = "\n".join(missing_files)
        result = messagebox.askokcancel(
            "FFmpeg Required",
            f"FFmpeg is needed for video processing.\n\nMissing files:\n{files_list}\n\n"
            "Press OK to download (~80MB), or Cancel to exit.\n\n"
            "You can also manually add 'ffmpeg-6.0-essentials' executables to './bin/ffmpeg'",
            icon="question"
        )
        return result
