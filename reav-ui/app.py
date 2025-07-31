# Standard library imports
import os
import sys
from typing import Optional

# GUI imports
import tkinter as tk
from tkinter import ttk

# Drag and Drop
from tkinterdnd2 import TkinterDnD
BaseWindow = TkinterDnD.Tk

# Local imports
from utils.ffmpeg_utils import FFmpegManager
from ui.ui_manager import UIManager


class Main(BaseWindow):
    """Main class and handler of reav-ui."""
    def __init__(self) -> None:
        super().__init__()
        self.init_variables()
        self.ui_manager = UIManager(self)
        self.ui_manager.create_interface()
        self.ui_manager.setup_window()
        self.init_ffmpeg()


    def init_variables(self) -> None:
        """Initialize application variables and UI refs."""
        # App vars
        self.is_compiled = self.check_if_compiled()
        self.app_path = self.get_app_path()
        # UI vars
        self.status_var = tk.StringVar(value="Ready")
        self.status_progress_var = tk.DoubleVar(value=0.0)
        # UI components, initialized in ui.UIManager
        self.main_frame: Optional[ttk.Frame] = None
        self.notebook: Optional[ttk.Notebook] = None


    def init_ffmpeg(self):
        self.ffmpeg_manager = FFmpegManager(self)
        self.ffmpeg_available = self.ffmpeg_manager.is_available
        if not self.ffmpeg_available:
            user_confirmed = self.ui_manager.show_ffmpeg_download_dialog()
            if user_confirmed:
                self.ffmpeg_manager.download_and_install_ffmpeg(progress_callback=self.ui_manager.status_bar.update_status)
            else:
                self.on_closing()


    def check_if_compiled(self) -> bool:
        """Return True if running as a compiled executable, else False."""
        return getattr(sys, 'frozen', False)


    def get_app_path(self) -> str:
        """Return the application path, handling both frozen and script modes."""
        return sys._MEIPASS if self.is_compiled else os.path.dirname(__file__)


    def on_closing(self) -> None:
        """Handle application close event."""
        self.quit()


def main():
    """Main entry point for the application."""
    app = Main()
    app.mainloop()


if __name__ == "__main__":
    main()
