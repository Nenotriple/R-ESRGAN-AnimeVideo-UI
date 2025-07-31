"""
FFmpeg utilities for video processing in reav-ui.

This module provides convenient functions for working with ffmpeg and ffprobe
for video extraction, processing, and merging operations.
"""

import os
import sys
import subprocess
from typing import Optional, List, Dict, Any
import ffmpeg


class FFmpegManager:
    """Manager class for FFmpeg operations."""
    def __init__(self):
        """Initialize FFmpeg manager with path detection."""
        self.ffmpeg_path = self._find_executable("ffmpeg")
        self.ffprobe_path = self._find_executable("ffprobe")
        self.is_available = self.ffmpeg_path is not None and self.ffprobe_path is not None


    def _get_base_path(self) -> str:
        """Get base path for executable search."""
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        else:
            return os.path.dirname(__file__)


    def _find_executable(self, exe_name: str) -> Optional[str]:
        """Find executable path (generic method for both ffmpeg and ffprobe)."""
        base_path = self._get_base_path()
        # Check local resrgan folder first
        local_exe = os.path.join(base_path, "resrgan", f"{exe_name}.exe")
        if os.path.exists(local_exe):
            return local_exe
        # Check system PATH
        try:
            result = subprocess.run([f"where", exe_name], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        return None


    def _ensure_available(self) -> None:
        """Ensure FFmpeg is available, raise error if not."""
        if not self.is_available:
            raise RuntimeError("FFmpeg/FFprobe not available")


    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using ffprobe."""
        self._ensure_available()
        try:
            probe = ffmpeg.probe(video_path, cmd=self.ffprobe_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if video_stream is None:
                raise ValueError("No video stream found")
            return {
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']),
                'duration': float(probe['format']['duration']),
                'codec': video_stream['codec_name'],
                'format': probe['format']['format_name']
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get video info: {e}")


    def _run_ffmpeg_operation(self, operation_func, error_message: str) -> bool:
        """Generic method to run FFmpeg operations with error handling."""
        self._ensure_available()
        try:
            operation_func()
            return True
        except Exception as e:
            print(f"{error_message}: {e}")
            return False


    def extract_frames(self, video_path: str, output_dir: str, format: str = "png") -> bool:
        """Extract frames from video to specified directory."""
        def operation():
            os.makedirs(output_dir, exist_ok=True)
            output_pattern = os.path.join(output_dir, f"frame_%06d.{format}")
            (
                ffmpeg
                .input(video_path, **{'hwaccel': 'auto'})
                .output(output_pattern, **{'q:v': 1})
                .global_args('-loglevel', 'error')
                .run(cmd=self.ffmpeg_path, overwrite_output=True)
            )
        return self._run_ffmpeg_operation(operation, "Error extracting frames")


    def create_video_from_frames(self, frames_dir: str, output_path: str, fps: float = 30.0, format: str = "mp4") -> bool:
        """Create video from frames directory."""
        def operation():
            frame_pattern = os.path.join(frames_dir, "frame_%06d.png")
            (
                ffmpeg
                .input(frame_pattern, framerate=fps)
                .output(output_path, **{
                    'c:v': 'libx264',
                    'pix_fmt': 'yuv420p',
                    'crf': 18
                })
                .global_args('-loglevel', 'error')
                .run(cmd=self.ffmpeg_path, overwrite_output=True)
            )
        return self._run_ffmpeg_operation(operation, "Error creating video")


    def get_supported_formats(self) -> List[str]:
        """Get list of supported video formats."""
        return ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.webm', '.m4v', '.gif']


# Global instance for easy access
ffmpeg_manager = FFmpegManager()
