# Standard library imports
import os
import sys
import ctypes
from typing import Optional

# GUI imports
import tkinter as tk
from tkinter import ttk

# Local imports
from ffmpeg_utils import ffmpeg_manager


class Application:
    """Main application class for a Python/Tkinter GUI."""
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application with the root Tkinter window."""
        self.root = root
        self.initialize_variables()
        self.create_interface()
        self.setup_window()


    def initialize_variables(self) -> None:
        """Initialize application variables and UI components."""
        # Application variables
        self.status_var = tk.StringVar(value="Ready")
        # UI components (initialized in create_interface)
        self.status_label: Optional[ttk.Label] = None
        self.main_frame: Optional[ttk.Frame] = None
        # Application state
        self.is_compiled = self.check_if_compiled()
        # Application paths
        self.app_path = self.get_app_path()
        # FFmpeg availability
        self.ffmpeg_available = ffmpeg_manager.is_available


    def create_interface(self) -> None:
        """Create the main user interface."""
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Configure grid weights for responsiveness
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        # Status bar
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.grid(row=2, column=0, sticky=(tk.W, tk.E))


    def setup_window(self) -> None:
        """Configure the main application window."""
        # Window settings
        WINDOW_TITLE = "Reav-UI"
        WINDOW_WIDTH = 600
        WINDOW_HEIGHT = 400
        WINDOW_MIN_WIDTH = 400
        WINDOW_MIN_HEIGHT = 300
        # Setup properties
        self.set_appid()
        self.root.title(WINDOW_TITLE)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}')
        # Close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


    def set_appid(self) -> None:
        """Set the application user model ID for Windows taskbar grouping."""
        try:
            myappid = 'Nenotriple.reav-ui'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except AttributeError:
            # Not Windows
            pass


    def check_if_compiled(self) -> bool:
        """Return True if running as a compiled executable, else False."""
        return getattr(sys, 'frozen', False)


    def get_app_path(self) -> str:
        """Return the application path, handling both frozen and script modes."""
        return sys._MEIPASS if self.is_compiled else os.path.dirname(__file__)


    def on_closing(self) -> None:
        """Handle application close event."""
        self.root.quit()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
