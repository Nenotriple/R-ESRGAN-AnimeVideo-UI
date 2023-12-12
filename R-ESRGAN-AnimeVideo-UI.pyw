"""
########################################
#                                      #
#        R-ESRGAN-AnimeVideo-UI        #
#                                      #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################

Description:
-------------
Display an image and text file side-by-side for easy manual caption editing.

More info here: https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI

Requirements: #
ffmpeg        # Included: Auto-download
ffprobe       # Included: Auto-download
pillow        # Included: Auto-install

"""

VERSION = "v1.15"

##########################################################################################################################################################################
##########################################################################################################################################################################
#                 #
#region - Imports #
#                 #

import os
import io
import re
import sys
import glob
import time
import ctypes
import shutil
import datetime
import threading
import mimetypes
import subprocess
import tkinter as tk
from tkinter import Tk, ttk, filedialog, simpledialog, messagebox, Button, Toplevel, Frame, X, BOTH, TclError
from subprocess import TimeoutExpired

# This script collects ffmpeg, realesrgan, and models.
import bin.collect_requirements

##################
#                #
# Install Pillow #
#                #
##################

try:
    from PIL import Image, ImageTk, ImageSequence
except ImportError:
    import subprocess, sys
    import threading
    from tkinter import Tk, Label, messagebox

    def download_pillow():
        cmd = ["pythonw", '-m', 'pip', 'install', 'pillow']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for line in iter(lambda: process.stdout.readline(), b''):
            pillow_label = Label(root, wraplength=450)
            pillow_label.pack(anchor="w")
            pillow_label.config(text=line.rstrip())
        process.stdout.close()
        process.wait()
        done_label = Label(root, text="\nAll done! This window will now close...", wraplength=450)
        done_label.pack(anchor="w")
        root.after(3000, root.destroy)

    root = Tk()
    root.title("Pillow Is Installing...")
    root.geometry('600x200')
    root.resizable(False, False)
    root.withdraw()
    root.protocol("WM_DELETE_WINDOW", lambda: None)

    install_pillow = messagebox.askyesno("Pillow not installed!", "Pillow not found!\npypi.org/project/Pillow\n\nWould you like to install it? ~2.5MB \n\n It's required to view and process images.")
    if install_pillow:
        root.deiconify()
        pillow_label = Label(root, wraplength=450)
        pillow_label.pack(anchor="w")
        pillow_label.config(text="Beginning Pillow install now...\n")
        threading.Thread(target=download_pillow).start()
        root.mainloop()
        from PIL import Image
    else:
        sys.exit()

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                     #
#region - AboutWindow #
#                     #

class AboutWindow(tk.Toplevel):

    info_text = (
    "\nSupported Video Types:\n"
    "   - mp4, gif, avi, mkv, webm, mov, m4v, wmv\n"

    "\nNOTE:\n"
    "   - The Upscale and Merge operations delete the previous frames by default.\n"
    "   - If you want to keep those frames, make sure to enable the Keep Frames option.\n"
    "   - The resize operation overwrites frames.\n"

    "\nUpscale Frames:\n"
    "   - Select a upscale model in the options menu. Default= realesr-animevideov3 \n"
    "   - Select a scaling factor in the options menu. Default= x2 \n"

    "\nTools:\n"
    "   - Batch Upscale: Upscales all images in a folder. The source images are not deleted.\n"
    "   - Upscale Image: Upscale a single image. The source image is not deleted.\n"
    "   - Resize: Scale extracted or upscaled frames to any size.\n"

    "\nYou can right-click grayed-out buttons to enable them out of sequence.\n"
    "   - Only use if you know what you're doing!\n"
    )

    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("About")
        self.geometry("450x550")
        self.maxsize(800, 600)
        self.minsize(450, 600)

        self.url_button = tk.Button(self, text="Open: github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI", fg="blue", command=self.open_url)
        self.url_button.pack(fill="x")

        self.info_label = tk.Label(self, text="Info", font=("Arial", 14))
        self.info_label.pack(pady=5)
        self.info_text = tk.Label(self, text=AboutWindow.info_text, width=100, anchor='w', justify='left')
        self.info_text.pack(pady=5)

        self.separator = tk.Label(self, height=1)
        self.separator.pack()

        self.credits_label = tk.Label(self, text="Credits", font=("Arial", 14))
        self.credits_label.pack(pady=5)
        self.made_by_label = tk.Label(self, text="(2023) Created by: Nenotriple", font=("Arial", 10))
        self.made_by_label.pack(pady=5)
        self.credits_text = tk.Label(self, text= ("ffmpeg-6.0-essentials: ffmpeg.org\nReal-ESRGAN_portable: github.com/xinntao/Real-ESRGAN\n Thank you!"), width=50)
        self.credits_text.pack(pady=5)

    def open_url(self):
        import webbrowser
        webbrowser.open('https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI')

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                  #
#region - ToolTips #
#                  #

class ToolTip:
    def __init__(self, widget, x_offset=0, y_offset=0):
        self.widget = widget
        self.tip_window = None
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.id = None
        self.hide_time = 0

    def show_tip(self, tip_text, x, y):
        if self.tip_window or not tip_text:
            return
        x += self.x_offset
        y += self.y_offset
        self.tip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.wm_attributes("-topmost", True)
        tw.wm_attributes("-disabled", True)
        label = tk.Label(tw, text=tip_text, background="#ffffee", relief="ridge", borderwidth=1, justify="left", padx=4, pady=4)
        label.pack()
        self.id = self.widget.after(3000, self.hide_tip)

    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()
        self.hide_time = time.time()

    @staticmethod
    def create_tooltip(widget, text, delay=0, x_offset=0, y_offset=0):
        tool_tip = ToolTip(widget, x_offset, y_offset)
        def enter(event):
            if tool_tip.id:
                widget.after_cancel(tool_tip.id)
            if time.time() - tool_tip.hide_time > 0.1:
                tool_tip.id = widget.after(delay, lambda: tool_tip.show_tip(text, widget.winfo_pointerx(), widget.winfo_pointery()))
        def leave(event):
            if tool_tip.id:
                widget.after_cancel(tool_tip.id)
            tool_tip.hide_tip()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                    #
#region - Main Class #
#                    #

class reav_ui(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        # Create interface.
        self.pack(fill=tk.BOTH, expand=1)
        self.create_interface()

        self.about_window = None
        self.video_file = []
        self.process = None
        self.process_stopped = False
        self.timer_running = False
        self.start_time = time.time()
        self.app_state = tk.StringVar()

        # This is used to track when the user selects a scale factor, so we can update the ui.
        self.scale_factor.trace('w', self.get_video_dimensions)

        # This is the framerate used if the value can't be retrieved from the video.
        self.FALLBACK_FPS = 30

        # These buttons are disabled on startup to guide the user to the "Select Video" button.
        self.extract_button.config(state='disabled')
        self.merge_button.config(state='disabled')
        self.upscale_button.config(state='disabled')

        # This is where we supply definitions for "mimetypes", so it knows these files are videos.
        mimetypes.add_type("video/mkv", ".mkv")
        mimetypes.add_type("video/webm", ".webm")
        mimetypes.add_type("video/wmv", ".wmv")
        mimetypes.add_type("video/3gp", ".3gp")

        # This is where we define all supported video types.
        self.supported_video_types = ["video/mp4", "video/avi", "video/mkv", "video/mov", "video/m4v", "video/wmv", "video/webm", "image/gif", "video/3gp"]

        # This is used to make sure folders are cleaned up when closing the window.
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                 #
#region - Menubar #
#                 #

    def create_interface(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # File Menu
        self.fileMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label="Open: Extracted Frames", command=lambda: os.startfile('raw_frames'))
        self.fileMenu.add_command(label="Open: Upscaled Frames", command=lambda: os.startfile('upscaled_frames'))
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Clear: Extracted Frames", command=lambda: self.fileMenu_clear_frames('raw_frames'))
        self.fileMenu.add_command(label="Clear: Upscaled Frames", command=lambda: self.fileMenu_clear_frames('upscaled_frames'))

        # Options Menu
        self.optionsMenu = tk.Menu(self.menubar, tearoff=0)
        # Upscale Model
        self.upscale_model = tk.StringVar(value="realesr-animevideov3")
        self.modelMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Upscale Model", menu=self.modelMenu)
        for model in ["realesr-animevideov3", "RealESRGAN_General_x4_v3", "realesrgan-x4plus", "realesrgan-x4plus-anime"]:
            self.modelMenu.add_radiobutton(label=model, variable=self.upscale_model, value=model)
        # Scale Factor
        self.scale_factor = tk.StringVar(value="2")
        self.scaleMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Upscale Factor", menu=self.scaleMenu)
        for i in ["1", "2", "3", "4"]:
            self.scaleMenu.add_radiobutton(label="x"+i, variable=self.scale_factor, value=i)
        self.menubar.add_cascade(label="Options", menu=self.optionsMenu)

        # Output Format
        self.output_format = tk.StringVar(value="mp4")
        self.formatMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Output Format", menu=self.formatMenu)
        for format in ["mp4", "HQ gif", "LQ gif"]:
            self.formatMenu.add_radiobutton(label=format, variable=self.output_format, value=format)

        # Tools Menu
        self.toolsMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=self.toolsMenu)
        #self.toolsMenu.add_command(label="Batch Upscale", command=self.batch_upscale_menu)
        self.toolsMenu.add_command(label="Upscale a Single Image", command=self.select_and_upscale_image)
        self.toolsMenu.add_separator()
        self.toolsMenu.add_command(label="Resize: Extracted Frames", command=lambda: self.confirm_scale("raw_frames"))
        self.toolsMenu.add_command(label="Resize: Upscaled Frames", command=lambda: self.confirm_scale("upscaled_frames"))

        # About Menu
        #self.menubar.add_command(label="About", command=self.open_about_window)
        self.menubar.add_command(label="About", underline=0, command=self.toggle_about_window)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                #
