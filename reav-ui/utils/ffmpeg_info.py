#region Imports


import os
import json
import subprocess

from typing import TYPE_CHECKING, Optional, Dict, Any, List
if TYPE_CHECKING:
    from app import Main


#endregion
#region FFmpegInfo


class FFmpegInfo:
    """Gathers video information using ffprobe for internal use."""

    def __init__(self, app: "Main", ffprobe_path: str):
        self.app = app
        self.ffprobe_path = ffprobe_path


    #region Format Checks


    def is_supported_format(self, video_path: str) -> bool:
        """Check if the file format is supported."""
        _, ext = os.path.splitext(video_path.lower())
        return ext in self.app.supported_video_types


    #endregion
    #region Info Extraction


    def get_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get video information using ffprobe."""
        if not self.is_supported_format(video_path):
            print(f"Unsupported file format: {video_path}")
            return None
        cmd = [self.ffprobe_path, "-v", "error", "-show_entries", "format:stream", "-of", "json", video_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            print(f"Failed to get video info: {e}")
            return None


    def get_parsed_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get parsed video information in a structured format."""
        raw_info = self.get_info(video_path)
        if not raw_info:
            return None
        parsed = {
            'file_path': video_path,
            'format': self._get_format_info(raw_info),
            'streams': self._get_streams_info(raw_info),
            'video_streams': self._get_video_streams(raw_info),
            'audio_streams': self._get_audio_streams(raw_info)
        }
        return parsed


    #endregion
    #region Stream Parsing


    def _get_format_info(self, raw_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract format information."""
        format_data = raw_info.get('format', {})
        duration = float(format_data.get('duration', 0))
        size = int(format_data.get('size', 0))
        bit_rate = int(format_data.get('bit_rate', 0))
        return {
            'filename': format_data.get('filename', ''),
            'format_name': format_data.get('format_name', ''),
            'format_long_name': format_data.get('format_long_name', ''),
            'duration': duration,
            'duration_formatted': self._format_duration(duration),
            'size': size,
            'size_formatted': self._format_file_size(size),
            'bit_rate': bit_rate,
            'bit_rate_formatted': self._format_bitrate(bit_rate),
            'nb_streams': int(format_data.get('nb_streams', 0)),
            'tags': format_data.get('tags', {})
        }


    def _get_streams_info(self, raw_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all streams information."""
        streams = raw_info.get('streams', [])
        parsed_streams = []
        for stream in streams:
            bit_rate = int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else 0
            stream_info = {
                'index': stream.get('index', -1),
                'codec_name': stream.get('codec_name', ''),
                'codec_long_name': stream.get('codec_long_name', ''),
                'codec_type': stream.get('codec_type', ''),
                'duration': float(stream.get('duration', 0)),
                'bit_rate': bit_rate,
                'bit_rate_formatted': self._format_bitrate(bit_rate) if bit_rate else 'N/A'
            }
            if stream.get('codec_type') == 'video':
                stream_info.update({
                    'width': stream.get('width', 0),
                    'height': stream.get('height', 0),
                    'resolution': f"{stream.get('width', 0)}x{stream.get('height', 0)}",
                    'pix_fmt': stream.get('pix_fmt', ''),
                    'profile': stream.get('profile', ''),
                    'level': stream.get('level', ''),
                    'r_frame_rate': stream.get('r_frame_rate', ''),
                    'avg_frame_rate': stream.get('avg_frame_rate', ''),
                    'framerate_formatted': self._format_framerate(stream.get('r_frame_rate', '') or stream.get('avg_frame_rate', '')),
                    'nb_frames': stream.get('nb_frames', ''),
                    'color_range': stream.get('color_range', ''),
                    'display_aspect_ratio': stream.get('display_aspect_ratio', ''),
                    'sample_aspect_ratio': stream.get('sample_aspect_ratio', '')
                })
            elif stream.get('codec_type') == 'audio':
                stream_info.update({
                    'sample_rate': stream.get('sample_rate', ''),
                    'channels': stream.get('channels', 0),
                    'channel_layout': stream.get('channel_layout', ''),
                    'sample_fmt': stream.get('sample_fmt', ''),
                    'profile': stream.get('profile', '')
                })
            parsed_streams.append(stream_info)
        return parsed_streams


    def _get_video_streams(self, raw_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract only video streams."""
        return [s for s in self._get_streams_info(raw_info) if s['codec_type'] == 'video']


    def _get_audio_streams(self, raw_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract only audio streams."""
        return [s for s in self._get_streams_info(raw_info) if s['codec_type'] == 'audio']


    #endregion
    #region Formatting


    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS.mmm format."""
        if seconds <= 0:
            return "00:00:00"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in bytes to human-readable format."""
        if size_bytes == 0:
            return "0 B"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.2f} {units[unit_index]}"


    def _format_bitrate(self, bitrate: int) -> str:
        """Format bitrate to human-readable format."""
        if bitrate == 0:
            return "0 bps"
        if bitrate >= 1000000:
            return f"{bitrate / 1000000:.2f} Mbps"
        elif bitrate >= 1000:
            return f"{bitrate / 1000:.0f} kbps"
        else:
            return f"{bitrate} bps"


    def _format_framerate(self, framerate_str: str) -> str:
        """Format framerate fraction to decimal."""
        if not framerate_str or framerate_str == '0/0':
            return 'N/A'
        try:
            if '/' in framerate_str:
                num, den = framerate_str.split('/')
                fps = float(num) / float(den)
                return f"{fps:.2f} fps"
            else:
                return f"{float(framerate_str):.2f} fps"
        except (ValueError, ZeroDivisionError):
            return 'N/A'


    #endregion
    #region Summary


    def get_summary(self, video_path: str) -> Optional[tuple[str, Dict[str, Any]]]:
        """Get a formatted summary of video information."""
        info = self.get_parsed_info(video_path)
        if not info:
            return None

        format_info = info['format']
        video_streams = info['video_streams']
        audio_streams = info['audio_streams']

        summary = []
        summary_dict = {
            'file': {
                'name': os.path.basename(format_info['filename']),
                'format': format_info['format_long_name'],
                'duration': format_info['duration'],
                'duration_formatted': format_info['duration_formatted'],
                'size': format_info['size'],
                'size_formatted': format_info['size_formatted'],
                'bitrate': format_info['bit_rate'],
                'bitrate_formatted': format_info['bit_rate_formatted'],
                'streams_total': format_info['nb_streams']
            }
        }

        summary.append(f"File: {os.path.basename(format_info['filename'])}")
        summary.append(f"Format: {format_info['format_long_name']}")
        summary.append(f"Duration: {format_info['duration_formatted']}")
        summary.append(f"Size: {format_info['size_formatted']}")
        summary.append(f"Overall Bitrate: {format_info['bit_rate_formatted']}")
        summary.append(f"Streams: {format_info['nb_streams']} total")

        if video_streams:
            v = video_streams[0]
            summary_dict['video'] = {
                'codec': v['codec_name'],
                'codec_long_name': v['codec_long_name'],
                'width': v['width'],
                'height': v['height'],
                'resolution': v['resolution'],
                'framerate_formatted': v['framerate_formatted'],
                'bitrate': v['bit_rate'],
                'bitrate_formatted': v['bit_rate_formatted'],
                'frame_count': v.get('nb_frames'),
                'color_range': v.get('color_range'),
                'profile': v.get('profile')
            }

            summary.append(f"\nVideo: {v['codec_name']} ({v['codec_long_name']})")
            summary.append(f"  Resolution: {v['resolution']}")
            summary.append(f"  Framerate: {v['framerate_formatted']}")
            if v.get('nb_frames'):
                summary.append(f"  Frame Count: {v['nb_frames']}")
            if v.get('color_range'):
                summary.append(f"  Color Range: {v['color_range']}")
            summary.append(f"  Bitrate: {v['bit_rate_formatted']}")
            if v.get('profile'):
                summary.append(f"  Profile: {v['profile']}")

        if audio_streams:
            a = audio_streams[0]
            summary_dict['audio'] = {
                'codec': a['codec_name'],
                'codec_long_name': a['codec_long_name'],
                'sample_rate': a.get('sample_rate'),
                'channels': a.get('channels'),
                'bitrate': a['bit_rate'],
                'bitrate_formatted': a['bit_rate_formatted']
            }

            summary.append(f"\nAudio: {a['codec_name']} ({a['codec_long_name']})")
            summary.append(f"  Sample Rate: {a.get('sample_rate', 'N/A')} Hz")
            summary.append(f"  Channels: {a.get('channels', 'N/A')}")
            summary.append(f"  Bitrate: {a['bit_rate_formatted']}")

        return ("\n".join(summary), summary_dict)


    #endregion


#endregion
