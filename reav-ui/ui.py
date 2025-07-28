#region - Imports


# Standard library imports
import ctypes
import os

# Standard GUI
import tkinter as tk
from tkinter import ttk

# Type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import Main


#endregion
#region - UI Manager Class


class UIManager:
    """Manages the user interface for the application."""
    def __init__(self, app: 'Main' = None):
        """Initialize the UI manager."""
        self.app = app


    def initialize(self, app: 'Main'):
        """Initialize the UI manager with an app reference."""
        self.app = app


    def create_interface(self):
        """Create the main user interface."""
        _setup_main_frame(self.app)
        _create_menubar(self.app)
        _create_tabbed_interface(self.app)
        _create_status_bar(self.app)


    def setup_window(self):
        """Configure the main application window."""
        # Window settings
        WINDOW_TITLE = "Reav-UI"
        WINDOW_WIDTH = 600
        WINDOW_HEIGHT = 400
        WINDOW_MIN_WIDTH = 400
        WINDOW_MIN_HEIGHT = 300
        # Setup properties
        _set_appid(self.app)
        _set_app_icon(self.app)
        self.app.title(WINDOW_TITLE)
        self.app.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        # Center window
        screen_width = self.app.winfo_screenwidth()
        screen_height = self.app.winfo_screenheight()
        x = (screen_width - WINDOW_WIDTH) // 2
        y = (screen_height - WINDOW_HEIGHT) // 2
        self.app.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}')
        # Close protocol
        self.app.protocol("WM_DELETE_WINDOW", self.app.on_closing)


def _set_appid(app: 'Main'):
    """Set the application user model ID for Windows taskbar grouping."""
    try:
        myappid = 'Nenotriple.reav-ui'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except AttributeError:
        # Not Windows
        pass


def _set_app_icon(app: 'Main'):
    """Set the application icon from icon.ico file in app path."""
    try:
        icon_path = os.path.join(app.app_path, 'icon.ico')
        if os.path.exists(icon_path):
            app.iconbitmap(icon_path)
    except Exception:
        pass


# Create a global instance
ui_manager = UIManager()


#endregion
#region - Main Frame Setup


def _setup_main_frame(app: 'Main'):
    """Setup the main frame and configure grid weights."""
    # Main frame
    app.main_frame = ttk.Frame(app, padding="10")
    app.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    # Configure grid weights for responsiveness
    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)
    app.main_frame.grid_rowconfigure(0, weight=1)
    app.main_frame.grid_columnconfigure(0, weight=1)



#endregion
#region - Menubar


def _create_menubar(app: 'Main'):
    """Create the main menubar."""
    # Create menubar
    menubar = tk.Menu(app)
    app.config(menu=menubar)
    # Menus
    _create_file_menu(app, menubar)
    _create_edit_menu(app, menubar)
    _create_help_menu(app, menubar)


def _create_file_menu(app: 'Main', menubar: tk.Menu):
    """Create the File menu."""
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Open Video...", command=lambda: None)
    file_menu.add_command(label="Save Settings", command=lambda: None)
    file_menu.add_separator()
    file_menu.add_command(label="Recent Files", state="disabled")
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=app.on_closing)


def _create_edit_menu(app: 'Main', menubar: tk.Menu):
    """Create the Edit menu."""
    edit_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Edit", menu=edit_menu)
    edit_menu.add_command(label="Preferences...", command=lambda: None)
    edit_menu.add_separator()
    edit_menu.add_command(label="Reset Settings", command=lambda: None)


def _create_help_menu(app: 'Main', menubar: tk.Menu):
    """Create the Help menu."""
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="Documentation", command=lambda: None)
    help_menu.add_command(label="About", command=lambda: None)


#endregion
#region - Tabbed Interface


def _create_tabbed_interface(app: 'Main'):
    """Create the main tabbed interface."""
    # Create notebook widget for tabs
    notebook = ttk.Notebook(app.main_frame)
    notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

    # Create tabs
    _create_select_video_tab(app, notebook)
    _create_settings_tab(app, notebook)

    # Store reference to notebook
    app.notebook = notebook


def _create_select_video_tab(app: 'Main', notebook: ttk.Notebook):
    """Create the Select Video tab."""
    # Create tab frame
    video_frame = ttk.Frame(notebook)
    notebook.add(video_frame, text="Select Video")

    # Configure grid weights
    video_frame.grid_rowconfigure(0, weight=1)
    video_frame.grid_columnconfigure(0, weight=1)

    # Placeholder content
    placeholder_label = ttk.Label(video_frame, text="Select Video tab content will go here")
    placeholder_label.grid(row=0, column=0, padx=20, pady=20)


def _create_settings_tab(app: 'Main', notebook: ttk.Notebook):
    """Create the Settings tab."""
    # Create tab frame
    settings_frame = ttk.Frame(notebook)
    notebook.add(settings_frame, text="Settings")

    # Configure grid weights
    settings_frame.grid_rowconfigure(0, weight=1)
    settings_frame.grid_columnconfigure(0, weight=1)

    # Placeholder content
    placeholder_label = ttk.Label(settings_frame, text="Settings tab content will go here")
    placeholder_label.grid(row=0, column=0, padx=20, pady=20)


#endregion
#region - Status Bar


def _create_status_bar(app: 'Main'):
    """Create the status bar at the bottom of the interface."""
    # Status bar
    app.status_label = ttk.Label(app.main_frame, textvariable=app.status_var)
    app.status_label.grid(row=2, column=0, sticky=(tk.W, tk.E))


#endregion