#region - Labels #
#                #

        self.label_frame = tk.Frame(self)
        self.label_frame.pack(side="top", fill="both", expand=True)

        # Filename
        self.top_label = tk.Label(self.label_frame)
        self.top_label["text"] = "Select a video to begin!"
        self.top_label['wraplength'] = 500
        self.top_label.pack(side="top", fill="x")
        self.top_label.bind("<Button-3>", self.copy_to_clipboard)

        # Console Output
        self.middle_label = tk.Label(self.label_frame)
        self.middle_label["wraplength"] = 500
        self.middle_label.pack(side="top", fill="x")
        self.middle_label.bind("<Button-3>", self.copy_to_clipboard)

        # Operation
        self.bottom_label = tk.Label(self.label_frame)
        self.bottom_label['wraplength'] = 500
        self.bottom_label.pack(side="top", fill="x")
        self.bottom_label.bind("<Button-3>", self.copy_to_clipboard)

        # Timer
        self.timer_label = tk.Label(self.label_frame)
        self.timer_label.pack(side="top", fill="x")

        # Progress Bar
        self.percent_complete = tk.StringVar()
        self.progressbar = ttk.Progressbar(self.label_frame)
        self.progressbar.configure(orient="horizontal", variable=self.percent_complete)
        self.progressbar.pack(side="bottom", fill="x", padx=4)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                          #
#region - Primary Notebook #
#                          #

        self.primary_notebook = ttk.Notebook(self)
        self.primary_tab1 = Frame(self.primary_notebook)
        self.primary_tab2 = Frame(self.primary_notebook)
        self.primary_notebook.add(self.primary_tab1, text='Video')
        self.primary_notebook.add(self.primary_tab2, text='Image')
        self.primary_notebook.pack(fill='both')

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                      #
#region - Video - tab1 #
#                      #

        self.video_frame = tk.Frame(self.primary_tab1)
        self.video_frame.pack(side="top", pady=4, fill="both", expand=True)

        # Select Video
        self.select_video_button = tk.Button(self.video_frame, takefocus=False)
        self.select_video_button["text"] = "1) Select Video\t\t\t"
        self.select_video_button["command"] = self.select_video
        self.select_video_button.pack(side="top", fill="x")
        self.select_video_button.bind("<Enter>", self.mouse_enter)
        self.select_video_button.bind("<Leave>", self.mouse_leave)

        self.button_frame1 = tk.Frame(self.video_frame)
        self.button_frame1.pack(anchor='center')

        # Extract
        self.extract_button = tk.Button(self.button_frame1, takefocus=False, text="2) Extract Frames  ", command=self.extract_frames, width=59, height=1)
        self.extract_button.grid(row=0, column=0, pady=3)
        self.extract_button.bind('<Button-3>', lambda event: self.extract_button.config(state='normal'))
        self.extract_button.bind("<Enter>", self.mouse_enter)
        self.extract_button.bind("<Leave>", self.mouse_leave)

        # Keep raw_frames
        self.keep_raw_var = tk.IntVar(value=0)
        self.keep_raw_check = tk.Checkbutton(self.button_frame1, takefocus=False, text="Keep Frames", variable=self.keep_raw_var)
        self.keep_raw_check.grid(row=0, column=1, pady=3)
        ToolTip.create_tooltip(self.keep_raw_check, "Enable this before Upscaling or closing the window to save Raw Frames.", 100, 6, 4)
        self.keep_raw_check.bind("<Enter>", self.mouse_enter, add="+")
        self.keep_raw_check.bind("<Leave>", self.mouse_leave, add="+")

        self.button_frame2 = tk.Frame(self.video_frame)
        self.button_frame2.pack(anchor='center')

        # Upscale
        self.upscale_button = tk.Button(self.button_frame2, takefocus=False, width=59, height=1)
        self.upscale_button["text"] = "3) Upscale Frames"
        self.upscale_button["command"] = self.upscale_frames
        self.upscale_button.grid(row=0, column=0)
        self.upscale_button.bind('<Button-3>', lambda event: self.upscale_button.config(state='normal'))
        self.upscale_button.bind("<Enter>", self.mouse_enter)
        self.upscale_button.bind("<Leave>", self.mouse_leave)

        # Keep upscaled_frames
        self.keep_upscaled_var = tk.IntVar(value=0)
        self.keep_upscaled_check = tk.Checkbutton(self.button_frame2, takefocus=False, text="Keep Frames", variable=self.keep_upscaled_var)
        self.keep_upscaled_check.grid(row=0, column=1, pady=3)
        ToolTip.create_tooltip(self.keep_upscaled_check, "Enable this before Merging or closing the window to save Upscaled Frames.", 100, 6, 4)
        self.keep_upscaled_check.bind("<Enter>", self.mouse_enter, add="+")
        self.keep_upscaled_check.bind("<Leave>", self.mouse_leave, add="+")

        self.button_frame3 = tk.Frame(self.video_frame)
        self.button_frame3.pack(anchor='center')

        # Merge
        self.merge_button = tk.Button(self.button_frame3, takefocus=False, text="4) Merge Frames ", command=self.merge_frames, width=59)
        self.merge_button.grid(row=0, column=0)
        self.merge_button.bind('<Button-3>', lambda event: self.merge_button.config(state='normal'))
        self.merge_button.bind("<Enter>", self.mouse_enter)
        self.merge_button.bind("<Leave>", self.mouse_leave)

        # Auto
        self.auto_var = tk.IntVar(value=0)
        self.auto_var.trace("w", lambda *args: self.toggle_auto_widgets())
        self.auto_check = tk.Checkbutton(self.button_frame3, takefocus=False, text="Auto\t       ", variable=self.auto_var, width=10)
        self.auto_check.grid(row=0, column=1, pady=3)
        ToolTip.create_tooltip(self.auto_check, "Enable this to automatically Upscale/Merge Frames after Extracting/Upscaling.", 100, 6, 4)
        self.auto_check.bind("<Enter>", self.mouse_enter, add="+")
        self.auto_check.bind("<Leave>", self.mouse_leave, add="+")

        # Stop
        self.stop_button = tk.Button(self.video_frame, takefocus=False, text="STOP", command=self.stop_process)
        self.stop_button.pack(side="top", fill="x")
        self.stop_button.bind("<Enter>", self.mouse_enter)
        self.stop_button.bind("<Leave>", self.mouse_leave)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                        #
