import tkinter as tk

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main

class MenuBar:
    """Manages the application menu bar."""
    def __init__(self, app: "Main"):
        self.app = app
        self.menubar = None


    def create(self):
        self.menubar = tk.Menu(self.app)
        self.app.config(menu=self.menubar)
        self._create_file_menu()
        self._create_edit_menu()
        self._create_help_menu()


    def _create_file_menu(self):
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Video...", command=self._on_open_video)
        file_menu.add_command(label="Save Settings", command=self._on_save_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Recent Files", state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app.on_closing)


    def _create_edit_menu(self):
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences...", command=self._on_preferences)
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset Settings", command=self._on_reset_settings)


    def _create_help_menu(self):
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._on_documentation)
        help_menu.add_command(label="About", command=self._on_about)


    def _on_open_video(self):
        pass


    def _on_save_settings(self):
        pass


    def _on_preferences(self):
        pass


    def _on_reset_settings(self):
        pass


    def _on_documentation(self):
        pass


    def _on_about(self):
        pass
