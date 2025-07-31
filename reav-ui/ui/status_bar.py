from tkinter import ttk
import tkinter as tk

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main

class StatusBar:
    """Manages the status bar at the bottom of the interface."""
    def __init__(self, app: "Main"):
        self.app = app
        self.label = None
        self.progress_bar = None


    def create(self, parent_frame: ttk.Frame):
        self.label = ttk.Label(parent_frame, textvariable=self.app.status_var)
        self.label.grid(row=2, column=0, sticky=(tk.W, tk.E))

        self.progress_bar = ttk.Progressbar(parent_frame, mode='determinate', variable=self.app.status_progress_var)
        self.progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))


    def update_progress(self, downloaded: int, total_size: int):
        """Update the progress bar value.

        Args:
            downloaded: Number of bytes downloaded
            total_size: Total size in bytes
        """
        percent = downloaded * 100 // total_size if total_size else 0
        self.app.status_progress_var.set(percent)
        self.app.update_idletasks()


    def update_status(self, message: str):
        """Update status with a text message."""
        self.app.status_var.set(message)