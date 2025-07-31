from tkinter import ttk


class SettingsTab:
    """Manages the Settings tab interface."""
    def __init__(self, app):
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