#region - Video_notebook #
#                        #

        self.video_notebook = ttk.Notebook(self.primary_tab1, takefocus=False)
        self.thumbnail_tab1 = Frame(self.video_notebook)
        self.extra_tab2 = Frame(self.video_notebook)
        self.video_notebook.add(self.thumbnail_tab1, text='Video Thumbnail')
        self.video_notebook.add(self.extra_tab2, text='Extra Settings')
        self.video_notebook.pack(fill='both')

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                        #
#region - thumbnail_tab1 #
#                        #

        self.thumbnail_label = tk.Label(self.thumbnail_tab1)
        self.thumbnail_label["text"] = "Info"
        self.thumbnail_label.pack(side="top", fill="both", expand=True)

        self.infotext_label = tk.Label(self.thumbnail_tab1, text=AboutWindow.info_text, anchor='w', justify=tk.LEFT, wraplength=500)
        self.infotext_label.pack(side="top", fill="x")

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                    #
#region - extra_tab2 #
#                    #

####### Upscale Options ##################################################
        self.options_frame = tk.Frame(self.extra_tab2)
        self.options_frame.pack(side="top", fill="x")

        # Upscale Model
        self.upscale_model_frame = tk.Frame(self.options_frame)
        self.upscale_model_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.model_label = tk.Label(self.upscale_model_frame)
        ToolTip.create_tooltip(self.model_label, "This changes the AI model used for upscaling", 100, 6, 4)
        self.model_label["text"] = "Upscale Model"
        self.model_label.pack(side="top", anchor="w")

        self.upscale_model_values = ["realesr-animevideov3", "RealESRGAN_General_x4_v3", "realesrgan-x4plus", "realesrgan-x4plus-anime"]
        self.upscale_model_combobox = ttk.Combobox(self.upscale_model_frame, takefocus=False, state="readonly", textvariable=self.upscale_model, values=self.upscale_model_values)
        self.upscale_model_combobox.set("realesr-animevideov3")
        self.upscale_model_combobox.pack(side="left", fill="x", expand=True)

        # Upscale Factor
        self.scale_factor_frame = tk.Frame(self.options_frame)
        self.scale_factor_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.scale_label = tk.Label(self.scale_factor_frame)
        ToolTip.create_tooltip(self.scale_label, "This is the scaling factor (2 = x2 image size)", 100, 6, 4)
        self.scale_label["text"] = "Upscale Factor"
        self.scale_label.pack(side="top", anchor="w")

        self.scale_factor_values = ["1", "2", "3", "4"]
        self.scale_factor_combobox = ttk.Combobox(self.scale_factor_frame, width="6", takefocus=False, state="readonly", textvariable=self.scale_factor, values=self.scale_factor_values)
        self.scale_factor_combobox.set("2")
        self.scale_factor_combobox.pack(side="left", fill="x", expand=True)
        self.upscale_model.trace('w', self.update_scale_factor)

        # Output Format Combobox
        self.output_frame = tk.Frame(self.options_frame)
        self.output_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.output_label = tk.Label(self.output_frame)
        ToolTip.create_tooltip(self.output_label, "This is the video output format", 100, 6, 4)
        self.output_label["text"] = "Output Format"
        self.output_label.pack(side="top", anchor="w")

        self.output_format_values = ["mp4", "HQ gif", "LQ gif"]
        self.output_format_combobox = ttk.Combobox(self.output_frame, width="6", takefocus=False, state="readonly", textvariable=self.output_format, values=self.output_format_values)
        self.output_format_combobox.set("mp4")
        self.output_format_combobox.pack(side="left", fill="x", expand=True)

        # Output Codec Combobox
        self.output_codec_frame = tk.Frame(self.options_frame)
        self.output_codec_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.output_codec_label = tk.Label(self.output_codec_frame)
        ToolTip.create_tooltip(self.output_codec_label, "libx264 = Works everywhere / Slightly bigger videos\n\nlibx265 = Saves space, Good for HD / Needs more power, not as much support", 100, 6, 4)
        self.output_codec_label["text"] = "Output Codec"
        self.output_codec_label.pack(side="top", anchor="w")

        self.output_codec = tk.StringVar(value="libx264")
        self.output_codec_values = ["libx264", "libx265"]
        self.output_codec_combobox = ttk.Combobox(self.output_codec_frame, takefocus=False, state="readonly", textvariable=self.output_codec, values=self.output_codec_values)
        self.output_codec_combobox.set("libx264")
        self.output_codec_combobox.pack(side="left", fill="x", expand=True)

        # Reset
        self.reset_frame = tk.Frame(self.extra_tab2)
        self.reset_frame.pack(side="top", fill="x", padx=2, pady=10)
        self.reset_button = tk.Button(self.reset_frame, takefocus=False, text="Reset settings to default", command=lambda: self.reset_settings())
        self.reset_button.pack(side="top", fill="x", expand=True)

####### Scale Options ##################################################
        self.scale_frame = tk.Frame(self.extra_tab2, borderwidth=1, relief="groove")
        self.scale_frame.pack(side="top", fill="x")

        self.extra_label = tk.Label(self.scale_frame, state="disabled")
        self.extra_label["text"] = ("Enter a percentage (default=50%, half size), or enter a specific resolution (width,height)")
        self.extra_label.pack(side="top")

        # Resize extracted frames
        self.scale_raw_frame = tk.Frame(self.scale_frame, borderwidth=1, relief="groove")
        self.scale_raw_frame.pack(side="top", fill="x")

        self.auto_resize_extracted_var = tk.IntVar(value=0)
        self.re_check = tk.Checkbutton(self.scale_raw_frame, text="Auto resize extracted frames before upscaling:   ", variable=self.auto_resize_extracted_var, takefocus=False, state="disabled")
        self.re_check.pack(side="left")
        self.re_check.bind("<Enter>", self.mouse_enter)
        self.re_check.bind("<Leave>", self.mouse_leave)

        self.scale_raw = tk.StringVar(value=50)
        self.scale_raw_entry = tk.Entry(self.scale_raw_frame, textvariable=self.scale_raw, takefocus=False, state="disabled")
        self.scale_raw_entry.pack(side="right", fill="both", expand=True)

        self.spacer_frame3 = tk.Frame(self.scale_frame, height=4)
        self.spacer_frame3.pack(fill="x")

        # Resize upscaled frames
        self.scale_upscaled_frame = tk.Frame(self.scale_frame, borderwidth=1, relief="groove")
        self.scale_upscaled_frame.pack(side="top", fill="x")

        self.auto_resize_upscaled_var = tk.IntVar(value=0)
        self.scale_upscaled_check = tk.Checkbutton(self.scale_upscaled_frame, text="Auto resize upscaled frames before merging:      ", variable=self.auto_resize_upscaled_var, takefocus=False, state="disabled")
        self.scale_upscaled_check.pack(side="left")
        self.scale_upscaled_check.bind("<Enter>", self.mouse_enter)
        self.scale_upscaled_check.bind("<Leave>", self.mouse_leave)

        self.scale_upscaled = tk.StringVar(value=50)
        self.scale_upscaled_entry = tk.Entry(self.scale_upscaled_frame, textvariable=self.scale_upscaled, takefocus=False, state="disabled")
        self.scale_upscaled_entry.pack(side="right", fill="both", expand=True)

        validate_cmd = self.register(self.validate_input)

        self.scale_raw_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))
        self.scale_upscaled_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                    #
