# Standard library imports
import os

# GUI imports
from tkinter import ttk
import tkinter as tk

# Local imports
from utils.drag_drop_widget import DragDropWidget

# Type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main


class SelectionTab:
    """Manages the Selection tab interface."""
    def __init__(self, app: "Main"):
        self.app = app
        self.frame = None
        self.drag_drop_widget = None


    def create(self, notebook: ttk.Notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Selection")
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self._create_content()


    def _create_content(self):
        # Title
        self.title_label = ttk.Label(self.frame, text="Video Selection", font=('Arial', 14, 'bold'))
        self.title_label.grid(row=0, column=0, pady=(10, 5), sticky=(tk.W, tk.E))
        # Drop target
        self.drag_drop_widget = DragDropWidget(
            self.frame,
            on_drop=self._on_file_dropped,
            text="📁 Drop video files here\n(or click to browse)",
            drop_text="📂 Release to drop video file here",
            success_text="✓ Video file loaded!\nDrop another file here"
        )
        self.drag_drop_widget.grid(row=1, column=0, padx=20, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        # File info
        self.file_info_label = ttk.Label(self.frame, text="No file selected")
        self.file_info_label.grid(row=2, column=0, pady=(0, 10), sticky=(tk.W, tk.E))


    def _on_file_dropped(self, file_path):
        self.app.status_var.set(f"File selected: {os.path.basename(file_path)}")
        file_info = self.drag_drop_widget.get_file_info(file_path)
        if file_info:
            info_text = f"Selected: {file_info['name']} ({file_info['size_str']})"
            self.file_info_label.config(text=info_text)
        else:
            self.file_info_label.config(text="Error reading file info")


    def set_state(self, state: str):
        """Set the state of selection tab widgets.

        Args:
            state: 'normal' or 'disabled'
        """
        self.drag_drop_widget.set_state(state)
        self.title_label.config(state=state)
        self.file_info_label.config(state=state)
