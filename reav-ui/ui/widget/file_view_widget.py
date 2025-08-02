#region Imports


# Standard library imports
import os

# GUI imports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Drag and Drop
from tkinterdnd2 import DND_FILES

# Type hinting
from typing import List, Dict, Any, Optional


#endregion
#region FileViewWidget


class FileViewWidget(ttk.Frame):
    """Custom Treeview widget for displaying video/image file information."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # Column definitions
        self.columns = {
            'index': {'text': '#', 'width': 30, 'anchor': 'center', 'stretch': False},
            'name': {'text': 'File Name', 'width': 200, 'anchor': 'w', 'stretch': True},
            'size': {'text': 'Size', 'width': 80, 'anchor': 'e', 'stretch': False},
            'length': {'text': 'Length', 'width': 80, 'anchor': 'center', 'stretch': False},
            'orig_dim': {'text': 'Orig Dim', 'width': 90, 'anchor': 'center', 'stretch': False},
            'scale': {'text': 'Scale', 'width': 60, 'anchor': 'center', 'stretch': False},
            'new_dim': {'text': 'New Dim', 'width': 90, 'anchor': 'center', 'stretch': False},
            'path': {'text': 'Path', 'width': 300, 'anchor': 'w', 'stretch': True}
        }
        self._sort_column = None
        self._sort_reverse = False
        self._setup_treeview()
        self._setup_scrollbars()
        self._setup_layout()
        self._setup_context_menu()
        self._bind_drop_target(state="normal")


    #region UI Setup


    def _setup_treeview(self):
        """Initialize the treeview with columns and headings."""
        column_ids = list(self.columns.keys())
        self.tree = ttk.Treeview(self, columns=column_ids, show='headings', selectmode='extended')
        # Configure columns
        for col_id, config in self.columns.items():
            # Bind header click to sort (skip index column)
            if col_id == 'index':
                self.tree.heading(col_id, text=config['text'])
            else:
                self.tree.heading(col_id, text=config['text'], command=lambda c=col_id: self._sort_by_column(c))
            self.tree.column(col_id, width=config['width'], anchor=config['anchor'], minwidth=30, stretch=config['stretch'])
        self.tree.bind('<Button-1>', self._on_left_click)


    def _setup_scrollbars(self):
        """Add vertical and horizontal scrollbars."""
        self.v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.v_scrollbar.set)
        self.h_scrollbar = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(xscrollcommand=self.h_scrollbar.set)


    def _setup_layout(self):
        """Configure the grid layout for the widget."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')


    def _setup_context_menu(self):
        """Create and configure the context menu."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Select Files...", command=self._select_files_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Reveal in File Explorer", command=self._reveal_in_explorer)
        self.context_menu.add_command(label="Open in Default App", command=self._open_in_default_app)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove from List", command=self._remove_from_list)
        self.tree.bind("<Button-3>", self._show_context_menu)


    def _bind_drop_target(self, state="normal"):
        """Register or unregister Treeview as a drop target for files based on state."""
        if state == "normal":
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind('<<Drop>>', self._on_drop_files)
        else:
            self.tree.drop_target_unregister()


    #endregion
    #region Data Management


    def update_files(self, files: List[Dict[str, Any]]):
        """
        Update the treeview with new file data.

        Args:
            files: List of dictionaries with keys: 'name', 'size', 'length', 'orig_dim', 'scale', 'new_dim', 'path'
        """
        self.clear()
        for i, file_data in enumerate(files, start=1):
            self.add_file(file_data, index=i)


    def add_file(self, file_data: Dict[str, Any], index: Optional[int] = None):
        """
        Add a single file to the treeview.

        Args:
            file_data: Dictionary with keys: 'name', 'size', 'length', 'orig_dim', 'scale', 'new_dim', 'path'
            index: Optional index for the file, used for the index column
        """
        if self._is_duplicate(file_data.get('path', '')):
            return
        values = [
            str(index) if index is not None else '',  # index column
            file_data.get('name', ''),
            file_data.get('size', ''),
            file_data.get('length', ''),
            file_data.get('orig_dim', ''),
            file_data.get('scale', ''),
            file_data.get('new_dim', ''),
            file_data.get('path', '')
        ]
        self.tree.insert('', 'end', values=values)


    def clear(self):
        """Remove all items from the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)


    def get_selected_files(self) -> List[Dict[str, str]]:
        """
        Get data for currently selected files.

        Returns:
            List of dictionaries containing selected file data
        """
        selected_items = self.tree.selection()
        files = []
        for item in selected_items:
            values = self.tree.item(item)['values']
            if values:
                files.append({
                    # skip index column
                    'name': values[1],
                    'size': values[2],
                    'length': values[3],
                    'orig_dim': values[4],
                    'scale': values[5],
                    'new_dim': values[6],
                    'path': values[7]
                })
        return files


    def _is_duplicate(self, path: str) -> bool:
        """Check if a file path already exists in the treeview."""
        return path in {self.tree.set(item, 'path') for item in self.tree.get_children()}


    #endregion
    #region Sorting


    def _sort_by_column(self, col_id):
        """Sort treeview by given column."""
        def parse_size(s):
            try:
                num, unit = s.split()
                num = float(num)
                unit = unit.lower()
                factor = {'kb': 1e3, 'mb': 1e6, 'gb': 1e9}.get(unit, 1)
                return num * factor
            except Exception:
                return 0

        def parse_dim(s):
            try:
                w, h = s.lower().split('x')
                return int(w) * int(h)
            except Exception:
                return 0

        def parse_scale(s):
            try:
                if s.startswith('x'):
                    return float(s[1:])
                return float(s)
            except Exception:
                return 0

        def parse_length(s):
            try:
                parts = [int(p) for p in s.split(':')]
                if len(parts) == 3:
                    return parts[0]*3600 + parts[1]*60 + parts[2]
                elif len(parts) == 2:
                    return parts[0]*60 + parts[1]
                else:
                    return int(parts[0])
            except Exception:
                return 0

        items = [(self.tree.set(k, col_id), k) for k in self.tree.get_children('')]
        key_funcs = {
            'size': parse_size,
            'orig_dim': parse_dim,
            'new_dim': parse_dim,
            'scale': parse_scale,
            'length': parse_length
        }
        key_func = key_funcs.get(col_id, lambda x: x)
        reverse = self._sort_column == col_id and not self._sort_reverse
        items.sort(key=lambda t: key_func(t[0]), reverse=reverse)
        # Rearrange items in treeview
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)
        # Update index column after sorting
        for idx, k in enumerate(self.tree.get_children(''), start=1):
            self.tree.set(k, 'index', str(idx))
        # Toggle sort order if same column, else set ascending
        if self._sort_column == col_id:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_reverse = False
        self._sort_column = col_id


    #endregion
    #region Event Binding


    def _on_left_click(self, event):
        """Handle left-click events on the treeview."""
        # If the click is on an empty area, clear the selection
        if not self.tree.identify_row(event.y):
            self.tree.selection_set([])


    def bind_selection_event(self, callback):
        """Bind a callback to selection events."""
        self.tree.bind('<<TreeviewSelect>>', callback)


    def bind_double_click(self, callback):
        """Bind a callback to double-click events."""
        self.tree.bind('<Double-1>', callback)


    #endregion
    #region Context Menu


    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        item = self.tree.identify_row(event.y)
        self.context_menu.entryconfig("Select Files...", state="normal")
        # Enable/disable other commands based on context
        state = "normal" if item else "disabled"
        for label in ("Reveal in File Explorer", "Open in Default App", "Remove from List"):
            self.context_menu.entryconfig(label, state=state)
        if item:
            self.tree.selection_set(item)
        else:
            self.tree.selection_remove(self.tree.selection())
        self.context_menu.post(event.x_root, event.y_root)


    def _reveal_in_explorer(self):
        """Reveal selected file in file explorer."""
        for file_data in self.get_selected_files():
            file_path = file_data.get('path', '')
            if file_path and os.path.exists(file_path):
                try:
                    os.startfile(os.path.dirname(file_path))
                except Exception as e:
                    messagebox.showerror("Error", f"Could not reveal file in explorer: {e}")
            else:
                messagebox.showwarning("Warning", f"File not found: {file_path}")


    def _open_in_default_app(self):
        """Open selected file in default application."""
        for file_data in self.get_selected_files():
            file_path = file_data.get('path', '')
            if file_path and os.path.exists(file_path):
                try:
                    os.startfile(file_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open file: {e}")
            else:
                messagebox.showwarning("Warning", f"File not found: {file_path}")


    def _remove_from_list(self):
        """Remove selected files from the list."""
        selected_items = self.tree.selection()
        for item in selected_items:
            self.tree.delete(item)
        for idx, item in enumerate(self.tree.get_children(''), start=1):
            self.tree.set(item, 'index', str(idx))


    def _select_files_dialog(self):
        """Open a file dialog to select files and add them to the list."""
        file_paths = filedialog.askopenfilenames(title="Select Files")
        if not file_paths:
            return
        for file_path in file_paths:
            if not self._is_duplicate(file_path) and os.path.isfile(file_path):
                file_info = self._get_file_info(file_path)
                if file_info:
                    self.add_file(file_info, index=len(self.tree.get_children()) + 1)


    #endregion
    #region Helper Methods


    def set_state(self, state: str):
        """Set the state of FileViewWidget. ('normal' or 'disabled')"""
        print(f"Setting state to: {state}")
        if state == 'normal':
            self._bind_drop_target(state)
            self.tree.config(selectmode='extended')
            self.tree.bind("<Button-3>", self._show_context_menu)
        else:
            self._bind_drop_target(state)
            self.tree.config(selectmode='none')
            self.tree.unbind("<Button-3>")


    #endregion
    #region Drag and Drop


    def _on_drop_files(self, event):
        """Handle files dropped onto the Treeview."""
        root = self.tree.winfo_toplevel()
        try:
            files = root.tk.splitlist(event.data)
        except Exception:
            files = [event.data]
        for file_path in files:
            file_path = file_path.strip('"')
            if os.path.isfile(file_path) and not self._is_duplicate(file_path):
                file_info = self._get_file_info(file_path)
                if file_info:
                    self.add_file(file_info, index=len(self.tree.get_children()) + 1)


    def _get_file_info(self, file_path):
        """Extract file info for display in the Treeview."""
        try:
            name = os.path.basename(file_path)
            size_bytes = os.path.getsize(file_path)
            size_str = self._format_file_size(size_bytes)
            ext = os.path.splitext(name)[1].lower()
            if ext in ['.mp4', '.avi', '.mov', '.mkv']:
                length = "..."
                orig_dim = "..."
            else:
                length = "..."
                orig_dim = "..."
            scale = ""
            new_dim = ""
            return {
                "name": name,
                "size": size_str,
                "length": length,
                "orig_dim": orig_dim,
                "scale": scale,
                "new_dim": new_dim,
                "path": file_path
            }
        except Exception:
            return None


    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"


#endregion
