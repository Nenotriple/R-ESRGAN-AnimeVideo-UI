from tkinter import ttk
import tkinter as tk


class StatusBar:
    """Manages the status bar at the bottom of the interface."""
    def __init__(self, app):
        self.app = app
        self.label = None


    def create(self, parent_frame: ttk.Frame):
        self.label = ttk.Label(parent_frame, textvariable=self.app.status_var)
        self.label.grid(row=2, column=0, sticky=(tk.W, tk.E))
        self.app.status_label = self.label
