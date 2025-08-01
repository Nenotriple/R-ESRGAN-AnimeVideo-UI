# GUI imports
from tkinter import ttk
import tkinter as tk

# Type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main


class SettingsTab:
    """Manages the Settings tab interface."""
    def __init__(self, app: "Main"):
        self.app = app
        self.frame = None


    def create(self, notebook: ttk.Notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Settings")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self._create_content()


    def _create_content(self):
        placeholder_label = ttk.Label(self.frame, text="Settings tab content will go here")
        placeholder_label.grid(row=0, column=0)


    def set_state(self, state: str):
        """Set the state of settings tab widgets.

        Args:
            state: 'normal' or 'disabled'
        """
        for widget in self.frame.winfo_children():
            if hasattr(widget, 'config'):
                try:
                    widget.config(state=state)
                except tk.TclError:
                    pass
