# Standard library imports
import ctypes
import os

# Type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main


class MainWindow:
    """Manages the main application window configuration."""
    WINDOW_TITLE = "Reav-UI"
    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 400
    WINDOW_MIN_WIDTH = 400
    WINDOW_MIN_HEIGHT = 300


    def __init__(self, app: "Main"):
        self.app = app


    def setup(self):
        self._set_appid()
        self._set_app_icon()
        self.app.title(self.WINDOW_TITLE)
        self.app.minsize(self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT)
        self._center_window()
        self.app.protocol("WM_DELETE_WINDOW", self.app.on_closing)


    def _set_appid(self):
        try:
            myappid = 'Nenotriple.reav-ui'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except AttributeError:
            pass


    def _set_app_icon(self):
        try:
            icon_path = os.path.join(self.app.app_path, 'icon.ico')
            if os.path.exists(icon_path):
                self.app.iconbitmap(icon_path)
        except Exception:
            pass


    def _center_window(self):
        self.app.update_idletasks()
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        x = (screen_width - self.WINDOW_WIDTH) // 2
        y = (screen_height - self.WINDOW_HEIGHT) // 2
        self.app.geometry(f'{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}')
        self.app.update()
