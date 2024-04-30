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
Easily upscale your videos and images using R-ESRGAN AI models.

More info here: https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI

Requirements: #
ffmpeg        # Included: Auto-download
ffprobe       # Included: Auto-download
R-ESRGAN      # Included: Auto-download
pillow        # Included: Auto-install

"""


VERSION = "v1.18"

FFMPEG = "./bin/ffmpeg.exe"
FFPROBE = "./bin/ffprobe.exe"
REALESRGAN = "./bin/realesrgan-ncnn-vulkan.exe"


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
from tkinter import ttk, scrolledtext, filedialog, simpledialog, messagebox, Toplevel, Frame, TclError
from subprocess import TimeoutExpired
from PIL import Image, ImageTk, ImageSequence


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                     #
#region - AboutWindow #
#                     #


class AboutWindow(tk.Toplevel):


    info_text  = (
                 "Supported Video Types:\n"
                 "   - mp4, gif, avi, mkv, webm, mov, m4v, wmv\n"

                 "\nNOTE:\n"
                 "   - The Upscale and Merge operations delete the previous frames by default.\n"
                 "   - If you want to keep those frames, make sure to enable the Keep Frames option.\n"
                 "   - The resize operation overwrites frames.\n"

                 "\nUpscale Frames:\n"
                 "   - Select a upscale model in the options/extra menu. Default= realesr-animevideov3 \n"
                 "   - Select a scaling factor in the options/extra menu. Default= x2 \n"

                 "\nTools:\n"
                 "   - Batch Upscale: Upscales all images in a folder. The source images are not deleted.\n"
                 "   - Upscale Image: Upscale a single image. The source image is not deleted.\n"
                 "   - Resize: Scale extracted or upscaled frames to any size.\n"
                 "   - Create Sample: Check this to create a short upscale sample of the selected video.\n"

                 "\nYou can right-click grayed-out buttons to enable them out of sequence.\n"
                 "   - Only use if you know what you're doing!"
                 )


    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("About")
        self.geometry("400x150")
        self.set_icon()


        self.url_button = tk.Button(self, text="Open: github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI", relief="flat", overrelief="groove", fg="blue", command=self.open_url)
        self.url_button.pack(fill="x")

        self.made_by_label = tk.Label(self, text=f"{VERSION} - (2023 - 2024) Created by: Nenotriple", font=("Arial", 11))
        self.made_by_label.pack(anchor="center", pady=5)

        self.credits_text = tk.Label(self, text= ("ffmpeg-6.0-essentials: ffmpeg.org\nReal-ESRGAN_portable: github.com/xinntao/Real-ESRGAN\n\nAnd thank you for using my app! I truly appreciate it (◠‿◠✿)"), justify="left", width=50)
        self.credits_text.pack(pady=5)



    def open_url(self):
        url = 'https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI'
        import webbrowser
        webbrowser.open(url)
        print(f"Opening URL: {url}")

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
        self.id = self.widget.after(20000, self.hide_tip)


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

print(f"rev-ui {VERSION} - https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI\n")

class reav_ui(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=1)


        self.app_state = tk.StringVar()
        self.scale_type = tk.StringVar()
        self.percent_complete = tk.StringVar()
        self.resize_resolution = tk.StringVar()
        self.sample_start_time = tk.StringVar()
        self.skip_upscale = tk.StringVar(value=0)
        self.selected_resize_file = tk.StringVar()
        self.scale_raw = tk.StringVar(value="50%")
        self.scale_factor = tk.StringVar(value="2")
        self.b_src_folder_entry_text = tk.StringVar()
        self.b_out_folder_entry_text = tk.StringVar()
        self.resize_folder_entry_text = tk.StringVar()

        self.output_format = tk.StringVar(value="mp4")
        self.audio_bitrate = tk.StringVar(value="Auto From Source")
        self.video_bitrate = tk.StringVar(value="Auto From Source")
        self.scale_upscaled = tk.StringVar(value="50%")
        self.output_codec = tk.StringVar(value="libx264")
        self.upscale_model = tk.StringVar(value="realesr-animevideov3")

        self.resize_factor = tk.DoubleVar()

        self.auto_var = tk.IntVar(value=0)
        self.keep_raw_var = tk.IntVar(value=0)
        self.sample_duration = tk.IntVar(value=5)
        self.keep_upscaled_var = tk.IntVar(value=0)
        self.generate_sample_var = tk.IntVar(value=0)
        self.auto_resize_upscaled_var = tk.IntVar(value=0)
        self.auto_resize_extracted_var = tk.IntVar(value=0)

        self.single_image_upscale_output = ""


        # Create interface
        self.create_interface()
        self.create_trace()

        # Create frame folders
        self.create_directory('raw_frames')
        self.create_directory('upscaled_frames')


        self.about_window = None
        self.video_file = []
        self.sample_video_file = []
        self.process = None
        self.process_stopped = False
        self.timer_running = False
        self.start_time = time.time()


        # This is the framerate used if the value can't be retrieved from the video.
        self.FALLBACK_FPS = 30


        # These buttons are disabled on startup to guide the user to the "Select Video" button.
        self.extract_button.config(state='disabled')
        self.merge_button.config(state='disabled')
        self.upscale_button.config(state='disabled')


        # This is where we supply definitions for "mimetypes", so it knows these files are videos.
        mimetypes.add_type("video/mkv",  ".mkv")
        mimetypes.add_type("video/webm", ".webm")
        mimetypes.add_type("video/wmv",  ".wmv")
        mimetypes.add_type("video/3gp",  ".3gp")


        # This is where we define all supported video types.
        self.supported_video_types = ["video/mp4", "video/avi",
                                      "video/mkv", "video/mov",
                                      "video/m4v", "video/wmv",
                                      "video/webm", "image/gif",
                                      "video/3gp"]


        # This is where we define all supported image types.
        self.supported_image_types = ['.jpg', '.jpeg', '.jpg_large', '.png', '.jfif', '.webp', '.bmp']


        # This is used to ensure a graceful shutdown when closing the window.
        root.protocol("WM_DELETE_WINDOW", self.on_closing)


    def create_interface(self):
        self.create_menubar()
        self.create_labels()
        self.create_primary_notebook()
        self.create_video_tab1()
        self.create_video_notebook()
        self.create_thumbnail_tab1()
        self.create_extra_settings_tab2()
        self.create_image_tab2()
        self.create_info_tab3()


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                 #
#region - Menubar #
#                 #


    def create_menubar(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)


        # File Menu
        self.fileMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", underline=0, menu=self.fileMenu)
        self.fileMenu.add_command(label="Open: Extracted Frames", underline=6, command=lambda: os.startfile('raw_frames'))
        self.fileMenu.add_command(label="Open: Upscaled Frames", underline=6, command=lambda: os.startfile('upscaled_frames'))
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Clear: Extracted Frames", command=lambda: self.fileMenu_clear_frames('raw_frames'))
        self.fileMenu.add_command(label="Clear: Upscaled Frames", command=lambda: self.fileMenu_clear_frames('upscaled_frames'))


        # Options Menu
        self.optionsMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Options", underline=0, menu=self.optionsMenu)


        # Upscale Model
        self.modelMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Upscale Model", underline=8, menu=self.modelMenu)
        for model in ["realesr-animevideov3", "RealESRGAN_General_x4_v3", "realesrgan-x4plus", "realesrgan-x4plus-anime"]:
            self.modelMenu.add_radiobutton(label=model, variable=self.upscale_model, value=model)


        # Scale Factor
        self.scaleMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Upscale Factor", underline=8, menu=self.scaleMenu)
        for i in ["1", "2", "3", "4"]:
            self.scaleMenu.add_radiobutton(label="x"+i, underline=1, variable=self.scale_factor, value=i)

        self.optionsMenu.add_separator()


        # Output Format
        self.formatMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Video Output: Format", underline=15, menu=self.formatMenu)
        for format in ["mp4", "HQ gif", "LQ gif"]:
            self.formatMenu.add_radiobutton(label=format, variable=self.output_format, value=format)


        # Output Codec
        self.formatMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Video Output: Codec", underline=14, menu=self.formatMenu)
        for format in ["libx264", "libx265"]:
            self.formatMenu.add_radiobutton(label=format, variable=self.output_codec, value=format)


        # Output Video Bitrate
        self.formatMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Output: Video Bitrate", underline=14, menu=self.formatMenu)
        for format in ["Auto", "Auto From Source", "250k", "500k", "1000k", "1500k", "2500k", "3500k", "5000k", "7500k", "10000k", "20000k", "35000k", "50000k", "80000k"]:
            self.formatMenu.add_radiobutton(label=format, variable=self.video_bitrate, value=format)


        # Output Audio Bitrate
        self.audioFormatMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Output: Audio Bitrate", underline=14, menu=self.audioFormatMenu)
        for format in ["Auto", "Auto From Source", "48k", "64k", "128k", "192k", "256k", "320k"]:
            self.audioFormatMenu.add_radiobutton(label=format, variable=self.audio_bitrate, value=format)


        # Tools Menu
        self.toolsMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", underline=0, menu=self.toolsMenu)

        self.toolsMenu.add_command(label="Batch/Single Image Upscale", underline=0, command=lambda: self.primary_notebook.select(self.primary_tab2))
        self.toolsMenu.add_command(label="Upscale a Single Image", underline=10, command=self.select_and_upscale_image)
        self.toolsMenu.add_separator()
        self.toolsMenu.add_command(label="Resize: Extracted Frames", underline=8, command=lambda: self.confirm_scale("raw_frames"))
        self.toolsMenu.add_command(label="Resize: Upscaled Frames", underline=8, command=lambda: self.confirm_scale("upscaled_frames"))


        # About Menu
        self.menubar.add_command(label="About", underline=0, command=self.toggle_about_window)


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                #
#region - Labels #
#                #


    def create_labels(self):
        self.label_frame = tk.Frame(self)
        self.label_frame.pack(side="top", fill="both", expand=True)


        # Filename
        self.top_label = tk.Label(self.label_frame, wraplength=500, text="Select a video to begin!\n\n")
        self.top_label.pack(side="top", fill="x")
        self.top_label.bind("<Button-3>", self.copy_to_clipboard)


        # Console Output
        self.middle_label = tk.Label(self.label_frame, wraplength=500, text="\n")
        self.middle_label.pack(side="top", fill="x")
        self.middle_label.bind("<Button-3>", self.copy_to_clipboard)


        # Operation
        self.bottom_label = tk.Label(self.label_frame, wraplength=500, text="\n")
        self.bottom_label.pack(side="top", fill="x")
        self.bottom_label.bind("<Button-3>", self.copy_to_clipboard)


        # Timer
        self.timer_label = tk.Label(self.label_frame, wraplength=500, text="\n")
        self.timer_label.pack(side="top", fill="x")


        # Progress Bar
        self.progressbar = ttk.Progressbar(self.label_frame)
        self.progressbar.configure(orient="horizontal", variable=self.percent_complete)
        self.progressbar.pack(side="bottom", fill="x", padx=4)


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                                 #
#region - Create Primary Notebook #
#                                 #


    def create_primary_notebook(self):
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


    def create_video_tab1(self):
        self.video_frame = tk.Frame(self.primary_tab1)
        self.video_frame.pack(side="top", pady=4, fill="both", expand=True)


        # Select Video
        self.select_video_frame = tk.Frame(self.video_frame)
        self.select_video_frame.pack(fill="x", expand=True)

        self.select_video_button = tk.Button(self.select_video_frame, takefocus=False, text="1) Select Video\t", width=57)
        self.select_video_button["command"] = self.select_video
        self.select_video_button.pack(side="left", fill="x")
        self.bind_widget_highlight(self.select_video_button)


        # Create Sample
        self.generate_sample_check = tk.Checkbutton(self.select_video_frame, text="Create Sample ", takefocus=False, variable=self.generate_sample_var)
        self.generate_sample_check.pack(side="left", fill="x")
        ToolTip.create_tooltip(self.generate_sample_check,
                                "Enable this to create a sample from the middle of the video."
                                " (Video thumbnail also starts at the middle of the video)\n\n"
                                "Three videos will be created during processing:\n"
                                "  1.*_SAMPLE.* - Created during extraction - Raw sample video\n"
                                "  2.*_UPSCALE.mp4 - Created during upscale - Upscaled sample video\n"
                                "  3.*_HSTACK.mp4 - Created during merge - Raw + Upscaled videos merged in an hstack\n\n"
                                "Samples cannot be created from gif files.\n"
                                "Some videos won't create perfect frame time samples."
                                " In these cases there will be a very small delay between the videos.",250,6,4)
        self.bind_widget_highlight(self.generate_sample_check, add="+")

        self.button_frame1 = tk.Frame(self.video_frame)
        self.button_frame1.pack(fill="x", anchor='center')


        # Extract
        self.extract_button = tk.Button(self.button_frame1, takefocus=False, text="2) Extract Frames  ", justify="left", command=self.extract_frames, width=57, height=1)
        self.extract_button.pack(side="left", fill="x", pady=3)
        self.extract_button.bind('<Button-3>', lambda event: self.extract_button.config(state='normal'))
        self.bind_widget_highlight(self.extract_button)


        # Keep raw_frames
        self.keep_raw_check = tk.Checkbutton(self.button_frame1, takefocus=False, text="Keep\t          ", variable=self.keep_raw_var)
        self.keep_raw_check.pack(side="left", fill="x", pady=3)
        ToolTip.create_tooltip(self.keep_raw_check, "Enable this before Upscaling or closing the window to save Raw Frames.", 250, 6, 4)
        self.bind_widget_highlight(self.keep_raw_check, add="+")

        self.button_frame2 = tk.Frame(self.video_frame)
        self.button_frame2.pack(fill="x", anchor='center')


        # Upscale
        self.upscale_button = tk.Button(self.button_frame2, takefocus=False, text="3) Upscale Frames", justify="left", width=57, height=1)
        self.upscale_button["command"] = self.upscale_frames
        self.upscale_button.pack(side="left", fill="x")
        self.upscale_button.bind('<Button-3>', lambda event: self.upscale_button.config(state='normal'))
        self.bind_widget_highlight(self.upscale_button)


        # Keep upscaled_frames
        self.keep_upscaled_check = tk.Checkbutton(self.button_frame2, takefocus=False, text="Keep", variable=self.keep_upscaled_var)
        self.keep_upscaled_check.pack(side="left", fill="x", pady=3)
        ToolTip.create_tooltip(self.keep_upscaled_check, "Enable this before Merging or closing the window to save Upscaled Frames.", 250, 6, 4)
        self.bind_widget_highlight(self.keep_upscaled_check, add="+")


        # Skip Upscale
        self.skip_upscale_checkbutton = tk.Checkbutton(self.button_frame2, text="Skip ", takefocus=False, variable=self.skip_upscale, command=self.toggle_upscale)
        ToolTip.create_tooltip(self.skip_upscale_checkbutton, "Skip the upscale process.\nUseful if you just want to resize a video", 250, 6, 4)
        self.skip_upscale_checkbutton.pack(side="left", anchor="w")
        self.bind_widget_highlight(self.skip_upscale_checkbutton, add="+")


        self.button_frame3 = tk.Frame(self.video_frame)
        self.button_frame3.pack(fill="x", anchor='center')


        # Merge
        self.merge_button = tk.Button(self.button_frame3, takefocus=False, text="4) Merge Frames  ", justify="left", command=self.merge_frames, width=57)
        self.merge_button.pack(side="left", fill="x")
        self.merge_button.bind('<Button-3>', lambda event: self.merge_button.config(state='normal'))
        self.bind_widget_highlight(self.merge_button)


        # Auto
        self.auto_var.trace_add("write", lambda *args: self.toggle_auto_widgets())
        self.auto_check = tk.Checkbutton(self.button_frame3, takefocus=False, text="Auto\t          ", variable=self.auto_var)
        self.auto_check.pack(side="left", fill="x", pady=3)
        ToolTip.create_tooltip(self.auto_check, "Enable this to automatically Upscale/Merge Frames after Extracting/Upscaling.", 250, 6, 4)
        self.bind_widget_highlight(self.auto_check, add="+")


        # Stop
        self.stop_button = tk.Button(self.video_frame, takefocus=False, text="STOP", command=self.stop_process)
        self.stop_button.pack(side="top", fill="x")
        self.bind_widget_highlight(self.stop_button)


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                               #
#region - Create Video_notebook #
#                               #

    def create_video_notebook(self):
        self.video_notebook = ttk.Notebook(self.primary_tab1, takefocus=False)
        self.thumbnail_tab1 = Frame(self.video_notebook)
        self.extra_tab2 = Frame(self.video_notebook)
        self.info_tab3 = Frame(self.video_notebook)
        self.video_notebook.add(self.thumbnail_tab1, text='Video Thumbnail')
        self.video_notebook.add(self.extra_tab2, text='Extra Settings')
        self.video_notebook.add(self.info_tab3, text='Info')
        self.video_notebook.pack(fill='both')


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                                             #
#region - Create thumbnail_tab1 and info_tab3 #
#                                             #

    def create_thumbnail_tab1(self):
        self.thumbnail_label = tk.Label(self.thumbnail_tab1)
        self.thumbnail_label.pack(side="top", fill="both", expand=True)

        self.infotext = scrolledtext.ScrolledText(self.thumbnail_tab1, wrap="word", font=("TkDefaultFont", 9))
        self.infotext.insert(tk.INSERT, AboutWindow.info_text)
        self.infotext.configure(state='disabled')
        self.infotext.pack(side="top", fill="both", expand=True)


    def create_info_tab3(self):
        infotext = scrolledtext.ScrolledText(self.info_tab3, wrap="word", font=("TkDefaultFont", 9))
        infotext.insert(tk.INSERT, AboutWindow.info_text)
        infotext.configure(state='disabled')
        infotext.pack(side="top", fill="both", expand=True)


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                    #
#region - extra_tab2 #
#                    #

    def create_extra_settings_tab2(self):
####### Video Options ##################################################
        self.options_frame = tk.Frame(self.extra_tab2)
        self.options_frame.pack(side="top", fill="x")


        # Upscale Model
        self.upscale_model_frame = tk.Frame(self.options_frame)
        self.upscale_model_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.model_label = tk.Label(self.upscale_model_frame, text="Upscale Model")
        ToolTip.create_tooltip(self.model_label, "This changes the AI model used for upscaling", 250, 6, 4)
        self.model_label.pack(side="top", anchor="w")

        self.upscale_model_values = ["realesr-animevideov3", "RealESRGAN_General_x4_v3", "realesrgan-x4plus", "realesrgan-x4plus-anime"]
        self.upscale_model_combobox = ttk.Combobox(self.upscale_model_frame, takefocus=False, state="readonly", textvariable=self.upscale_model, values=self.upscale_model_values)
        self.upscale_model_combobox.set("realesr-animevideov3")
        self.upscale_model_combobox.pack(side="left", fill="x", expand=True)


        # Upscale Factor
        self.scale_factor_frame = tk.Frame(self.options_frame)
        self.scale_factor_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.scale_label = tk.Label(self.scale_factor_frame, text="Upscale Factor")
        ToolTip.create_tooltip(self.scale_label, "This is the scaling factor (2 = x2 image size)", 250, 6, 4)
        self.scale_label.pack(side="top", anchor="w")

        self.scale_factor_values = ["1", "2", "3", "4"]
        self.scale_factor_combobox = ttk.Combobox(self.scale_factor_frame, width="6", takefocus=False, state="readonly", textvariable=self.scale_factor, values=self.scale_factor_values)
        self.scale_factor_combobox.set("2")
        self.scale_factor_combobox.pack(side="left", fill="x", expand=True)


        # Output Format Combobox
        self.output_frame = tk.Frame(self.options_frame)
        self.output_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.output_label = tk.Label(self.output_frame, text="Output Format")
        ToolTip.create_tooltip(self.output_label, "This is the video output format", 250, 6, 4)
        self.output_label.pack(side="top", anchor="w")

        self.output_format_values = ["mp4", "HQ gif", "LQ gif"]
        self.output_format_combobox = ttk.Combobox(self.output_frame, width="6", takefocus=False, state="readonly", textvariable=self.output_format, values=self.output_format_values)
        self.output_format_combobox.set("mp4")
        self.output_format_combobox.pack(side="left", fill="x", expand=True)


        # Output Codec Combobox
        self.output_codec_frame = tk.Frame(self.options_frame)
        self.output_codec_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.output_codec_label = tk.Label(self.output_codec_frame, text="Output Codec")
        ToolTip.create_tooltip(self.output_codec_label, "libx264 = Works everywhere / Slightly bigger videos\n\nlibx265 = Saves space, Good for HD / Needs more power, not as much support", 250, 6, 4)
        self.output_codec_label.pack(side="top", anchor="w")

        self.output_codec_values = ["libx264", "libx265"]
        self.output_codec_combobox = ttk.Combobox(self.output_codec_frame, takefocus=False, state="readonly", textvariable=self.output_codec, values=self.output_codec_values)
        self.output_codec_combobox.set("libx264")
        self.output_codec_combobox.pack(side="left", fill="x", expand=True)


        # Options Row 2
        self.options_frame2 = tk.Frame(self.extra_tab2)
        self.options_frame2.pack(side="top", fill="x", padx=2, pady=2)


        # Output video Bitrate
        self.output_bitrate_frame = tk.Frame(self.options_frame2)
        self.output_bitrate_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.output_video_bitrate_label = tk.Label(self.output_bitrate_frame, text="Video Bitrate")
        ToolTip.create_tooltip(self.output_video_bitrate_label, "(Kilobits per second)\nLow value = Smaller file size and lower quality.\nHigher value = Better video quality and larger file.\nOr enter a custom value.\n\nAuto fs - Attempt to force a higher bitrate based on the source bitrate.\nAuto - Let ffmpeg handle bitrate.", 250, 6, 4)
        self.output_video_bitrate_label.pack(side="top", anchor="w")

        self.output_bitrate_values = ["Auto", "Auto From Source", "250k", "500k", "1000k", "1500k", "2500k", "3500k", "5000k", "7500k", "10000k", "20000k", "35000k", "50000k", "80000k"]
        self.output_video_bitrate_combobox = ttk.Combobox(self.output_bitrate_frame, width="16", takefocus=False, textvariable=self.video_bitrate, values=self.output_bitrate_values)
        self.output_video_bitrate_combobox.set("Auto From Source")
        self.output_video_bitrate_combobox.pack(side="left", fill="x", expand=True)


        # Output audio Bitrate
        self.output_audio_bitrate_frame = tk.Frame(self.options_frame2)
        self.output_audio_bitrate_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.output_audio_bitrate_label = tk.Label(self.output_audio_bitrate_frame, text="Audio Bitrate")
        ToolTip.create_tooltip(self.output_audio_bitrate_label, "(Kilobits per second)\nLow value = Smaller file size and lower quality.\nHigher value = Better audio quality and larger file.\nOr enter a custom value.\n\nAuto fs - Attempt to force a higher bitrate based on the source bitrate.\nAuto - Let ffmpeg handle bitrate.", 250, 6, 4)
        self.output_audio_bitrate_label.pack(side="top", anchor="w")

        self.output_audio_bitrate_values = ["Auto", "Auto From Source", "48k", "64k", "128k", "192k", "256k", "320k"]
        self.output_audio_bitrate_combobox = ttk.Combobox(self.output_audio_bitrate_frame, width="16", takefocus=False, textvariable=self.audio_bitrate, values=self.output_audio_bitrate_values)
        self.output_audio_bitrate_combobox.set("Auto From Source")
        self.output_audio_bitrate_combobox.pack(side="left", fill="x", expand=True)


        # Sample Duration Combobox
        self.sample_duration_frame = tk.Frame(self.options_frame2)
        self.sample_duration_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.sample_duration_label = tk.Label(self.sample_duration_frame, text="Sample Duration", state="disabled")
        ToolTip.create_tooltip(self.sample_duration_label, "Sample Duration in seconds\nEnable 'Create Sample' to access.", 250, 6, 4)
        self.sample_duration_label.pack(side="top", anchor="w")

        self.sample_duration_values = [str(i) for i in range(1, 11)]
        self.sample_duration_combobox = ttk.Combobox(self.sample_duration_frame, width="6", takefocus=False, state="disabled", textvariable=self.sample_duration, values=self.sample_duration_values)
        self.sample_duration_combobox.set("5")
        self.sample_duration_combobox.pack(side="left", fill="x", expand=True)


        # Sample Start Time Combobox
        self.sample_start_time_frame = tk.Frame(self.options_frame2)
        self.sample_start_time_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.sample_start_time_label = tk.Label(self.sample_start_time_frame, text="Sample Start Time", state="disabled")
        ToolTip.create_tooltip(self.sample_start_time_label, "Sample Start Time in seconds\nAuto=Middle of video.\nFormat: 00:00:00 - hours:minutes:seconds\nEnable 'Create Sample' to access.", 250, 6, 4)
        self.sample_start_time_label.pack(side="top", anchor="w")

        self.sample_start_time_values = ["Auto", "00:00:00", "00:00:30", "00:05:00", "00:10:00"]
        self.sample_start_time_combobox = ttk.Combobox(self.sample_start_time_frame, values=self.sample_start_time_values, width="6", takefocus=False, textvariable=self.sample_start_time)
        self.sample_start_time.set("Auto")
        self.sample_start_time_combobox.config(state="disabled")
        self.sample_start_time_combobox.pack(side="left", fill="x", expand=True)

        # Reset
        self.reset_frame = tk.Frame(self.extra_tab2)
        self.reset_frame.pack(side="top", fill="x", padx=2, pady=10)
        self.reset_button = tk.Button(self.reset_frame, takefocus=False, text="Reset settings to default", command=lambda: self.reset_settings())
        self.reset_button.pack(fill="x", expand=True)
        self.bind_widget_highlight(self.reset_button)


####### Scale Options ##################################################
        self.scale_frame = tk.Frame(self.extra_tab2, borderwidth=1, relief="groove")
        self.scale_frame.pack(side="top", fill="x")

        self.extra_title_label = tk.Label(self.scale_frame, text="Auto Resize Frames", font=(None, 14))
        ToolTip.create_tooltip(self.extra_title_label, "Enable 'Auto' to interact with these options", 250, 6, 4)
        self.extra_title_label.pack(side="top")


        # Resize extracted frames
        self.scale_raw_frame = tk.Frame(self.scale_frame, borderwidth=1, relief="groove")
        self.scale_raw_frame.pack(side="top", fill="x")

        self.resize_extracted_check = tk.Checkbutton(self.scale_raw_frame, text="Auto resize extracted frames before upscaling:   ", variable=self.auto_resize_extracted_var, takefocus=False, state="disabled")
        self.resize_extracted_check.pack(side="left")
        ToolTip.create_tooltip(self.resize_extracted_check, "This will resize the extracted frames\nIt may be useful to downscale the image, then upscale to the target resolution", 250, 6, 4)
        self.bind_widget_highlight(self.resize_extracted_check, add="+")

        self.scale_raw_entry = tk.Entry(self.scale_raw_frame, textvariable=self.scale_raw, takefocus=False, state="disabled")
        self.scale_raw_entry.pack(side="right", fill="both", expand=True)

        self.spacer_frame3 = tk.Frame(self.scale_frame, height=4)
        self.spacer_frame3.pack(fill="x")


        # Resize upscaled frames
        self.scale_upscaled_frame = tk.Frame(self.scale_frame, borderwidth=1, relief="groove")
        self.scale_upscaled_frame.pack(side="top", fill="x")

        self.scale_upscaled_check = tk.Checkbutton(self.scale_upscaled_frame, text="Auto resize upscaled frames before merging:      ", variable=self.auto_resize_upscaled_var, takefocus=False, state="disabled")
        self.scale_upscaled_check.pack(side="left")
        ToolTip.create_tooltip(self.scale_upscaled_check, "This will resize the upscaled frames\nIt can be used to set the output video resolution", 250, 6, 4)
        self.bind_widget_highlight(self.scale_upscaled_check, add="+")

        self.scale_upscaled_entry = tk.Entry(self.scale_upscaled_frame, textvariable=self.scale_upscaled, takefocus=False, state="disabled")
        self.scale_upscaled_entry.pack(side="right", fill="both", expand=True)

        self.extra_label = tk.Label(self.scale_frame, state="disabled", justify="left", wraplength=480, text="You can enter values in 3 ways:\nPercentage = 10%, 50%, Multiplier = x0.25, x2, Exact Resolution = 100x100 or 200,200")
        self.extra_label.pack(side="top", anchor="w")


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                    #
#region - Image tab2 #
#                    #

    def create_image_tab2(self):
        self.image_options_frame = tk.Frame(self.primary_tab2)
        self.image_options_frame.pack(side="top", fill="x", padx=2, pady=2)

        self.update_model_menu()


        # Upscale Model
        self.upscale_model_frame = tk.Frame(self.image_options_frame)
        self.upscale_model_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.model_label_tab2 = tk.Label(self.upscale_model_frame, text="Upscale Model")
        ToolTip.create_tooltip(self.model_label_tab2, "This changes the AI model used for upscaling", 250, 6, 4)
        self.model_label_tab2.pack(side="top", anchor="w")

        self.upscale_model_combobox_tab2 = ttk.Combobox(self.upscale_model_frame, takefocus=False, state="readonly", textvariable=self.upscale_model, values=self.upscale_model_values)
        self.upscale_model_combobox_tab2.set("realesr-animevideov3")
        self.upscale_model_combobox_tab2.pack(side="left", fill="x", expand=True)


        # Upscale Factor
        self.scale_factor_frame = tk.Frame(self.image_options_frame)
        self.scale_factor_frame.pack(side="left", fill="x", padx=2, pady=2, expand=True)

        self.scale_label_tab2 = tk.Label(self.scale_factor_frame, text="Upscale Factor")
        ToolTip.create_tooltip(self.scale_label_tab2, "This is the scaling factor (2 = x2 image size)", 250, 6, 4)
        self.scale_label_tab2.pack(side="top", anchor="w")

        self.scale_factor_combobox_tab2 = ttk.Combobox(self.scale_factor_frame, takefocus=False, state="readonly", textvariable=self.scale_factor, values=self.scale_factor_values)
        self.scale_factor_combobox_tab2.set("2")
        self.scale_factor_combobox_tab2.pack(side="left", fill="x", expand=True)


####### Single Image ##################################################
        self.image_upscale_frame = tk.Frame(self.primary_tab2)
        self.image_upscale_frame.pack(side="top", pady=4, fill="x")

        self.image_upscale_title_label = tk.Label(self.image_upscale_frame, text="Single Image Upscale", font=(None, 14))
        self.image_upscale_title_label.pack(side="top")

        self.image_upscale_label = tk.Label(self.image_upscale_frame, text="Select a single image to upscale.\nThe output will be saved in the same directory with '_UP' appened to the filename.")
        self.image_upscale_label.pack(side="top")

        self.upscale_image_button = tk.Button(self.image_upscale_frame, takefocus=False, text="Select and upscale image", command=lambda: self.select_and_upscale_image())
        self.upscale_image_button.pack(fill="x", expand=True)
        self.bind_widget_highlight(self.upscale_image_button)

        self.open_dir_button = tk.Button(self.image_upscale_frame, text="Open directory of last upscaled image", takefocus=False, command=lambda: self.open_directory(self.single_image_upscale_output))
        self.open_dir_button.pack(fill="x", expand=True)
        self.bind_widget_highlight(self.open_dir_button)


####### Batch Upscale ##################################################
        self.b_upscale_frame = tk.Frame(self.primary_tab2)
        self.b_upscale_frame.pack(side="top", pady=4, fill="x")

        self.b_upscale_title_label = tk.Label(self.b_upscale_frame, text="Batch Upscale", font=(None, 14))
        self.b_upscale_title_label.pack(side="top")

        self.b_upscale_label = tk.Label(self.b_upscale_frame, text="Select a folder containing images to upscale.\nIf no output folder is selected, an 'output' folder will be created in the source folder.")
        self.b_upscale_label.pack(side="top")


        # Source Folder Frame

        self.b_src_folder_frame = tk.Frame(self.b_upscale_frame)
        self.b_src_folder_frame.pack(side="top", pady=4, fill="x")

        self.b_src_folder_label = tk.Label(self.b_src_folder_frame, text="Source Folder:")
        self.b_src_folder_label.pack(side="left")

        self.b_src_folder_entry = tk.Entry(self.b_src_folder_frame, textvariable=self.b_src_folder_entry_text)
        self.b_src_folder_entry.pack(side="left", fill="x", expand=True)
        self.b_src_folder_button = tk.Button(self.b_src_folder_frame, text="Browse", command=self.browse_source_folder)
        self.b_src_folder_button.pack(side="left")
        self.bind_widget_highlight(self.b_src_folder_button)

        self.b_src_folder_open_button = tk.Button(self.b_src_folder_frame, text="Open", command=lambda: self.open_directory(self.b_src_folder_entry.get()))
        self.b_src_folder_open_button.pack(side="left")
        self.bind_widget_highlight(self.b_src_folder_open_button)

        self.b_src_folder_clr_button = tk.Button(self.b_src_folder_frame, text="X", command=lambda: self.b_src_folder_entry.delete(0, 'end'))
        self.b_src_folder_clr_button.pack(side="left")
        self.bind_widget_highlight(self.b_src_folder_clr_button, color='#ffcac9')


        # Output Folder Frame
        self.b_out_folder_frame = tk.Frame(self.b_upscale_frame)
        self.b_out_folder_frame.pack(side="top", pady=4, fill="x")

        self.b_out_folder_label = tk.Label(self.b_out_folder_frame, text="Output Folder:")
        self.b_out_folder_label.pack(side="left")

        self.b_out_folder_entry = tk.Entry(self.b_out_folder_frame, textvariable=self.b_out_folder_entry_text)
        self.b_out_folder_entry.pack(side="left", fill="x", expand=True)
        self.b_out_folder_button = tk.Button(self.b_out_folder_frame, text="Browse", command=self.browse_output_folder)
        self.b_out_folder_button.pack(side="left")
        self.bind_widget_highlight(self.b_out_folder_button)

        self.b_out_folder_open_button = tk.Button(self.b_out_folder_frame, text="Open", command=lambda: self.open_directory(self.b_out_folder_entry.get()))
        self.b_out_folder_open_button.pack(side="left")
        self.bind_widget_highlight(self.b_out_folder_open_button)

        self.b_out_folder_clr_button = tk.Button(self.b_out_folder_frame, text="X", command=lambda: self.b_out_folder_entry.delete(0, 'end'))
        self.b_out_folder_clr_button.pack(side="left")
        self.bind_widget_highlight(self.b_out_folder_clr_button, color='#ffcac9')


        # Create Run button
        self.run_batch_button = tk.Button(self.b_upscale_frame, text="Run - Batch Upscale", command=self.batch_upscale)
        self.run_batch_button.pack(side="left", fill="x", expand=True)
        self.bind_widget_highlight(self.run_batch_button)


####### Batch Resize Image ##################################################
        self.resize_frame = tk.Frame(self.primary_tab2)
        self.resize_frame.pack(side="top", pady=4, fill="x")

        self.resize_title_label = tk.Label(self.resize_frame, text="Batch Resize Image", font=(None, 14))
        self.resize_title_label.pack(side="top")

        self.resize_label = tk.Label(self.resize_frame, text="Select a folder, click run, choose a scale/resolution. Images are saved to a new folder")
        self.resize_label.pack(side="top")


        # Resize Folder Frame
        self.resize_folder_frame = tk.Frame(self.resize_frame)
        self.resize_folder_frame.pack(side="top", pady=4, fill="x")

        self.resize_folder_label = tk.Label(self.resize_folder_frame, text="Batch Folder:")
        self.resize_folder_label.pack(side="left")

        self.resize_folder_entry = tk.Entry(self.resize_folder_frame, textvariable=self.resize_folder_entry_text)
        self.resize_folder_entry.pack(side="left", fill="x", expand=True)
        self.resize_folder_button = tk.Button(self.resize_folder_frame, text="Browse", command=self.browse_batch_resize_directory)
        self.resize_folder_button.pack(side="left")
        self.bind_widget_highlight(self.resize_folder_button)

        self.resize_folder_open_button = tk.Button(self.resize_folder_frame, text="Open", command=lambda: self.open_directory(self.resize_folder_entry.get()))
        self.resize_folder_open_button.pack(side="left")
        self.bind_widget_highlight(self.resize_folder_open_button)

        self.resize_folder_clr_button = tk.Button(self.resize_folder_frame, text="X", command=lambda: self.resize_folder_entry.delete(0, 'end'))
        self.resize_folder_clr_button.pack(side="left")
        self.bind_widget_highlight(self.resize_folder_clr_button, color='#ffcac9')


        # Resize Button Frame
        self.resize_button_frame = tk.Frame(self.resize_frame)
        self.resize_button_frame.pack(side="top", fill="x", expand=True)

        self.resize_single_button = tk.Button(self.resize_button_frame, text="Run - Resize Single Image", command=lambda: [self.selected_resize_file.set(filedialog.askopenfilename()), self.confirm_scale(self.selected_resize_file.get()), self.open_directory(self.selected_resize_file.get())])
        self.resize_single_button.pack(side="left", fill="x", expand=True)
        self.bind_widget_highlight(self.resize_single_button)

        self.run_resize_button = tk.Button(self.resize_button_frame, text="Run - Batch Resize Image", command=lambda: self.confirm_scale(self.resize_folder_entry.get()))
        self.run_resize_button.pack(side="left", fill="x", expand=True)
        self.bind_widget_highlight(self.run_resize_button)


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                 #
#region - Threads #
#                 #


    def extract_frames(self):
        self.bottom_label["text"] = "Extracting... This may take a while..."
        print("\nExtract Frames: Starting...")
        thread = threading.Thread(target=self._extract_frames)
        thread.daemon = True
        thread.start()


    def upscale_frames(self):
        self.bottom_label["text"] = "Upscaling... This may take a while..."
        print("\nUpscale Frames: Starting...")
        thread = threading.Thread(target=self._upscale_frames)
        thread.daemon = True
        thread.start()


    def merge_frames(self):
        self.bottom_label["text"] = "Merging... This may take a while..."
        print("\nMerge Frames: Starting...")
        thread = threading.Thread(target=self._merge_frames)
        thread.daemon = True
        thread.start()


    def scale_frames(self, app_state=None):
        self.bottom_label["text"] = "Resizing... This may take a while..."
        print("\nResize Frames: Starting...")
        thread = threading.Thread(target=self._scale_frames, args=(app_state,))
        thread.daemon = True
        thread.start()


    def batch_upscale(self):
        self.bottom_label["text"] = "Batch Upscaling... This may take a while..."
        print("\nBatch Upscale: Starting...")
        thread = threading.Thread(target=self._batch_upscale)
        thread.daemon = True
        thread.start()


    def select_and_upscale_image(self):
        self.bottom_label["text"] = "Upscaling Single Image... This may take a while..."
        print("\nUpscale Image: Starting...")
        thread = threading.Thread(target=self._select_and_upscale_image)
        thread.daemon = True
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
                    sys.stdout.write(f"\rExtract Frames: Extracted {frame_count:08d}, of {total_frames:08d}, {percent_complete:.2f}%, ETA: {eta_str}, FPS: {fps:.2f}")
                    sys.stdout.flush()
            else:
                self.middle_label["text"] = f"Extracted {frame_count:08d} frames"

        frame_count = len(glob.glob('raw_frames/*.jpg'))
        if total_frames is not None and not self.process_stopped:
            fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time)
            self.percent_complete.set(100)
            self.middle_label["text"] = f"Extracted {frame_count:08d}, of {frame_count:08d}, 100%\nETA: {eta_str}, FPS: {fps:.2f}"
            sys.stdout.write(f"\rExtract Frames: Extracted {frame_count:08d}, of {frame_count:08d}, 100.00%, ETA: {eta_str}, FPS: {fps:.2f}")
            sys.stdout.flush()
        elif not self.process_stopped:
            self.middle_label["text"] = f"Extracted {frame_count:08d} frames"
        print()


    def monitor_upscale_frames(self, frame_total, start_time):
        self.percent_complete.set(0)
        while self.process.poll() is None:
            frame_count = len(glob.glob('upscaled_frames/*.jpg'))
            if frame_count > 0:
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, frame_total, start_time)
                self.percent_complete.set(percent_complete)
                self.middle_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
                print(f"\rUpscale Frames: Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%, ETA: {eta_str}, FPS: {fps:.2f}", end='')
        print()


    def monitor_merge_frames(self, process, frame_count, total_frames, start_time, start_file_size):
        self.percent_complete.set(0)
        for line in iter(process.stdout.readline, ""):
            frame_number_search = re.search(r'frame=\s*(\d+)', line)
            if frame_number_search:
                frame_count = int(frame_number_search.group(1))
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time, start_file_size)
                self.percent_complete.set(percent_complete)
                self.middle_label["text"] = f"Frame: {frame_count:08d}, of {total_frames:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
                print(f"\rMerge Frames: Merged: {frame_count:08d}, of {total_frames:08d}, {percent_complete:.2f}%, ETA: {eta_str}, FPS: {fps:.2f}", end='')
        print()
        return frame_count


    def monitor_batch_upscale(self, frame_total, start_time):
        self.percent_complete.set(0)
        while self.process.poll() is None:
            frame_count = len(glob.glob(f'{self.batch_output_folder}/*.jpg'))
            fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, frame_total, start_time)
            self.percent_complete.set(percent_complete)
            self.middle_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
            print(f"\rBatch Upscale: Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%, ETA: {eta_str}, FPS: {fps:.2f}", end='')
            time.sleep(0.1)
        print()


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                           #
#region - Primary Functions #
#                           #


    def select_video(self):
        self.percent_complete.set(0)
        self.disable_buttons()
        self.middle_label["text"] = "\n"
        self.bottom_label["text"] = "\n"
        self.timer_label["text"] = "\n"
        self.video_file = filedialog.askopenfilename()
        if self.video_file:
            self.top_label["text"] = f"{os.path.basename(self.video_file)}"
            self.file_extension = os.path.splitext(self.video_file)[1]
            if mimetypes.guess_type(self.video_file)[0] not in self.supported_video_types:
                self.select_video_button.config(state='normal')
                self.top_label["text"] = "Invalid filetype!"
                self.bottom_label["text"] = self.sad_faces()
                print("\nERROR - Select Video: Invalid filetype!")
                if self.thumbnail_label is not None:
                    self.thumbnail_label.config(image='')
                self.video_file = None
                return
            frame_rate, duration, total_frames, dimensions, file_size_megabytes, _, _ = self.collect_stream_info()
            duration_in_seconds = duration
            hours, remainder = divmod(duration_in_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_duration = "{:02}:{:02}:{:02}".format(int(hours)%12, int(minutes), int(seconds))
            self.total_frames = total_frames
            middle_frame_number = int(total_frames) // 2
            middle_frame_time = middle_frame_number / float(frame_rate)
            self.infotext.pack_forget()
            self.show_thumbnail(middle_frame_time)
            self.get_video_dimensions(frame_rate, total_frames, dimensions)
            self.timer_label["text"] = ""
            self.select_video_button.config(state='normal')
            self.extract_button.config(state='normal')
            self.stop_button.config(text="STOP", command=self.stop_process)
            print(f"\n\nSelected Video: {self.video_file}")
            print(f"Selected Video: Frame Rate: {frame_rate:.2f}, Duration: {formatted_duration}, Total Frames: ~{total_frames}, Dimensions: {dimensions}, Filesize: {file_size_megabytes:.2f}MB")
        else:
            self.top_label["text"] = "No file selected!"
            self.bottom_label["text"] = f"{self.sad_faces()}"
            print("\nERROR - Select Video: No file selected!")
            self.select_video_button.config(state='normal')


    def _extract_frames(self):
        if not self.video_file:
            self.bottom_label["text"] = f"Error: No video file selected!\n\n{self.sad_faces()}"
            print("ERROR - Extract Frames: No video file selected!")
            return
        self.process_stopped = False
        try:
            print("Extract Frames: Preparing for extraction...")
            start_time = time.time()
            self.start_timer()
            self.update_timer()
            self.disable_all()
            self.create_directory('raw_frames')
            self.clean_directory('raw_frames')
            try:
                total_frames = int(self.total_frames)
                print(f"Extract Frames: Total frames - ~{total_frames} (Approximate)")
            except Exception as e:
                total_frames = None
                self.bottom_label["text"] = f"Error: {str(e)}\n\n{self.sad_faces()}"
                print(f"ERROR - Extract Frames: {str(e)}")
            print(f"Extract Frames: Sample mode, {'on' if self.generate_sample_var.get() else 'off'}")
            if self.generate_sample_var.get() == 1:
                self.create_sample()
            self.get_video_file()
            self.process = subprocess.Popen([FFMPEG, "-i", self.video_file, "-qscale:v", "3", "-qmin", "3", "-qmax", "3", "-vsync", "0", "raw_frames/frame%08d.jpg"], creationflags=subprocess.CREATE_NO_WINDOW)
            print("Extract Frames: Running")
            self.monitor_extract_frames(self.process, total_frames, start_time)
        finally:
            self.stop_timer()
            self.enable_all()
            if not self.process_stopped:
                self.bottom_label["text"] = f"Done Extracting! {self.happy_faces()}"
                print("Extract Frames: Done!")
            self.stop_button.config(text="STOP", command=self.stop_process)
            if self.auto_var.get() == 1 and self.auto_resize_extracted_var.get() == 1:
                self.app_state.set("auto_resize_extracted")
                self.process_scale_command(("raw_frames"))
            elif self.auto_var.get() == 1:
                self.upscale_frames()
            for button in [self.extract_button, self.merge_button]:
                button.config(state='disabled')


    def _upscale_frames(self):
        if not glob.glob('raw_frames/*.jpg'):
            self.bottom_label["text"] = f"Error: No images to upscale!\n\n{self.sad_faces()}"
            print("ERROR - Upscale Frames: No images to upscale!")
            return
        self.process_stopped = False
        try:
            if self.skip_upscale.get() == '1':
                print("Upscale Frames: Skipping upscaling...")
                raise Exception("Skipping upscaling")
            print("Upscale Frames: Preparing for upscaling...")
            self.create_directory('upscaled_frames')
            self.clean_directory("upscaled_frames")
            self.start_timer()
            self.update_timer()
            self.disable_all()
            frame_total = len(glob.glob('raw_frames/*.jpg'))
            start_time = time.time()
            print(f"Upscale Frames: Found {frame_total} frames to upscale.")
            self.process = subprocess.Popen([REALESRGAN, "-i", "raw_frames", "-o", "upscaled_frames", "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"], creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"Upscale Frames: Running...")
            self.monitor_upscale_frames(frame_total, start_time)
        except Exception as e:
            self.bottom_label["text"] = f"Error: {str(e)}\n\n{self.sad_faces()}"
            print(f"ERROR - Upscale Frames: {str(e)}")
        finally:
            self.stop_timer()
            self.enable_all()
            self.stop_button.config(text="STOP", command=self.stop_process)
            for button in [self.extract_button, self.upscale_button]:
                button.config(state='disabled')
        if self.keep_raw_var.get() == 0:
            print("Upscale Frames: Removing raw frames...")
            self.clean_directory("raw_frames")
        if not self.process_stopped:
            if self.skip_upscale.get() == '1':
                self.bottom_label["text"] = f"Skipped Upscaling!  {self.happy_faces()}"
            else:
                self.bottom_label["text"] = f"Done Upscaling!  {self.happy_faces()}"
            print("Upscale Frames: Done!")
        if self.auto_var.get() == 1 and self.auto_resize_upscaled_var.get() == 1:
            self.app_state.set("auto_resize_upscaled")
            self.process_scale_command(("upscaled_frames"))
        elif self.auto_var.get() == 1:
            self.merge_frames()


    def _merge_frames(self):
        if not self.video_file:
            self.bottom_label["text"] = f"Error: No video file selected!\n\n{self.sad_faces()}"
            print("ERROR - Merge Frames: No video file selected!")
            return
        self.process_stopped = False
        try:
            print("Merge Frames: Preparing for frame merge...")
            self.get_video_file()
            self.start_timer()
            self.disable_all()
            total_frames = len(os.listdir("upscaled_frames"))
            print(f"Merge Frames: Total frames to merge - {total_frames}")
            self.file_extension = os.path.splitext(self.video_file)[1]
            start_file_size = os.path.getsize(self.video_file)
            command, self.output_file_path = self.get_merge_frames_command()
            print(f"Merge Frames: Input Video - {os.path.normpath(self.video_file)}\nMerge Frames: Output Video - {os.path.normpath(self.output_file_path)}")
            print(f"Merge Frames: Command - {command}")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"Merge Frames: Running...")
            start_time = time.time()
            frame_count = 0
            frame_count = self.monitor_merge_frames(process, frame_count, total_frames, start_time, start_file_size)
            process.stdout.close()
            process.wait()
            end_file_size = os.path.getsize(self.output_file_path)
            _, _, _, percent_change, start_file_size_MB, end_file_size_MB = self.calculate_metrics(frame_count, total_frames, start_time, start_file_size, end_file_size)
            _, _, _, dimensions, _, _, _ = self.collect_stream_info()
            input_size = dimensions
            width, heigth = self.first_frame_size
            self.stop_timer()
            if not self.process_stopped:
                self.bottom_label["text"] = f"Done Merging!  {self.happy_faces()}\nOriginal size: {start_file_size_MB:.2f}MB, Final size: {end_file_size_MB:.2f}MB, Change: {percent_change:.2f}%"
                print(f"Merge Frames: Done Merging! - Original size: {start_file_size_MB:.2f}MB, Final size: {end_file_size_MB:.2f}MB, Change: {percent_change:.2f}%")
                print(f"Merge Frames: Input size ({input_size})")
                print(f"Merge Frames: Output Size {width, heigth}")
                print(f"Merge Frames: Done!")
            if os.path.isfile("bin/palette001.png"):
                os.remove("bin/palette001.png")
            if not self.keep_upscaled_var.get():
                print("Merge Frames: Removing upscaled frames...")
                self.clean_directory("upscaled_frames")
            if self.skip_upscale.get() == '1':
                print("Merge Frames: Removing raw frames...")
                self.clean_directory("raw_frames")
            if not self.process_stopped:
                self.middle_label["text"] = "Output:\n" + os.path.normpath(self.output_file_path)
            self.stop_button.config(text="Open Output Folder...", command=self.open_output_folder)
        except AttributeError as e:
            self.stop_timer()
            self.bottom_label["text"] = f"Error: {str(e)}\n\n{self.sad_faces()}"
            print(f"ERROR - Merge Frames: {str(e)}")
        finally:
            self.enable_all()
            for button in [self.extract_button, self.upscale_button, self.merge_button]:
                button.config(state='disabled')
            print("Merge Frames: Process complete!")
        if self.generate_sample_var.get() == 1:
            self.merge_samples()


    def get_video_file(self):
        if self.video_file.endswith('.gif'):
            print("ERROR - Merge Frames: Cannot create a sample of a .gif file")
        if self.generate_sample_var.get() == 1:
            self.original_video_file = self.video_file
            self.video_file = self.sample_video_file
        elif self.generate_sample_var.get() == 0:
            self.video_file = self.video_file


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                           #
#region - Get Merge Command #
#                           #


    def get_merge_frames_command(self):
        if not self.video_file:
            return
        frame_rate, _, _, _, _, src_video_bitrate, src_audio_bitrate = self.collect_stream_info()
        print(f"Video Bitrate: {src_video_bitrate}, Audio Bitrate: {src_audio_bitrate}")
        output_file_name = os.path.splitext(os.path.basename(self.video_file))[0] + "_UPSCALE"
        is_gif = self.output_format.get() in ['HQ gif', 'LQ gif']
        output_file_name += f"_{self.output_format.get().split()[0]}" if is_gif else ''
        output_file_name += '.gif' if is_gif else '.mp4'
        self.output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)
        print(f"Skip Upscale: {self.skip_upscale.get()}")
        frame_folder = 'raw_frames' if self.skip_upscale.get() == '1' else 'upscaled_frames'
        first_frame = Image.open(f'{frame_folder}/frame00000001.jpg')
        self.first_frame_size = first_frame.size
        width, height = first_frame.size
        frame_input = f"{frame_folder}/frame%08d.jpg"
        if is_gif:
            print(f"Merge Frames: Preparing {'HQ' if self.output_format.get() == 'HQ gif' else 'LQ'} gif command.")
            if self.output_format.get() == 'HQ gif':
                palette_path = "bin/palette%03d.png"
                command_palettegen = [FFMPEG, "-y", "-i", frame_input, "-vf", "palettegen", palette_path]
                subprocess.call(command_palettegen, creationflags=subprocess.CREATE_NO_WINDOW)
                command = [FFMPEG, "-y", "-r", str(frame_rate), "-i", frame_input, "-i", palette_path, "-filter_complex", "paletteuse", "-s", f"{width}x{height}", self.output_file_path]
            else:
                command = [FFMPEG, "-y", "-r", str(frame_rate), "-i", frame_input, "-c:v", 'gif', "-s", f"{width}x{height}", self.output_file_path]
        else:
            print("Merge Frames: Preparing video command.")
            command = [FFMPEG, "-y", "-r", str(frame_rate), "-i", frame_input, "-i", self.video_file, "-c:v", self.output_codec.get(), "-g", "10"]
            command.extend(self.get_bitrate_command('v', self.video_bitrate.get(), src_video_bitrate))
            command.extend(self.get_bitrate_command('a', self.audio_bitrate.get(), src_audio_bitrate))
            command.extend(["-s", f"{width}x{height}", self.output_file_path])
        if self.file_extension != '.gif':
            command.extend(["-c:a", "copy", "-vsync", "0", "-map", "0:0", "-map", "0:1", "-pix_fmt", "yuv420p"])
        return command, self.output_file_path


    def get_bitrate_command(self, type: str, bitrate: str, src_bitrate: int):
        command = []
        if bitrate.startswith('Auto From Source'):
            extra_bitrate = int(bitrate.split('+')[1]) if '+' in bitrate else 1500
            if src_bitrate is not None:
                bitrate = str(int(src_bitrate) + extra_bitrate) + 'k'
                command.extend([f"-b:{type}", bitrate])
        elif bitrate != 'Auto':
            bitrate = bitrate if bitrate.endswith('k') else bitrate + 'k'
            command.extend([f"-b:{type}", bitrate])
        return command


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                             #
#region - Secondary Functions #
#                             #


    def run_ffprobe(self, args):
        if not self.video_file:
            return
        return subprocess.run([FFPROBE] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW).stdout.decode().strip()


    def create_sample(self):
        print("Create Sample: Starting...")
        self.percent_complete.set(0)
        frame_rate, _, total_frames, _, _, _, _ = self.collect_stream_info()
        video_duration = total_frames / float(frame_rate)
        middle_frame_number = int(total_frames) // 2
        middle_frame_time = middle_frame_number / float(frame_rate)
        trim_duration = min(self.sample_duration.get(), video_duration)
        try:
            time_parts = [int(part) for part in self.sample_start_time.get().split(':')]
            if len(time_parts) != 3:
                raise ValueError
            start_time = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]
            if start_time < 0 or start_time > video_duration:
                raise ValueError
        except ValueError:
            print("ERROR - Create Sample: Invalid time format for sample_start_time. It should be in the format '00:00:00' or 'hours:minutes:seconds'\nERROR - Create Sample: Reverting to 'middle frame time'.")
            start_time = max(0, middle_frame_time - trim_duration / 2)

        end_time = start_time + trim_duration
        self.sample_video_file = os.path.splitext(self.video_file)[0] + "_SAMPLE" + self.file_extension
        print(f"Create Sample: Duration {trim_duration}s")
        print(f"Create Sample: Input, {os.path.normpath(self.video_file)}")
        command = [FFMPEG, "-y", "-i", self.video_file, "-ss", str(start_time), "-to", str(end_time), "-c:v", "libx264", "-crf", "18", "-preset", "slow", self.sample_video_file]
        self.percent_complete.set(25)
        self.process = subprocess.Popen(command, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
        self.process.wait()
        self.percent_complete.set(100)
        print(f"Create Sample: Output {os.path.normpath(self.sample_video_file)}")


    def merge_samples(self):
        print("\nCreate Sample: Merge - Starting...")
        try:
            self.start_timer()
            self.percent_complete.set(0)
            width, height = self.first_frame_size
            dimensions = f"{width}x{height}"
            filename, _ = os.path.splitext(self.sample_video_file)
            _, output_extension = os.path.splitext(self.output_file_path)
            resized_sample_output = f"{filename}_RESIZE{output_extension}"
            resize_command = [FFMPEG, "-y", "-i", self.sample_video_file, "-vf", f"scale={dimensions}", resized_sample_output]
            self.middle_label["text"] = f"Create Sample: \n Resizing - {filename}"
            self.bottom_label["text"] = "Resizing Sample..."
            print("Create Sample: Merge - Resizing...")
            self.percent_complete.set(25)
            resize_process = subprocess.Popen(resize_command, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
            resize_process.wait()
            self.percent_complete.set(100)
            print("Create Sample: Merge - Resize Complete!")
            final_output = f"{filename}_HSTACK{output_extension}"
            merge_command = [FFMPEG, "-y", "-i", resized_sample_output, "-i", self.output_file_path, "-filter_complex", "hstack", final_output]
            self.middle_label["text"] = "Create Sample: \n Merging resized + Upscaled sample"
            self.bottom_label["text"] = "Merging Samples..."
            print("Create Sample: Merge - Merging samples...")
            self.percent_complete.set(50)
            merge_process = subprocess.Popen(merge_command, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
            merge_process.wait()
            self.percent_complete.set(100)
            self.middle_label["text"] = f"Create Sample: Output: \n{os.path.normpath(final_output)}"
            self.bottom_label["text"] = "Merge Complete!"
            self.stop_timer()
            print(f"Create Sample: Merge - Output - {os.path.normpath(final_output)}")
            print("Create Sample: Merge - Merge Complete!")
            if os.path.exists(resized_sample_output):
                os.remove(resized_sample_output)
        except Exception as e:
            self.stop_timer()
            self.percent_complete.set(0)
            print(f"ERROR - Create Sample: Merge - An error occurred: {e}")


    def show_thumbnail(self, middle_frame_time):
        _, duration, _, _, _, _, _ = self.collect_stream_info()

        def create_image(img):
            max_size = (500, 400)
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
                self.after_id = self.thumbnail_label.after(120, update, (index+1)%len(frames))

            self.after_id = self.thumbnail_label.after(120, update, 1)
        else:
            def update_thumbnail():
                nonlocal middle_frame_time
                if not animation_running:
                    return
                middle_frame_time = (middle_frame_time + 2) % duration
                if middle_frame_time > duration:
                    middle_frame_time = duration
                result = subprocess.run([FFMPEG, "-ss", str(middle_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    img = Image.open(io.BytesIO(result.stdout))
                    photoImg = create_image(img)
                    self.thumbnail_label.configure(image=photoImg)
                    self.thumbnail_label.image = photoImg
                    self.after_id = self.thumbnail_label.after(2000, update_thumbnail)
                except Image.UnidentifiedImageError:
                    print("ERROR - Unable to process animated thumbnail...")

            def show_context_menu(event):
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()

            def toggle_thumbnail_update():
                nonlocal animation_running
                animation_running = not animation_running
                if animation_running:
                    update_thumbnail()
                else:
                    if hasattr(self, 'after_id'):
                        self.thumbnail_label.after_cancel(self.after_id)

            result = subprocess.run([FFMPEG, "-ss", str(middle_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            img = Image.open(io.BytesIO(result.stdout))
            photoImg = create_image(img)
            self.thumbnail_label.configure(image=photoImg)
            self.thumbnail_label.bind("<Double-1>", lambda e: self.open_output_folder())
            self.thumbnail_label.image = photoImg
            ToolTip.create_tooltip(self.thumbnail_label, "Double click to open source folder", 1000, 6, 4)
            self.context_menu = tk.Menu(self.thumbnail_label, tearoff=0)
            self.context_menu.add_command(label="Open Source Folder", command=lambda: self.open_output_folder())
            self.context_menu.add_separator()
            self.context_menu.add_checkbutton(label="Toggle Animated Thumbnail", command=toggle_thumbnail_update)
            self.thumbnail_label.bind("<Button-3>", show_context_menu)
            animation_running = False


    def update_scale_factor(self, *args):
        model_names_without_extension = [os.path.splitext(model)[0] for model in self.new_models]
        if self.upscale_model.get() in model_names_without_extension:
            state = "normal"
            self.scale_factor.set("4")
        elif self.upscale_model.get() == "realesr-animevideov3":
            state = "normal"
            self.scale_factor.set("2")
        else:
            state = "disabled"
            self.scale_factor.set("4")
        for i in range(4):
            self.scaleMenu.entryconfig(i, state=state)
        self.scale_factor_combobox.config(state="readonly" if state == "normal" else state)
        self.scale_factor_combobox_tab2.config(state="readonly" if state == "normal" else state)


    def update_model_menu(self):
        existing_models = ["realesr-animevideov3-x1.bin", "realesr-animevideov3-x2.bin", "realesr-animevideov3-x3.bin", "realesr-animevideov3-x4.bin", "RealESRGAN_General_x4_v3.bin", "realesrgan-x4plus.bin", "realesrgan-x4plus-anime.bin"]
        self.modelMenu.add_separator()
        all_models = [f for f in os.listdir("bin/models") if f.endswith('.bin')]
        self.new_models = [model for model in all_models if model not in existing_models]
        for model in self.new_models:
            model_name, _ = os.path.splitext(model)
            self.modelMenu.add_radiobutton(label=model_name, variable=self.upscale_model, value=model_name)
            self.upscale_model_values.append(model_name)
            print(f"Additional upscale models found: {self.new_models}")
        self.upscale_model_combobox['values'] = self.upscale_model_values


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
            _, _, self.total_frames, _, _, _, _ = self.collect_stream_info()
            self.total_frames = int(self.total_frames) if self.total_frames else self.FALLBACK_FPS
        self.frame_rate = self.run_ffprobe(["-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file])
        numerator, denominator = map(int, self.frame_rate.split('/'))
        self.frame_rate = numerator / denominator


    def collect_stream_info(self):
        if not self.video_file:
            return
        cmd = ["-show_format", "-show_streams", self.video_file]
        ffprobe_output = self.run_ffprobe(cmd)
        video_info = re.search(r"Stream #0:0.* (\d+) kb/s", ffprobe_output)
        if video_info:
            src_video_bitrate = int(video_info.group(1))
        else:
            src_video_bitrate = None
        audio_info = re.search(r"Stream #0:1.* (\d+) kb/s", ffprobe_output)
        if audio_info:
            src_audio_bitrate = int(audio_info.group(1))
        else:
            src_audio_bitrate = None
        r_frame_rate = re.search(r"r_frame_rate=(\d+)/(\d+)", ffprobe_output)
        if r_frame_rate:
            numerator = int(r_frame_rate.group(1))
            denominator = int(r_frame_rate.group(2))
            if denominator != 0:
                frame_rate = numerator / denominator
            else:
                stream_info = re.search(r"Stream #0:1.* (\d+\.\d+) fps", ffprobe_output)
                if stream_info:
                    frame_rate = float(stream_info.group(1))
                else:
                    frame_rate = None
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
        return frame_rate, duration, total_frames, f"{coded_width}x{coded_height}", file_size_megabytes, src_video_bitrate, src_audio_bitrate


    def get_video_dimensions(self, *args):
        if not self.video_file:
            return
        frame_rate, _, total_frames, dimensions, file_size_megabytes, _, _ = self.collect_stream_info()
        scale_factor = int(self.scale_factor.get())
        coded_width, coded_height = map(int, dimensions.split('x'))
        new_dimensions = f"{coded_width*scale_factor}x{coded_height*scale_factor}"
        if total_frames:
            video_length_seconds = int(total_frames) / float(frame_rate)
            video_length_time_string = str(datetime.timedelta(seconds=int(video_length_seconds)))
            self.middle_label["text"] = f"Video Dimensions: {dimensions}\nUpscaled:  x{scale_factor}, {new_dimensions}"
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
            print("Upscale Image: Preparing for upscale...")
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
                    print("ERROR - Upscale Image: Invalid image type.")
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
                        print("Upscale Image: Operation canceled by user.")
                        return
                self.start_timer()
                self.select_video_button.config(state='disabled')
                print(f"Upscale Image: Input, {os.path.normpath(input_image)}\nUpscale Image: Output, {os.path.normpath(output_image)}")
                print(f"Upscale Image: Upscale Model, {self.upscale_model.get()}\nUpscale Image: Scale Factor, {self.scale_factor.get()}")
                with subprocess.Popen([REALESRGAN, "-i", input_image, "-o", output_image, "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"], creationflags=subprocess.CREATE_NO_WINDOW) as self.process:
                    print(f"Upscale Image: Running")
                    self.process.wait()
                os.rename(output_image, final_output)
                self.top_label["text"] = "Output:\n" + final_output
                if not self.process_stopped:
                    self.bottom_label["text"] = f"Done Upscaling! {self.happy_faces()}"
                    print("Upscale Image: Upscaling completed.")
                self.select_video_button.config(state='normal')
                self.percent_complete.set(100)
                time.sleep(0.1)
                os.startfile(final_output)
                self.single_image_upscale_output = final_output
                print("Upscale Image: Opening upscaled image...")
                self.stop_timer()
                self.stop_button.config(text="Open Upscaled Image...", command=lambda: os.startfile(final_output))
            else:
                self.top_label["text"] = "No image selected..."
                self.bottom_label["text"] = self.sad_faces()
                print("Upscale Image: No image selected.")
        except Exception as e:
            self.bottom_label["text"] = f"An error occurred: {str(e)}"
            self.select_video_button.config(state='normal')
            self.stop_timer()
            print(f"ERROR - Upscale Image: {str(e)}")


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                       #
#region - Batch Upscale #
#                       #


    def browse_source_folder(self):
        self.batch_source_folder = filedialog.askdirectory()
        self.b_src_folder_entry.delete(0, tk.END)
        self.b_src_folder_entry.insert(0, os.path.normpath(self.batch_source_folder))
        ToolTip.create_tooltip(self.b_src_folder_entry, os.path.normpath(self.batch_source_folder), 250, 6, 16)


    def browse_output_folder(self):
        self.batch_output_folder = filedialog.askdirectory()
        self.b_out_folder_entry.delete(0, tk.END)
        self.b_out_folder_entry.insert(0, os.path.normpath(self.batch_output_folder))
        ToolTip.create_tooltip(self.b_out_folder_entry, os.path.normpath(self.batch_output_folder), 250, 6, 16)


    def _batch_upscale(self):
        self.batch_source_folder = self.b_src_folder_entry.get()
        self.batch_output_folder = self.b_out_folder_entry.get()
        self.process_stopped = False
        try:
            print("Batch Upscale: Preparing for batch upscale...")
            self.start_timer()
            self.update_timer()
            self.disable_all()
            image_files = [file for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp'] for file in glob.glob(f'{self.batch_source_folder}/{ext}')]
            if not image_files:
                self.top_label["text"] = f"Error: No images found in the source folder."
                self.middle_label["text"] = ""
                self.bottom_label["text"] = self.sad_faces()
                print("ERROR - Batch Upscale: No images found in the source folder.")
                self.stop_timer()
                self.timer_label["text"] = ""
                return
            if not self.batch_output_folder or not os.path.isdir(self.batch_output_folder):
                self.batch_output_folder = os.path.join(self.batch_source_folder, 'output')
            self.create_directory(f'{self.batch_output_folder}')
            self.b_out_folder_entry_text.set(f"{os.path.normpath(self.batch_output_folder)}")
            print("Batch Upscale: Cleaning output folder...")
            for filename in os.listdir(self.batch_output_folder):
                file_path = os.path.join(self.batch_output_folder, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            start_time = time.time()
            self.top_label["text"] = "Output:\n" + self.batch_output_folder
            frame_total = len(image_files)
            print(f"Batch Upscale: Input, {os.path.normpath(self.batch_source_folder)}\nBatch Upscale: Output, {os.path.normpath(self.batch_output_folder)}")
            self.process = subprocess.Popen([REALESRGAN, "-i", self.batch_source_folder, "-o", self.batch_output_folder, "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"], creationflags=subprocess.CREATE_NO_WINDOW)
            print("Batch Upscale: Running...")
            self.monitor_batch_upscale(frame_total, start_time)
            if not self.process_stopped:
                self.bottom_label["text"] = f"Done Upscaling! {self.happy_faces()}"
                print(f"Batch Upscale: Upscaling completed. Output: {os.path.normpath(self.batch_output_folder)}")
        except Exception as e:
            self.bottom_label["text"] = f"Error:\n{str(e)}\n\n{self.sad_faces()}"
            print(f"ERROR - Batch Upscale: {str(e)}")
            self.stop_timer()
        finally:
            self.stop_timer()
            self.enable_all()


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                      #
#region - Scale Images #
#                      #


    def browse_batch_resize_directory(self):
        batch_resize_directory = filedialog.askdirectory()
        self.resize_folder_entry_text.set(os.path.normpath(batch_resize_directory))
        ToolTip.create_tooltip(self.resize_folder_entry, batch_resize_directory, 250, 6, 16)


    def process_scale_command(self, scale_path):
        print("\nProcess Scale Command: Starting...")
        self.scale_path = scale_path
        print(f"Process Scale Command: Scaling path, '{self.scale_path}'.")
        if self.app_state.get() == "auto_resize_extracted":
            scale_value = self.scale_raw.get()
        elif self.app_state.get() == "auto_resize_upscaled":
            scale_value = self.scale_upscaled.get()
        else:
            scale_value = self.resize_resolution.get()
        print(f"Process Scale Command: Scale value set to {scale_value}.")
        if ',' in scale_value:
            self.resize_resolution.set(scale_value)
            self.scale_frames(app_state=self.app_state.get())
        elif 'x' in scale_value:
            if scale_value.startswith('x'):
                resize_factor = float(scale_value.replace('x', ''))
                self.resize_factor.set(resize_factor)
                self.scale_type.set('multiplier')
                self.scale_frames(app_state=self.app_state.get())
            else:
                width, height = scale_value.split('x')
                self.resize_resolution.set(f"{width}x{height}")
                self.scale_frames(app_state=self.app_state.get())
        else:
            if '%' in scale_value:
                resize_factor = int(scale_value.replace('%', ''))
                self.scale_type.set('percentage')
            else:
                resize_factor = int(scale_value)
            if resize_factor > 500:
                self.resize_factor.set(resize_factor)
                self.scale_frames(app_state=self.app_state.get())
            elif resize_factor > 0:
                self.resize_factor.set(resize_factor)
                self.scale_frames(app_state=self.app_state.get())


    def confirm_scale(self, scale_path):
        if not scale_path:
            return
        while True:
            resize_input = simpledialog.askstring(f"Resize: '{scale_path}'", "Enter a percentage, (default=50%) \n\nOr Multiplier, (x2, x0.25)\n\nOr a specific resolution, (width,height or widthxheight)\n", initialvalue="50%")
            if resize_input is None or resize_input == '':
                break
            else:
                if re.match("^[0-9,%,x,.]*$", resize_input):
                    self.resize_resolution.set(resize_input)
                    self.process_scale_command(f'{scale_path}')
                    break
                else:
                    messagebox.showerror("Invalid Input", "Expected input includes:\nDigits, Comma, Perioid, Percent, and x\n\nExamples:\nPercentage = 50%\nExact resolution = 100,100 or 200x200\nMultiplier= x2, x0.25")


    def _scale_frames(self, app_state=None):
        self.percent_complete.set(0)
        self.process_stopped = False
        try:
            print("Resize Frames: Preparing for Resize...")
            if os.path.isdir(self.scale_path):
                image_files = [f for f in glob.glob(f'{self.scale_path}/*') if os.path.splitext(f)[1] in self.supported_image_types]
            else:
                image_files = [self.scale_path] if os.path.splitext(self.scale_path)[1] in self.supported_image_types else []
            image_total = len(image_files)
            print(f"Resize Frames: Found {image_total} images to resize.")
            if not image_files:
                self.top_label["text"] = "No images found!"
                self.bottom_label["text"] = self.sad_faces()
                print("ERROR - Resize Frames: No images found!")
                self.stop_timer()
                self.timer_label["text"] = ""
                return
            self.start_timer()
            self.update_timer()
            self.disable_all()
            self.perform_scale(image_total)
            if not self.process_stopped:
                self.bottom_label["text"] = f"Done Resizing! {self.happy_faces()}"
                self.stop_timer()
                print("Resize Frames: Done!")
                if app_state == "auto_resize_extracted":
                    self.upscale_frames()
                elif app_state == "auto_resize_upscaled":
                    self.merge_frames()
        except Exception as e:
            self.bottom_label["text"] = f"Error:\n{str(e)}\n\n{self.sad_faces()}"
            print(f"\nERROR - Resize Frames: {str(e)}")
            self.stop_timer()
        finally:
            self.enable_all()
            self.stop_button.config(text="STOP", command=self.stop_process)


    def perform_scale(self, image_total):
        image_count = 0
        scale_value = self.resize_resolution.get()
        start_time = time.time()
        if os.path.isdir(self.scale_path):
            filenames = os.listdir(self.scale_path)
        else:
            filenames = [os.path.basename(self.scale_path)] if self.scale_path.endswith(tuple(self.supported_image_types)) else []
            self.scale_path = os.path.dirname(self.scale_path)
        output_folder = os.path.join(self.scale_path, 'Resize Output')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        for filename in filenames:
            file_path = os.path.join(self.scale_path, filename)
            if os.path.isfile(file_path) and filename.endswith(tuple(self.supported_image_types)):
                img = Image.open(file_path)
                original_size = img.size
                if ',' in scale_value:
                    new_width, new_height = map(int, scale_value.split(','))
                elif 'x' in scale_value:
                    if self.scale_type.get() == 'multiplier':
                        resize_factor = float(scale_value.replace('x', ''))
                        new_width, new_height = None, None
                    else:
                        new_width, new_height = map(int, scale_value.split('x'))
                else:
                    resize_factor = self.resize_factor.get()
                    if self.scale_type.get() == 'percentage':
                        resize_factor /= 100.0
                    new_width, new_height = None, None
                if new_width and new_height:
                    img = img.resize((new_width, new_height))
                else:
                    img = img.resize((int(img.size[0]*resize_factor), int(img.size[1]*resize_factor)))
                new_size = img.size
                output_file_path = os.path.join(output_folder, filename)
                img.save(output_file_path, "JPEG", quality=100)
                image_count += 1
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(image_count, image_total, start_time)
                self.percent_complete.set(percent_complete)
                self.middle_label["text"] = f"Scaled {image_count:08d}, of {image_total:08d}, {percent_complete:.2f}%\n ETA {eta_str}, FPS {fps:.2f}"
                if image_count == 1:
                    print(f"Resize Frames: Original resolution {original_size}.")
                    print(f"Resize Frames: New resolution {new_size}.")
                else:
                    print(f"\rResize Frames: Scaled {image_count} of {image_total} images.", end="")
            else:
                pass
        print()



#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#               #
#region - Timer #
#               #


    def start_timer(self):
        self.start_time = time.time()
        self.timer_running = True
        print(f'TIMER - {time.strftime("%I:%M:%S %p")}, Start')
        self.update_timer()


    def stop_timer(self):
        self.timer_running = False
        elapsed_time = time.time() - self.start_time
        formatted_time = self.format_time(elapsed_time)
        print(f'TIMER - {time.strftime("%I:%M:%S %p")}, End\nTIMER - {formatted_time}, Elapsed')


    def update_timer(self):
        if self.timer_running:
            elapsed_time = time.time() - self.start_time
            self.timer_label["text"] = f"Elapsed Time: {self.format_time(elapsed_time)}"
            self.after(50, self.update_timer)


    @staticmethod
    def format_time(elapsed_time):
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        if hours > 0:
            return f"{int(hours)}hrs, {int(minutes)}min, {seconds:.2f}s"
        elif minutes > 0:
            return f"{int(minutes)}min, {seconds:.2f}s"
        else:
            return f"{seconds:.2f}s"


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                         #
#region - File Management #
#                         #


    def clean_directory(self, directory):
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            return True
        except Exception as e:
            print(f"ERROR - An error occurred while cleaning the directory: {directory}\nERROR - {str(e)}")
            return False


    def fileMenu_clear_frames(self, directory):
        result = messagebox.askquestion("Delete Frames", f"Are you sure you want to delete all frames in {directory}?", icon='warning')
        if result == 'yes':
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'ERROR - Failed to delete {file_path}\nERROR - {e}')


    def create_directory(self, dir_name):
        try:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            return True
        except Exception as e:
            print(f"ERROR - Failed creating the directory: {dir_name}\nERROR - {str(e)}")
            return False


    def open_directory(self, path):
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.startfile(os.path.dirname(path))
                else:
                    os.startfile(path)
            return True
        except Exception as e:
            print(f"ERROR - Failed opening the directory: {path}\nERROR - {str(e)}")
            return False


    def open_output_folder(self):
        output_file_name = f"{os.path.splitext(os.path.basename(self.video_file))[0]}_UPSCALE{self.file_extension}"
        self.output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)
        output_folder = os.path.dirname(self.output_file_path)
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
        main_window_x = root.winfo_x() - 200 + main_window_width // 2
        main_window_y = root.winfo_y() - 250 + main_window_height // 2
        self.about_window.geometry("+{}+{}".format(main_window_x, main_window_y))
        if self.timer_running == False:
            print(f"{VERSION} - rev-ui - (2023 - 2024) Created by: Nenotriple")


    def close_about_window(self):
        self.about_window.destroy()
        self.about_window = None


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                                  #
#region - Enable / Disable widgets #
#                                  #


    def enable_all(self):
            self.enable_buttons()
            self.enable_widgets()
            self.enable_menus()

    def disable_all(self):
            self.disable_buttons()
            self.disable_widgets()
            self.disable_menus()


    def get_widgets(self):
        return [self.model_label,
                self.upscale_model_combobox,
                self.scale_label,
                self.scale_factor_combobox,
                self.output_label,
                self.output_format_combobox,
                self.output_codec_label,
                self.output_codec_combobox,
                self.output_video_bitrate_label,
                self.output_video_bitrate_combobox,
                self.output_audio_bitrate_label,
                self.output_audio_bitrate_combobox,
                self.sample_duration_combobox,
                self.sample_duration_label,
                self.sample_start_time_label,
                self.sample_start_time_combobox,
                self.reset_button,
                self.extra_title_label,
                self.extra_label,
                self.resize_extracted_check,
                self.scale_raw_entry,
                self.scale_upscaled_check,
                self.scale_upscaled_entry,

                self.image_upscale_title_label,
                self.model_label_tab2,
                self.upscale_model_combobox_tab2,
                self.scale_label_tab2,
                self.scale_factor_combobox_tab2,

                self.image_upscale_label,
                self.upscale_image_button,

                self.b_upscale_title_label,
                self.b_upscale_label,
                self.b_src_folder_label,
                self.b_src_folder_entry,
                self.b_src_folder_open_button,
                self.b_src_folder_button,
                self.b_src_folder_clr_button,
                self.b_out_folder_label,
                self.b_out_folder_entry,
                self.b_out_folder_open_button,
                self.b_out_folder_button,
                self.b_out_folder_clr_button,
                self.run_batch_button,

                self.run_resize_button,
                self.resize_single_button,
                self.resize_folder_clr_button,
                self.resize_folder_open_button,
                self.resize_folder_label,
                self.resize_folder_entry,
                self.resize_folder_button,
                self.resize_label,
                self.resize_title_label,

                self.generate_sample_check
                ]


    def get_readonly_widgets(self):
        return [self.upscale_model_combobox,
                self.scale_factor_combobox,
                self.output_format_combobox,
                self.output_codec_combobox,
                #self.output_video_bitrate_combobox,
                #self.output_audio_bitrate_combobox,
                self.sample_duration_combobox,
                #self.sample_start_time_combobox,
                self.upscale_model_combobox_tab2,
                self.scale_factor_combobox_tab2,
                ]


    def get_buttons(self):
        return [self.select_video_button,
                self.extract_button,
                self.upscale_button,
                self.merge_button
                ]


    def disable_widgets(self):
        for widget in self.get_widgets():
            widget.config(state='disabled')


    def enable_widgets(self):
        for widget in self.get_widgets():
            widget.config(state='normal')
        self.toggle_sample_widgets()
        self.toggle_auto_widgets()
        self.ensure_widget_readonly()


    def ensure_widget_readonly(self):
        for widget in self.get_readonly_widgets():
            widget.config(state='readonly')


    def disable_buttons(self):
        for button in self.get_buttons():
            button.configure(state='disabled')


    def enable_buttons(self):
        for button in self.get_buttons():
            button.configure(state='normal')


    def disable_menus(self):
        for menu_item in ["Tools", "Options", "File"]:
            self.menubar.entryconfig(menu_item, state="disabled")

    def enable_menus(self):
        for menu_item in ["Tools", "Options", "File"]:
            self.menubar.entryconfig(menu_item, state="normal")


    def toggle_auto_widgets(self):
        state = "normal" if self.auto_var.get() else "disabled"
        self.extra_label.configure(state=state)
        self.resize_extracted_check.configure(state=state)
        self.scale_raw_entry.configure(state=state)
        self.scale_upscaled_check.configure(state=state)
        self.scale_upscaled_entry.configure(state=state)


    def toggle_sample_widgets(self, *args):
        if self.generate_sample_var.get() == 1:
            self.sample_duration_combobox.config(state='readonly')
            self.sample_duration_label.config(state='normal')
            self.sample_start_time_combobox.config(state='normal')
            self.sample_start_time_label.config(state='normal')
        else:
            self.sample_duration_combobox.config(state='disabled')
            self.sample_duration_label.config(state='disabled')
            self.sample_start_time_combobox.config(state='disabled')
            self.sample_start_time_label.config(state='disabled')


    def toggle_upscale(self):
        if self.skip_upscale.get() == '1':
            self.keep_raw_var.set('1')
            self.keep_raw_check.config(state="disabled")
            self.keep_upscaled_var.set('0')
            self.keep_upscaled_check.config(state="disabled")
        else:
            self.keep_raw_var.set('0')
            self.keep_raw_check.config(state="normal")
            self.keep_upscaled_check.config(state="normal")


#endregion
##########################################################################################################################################################################
##########################################################################################################################################################################
#                        #
#region - Misc Functions #
#                        #


    def copy_to_clipboard(self, event):
        if self.select_video_button.cget('state') == 'disabled':
            return
        widget = event.widget
        text = widget.cget("text")
        if text != "":
            widget.clipboard_clear()
            widget.clipboard_append(text)
            original_text = text
            widget.config(text=f"Copied!\n{self.happy_faces()}")
            widget.after(250, lambda: widget.config(text=original_text))


    def happy_faces(self):
        string_list = ("(^_^)", "(^‿^)", "(＾▽＾)", "(•‿•)", "(◕‿◕)", "(｡♥‿♥｡)", "(✿◠‿◠)", "(‾◡◝ )", "(°◡°♡)", "(≖ᴗ≖✿)",
                       "(♥ ‿ ♥)", "(✿╹◡╹)", "(✿ ♡‿♡)", "⊂((・▽・))⊃", "ʘ‿ʘ", "(◕ᗜ◕)", "ʕっ•ᴥ•ʔっ", "໒(＾ᴥ＾)७", "(=^ ◡ ^=)", "ᵔᴥᵔ",
                       "ʕ ● ᴥ ●ʔ", "(っ◕‿◕)っ", "(◑‿◐)", "(─‿─)", "(＊๑˘◡˘)", "(ᴗᵔᴥᵔ)", "٩( ^ᴗ^ )۶", "ヽ(•‿•)/", "(✿◠‿◠)✌", "(´• ω •`)",
                       "(✿ʘ‿ʘ)", "(ʘ‿ʘ✿)", "(ʘ‿ʘ)", "(^‿^✿)", "(◠‿◠)", "(◠‿◠✿)", "(◕‿◕✿)", "(◠‿◠✿)✌", "｡◕‿◕｡", "(◕‿-)✌")
        pseudo_random_number = hash(str(time.time())) % len(string_list)
        return string_list[pseudo_random_number]


    def sad_faces(self):
        string_list = ("( ◎ _ ◎ )", "(╥╯ᗝ╰╥)", "(✖_✖)", "└[ ☉ ل͟ ☉ ]┘", "( ͡ ಠ ʖ̯ ͡ಠ)", "(-`д´-)", "๑(•̀_•́ )ﾉ", "ʕ ͡ಠ ‸ ͡ಠʔ", "[¬＿¬]", "(ಠ︹ಠ)",
                       "(*︵*)", "(ᵔ╭╮ᵔ)", "(-_-)", "(ಥ╭╮ಥ)", "(ᗒ༎︵༎ᗕ)", "(◞╭╮◟)", "(¬︹¬)", "┗(⊙_☉)┘", "(⊚_☉)", "(◈ дﾟ◈)",
                       "〘ఠ _ ఠ〙", "(҂◡╭╮◡)", "⤜(⚆︵⚆)⤏", "|⊙▂⊙|", "(ó︹ò ｡)", "(◡︵◡〞)", "•︵•", "(〃╯︵╰〃)", "(◞ ‸ ◟〟)", "ヽ(☉_☉ )〴",
                       "(ಥ﹏ಥ)", "(⏓﹏⏓)", "(ㆆ _ ㆆ)", "(> _ <)", "(⚆ᗝ⚆)", "⊙︿⊙", "˚‧º·(ᵒ﹏ᵒ)‧º·˚", "¯\_(⊙︿⊙)_/¯", "⁀⊙﹏☉⁀", "¯\_(⊙_ʖ⊙)_/¯",
                       "( ⚆ _ ⚆ )", "(╥﹏╥)", "( T ʖ̯ T)", "(ー_ーゞ", "( º﹃º )", "╮(╯_╰)╭", "(;⌣̀_⌣́)", "꒰•⌓•꒱", "(.づ◡﹏◡)づ.", "◕︵◕")
        pseudo_random_number = hash(str(time.time())) % len(string_list)
        return string_list[pseudo_random_number]


    def reset_settings(self):
        print("Settings Reset!")
        self.upscale_model.set("realesr-animevideov3")
        self.scale_factor.set("2")
        self.output_format.set("mp4")
        self.output_codec.set("libx264")
        self.sample_duration.set(5)
        self.sample_start_time.set("Auto")
        self.video_bitrate.set("Auto From Source")
        self.audio_bitrate.set("Auto From Source")


    def create_trace(self):
        validate_cmd = self.register(self.validate_input)
        self.scale_raw_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))
        self.scale_upscaled_entry.config(validate="key", validatecommand=(validate_cmd, '%P'))
        self.scale_factor.trace_add('write', self.get_video_dimensions)
        self.generate_sample_var.trace_add('write', self.toggle_sample_widgets)
        self.upscale_model.trace_add('write', self.update_scale_factor)


    # Used to ensure only proper characters can be entered in the resize boxes.
    @staticmethod
    def validate_input(input):
        if all(char.isdigit() or char in {',', '%', 'x', '.'} for char in input):
            if (input.count(',') <= 1 and input.count('%') == 0 and input.count('x') == 0 and input.count('.') <= 1) or \
               (input.count('%') <= 1 and input.count(',') == 0 and input.count('x') == 0 and input.count('.') <= 1) or \
               (input.count('x') <= 1 and input.count(',') == 0 and input.count('%') == 0 and (input.count('.') <= 1 if 'x' in input else input.count('.') == 0)):
                return True
        return False


    def bind_widget_highlight(self, widget, add=False, color=None):
        add = '+' if add else ''
        if color:
            widget.bind("<Enter>", lambda event: self.mouse_enter(event, color), add=add)
        else:
            widget.bind("<Enter>", self.mouse_enter, add=add)
        widget.bind("<Leave>", self.mouse_leave, add=add)

    def mouse_enter(self, event, color='#e5f3ff'):
        if event.widget['state'] == 'normal':
            event.widget['background'] = color

    def mouse_leave(self, event):
        event.widget['background'] = 'SystemButtonFace'


    def stop_process(self):
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.communicate(timeout=5)
            except TimeoutExpired:
                self.process.kill()
                self.process.communicate()
            self.process_stopped = True
            self.bottom_label["text"] = "Process Stopped!"
            if self.auto_var.get() == 1:
                self.auto_var.set(0)


    def on_closing(self):
        self.stop_process
        if not self.keep_raw_var.get() and os.path.exists("raw_frames"):
            self.clean_directory("raw_frames")
        if not self.keep_upscaled_var.get() and os.path.exists("upscaled_frames"):
            self.clean_directory("upscaled_frames")
        self.after(150, root.destroy)


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
    window_height = 715
    position_right = root.winfo_screenwidth()//2 - window_width//2
    position_top = root.winfo_screenheight()//2 - window_height//2
    root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")


root = tk.Tk()
root.title(f'{VERSION} - R-ESRGAN-AnimeVideo-UI')
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

v1.18 changes:

- New:
  -


<br>


- Fixed:
  - Fixed issue with downloading file requirements. The executable version is now bundled with all the needed resources.
  - Fix output folder selection in Batch Upscale function not working.
  - Fix "Skip Upscale" checkbutton permanently disabling the "Keep upscaled frames" checkbutton.
    - Also fixed button alignment.
  - Fixed "Batch Resize Images" error when attempting to resize a folder of images containing non-image files.
    - "Batch Resize Images" now saves resized images to a new "output" folder.


- Other changes:
  - (script) Pillow is no longer automatically installed on startup.


'''


##########################################################################################################################################################################
##########################################################################################################################################################################
#      #
# todo #
#      #



'''


- Todo
  - Select multiple videos and upscale sequentially
  - Preserve subtitles and additional audio tracks


- Tofix
  -


'''
