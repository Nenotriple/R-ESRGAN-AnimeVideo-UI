# Standard library imports
from typing import Optional, Callable

# Local imports
from .ffmpeg_setup import FFmpegSetup
from .ffmpeg_downloader import FFmpegDownloader
from .ffmpeg_info import FFmpegInfo

# Type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main


#region FFmpegManager


class FFmpegManager:
    """High-level manager for FFmpeg operations and installation."""

    def __init__(self, app: "Main"):
        self.app = app
        self.setup = FFmpegSetup(app)
        self.downloader = FFmpegDownloader(app, self.setup)
        self.is_available = self.setup.is_available()
        self.ffmpeg_info = FFmpegInfo(app, self.setup.ffprobe_exe)


    def refresh_availability(self) -> bool:
        """Refresh and return the current availability status."""
        self.is_available = self.setup.is_available()
        return self.is_available


    def download_and_install_ffmpeg(self, progress_callback: Optional[Callable[[str], None]] = None, completion_callback: Optional[Callable[[str], None]] = None) -> None:

        def callback(msg: str):
            # Refresh availability after download completes
            self.refresh_availability()
            if completion_callback:
                completion_callback(msg)

        self.downloader.download_and_install(progress_callback, callback)
