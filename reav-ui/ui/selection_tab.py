# Standard library imports
import os

# GUI imports
from tkinter import ttk
import tkinter as tk

# Local imports
from ui.widget import FileViewWidget

# Type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main


class SelectionTab:
    """Manages the Selection tab interface."""
    def __init__(self, app: "Main"):
        self.app = app
        self.frame = None
        self.file_view_widget = None


    def create(self, notebook: ttk.Notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Selection")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self._create_content()


    def _create_content(self):
        # Label frame for file selection
        self.selection_labelframe = ttk.LabelFrame(self.frame, text="File Selection")
        self.selection_labelframe.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.selection_labelframe.grid_rowconfigure(0, weight=1)
        self.selection_labelframe.grid_columnconfigure(0, weight=1)
        # File view widget
        self.file_view_widget = FileViewWidget(self.selection_labelframe)
        self.file_view_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self.file_view_widget.bind_selection_event(self._on_selection_changed)
        # File info
        self.file_info_label = ttk.Label(self.selection_labelframe, text="No file selected")
        self.file_info_label.grid(row=1, column=0, sticky=(tk.W, tk.E))


    def _on_selection_changed(self, event=None):
        selected_files = self.file_view_widget.get_selected_files()
        if selected_files:
            file_info = selected_files[0]
            info_text = f"Selected: {file_info['name']} ({file_info['size']})"
            self.file_info_label.config(text=info_text)
        else:
            self.file_info_label.config(text="No file selected")


    def set_state(self, state: str):
        """Set the state of selection tab widgets.

        Args:
            state: 'normal' or 'disabled'
        """
        self.file_view_widget.set_state(state)
        self.file_info_label.config(state=state)
