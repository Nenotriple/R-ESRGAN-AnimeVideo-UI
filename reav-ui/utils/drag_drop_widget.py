"""
Tkinter Drag-and-Drop Widget Module

A self-contained drag-and-drop widget that inherits from ttk.Label
With callbacks for file drop, drag enter, and drag leave events.

Usage:
    from drag_drop_widget import DragDropWidget

    def on_file_drop(file_path):
        print(f"File dropped: {file_path}")

    widget = DragDropWidget(parent, on_drop=on_file_drop)
    widget.pack()
"""

# Standard library imports
import os

# GUI imports
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

# Third-party imports
from tkinterdnd2 import DND_FILES, TkinterDnD


class DragDropWidget(tk.Label):
    """
    A reusable drag-and-drop widget that inherits from tk.Label.

    Args:
        parent: The parent widget
        on_drop: Callback function called when a file is dropped (receives file_path)
        on_drag_enter: Optional callback for drag enter event
        on_drag_leave: Optional callback for drag leave event
        text: Default text to display
        drop_text: Text to display during drag operation
        success_text: Text to display after successful drop
        browse_dialog: Whether to enable click-to-browse functionality
        state: Initial state of the widget ('normal' or 'disabled')
        **kwargs: Additional arguments passed to tk.Label
    """

    def __init__(self, parent, on_drop=None, on_drag_enter=None, on_drag_leave=None,
                 text="📁 Drop files here\n(or click to browse)",
                 drop_text="📂 Release to drop file here",
                 success_text="✓ File received!\nDrop another file here",
                 browse_dialog=True, state='normal', **kwargs):
        # Default styling
        default_kwargs = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'font': ('Arial', 12),
            'relief': 'ridge',
            'bd': 3,
            'width': 50,
            'height': 10,
            'cursor': 'hand2' if browse_dialog and state == 'normal' else 'arrow'
        }
        # Merge user kwargs with defaults
        default_kwargs.update(kwargs)
        super().__init__(parent, text=text, **default_kwargs)
        # Store configuration
        self.on_drop_callback = on_drop
        self.on_drag_enter_callback = on_drag_enter
        self.on_drag_leave_callback = on_drag_leave
        self.default_text = text
        self.drop_text = drop_text
        self.success_text = success_text
        self.browse_dialog = browse_dialog
        self.state = state
        self.setup_drag_drop()
        # Setup click to browse if enabled
        if self.browse_dialog and self.state == 'normal':
            self.bind("<Button-1>", self.open_file_dialog)


    def setup_drag_drop(self):
        """Set up drag and drop using tkinterdnd2 if available"""
        try:
            if self.state == 'normal':
                self.drop_target_register(DND_FILES)
                self.dnd_bind('<<Drop>>', self.on_drop)
                self.dnd_bind('<<DragEnter>>', self.on_drag_enter)
                self.dnd_bind('<<DragLeave>>', self.on_drag_leave)
        except Exception as e:
            print(f"Warning: Could not setup drag and drop: {e}")


    def on_drop(self, event):
        """Handle file drop event"""
        if self.state == 'disabled':
            return
        try:
            # Get the root window to access tk methods
            root = self.winfo_toplevel()
            files = root.tk.splitlist(event.data)
            if files:
                file_path = files[0]
                # Call user callback if provided
                if self.on_drop_callback:
                    self.on_drop_callback(file_path)
                # Animate success
                self.animate_success()
        except Exception as e:
            print(f"Error handling file drop: {e}")


    def on_drag_enter(self, event):
        """Handle drag enter event"""
        if self.state == 'disabled':
            return
        self.config(bg="#cce7ff", text=self.drop_text)
        if self.on_drag_enter_callback:
            self.on_drag_enter_callback(event)


    def on_drag_leave(self, event):
        """Handle drag leave event"""
        if self.state == 'disabled':
            return
        self.reset_appearance()
        if self.on_drag_leave_callback:
            self.on_drag_leave_callback(event)


    def animate_success(self):
        """Animate successful file drop"""
        self.config(bg="#ccffcc", text=self.success_text)
        self.after(2000, self.reset_appearance)


    def reset_appearance(self):
        """Reset the widget to its default appearance"""
        self.config(bg="#f0f0f0", text=self.default_text)


    def open_file_dialog(self, event):
        """Open file dialog when clicking the widget"""
        if not self.browse_dialog or self.state == 'disabled':
            return
        file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[
                ("All files", "*.*"),
                ("Text files", "*.txt"),
                ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("Video files", "*.mp4;*.avi;*.mov;*.mkv")
            ]
        )
        if file_path:
            # Call user callback if provided
            if self.on_drop_callback:
                self.on_drop_callback(file_path)
            # Animate success
            self.animate_success()


    def set_on_drop_callback(self, callback):
        """Set or change the on_drop callback function"""
        self.on_drop_callback = callback


    def set_state(self, state):
        """Set the widget state to 'normal' or 'disabled'"""
        if state not in ('normal', 'disabled'):
            raise ValueError("State must be 'normal' or 'disabled'")
        old_state = self.state
        self.state = state
        if state == 'disabled':
            # Disable appearance
            self.config(bg="#e0e0e0", fg="#888888", cursor="arrow")
            # Remove event bindings
            self.unbind("<Button-1>")
            try:
                self.drop_target_unregister()
            except:
                pass
        elif state == 'normal' and old_state == 'disabled':
            # Restore normal appearance
            self.reset_appearance()
            self.config(cursor='hand2' if self.browse_dialog else 'arrow')
            # Restore event bindings
            if self.browse_dialog:
                self.bind("<Button-1>", self.open_file_dialog)
            self.setup_drag_drop()


    def get_state(self):
        """Get the current widget state"""
        return self.state


    def get_file_info(self, file_path):
        """Utility method to get file information"""
        try:
            if not os.path.exists(file_path):
                return None
            file_name = os.path.basename(file_path)
            size_bytes = os.path.getsize(file_path)
            size_str = self.format_file_size(size_bytes)
            return {
                'path': file_path,
                'name': file_name,
                'size_bytes': size_bytes,
                'size_str': size_str
            }

        except Exception:
            return None


    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