#region - Image tab2 #
#                    #

        self.image_options_frame = tk.Frame(self.primary_tab2)
        self.image_options_frame.pack(side="top", fill="x", padx=2, pady=2)

        # Upscale Model
        self.upscale_model_frame = tk.Frame(self.image_options_frame)
        self.upscale_model_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.model_label_tab2 = tk.Label(self.upscale_model_frame)
        ToolTip.create_tooltip(self.model_label_tab2, "This changes the AI model used for upscaling", 100, 6, 4)
        self.model_label_tab2["text"] = "Upscale Model"
        self.model_label_tab2.pack(side="top", anchor="w")

        self.upscale_model_combobox_tab2 = ttk.Combobox(self.upscale_model_frame, takefocus=False, state="readonly", textvariable=self.upscale_model, values=self.upscale_model_values)
        self.upscale_model_combobox_tab2.set("realesr-animevideov3")
        self.upscale_model_combobox_tab2.pack(side="left", fill="x", expand=True)

        # Upscale Factor
        self.scale_factor_frame = tk.Frame(self.image_options_frame)
        self.scale_factor_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.scale_label_tab2 = tk.Label(self.scale_factor_frame)
        ToolTip.create_tooltip(self.scale_label_tab2, "This is the scaling factor (2 = x2 image size)", 100, 6, 4)
        self.scale_label_tab2["text"] = "Upscale Factor"
        self.scale_label_tab2.pack(side="top", anchor="w")

        self.scale_factor_combobox_tab2 = ttk.Combobox(self.scale_factor_frame, takefocus=False, state="readonly", textvariable=self.scale_factor, values=self.scale_factor_values)
        self.scale_factor_combobox_tab2.set("2")
        self.scale_factor_combobox_tab2.pack(side="left", fill="x", expand=True)
        self.upscale_model.trace('w', self.update_scale_factor)

        # SPACER
        self.spacer_frame4 = tk.Frame(self.primary_tab2, height=30)
        self.spacer_frame4.pack(side="top", pady=4, fill="x")
        self.separator2 = ttk.Separator(self.primary_tab2)
        self.separator2.pack(fill="x", anchor="s")

####### Single Image ##################################################
        self.image_upscale_frame = tk.Frame(self.primary_tab2)
        self.image_upscale_frame.pack(side="top", pady=4, fill="x")

        self.image_upscale_label = tk.Label(self.image_upscale_frame, text="Select a single image to upscale.\n\nThe output will be saved in the same directory with '_UP' appened to the filename.")
        self.image_upscale_label.pack(side="top")

        self.upscale_image_button = tk.Button(self.image_upscale_frame, takefocus=False, text="Select an image to upscale", command=lambda: self.select_and_upscale_image())
        self.upscale_image_button.pack(fill="x", expand=True)
        self.upscale_image_button.bind("<Enter>", self.mouse_enter)
        self.upscale_image_button.bind("<Leave>", self.mouse_leave)

        # SPACER
        self.spacer_frame5 = tk.Frame(self.primary_tab2, height=30)
        self.spacer_frame5.pack(side="top", pady=4, fill="x")
        self.separator2 = ttk.Separator(self.primary_tab2)
        self.separator2.pack(fill="x", anchor="s")

####### Batch Upscale ##################################################
        self.batch_upscale_frame = tk.Frame(self.primary_tab2)
        self.batch_upscale_frame.pack(side="top", pady=4, fill="x")

        self.batch_upscale_label = tk.Label(self.batch_upscale_frame, text="Select a folder containing images to upscale.\n\nIf no output folder is selected, an 'output' folder will be created in the source folder.")
        self.batch_upscale_label.pack(side="top")

        # Source Folder Frame
        self.source_folder_frame = tk.Frame(self.batch_upscale_frame)
        self.source_folder_frame.pack(side="top", pady=4, fill="x")

        self.source_folder_label = tk.Label(self.source_folder_frame, text="Source Folder:")
        self.source_folder_label.pack(side="left")
        self.source_folder_entry = tk.Entry(self.source_folder_frame)
        self.source_folder_entry.pack(side="left", fill="x", expand=True)
        self.source_folder_button = tk.Button(self.source_folder_frame, text="Browse", command=self.browse_source_folder)
        self.source_folder_button.pack(side="left")
        self.source_folder_button.bind("<Enter>", self.mouse_enter)
        self.source_folder_button.bind("<Leave>", self.mouse_leave)
        self.source_folder_clear_button = tk.Button(self.source_folder_frame, text="X", command=lambda: self.source_folder_entry.delete(0, 'end'))
        self.source_folder_clear_button.pack(side="left")
        self.source_folder_clear_button.bind("<Enter>", lambda event: self.mouse_enter(event, '#ffcac9'))
        self.source_folder_clear_button.bind("<Leave>", self.mouse_leave)

        # Output Folder Frame
        self.output_folder_frame = tk.Frame(self.batch_upscale_frame)
        self.output_folder_frame.pack(side="top", pady=4, fill="x")

        self.output_folder_label = tk.Label(self.output_folder_frame, text="Output Folder:")
        self.output_folder_label.pack(side="left")
        self.output_folder_entry = tk.Entry(self.output_folder_frame)
        self.output_folder_entry.pack(side="left", fill="x", expand=True)
        self.output_folder_button = tk.Button(self.output_folder_frame, text="Browse", command=self.browse_output_folder)
        self.output_folder_button.pack(side="left")
        self.output_folder_button.bind("<Enter>", self.mouse_enter)
        self.output_folder_button.bind("<Leave>", self.mouse_leave)
        self.output_folder_clear_button = tk.Button(self.output_folder_frame, text="X", command=lambda: self.output_folder_entry.delete(0, 'end'))
        self.output_folder_clear_button.pack(side="left")
        self.output_folder_clear_button.bind("<Enter>", lambda event: self.mouse_enter(event, '#ffcac9'))
        self.output_folder_clear_button.bind("<Leave>", self.mouse_leave)

        # Create Run button
        self.run_batch_button = tk.Button(self.batch_upscale_frame, text="Run Batch Upscale", command=self.batch_upscale)
        self.run_batch_button.pack(side="left", fill="x", expand=True)
        self.run_batch_button.bind("<Enter>", self.mouse_enter)
        self.run_batch_button.bind("<Leave>", self.mouse_leave)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                 #
#region - Threads #
#                 #

    def extract_frames(self):
        self.bottom_label["text"] = "Extracting... This may take a while..."
        thread = threading.Thread(target=self._extract_frames)
        thread.start()

    def upscale_frames(self):
        self.bottom_label["text"] = "Upscaling... This may take a while..."
        thread = threading.Thread(target=self._upscale_frames)
        thread.start()

    def merge_frames(self):
        self.bottom_label["text"] = "Merging... This may take a while..."
        thread = threading.Thread(target=self._merge_frames)
        thread.start()

    def scale_frames(self, app_state=None):
        self.bottom_label["text"] = "Resizing... This may take a while..."
        thread = threading.Thread(target=self._scale_frames, args=(app_state,))
        thread.start()

    def batch_upscale(self):
        self.bottom_label["text"] = "Batch Upscaling... This may take a while..."
        thread = threading.Thread(target=self._batch_upscale)
        thread.start()

    def select_and_upscale_image(self):
        self.bottom_label["text"] = "Upscaling Single Image... This may take a while..."
        thread = threading.Thread(target=self._select_and_upscale_image)
        thread.start()

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                  #
#region - Monitors #
#                  #

    def monitor_extract_frames(self, process, total_frames, start_time):
        self.percent_complete.set(0)
        while self.process.poll() is None:
            frame_count = len(glob.glob('raw_frames/*.jpg'))
            if total_frames is not None:
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time)
                self.percent_complete.set(percent_complete)
                if not self.process_stopped:
                    self.middle_label["text"] = f"Extracted {frame_count:08d}, of {total_frames:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
            else:
                self.middle_label["text"] = f"Extracted {frame_count:08d} frames"
        frame_count = len(glob.glob('raw_frames/*.jpg'))
        if total_frames is not None and not self.process_stopped:
            fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time)
            self.percent_complete.set(100)
            self.middle_label["text"] = f"Extracted {frame_count:08d}, of {frame_count:08d}, 100%\nETA: {eta_str}, FPS: {fps:.2f}"
        elif not self.process_stopped:
            self.middle_label["text"] = f"Extracted {frame_count:08d} frames"

    def monitor_upscale_frames(self, frame_total, start_time):
        self.percent_complete.set(0)
        while self.process.poll() is None:
            frame_count = len(glob.glob('upscaled_frames/*.jpg'))
            if frame_count > 0:
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, frame_total, start_time)
                self.percent_complete.set(percent_complete)
                self.middle_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"

    def monitor_merge_frames(self, process, frame_count, total_frames, start_time, start_file_size):
        self.percent_complete.set(0)
        for line in iter(process.stdout.readline, ""):
            frame_number_search = re.search(r'frame=\s*(\d+)', line)
            if frame_number_search:
                frame_count = int(frame_number_search.group(1))
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time, start_file_size)
                self.percent_complete.set(percent_complete)
                self.middle_label["text"] = f"Frame: {frame_count:08d}, of {total_frames:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
        return frame_count

    def monitor_batch_upscale(self, frame_total, start_time):
        self.percent_complete.set(0)
        while self.process.poll() is None:
            frame_count = len(glob.glob(f'{self.output_folder}/*.jpg'))
            fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, frame_total, start_time)
            self.percent_complete.set(percent_complete)
            self.middle_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                           #
