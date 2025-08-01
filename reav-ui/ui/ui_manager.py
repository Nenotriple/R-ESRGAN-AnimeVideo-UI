from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main

from .main_window import MainWindow
from .menu_bar import MenuBar
from .selection_tab import SelectionTab
from .settings_tab import SettingsTab
from .status_bar import StatusBar

import tkinter as tk
from tkinter import messagebox


class UIManager:
    """Manages the user interface for the application."""
    def __init__(self, app: "Main"):
        self.app = app
        self.main_window = None
        self.menubar = None
        self.selection_tab = None
        self.settings_tab = None
        self.status_bar = None


    def initialize(self, app: "Main"):
        self.app = app


    def create_interface(self):
        self._setup_main_frame()
        self.menubar = MenuBar(self.app)
        self.selection_tab = SelectionTab(self.app)
        self.settings_tab = SettingsTab(self.app)
        self.status_bar = StatusBar(self.app)
        self.menubar.create()
        self._create_tabbed_interface()
        self.status_bar.create(self.app.main_frame)


    def setup_window(self):
        self.main_window = MainWindow(self.app)
        self.main_window.setup()


    def _setup_main_frame(self):
        from tkinter import ttk
        self.app.main_frame = ttk.Frame(self.app)
        self.app.main_frame.grid(row=0, column=0, sticky=("w", "e", "n", "s"))
        self.app.grid_rowconfigure(0, weight=1)
        self.app.grid_columnconfigure(0, weight=1)
        self.app.main_frame.grid_rowconfigure(0, weight=1)
        self.app.main_frame.grid_columnconfigure(0, weight=1)


    def _create_tabbed_interface(self):
        from tkinter import ttk
        notebook = ttk.Notebook(self.app.main_frame)
        notebook.grid(row=0, column=0, sticky=("w", "e", "n", "s"))
        self.selection_tab.create(notebook)
        self.settings_tab.create(notebook)
        self.app.notebook = notebook


    def show_ffmpeg_download_dialog(self, missing_files: list) -> bool:
        """
        Show a dialog asking user if they want to download FFmpeg.

        Returns:
            bool: True if user confirms download, False if they cancel
        """
        files_list = "\n".join(missing_files)
        result = messagebox.askokcancel(
            "FFmpeg Required",
            f"FFmpeg is required for video processing but was not found on your system.\n\n"
            f"The following files are missing:\n{files_list}\n\n"
            "Press OK to download and install FFmpeg locally.\n"
            "(This will download approximately ~80MB)",
            icon="question"
        )
        return result
