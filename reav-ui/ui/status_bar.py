# GUI imports
from tkinter import ttk
import tkinter as tk

# Type hinting
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
        # frame
        status_frame = ttk.Frame(parent_frame)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        # label
        self.label = ttk.Label(status_frame, textvariable=self.app.status_var)
        self.label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        # progress
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.app.status_progress_var, length=200)
        self.progress_bar.grid(row=0, column=1, sticky=tk.E)
        # Configure weights
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=2)


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


    def set_state(self, state: str):
        """Set the state of status bar widgets.

        Args:
            state: 'normal' or 'disabled'
        """
        self.label.config(state=state)
        self.progress_bar.config(state=state)