#region - Primary Functions #
#                           #

    def select_video(self):
        self.percent_complete.set(0)
        self.disable_buttons()
        self.middle_label["text"] = ""
        self.bottom_label["text"] = ""
        self.timer_label["text"] = ""
        self.video_file = filedialog.askopenfilename()
        if self.video_file:
            self.top_label["text"] = f"{os.path.basename(self.video_file)}"
            self.file_extension = os.path.splitext(self.video_file)[1]
            if mimetypes.guess_type(self.video_file)[0] not in self.supported_video_types:
                self.select_video_button.config(state='normal')
                self.top_label["text"] = "Invalid filetype!"
                self.bottom_label["text"] = self.sad_faces()
                if self.thumbnail_label is not None:
                    self.thumbnail_label.destroy()
                self.video_file = None
                return
            frame_rate, _, total_frames, dimensions, _ = self.collect_stream_info()
            self.total_frames = total_frames
            middle_frame_number = int(total_frames) // 2
            middle_frame_time = middle_frame_number / float(frame_rate)
            self.infotext_label.pack_forget()
            self.show_thumbnail(middle_frame_time)
            self.get_video_dimensions(frame_rate, total_frames, dimensions)
            self.timer_label["text"] = ""
            self.select_video_button.config(state='normal')
            self.extract_button.config(state='normal')
            self.stop_button.config(text="STOP", command=self.stop_process)
        else:
            self.top_label["text"] = "No file selected!"
            self.select_video_button.config(state='normal')

    def _extract_frames(self):
        if not self.video_file:
            self.bottom_label["text"] = f"Error: No video file selected.\n\n{self.sad_faces()}"
            return
        self.process_stopped = False
        try:
            start_time = time.time()
            self.start_timer()
            self.update_timer()
            self.disable_buttons()
            self.disable_widgets()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            os.makedirs("raw_frames", exist_ok=True)
            self.clean_directory('raw_frames')
            try:
                total_frames = int(self.total_frames)
            except Exception as e:
                total_frames = None

                self.bottom_label["text"] = f"Error: {str(e)}\n\n{self.sad_faces()}"
            self.process = subprocess.Popen(["./bin/ffmpeg.exe", "-i", self.video_file, "-qscale:v", "3", "-qmin", "3", "-qmax", "3", "-vsync", "0", "raw_frames/frame%08d.jpg"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.monitor_extract_frames(self.process, total_frames, start_time)
        finally:
            self.stop_timer()
            self.enable_buttons()
            self.enable_widgets()
            if not self.process_stopped:
                self.bottom_label["text"] = "Done Extracting!"
            self.stop_button.config(text="STOP", command=self.stop_process)
            if self.auto_var.get() == 1 and self.auto_resize_extracted_var.get() == 1:
                self.app_state.set("auto_resize_extracted")
                self.auto_scale(("raw_frames"))
            elif self.auto_var.get() == 1:
                self.upscale_frames()
            for button in [self.extract_button, self.merge_button]:
                button.config(state='disabled')
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def _upscale_frames(self):
        if not glob.glob('raw_frames/*.jpg'):
            self.bottom_label["text"] = f"Error: No images to upscale.\n\n{self.sad_faces()}"
            return
        self.process_stopped = False
        try:
            os.makedirs("upscaled_frames", exist_ok=True)
            self.clean_directory("upscaled_frames")
            self.start_timer()
            self.update_timer()
            self.disable_buttons()
            self.disable_widgets()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            frame_total = len(glob.glob('raw_frames/*.jpg'))
            start_time = time.time()
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", "raw_frames", "-o", "upscaled_frames", "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.monitor_upscale_frames(frame_total, start_time)
        except Exception as e:
            self.bottom_label["text"] = f"Error: {str(e)}\n\n{self.sad_faces()}"
        finally:
            self.stop_timer()
            self.enable_buttons()
            self.enable_widgets()
            self.stop_button.config(text="STOP", command=self.stop_process)
            for button in [self.extract_button, self.upscale_button]:
                button.config(state='disabled')
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")
        if self.keep_raw_var.get() == 0:
            self.clean_directory("raw_frames")
        if not self.process_stopped:
            self.bottom_label["text"] = "Done Upscaling!"
        if self.auto_var.get() == 1 and self.auto_resize_upscaled_var.get() == 1:
            self.app_state.set("auto_resize_upscaled")
            self.auto_scale(("upscaled_frames"))
        elif self.auto_var.get() == 1:
            self.merge_frames()

    def _merge_frames(self):
        if not self.video_file:
            self.bottom_label["text"] = f"Error: No video file selected.\n\n{self.sad_faces()}"
            return
        self.process_stopped = False
        try:
            self.start_timer()
            self.disable_buttons()
            self.disable_widgets()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            total_frames = len(os.listdir("upscaled_frames"))
            self.file_extension = os.path.splitext(self.video_file)[1]
            start_file_size = os.path.getsize(self.video_file)
            command, output_file_path = self.get_merge_frames_command()
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
            start_time = time.time()
            frame_count = 0
            frame_count = self.monitor_merge_frames(process, frame_count, total_frames, start_time, start_file_size)
            process.stdout.close()
            process.wait()
            end_file_size = os.path.getsize(output_file_path)
            _, _, _, percent_change, start_file_size_MB, end_file_size_MB = self.calculate_metrics(frame_count, total_frames, start_time, start_file_size, end_file_size)
            self.stop_timer()
            if not self.process_stopped:
                self.bottom_label["text"] = f"Done Merging!\nOriginal size: {start_file_size_MB:.2f}MB, Final size: {end_file_size_MB:.2f}MB, Change: {percent_change:.2f}%"
            if os.path.isfile("bin/palette001.png"):
                os.remove("bin/palette001.png")
            if not self.keep_upscaled_var.get():
                self.clean_directory("upscaled_frames")
            if not self.process_stopped:
                self.middle_label["text"] = "Output:\n" + output_file_path
            self.stop_button.config(text="Open Output Folder...", command=self.open_output_folder)
        except AttributeError as e:
            self.stop_timer()
            self.bottom_label["text"] = f"Error: {str(e)}\n\n{self.sad_faces()}"
        finally:
            self.enable_buttons()
            self.enable_widgets()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")
            for button in [self.extract_button, self.upscale_button, self.merge_button]:
                button.config(state='disabled')

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                             #
#region - Secondary Functions #
#                             #

    def show_thumbnail(self, middle_frame_time):
        _, duration, _, _, _ = self.collect_stream_info()

        def create_image(img):
            max_size = (512, 512)
            aspect_ratio = img.width / img.height
            new_width = max_size[0] if aspect_ratio > 1 else int(max_size[1] * aspect_ratio)
            new_height = int(max_size[0] / aspect_ratio) if aspect_ratio > 1 else max_size[1]
            img = img.resize((new_width, new_height), Image.LANCZOS)
            return ImageTk.PhotoImage(img)

        if self.video_file.endswith('.gif'):
            img = Image.open(self.video_file)
            frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
            photoImg = ImageTk.PhotoImage(frames[0])
            self.thumbnail_label.configure(image=photoImg)
            self.thumbnail_label.bind("<Double-1>", lambda e: self.open_output_folder())
            self.thumbnail_label.image = photoImg
            ToolTip.create_tooltip(self.thumbnail_label, "Double click to open source folder", 1000, 6, 4)

            def update(index):
                frame = frames[index]
                photoImg.paste(frame)
                self.thumbnail_label.after(120, update, (index+1)%len(frames))

            self.thumbnail_label.after(120, update, 1)
        else:
            def update_thumbnail(e):
                nonlocal middle_frame_time
                middle_frame_time = (middle_frame_time + 2) % duration
                result = subprocess.run(["./bin/ffmpeg.exe", "-ss", str(middle_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                img = Image.open(io.BytesIO(result.stdout))
                photoImg = create_image(img)
                self.thumbnail_label.configure(image=photoImg)
                self.thumbnail_label.image = photoImg

            result = subprocess.run(["./bin/ffmpeg.exe", "-ss", str(middle_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            img = Image.open(io.BytesIO(result.stdout))
            photoImg = create_image(img)
            self.thumbnail_label.configure(image=photoImg)
            self.thumbnail_label.bind("<Double-1>", lambda e: self.open_output_folder())
            self.thumbnail_label.bind("<Button-3>", update_thumbnail)
            self.thumbnail_label.image = photoImg
            ToolTip.create_tooltip(self.thumbnail_label, "Double click to open source folder\nRight click to jump forward ~2sec", 1000, 6, 4)

    def get_merge_frames_command(self):
        if not self.video_file:
            return
        frame_rate, _, _, _, _ = self.collect_stream_info()
        output_file_name = os.path.splitext(os.path.basename(self.video_file))[0] + "_UPSCALE"
        if self.output_format.get() in ['HQ gif', 'LQ gif']:
            output_file_name += "_" + self.output_format.get().split()[0]
        output_file_name += ('.gif' if self.output_format.get() in ['HQ gif', 'LQ gif'] else '.mp4')
        output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)
        first_frame = Image.open('upscaled_frames/frame00000001.jpg')
        width, height = first_frame.size
        if self.output_format.get() == 'HQ gif':
            palette_path = "bin/palette%03d.png"
            command_palettegen = ["./bin/ffmpeg.exe", "-y", "-i", "upscaled_frames/frame%08d.jpg", "-vf", "palettegen", palette_path]
            subprocess.call(command_palettegen, creationflags=subprocess.CREATE_NO_WINDOW)
            command = ["./bin/ffmpeg.exe", "-y", "-r", str(frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                       "-i", palette_path,
                       "-filter_complex", "paletteuse",
                       "-s", f"{width}x{height}",
                       output_file_path]
        elif self.output_format.get() == 'LQ gif':
            command = ["./bin/ffmpeg.exe", "-y", "-r", str(frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                       "-c:v", 'gif',
                       "-s", f"{width}x{height}",
                       output_file_path]
        else:
            command = ["./bin/ffmpeg.exe", "-y", "-r", str(frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                       "-i", self.video_file,
                       "-c:v", self.output_codec.get(),
                       "-s", f"{width}x{height}",
                       output_file_path]
        if self.file_extension != '.gif':
            command.extend(["-c:a", "copy",
                           "-vsync", "0",
                           "-map", "0:v:0",
                           "-map", "1:a:0",
                           "-pix_fmt", "yuv420p"])
        return command, output_file_path

    def update_scale_factor(self, *args):
        state = "normal" if self.upscale_model.get() == "realesr-animevideov3" else "disabled"
        self.scale_factor.set("2" if state == "normal" else "4")
        for i in range(4):
            self.scaleMenu.entryconfig(i, state=state)
        self.scale_factor_combobox.config(state="readonly" if state == "normal" else state)

    def run_ffprobe(self, args):
        if not self.video_file:
            return
        return subprocess.run(["./bin/ffprobe.exe"] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW).stdout.decode().strip()

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                               #
#region - Media Info Collection #
#                               #

    def select_video_get_media_info(self):
        if not self.video_file:
            return
        self.total_frames = self.run_ffprobe(["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "default=nokey=1:noprint_wrappers=1", self.video_file])
        if not self.total_frames.isdigit():
            _, _, self.total_frames, _, _ = self.collect_stream_info()
            self.total_frames = int(self.total_frames) if self.total_frames else self.FALLBACK_FPS
        self.frame_rate = self.run_ffprobe(["-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file])
        numerator, denominator = map(int, self.frame_rate.split('/'))
        self.frame_rate = numerator / denominator

    def collect_stream_info(self):
        if not self.video_file:
            return
        cmd = ["-show_format", "-show_streams", self.video_file]
        ffprobe_output = self.run_ffprobe(cmd)
        r_frame_rate = re.search(r"r_frame_rate=(\d+)/(\d+)", ffprobe_output)
        if r_frame_rate:
            numerator = int(r_frame_rate.group(1))
            denominator = int(r_frame_rate.group(2))
            frame_rate = numerator / denominator
        else:
            frame_rate = None
        duration = re.search(r"duration=(\d+\.\d+)", ffprobe_output)
        if duration:
            duration = float(duration.group(1))
        else:
            duration = None
        if frame_rate and duration:
            total_frames = frame_rate * duration
            total_frames = int(total_frames) + (total_frames % 1 > 0)
        else:
            total_frames = None
        coded_width = re.search(r"coded_width=(\d+)", ffprobe_output)
        if coded_width:
            coded_width = int(coded_width.group(1))
        else:
            coded_width = None
        coded_height = re.search(r"coded_height=(\d+)", ffprobe_output)
        if coded_height:
            coded_height = int(coded_height.group(1))
        else:
            coded_height = None
        file_size_bytes = os.path.getsize(self.video_file)
        file_size_megabytes = file_size_bytes / (1024 * 1024)
        return frame_rate, duration, total_frames, f"{coded_width}x{coded_height}", file_size_megabytes

    def get_video_dimensions(self, *args):
        if not self.video_file:
            return
        frame_rate, _, total_frames, dimensions, file_size_megabytes = self.collect_stream_info()
        scale_factor = int(self.scale_factor.get())
        coded_width, coded_height = map(int, dimensions.split('x'))
        new_dimensions = f"{coded_width*scale_factor}x{coded_height*scale_factor}"
        if total_frames:
            video_length_seconds = int(total_frames) / float(frame_rate)
            video_length_time_string = str(datetime.timedelta(seconds=int(video_length_seconds)))
            self.middle_label["text"] = f"Video Dimensions: {dimensions}\n Upscaled:  x{scale_factor}, {new_dimensions}"
            self.bottom_label["text"] = f"Video Length: {video_length_time_string}\nTotal Frames: {total_frames}\nFile Size: {file_size_megabytes:.2f} MB"
        else:
            self.bottom_label["text"] = f"Info collection failed... You can probably ignore this error."

    def calculate_metrics(self, frame_count, total_frames, start_time, start_file_size=None, end_file_size=None):
        elapsed_time = time.time() - start_time
        fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        eta = (total_frames / frame_count - 1) * elapsed_time if frame_count > 0 else 0
        eta_str = str(datetime.timedelta(seconds=int(eta)))
        percent_complete = (frame_count / total_frames) * 100 if total_frames > 0 else 0
        percent_change = None
        start_file_size_MB = None
        end_file_size_MB = None
        if start_file_size is not None and end_file_size is not None:
            percent_change = ((end_file_size - start_file_size) / start_file_size) * 100
            start_file_size_MB = start_file_size / (1024 * 1024)
            end_file_size_MB = end_file_size / (1024 * 1024)
        return fps, eta_str, percent_complete, percent_change, start_file_size_MB, end_file_size_MB

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                       #
#region - Upscale Image #
#                       #

    def _select_and_upscale_image(self):
        self.percent_complete.set(0)
        self.process_stopped = False
        try:
            self.top_label["text"] = ""
            input_image = filedialog.askopenfilename()
            if input_image:
                try:
                    if input_image.lower().endswith('.gif'):
                        raise IOError
                    Image.open(input_image)
                except IOError:
                    self.top_label["text"] = "Invalid, or not an image type!"
                    self.bottom_label["text"] = self.sad_faces()
                    return
                filename_without_ext = os.path.splitext(input_image)[0]
                output_image = filename_without_ext + "_UP" + os.path.splitext(input_image)[1]
                final_output = filename_without_ext + "_UP.jpg"
                if os.path.exists(final_output):
                    result = messagebox.askquestion("File Exists", "The output file already exists. Do you want to overwrite it?", icon='warning')
                    if result == 'yes':
                        os.remove(final_output)
                    else:
                        self.top_label["text"] = "Upscale Image: Canceled by user..."
                        self.bottom_label["text"] = self.sad_faces()
                        return
                self.start_timer()
                self.select_video_button.config(state='disabled')
                for menu_item in ["Tools", "Options", "File"]:
                    self.menubar.entryconfig(menu_item, state="disabled")
                with subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", input_image, "-o", output_image, "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"], creationflags=subprocess.CREATE_NO_WINDOW) as self.process:
                    self.process.wait()
                os.rename(output_image, final_output)
                self.top_label["text"] = "Output:\n" + final_output
                if not self.process_stopped:
                    self.bottom_label["text"] = "Done Upscaling!"
                self.select_video_button.config(state='normal')
                for menu_item in ["Tools", "Options", "File"]:
                    self.menubar.entryconfig(menu_item, state="normal")
                self.percent_complete.set(100)
                time.sleep(0.1)
                os.startfile(final_output)
                self.stop_timer()
                self.stop_button.config(text="Open Upscaled Image...", command=lambda: os.startfile(final_output))
            else:
                self.top_label["text"] = "No image selected..."
                self.bottom_label["text"] = self.sad_faces()
        except Exception as e:
            self.bottom_label["text"] = f"An error occurred: {str(e)}"
            self.select_video_button.config(state='normal')
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                       #
#region - Batch Upscale #
#                       #

    def browse_source_folder(self):
        self.source_folder = filedialog.askdirectory()
        self.source_folder_entry.delete(0, tk.END)
        self.source_folder_entry.insert(0, self.source_folder)

    def browse_output_folder(self):
        self.output_folder = filedialog.askdirectory()
        self.output_folder_entry.delete(0, tk.END)
        self.output_folder_entry.insert(0, self.output_folder)

    def _batch_upscale(self):
        self.source_folder = self.source_folder_entry.get()
        self.output_folder = self.output_folder_entry.get()
        self.process_stopped = False
        try:
            self.start_timer()
            self.update_timer()
            image_files = [file for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp'] for file in glob.glob(f'{self.source_folder}/{ext}')]
            if not image_files:
                self.top_label["text"] = f"Error: No images found in the source folder."
                self.middle_label["text"] = ""
                self.bottom_label["text"] = self.sad_faces()
                self.stop_timer()
                self.timer_label["text"] = ""
                return
            if not hasattr(self, 'output_folder') or not self.output_folder:
                self.output_folder = os.path.join(self.source_folder, 'output')
                os.makedirs(self.output_folder, exist_ok=True)
            for filename in os.listdir(self.output_folder):
                file_path = os.path.join(self.output_folder, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            start_time = time.time()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            self.top_label["text"] = "Output:\n" + self.output_folder
            frame_total = len(image_files)
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", self.source_folder, "-o", self.output_folder, "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"], creationflags=subprocess.CREATE_NO_WINDOW)
            self.monitor_batch_upscale(frame_total, start_time)
            if not self.process_stopped:
                self.bottom_label["text"] = "Done Upscaling!"
            self.stop_timer()
        except Exception as e:
            self.bottom_label["text"] = f"Error:\n{str(e)}\n\n{self.sad_faces()}"
            self.stop_timer()
        finally:
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                      #
#region - Scale Images #
#                      #

    def auto_scale(self, scale_path):
        self.resize_factor = tk.IntVar()
        self.resize_resolution = tk.StringVar()
        self.scale_path = scale_path
        if self.app_state.get() == "auto_resize_extracted":
            scale_value = self.scale_raw.get()
        elif self.app_state.get() == "auto_resize_upscaled":
            scale_value = self.scale_upscaled.get()
        else:
            scale_value = self.scale_raw.get()
        if ',' in scale_value:
            self.resize_resolution.set(scale_value)
            self.scale_frames(app_state=self.app_state.get())
        else:
            resize_factor = int(scale_value)
            if resize_factor > 500:
                self.resize_factor.set(resize_factor)
                self.scale_frames(app_state=self.app_state.get())
            elif resize_factor > 0:
                self.resize_factor.set(resize_factor)
                self.scale_frames(app_state=self.app_state.get())

    def confirm_scale(self, scale_path):
        self.resize_factor = tk.IntVar()
        self.resize_resolution = tk.StringVar()
        self.scale_path = scale_path
        while True:
            resize_input = simpledialog.askstring("Resize Factor", "Enter a percentage (default=50%) \n\nOr enter a specific resolution (width,height):", initialvalue="50")
            if resize_input is None:
                break
            elif ',' in resize_input:
                self.resize_resolution.set(resize_input)
                self.scale_frames()
                break
            else:
                resize_factor = int(resize_input)
                if resize_factor > 500:
                    result = messagebox.askquestion(f"Large Scale Factor", f"You entered a large scale factor of: {resize_factor}\n\nAre you sure you want to continue?", icon='warning')
                    if result == 'yes':
                        self.resize_factor.set(resize_factor)
                        self.scale_frames()
                        break
                elif resize_factor > 0:
                    self.resize_factor.set(resize_factor)
                    self.scale_frames()
                    break

    def _scale_frames(self, app_state=None):
        self.percent_complete.set(0)
        self.process_stopped = False
        try:
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            image_files = glob.glob(f'{self.scale_path}/*.jpg')
            image_total = len(image_files)
            if not image_files:
                self.top_label["text"] = "No images found!"
                self.bottom_label["text"] = self.sad_faces()
                self.stop_timer()
                self.timer_label["text"] = ""
                return
            self.start_timer()
            self.update_timer()
            image_count = 0
            if ',' in self.resize_resolution.get():
                new_width, new_height = map(int, self.resize_resolution.get().split(','))
            else:
                resize_factor = int(self.resize_factor.get()) / 100
                new_width, new_height = None, None
            start_time = time.time()
            for filename in os.listdir(self.scale_path):
                file_path = os.path.join(self.scale_path, filename)
                if os.path.isfile(file_path):
                    img = Image.open(file_path)
                    if new_width and new_height:
                        img = img.resize((new_width, new_height))
                    else:
                        img = img.resize((int(img.size[0]*resize_factor), int(img.size[1]*resize_factor)))
                    img.save(file_path, "JPEG", quality=100)
                    image_count += 1
                    fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(image_count, image_total, start_time)
                    self.percent_complete.set(percent_complete)
                    self.middle_label["text"] = f"Scaled {image_count:08d}, of {image_total:08d}, {percent_complete:.2f}%\n ETA {eta_str}, FPS {fps:.2f}"
                else:
                    pass
            if not self.process_stopped:
                self.bottom_label["text"] = "Done Resizing!"
            self.stop_timer()
            if app_state == "auto_resize_extracted":
                self.upscale_frames()
            elif app_state == "auto_resize_upscaled":
                self.merge_frames()
        except Exception as e:
            self.top_label["text"] = self.sad_faces()
            self.bottom_label["text"] = f"Error:\n{str(e)}\n\n{self.sad_faces()}"
            self.stop_timer()
        finally:
            self.stop_button.config(text="STOP", command=self.stop_process)
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#               #
#region - Timer #
#               #

    def start_timer(self):
        self.start_time = time.time()
        self.timer_running = True
        self.update_timer()

    def stop_timer(self):
        self.timer_running = False
        elapsed_time = time.time() - self.start_time
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        if hours > 0:
            self.timer_label["text"] = f"Elapsed Time: {int(hours)}hrs, {int(minutes)}min, {seconds:.2f}s"
        elif minutes > 0:
            self.timer_label["text"] = f"Elapsed Time: {int(minutes)}min, {seconds:.2f}s"
        else:
            self.timer_label["text"] = f"Elapsed Time: {seconds:.2f}s"

    def update_timer(self):
        if self.timer_running:
            elapsed_time = time.time() - self.start_time
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)
            if hours > 0:
                self.timer_label["text"] = f"Elapsed Time: {int(hours)}hrs, {int(minutes)}min, {seconds:.2f}s"
            elif minutes > 0:
                self.timer_label["text"] = f"Elapsed Time: {int(minutes)}min, {seconds:.2f}s"
            else:
                self.timer_label["text"] = f"Elapsed Time: {seconds:.2f}s"
            self.after(50, self.update_timer)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                         #
#region - File Management #
#                         #

    def clean_directory(self, directory):
        for filename in os.listdir(directory):
            if os.path.isfile(f'{directory}/{filename}'):
                os.remove(f'{directory}/{filename}')

    def fileMenu_clear_frames(self, directory):
        result = messagebox.askquestion("Delete Frames", "Are you sure you want to delete all frames in {}?".format(directory), icon='warning')
        if result == 'yes':
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

    def open_output_folder(self):
        output_file_name = os.path.splitext(os.path.basename(self.video_file))[0] + "_UPSCALE" + self.file_extension
        output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)
        output_folder = os.path.dirname(output_file_path)
        try:
            os.startfile(os.path.realpath(output_folder))
        except:
            pass
        self.stop_button.config(text="STOP", command=self.stop_process)

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                      #
#region - About Window #
#                      #

    def toggle_about_window(self):
        if self.about_window is not None:
            self.close_about_window()
        else:
            self.open_about_window()

    def open_about_window(self):
        self.about_window = AboutWindow(self.master)
        self.about_window.protocol("WM_DELETE_WINDOW", self.close_about_window)
        main_window_width = root.winfo_width()
        main_window_height = root.winfo_height()
        main_window_x = root.winfo_x() - 225 + main_window_width // 2
        main_window_y = root.winfo_y() - 250 + main_window_height // 2
        self.about_window.geometry("+{}+{}".format(main_window_x, main_window_y))

    def close_about_window(self):
        self.about_window.destroy()
        self.about_window = None

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                        #
#region - Misc Functions #
#                        #

    # Used to position new windows beside the main window.
    def position_dialog(self, dialog, window_width, window_height):
        root_x = self.master.winfo_rootx()
        root_y = self.master.winfo_rooty()
        root_width = self.master.winfo_width()
        position_right = root_x + root_width
        position_top = root_y + -50
        dialog.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

    def copy_to_clipboard(self, event):
        if self.select_video_button.cget('state') == 'disabled':
            return
        widget = event.widget
        text = widget.cget("text")
        if text != "":
            widget.clipboard_clear()
            widget.clipboard_append(text)
            original_text = text
            widget.config(text="Copied!")
            widget.after(250, lambda: widget.config(text=original_text))

    def sad_faces(self):
        string_list = ("( ◎ _ ◎ )", "(╥╯ᗝ╰╥)", "(✖_✖)", "└[ ☉ ل͟ ☉ ]┘", "( ͡ ಠ ʖ̯ ͡ಠ)", "(-`д´-)", "๑(•̀_•́ )ﾉ", "ʕ ͡ಠ ‸ ͡ಠʔ", "[¬＿¬]", "(ಠ︹ಠ)",
                       "(*︵*)", "(ᵔ╭╮ᵔ)", "(-_-)", "(ಥ╭╮ಥ)", "(ᗒ༎︵༎ᗕ)", "(◞╭╮◟)", "(¬︹¬)", "┗(⊙_☉)┘", "(⊚_☉)", "(◈ дﾟ◈)",
                       "〘ఠ _ ఠ〙", "(҂◡╭╮◡)", "⤜(⚆︵⚆)⤏", "|⊙▂⊙|", "(ó︹ò ｡)", "(◡︵◡〞)", "•︵•", "(〃╯︵╰〃)", "(◞ ‸ ◟〟)", "ヽ(☉_☉ )〴",
                       "(ಥ﹏ಥ)", "(⏓﹏⏓)", "(ㆆ _ ㆆ)", "(> _ <)", "(⚆ᗝ⚆)", "⊙︿⊙", "˚‧º·(ᵒ﹏ᵒ)‧º·˚", "¯\_(⊙︿⊙)_/¯", "⁀⊙﹏☉⁀", "¯\_(⊙_ʖ⊙)_/¯",
                       "( ⚆ _ ⚆ )", "(╥﹏╥)", "( T ʖ̯ T)", "(ー_ーゞ", "( º﹃º )", "╮(╯_╰)╭", "(;⌣̀_⌣́)", "꒰•⌓•꒱", "(.づ◡﹏◡)づ.", "◕︵◕")
        pseudo_random_number = hash(str(time.time())) % len(string_list)
        return string_list[pseudo_random_number]

    def reset_settings(self):
        self.upscale_model.set("realesr-animevideov3")
        self.scale_factor.set("2")
        self.output_format.set("mp4")
        self.output_codec.set("libx264")

    # Used to ensure only numbers and a comma can be entered in the resize boxes.
    @staticmethod
    def validate_input(input):
        if all(char.isdigit() or char == ',' for char in input) and input.count(',') <= 1:
            return True
        else:
            return False

    # Handles button highlights.
    def mouse_enter(self, event, color='#e5f3ff'):
        if event.widget['state'] == 'normal':
            event.widget['background'] = color
    def mouse_leave(self, event):
        event.widget['background'] = 'SystemButtonFace'




    def get_widgets(self):
        return [self.model_label,
                self.upscale_model_combobox,
                self.scale_label,
                self.scale_factor_combobox,
                self.output_label,
                self.output_format_combobox,
                self.output_codec_label,
                self.output_codec_combobox,
                self.reset_button,
                self.extra_label,
                self.re_check,
                self.scale_raw_entry,
                self.scale_upscaled_check,
                self.scale_upscaled_entry,

                self.model_label_tab2,
                self.upscale_model_combobox_tab2,
                self.scale_label_tab2,
                self.scale_factor_combobox_tab2,

                self.image_upscale_label,
                self.upscale_image_button,

                self.batch_upscale_label,
                self.source_folder_entry,
                self.source_folder_button,
                self.source_folder_clear_button,
                self.output_folder_label,
                self.output_folder_entry,
                self.output_folder_button,
                self.output_folder_clear_button,
                self.run_batch_button]

    def disable_widgets(self):
        for widget in self.get_widgets():
            widget.config(state='disabled')
    def enable_widgets(self):
        for widget in self.get_widgets():
            widget.config(state='normal')

    def get_buttons(self):
        return [self.select_video_button, self.extract_button, self.merge_button, self.upscale_button]

    def disable_buttons(self):
        for button in self.get_buttons():
            button.configure(state='disabled')
    def enable_buttons(self):
        for button in self.get_buttons():
            button.configure(state='normal')

    def toggle_auto_widgets(self):
        state = "normal" if self.auto_var.get() else "disabled"
        self.extra_label.configure(state=state)
        self.re_check.configure(state=state)
        self.scale_raw_entry.configure(state=state)
        self.scale_upscaled_check.configure(state=state)
        self.scale_upscaled_entry.configure(state=state)

    def stop_process(self):
        if self.process:
            self.process.kill()
            self.process_stopped = True
            self.bottom_label["text"] = "Process Stopped!"
            if self.auto_var.get() == 1:
                self.auto_var.set(0)

    def on_closing(self):
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.communicate(timeout=5)
            except TimeoutExpired:
                self.process.kill()
                self.process.communicate()
        if not self.keep_raw_var.get() and os.path.exists("raw_frames"):
            self.clean_directory("raw_frames")
        if not self.keep_upscaled_var.get() and os.path.exists("upscaled_frames"):
            self.clean_directory("upscaled_frames")
        root.destroy()

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                   #
#region - Framework #
#                   #

def set_appid():
    myappid = 'reav-ui.Nenotriple'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def set_icon(root):
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    elif __file__:
        application_path = os.path.dirname(__file__)
    icon_path = os.path.join(application_path, "icon.ico")
    try:
        root.iconbitmap(icon_path)
    except TclError:
        pass

def set_window_size(root):
    root.resizable(False, False)
    window_width = 520
    window_height = 650
    position_right = root.winfo_screenwidth()//2 - window_width//2
    position_top = root.winfo_screenheight()//2 - window_height//2
    root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

root = tk.Tk()
root.title('v1.15 - R-ESRGAN-AnimeVideo-UI')
app = reav_ui(master=root)
set_appid()
set_window_size(root)
set_icon(root)
app.mainloop()

#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Changelog #
#           #

'''

v1.15 changes:

- New:
  - Tools and options are now displayed in a tabbed interface. This makes using tools like Batch Upscale much easier!
  - Progress bar added.
  - Tons of additional small tweaks and fixes.

<br>

- Fixed:
  -

'''

##########################################################################################################################################################################
##########################################################################################################################################################################
#      #
# todo #
#      #

'''

- Todo
  - Try and process variable frame rate video files.

- Tofix
  -
'''
