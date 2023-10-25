##########################
#                        #
# R-ESRGAN-AnimeVideo-UI #
#         reav-ui        #
#      Version 1.11      #
#                        #
##########################
# Requirements: #
# ffmpeg        # Included: Auto-download
# ffprobe       # Included: Auto-download
# pillow        # Included: Auto-install
##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Imports #
#         #

import os
import io
import re
import glob
import time
import shutil
import datetime
import threading
import mimetypes
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Tk
from subprocess import TimeoutExpired

try:
    from PIL import ImageTk, Image, ImageSequence
except ImportError:
    print("Pillow not found...")
    import subprocess, sys
    root = Tk()
    root.withdraw()
    install_pillow = messagebox.askyesno("Pillow not installed!", " Pillow (Image Processor) not found. Would you like to install it? ~2.5MB \n\n This is a hard requirement.")
    if install_pillow:
        subprocess.check_call(["python", '-m', 'pip', 'install', 'pillow'])
        messagebox.showinfo("Pillow Installed", " Successfully installed Pillow. \n\n Please restart the program.")
    sys.exit()

##########################################################################################################################################################################
##########################################################################################################################################################################
#             #
# AboutWindow #
#             #

class AboutWindow(tk.Toplevel):

    info_text = (
    "\nSelect a video:\n"
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

    "\nThis program will open several command prompts during operation.\n"
    "   - (ffmpeg, realesrgan)"
    )

    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("About")
        self.geometry("450x550")
        self.maxsize(800, 600)
        self.minsize(450, 600)

        self.button = tk.Button(self, text="Open: github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI", fg="blue", command=self.open_url)
        self.button.pack(fill="x")

        self.info_label = tk.Label(self, text="Info", font=("Arial", 14))
        self.info_label.pack(pady=5)

        self.info_text = tk.Label(self, text=AboutWindow.info_text, width=100, anchor='w', justify='left')
        self.info_text.pack(pady=5)

        self.separator = tk.Label(self, height=1)
        self.separator.pack()

        self.credits_label = tk.Label(self, text="Credits", font=("Arial", 14))
        self.credits_label.pack(pady=5)

        self.info_label = tk.Label(self, text="(2023) Created by: Nenotriple", font=("Arial", 10))
        self.info_label.pack(pady=5)

        self.credits_text = tk.Label(self, text= ("ffmpeg-6.0-essentials: ffmpeg.org\nReal-ESRGAN_portable: github.com/xinntao/Real-ESRGAN\n Thank you!"), width=50)
        self.credits_text.pack(pady=5)

    def open_url(self):
        import webbrowser
        webbrowser.open('https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI')

##########################################################################################################################################################################
##########################################################################################################################################################################
#          #
# ToolTips #
#          #

class ToolTip:
    def __init__(self, widget, x_offset=0, y_offset=0):
        self.widget = widget
        self.tip_window = None
        self.x_offset = x_offset
        self.y_offset = y_offset

    def show_tip(self, tip_text):
        if self.tip_window or not tip_text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + self.x_offset
        y = y + self.widget.winfo_rooty() + self.y_offset
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=tip_text, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()

    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

    def create_tooltip(widget, text, delay=500, x_offset=0, y_offset=0):
        tool_tip = ToolTip(widget, x_offset, y_offset)
        id = None
        def enter(event):
            nonlocal id
            id = widget.after(delay, lambda: tool_tip.show_tip(text))
        def leave(event):
            nonlocal id
            widget.after_cancel(id)
            tool_tip.hide_tip()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

##########################################################################################################################################################################
##########################################################################################################################################################################
#            #
# Main Class #
#            #

class reav_ui(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        # Create interface.
        self.pack(fill=tk.BOTH, expand=1)
        self.create_interface()

        # initialize process and timer.
        self.process = None
        self.process_stopped = False
        self.start_time = time.time()

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

        # This script collects ffmpeg, realesrgan, and models.
        subprocess.run(["python", "bin/collect_requirements.py"])

        # This is used to make sure folders are cleaned up when closing the window.
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Menubar #
#         #

    def create_interface(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # File Menu
        self.fileMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label="Open: Extracted Frames", command=lambda: os.startfile('raw_frames'))
        self.fileMenu.add_command(label="Open: Upscaled Frames", command=lambda: os.startfile('upscaled_frames'))
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Clear: Extracted Frames", command=lambda: self.toolsmenu_clear_frames('raw_frames'))
        self.fileMenu.add_command(label="Clear: Upscaled Frames", command=lambda: self.toolsmenu_clear_frames('upscaled_frames'))

        # Options Menu
        self.optionsMenu = tk.Menu(self.menubar, tearoff=0)
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
            self.scaleMenu.add_radiobutton(label=i, variable=self.scale_factor, value=i)
        self.menubar.add_cascade(label="Options", menu=self.optionsMenu)
        self.upscale_model.trace('w', self.update_scale_factor)

        # Output Format
        self.output_format = tk.StringVar(value="mp4")
        self.formatMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Output Format", menu=self.formatMenu)
        for format in ["mp4", "HQ gif", "LQ gif"]:
            self.formatMenu.add_radiobutton(label=format, variable=self.output_format, value=format)

        # Tools Menu
        self.toolsMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=self.toolsMenu)

        # Batch Upscale
        self.batchUpscaleMenu = tk.Menu(self.toolsMenu, tearoff=0)
        self.source_folder_index = 0
        self.output_folder_index = 1
        self.clear_folder_choice_index = 2
        self.toolsMenu.add_cascade(label="Batch Upscale", menu=self.batchUpscaleMenu)
        self.batchUpscaleMenu.add_command(label="Select: Source Folder", command=self.select_source_folder)
        self.batchUpscaleMenu.add_command(label="Select: Output Folder (optional)", command=self.select_output_folder)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Clear Folder Choice", command=self.clear_folder_choice)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Run", command=self.batch_upscale)

        # Single Image Upscale
        self.toolsMenu.add_command(label="Upscale a Single Image", command=self.select_and_upscale_image)
        self.toolsMenu.add_separator()

        # Resize Frames
        self.toolsMenu.add_command(label="Resize: Extracted Frames", command=lambda: self.confirm_scale("raw_frames"))
        self.toolsMenu.add_command(label="Resize: Upscaled Frames", command=lambda: self.confirm_scale("upscaled_frames"))

        # About Menu
        self.menubar.add_command(label="About", command=self.open_about_window)

##########################################################################################################################################################################
##########################################################################################################################################################################
#        #
# Labels #
#        #

        # Filename
        self.filename_label = tk.Label(self)
        self.filename_label["text"] = "Select a video to begin!"
        self.filename_label['wraplength'] = 500
        self.filename_label.pack(side="top", fill=tk.X)

        # Console Output
        self.console_output_label = tk.Label(self)
        self.console_output_label["wraplength"] = 500
        self.console_output_label.pack(side="top", fill=tk.X)

        # Operation
        self.operation_label = tk.Label(self)
        self.operation_label['wraplength'] = 500
        self.operation_label.pack(side="top", fill=tk.X)

        # Timer
        self.timer_label = tk.Label(self)
        self.operation_label['wraplength'] = 500
        self.timer_label.pack(side="top", fill=tk.X)
        self.timer_running = False

        # Video Thumbnail (see "show_thumbnail")
        self.thumbnail_label = None

##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Buttons #
#         #

        # Select Video
        self.select_video_button = tk.Button(self)
        self.select_video_button["text"] = "1) Select Video\t\t\t"
        self.select_video_button["command"] = self.select_video
        self.select_video_button.pack(side="top", fill=tk.X)

        self.button_frame1 = tk.Frame(self)
        self.button_frame1.pack(anchor='center')

        # Extract
        self.extract_button = tk.Button(self.button_frame1, text="2) Extract Frames  ", command=self.extract_frames, width=59, height=1)
        self.extract_button.grid(row=0, column=0, pady=3)
        self.extract_button.bind('<Button-3>', lambda event: self.extract_button.config(state='normal'))

        # Keep raw_frames
        self.keep_raw_var = tk.IntVar(value=0)
        self.keep_raw_check = tk.Checkbutton(self.button_frame1, text="Keep Frames", variable=self.keep_raw_var)
        self.keep_raw_check.grid(row=0, column=1, pady=3)
        ToolTip.create_tooltip(self.keep_raw_check, "Enable this before Upscaling or closing the window to save Raw Frames.", 500, 20, 30)

        self.button_frame2 = tk.Frame(self)
        self.button_frame2.pack(anchor='center')

        # Upscale
        self.upscale_button = tk.Button(self.button_frame2, width=59, height=1)
        self.upscale_button["text"] = "3) Upscale Frames"
        self.upscale_button["command"] = self.upscale_frames
        self.upscale_button.grid(row=0, column=0)
        self.upscale_button.bind('<Button-3>', lambda event: self.upscale_button.config(state='normal'))

        # Keep upscaled_frames
        self.keep_upscaled_var = tk.IntVar(value=0)
        self.keep_upscaled_check = tk.Checkbutton(self.button_frame2, text="Keep Frames", variable=self.keep_upscaled_var)
        self.keep_upscaled_check.grid(row=0, column=1, pady=3)
        ToolTip.create_tooltip(self.keep_upscaled_check, "Enable this before Merging or closing the window to save Upscaled Frames.", 500, 20, 30)

        self.button_frame3 = tk.Frame(self)
        self.button_frame3.pack(anchor='center')

        # Merge
        self.merge_button = tk.Button(self.button_frame3, text="4) Merge Frames ", command=self.merge_frames, width=59)
        self.merge_button.grid(row=0, column=0)
        self.merge_button.bind('<Button-3>', lambda event: self.merge_button.config(state='normal'))

        # Auto
        self.auto_var = tk.IntVar(value=0)
        self.auto_check = tk.Checkbutton(self.button_frame3, text="Auto\t       ", variable=self.auto_var, width=10)
        self.auto_check.grid(row=0, column=1, pady=3)
        ToolTip.create_tooltip(self.auto_check, "Enable this to automatically Upscale/Merge Frames after Extracting/Upscaling.", 500, 20, 30)

        # Stop
        self.stop_button = tk.Button(self, text="STOP", command=self.stop_process)
        self.stop_button.pack(side="top", fill=tk.X)

##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Info Text #
#           #

        self.infotext_label = tk.Label(self, text=AboutWindow.info_text, anchor='w', justify=tk.LEFT, wraplength=500)
        self.infotext_label.pack(side="top", fill=tk.X)

##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Threads #
#         #

    def extract_frames(self):
        self.operation_label["text"] = "Extracting... This may take a while..."
        thread = threading.Thread(target=self._extract_frames)
        thread.start()

    def upscale_frames(self):
        self.operation_label["text"] = "Upscaling... This may take a while..."
        thread = threading.Thread(target=self._upscale_frames)
        thread.start()

    def merge_frames(self):
        self.operation_label["text"] = "Merging... This may take a while..."
        thread = threading.Thread(target=self._merge_frames)
        thread.start()

    def scale_frames(self):
        self.operation_label["text"] = "Resizing... This may take a while..."
        thread = threading.Thread(target=self._scale_frames)
        thread.start()

    def batch_upscale(self):
        self.operation_label["text"] = "Batch Upscaling... This may take a while..."
        thread = threading.Thread(target=self._batch_upscale)
        thread.start()

    def select_and_upscale_image(self):
        self.operation_label["text"] = "Upscaling Single Image... This may take a while..."
        thread = threading.Thread(target=self._select_and_upscale_image)
        thread.start()

##########################################################################################################################################################################
##########################################################################################################################################################################
#          #
# Monitors #
#          #

    def monitor_extract_frames(self, process, total_frames, start_time):
        while self.process.poll() is None:
            frame_count = len(glob.glob('raw_frames/*.jpg'))
            if total_frames is not None:
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time)
                self.console_output_label["text"] = f"Extracted {frame_count:08d}, of {total_frames:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
            else:
                self.console_output_label["text"] = f"Extracted {frame_count:08d} frames"
        frame_count = len(glob.glob('raw_frames/*.jpg'))
        if total_frames is not None:
            fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time)
            self.console_output_label["text"] = f"Extracted {frame_count:08d}, of {frame_count:08d}, 100%\nETA: {eta_str}, FPS: {fps:.2f}"
        else:
            self.console_output_label["text"] = f"Extracted {frame_count:08d} frames"

    def monitor_upscale_frames(self, frame_total, start_time):
        while self.process.poll() is None:
            frame_count = len(glob.glob('upscaled_frames/*.jpg'))
            if frame_count > 0:
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, frame_total, start_time)
                self.console_output_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"

    def monitor_merge_frames(self, process, frame_count, total_frames, start_time, start_file_size):
        for line in iter(process.stdout.readline, ""):
            frame_number_search = re.search(r'frame=\s*(\d+)', line)
            if frame_number_search:
                frame_count = int(frame_number_search.group(1))
                fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, total_frames, start_time, start_file_size)
                self.console_output_label["text"] = f"Frame: {frame_count:08d}, of {total_frames:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
        return frame_count

    def monitor_batch_upscale(self, frame_total, start_time):
        while self.process.poll() is None:
            frame_count = len(glob.glob(f'{self.output_folder}/*.jpg'))
            fps, eta_str, percent_complete, _, _, _ = self.calculate_metrics(frame_count, frame_total, start_time)
            self.console_output_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"

##########################################################################################################################################################################
##########################################################################################################################################################################
#                   #
# Primary Functions #
#                   #

    def select_video(self):
        self.disable_buttons()
        self.infotext_label.pack_forget()
        self.console_output_label["text"] = ""
        self.operation_label["text"] = ""
        self.timer_label["text"] = ""
        self.video_file = filedialog.askopenfilename()
        self.filename_label["text"] = f"{os.path.basename(self.video_file)}"
        self.file_extension = os.path.splitext(self.video_file)[1]
        if mimetypes.guess_type(self.video_file)[0] not in self.supported_video_types:
            self.select_video_button.config(state='normal')
            self.filename_label["text"] = "Unsupported filetype or no file selected"
            self.operation_label["text"] = self.sad_faces()
            if self.thumbnail_label is not None:
                self.thumbnail_label.destroy()
            return
        frame_rate, _, total_frames, dimensions, _ = self.collect_stream_info()
        self.total_frames = total_frames
        middle_frame_number = int(total_frames) // 2
        middle_frame_time = middle_frame_number / float(frame_rate)
        self.show_thumbnail(middle_frame_time)
        self.get_video_dimensions(frame_rate, total_frames, dimensions)
        self.timer_label["text"] = ""
        self.select_video_button.config(state='normal')
        self.extract_button.config(state='normal')
        self.stop_button.config(text="STOP", command=self.stop_process)

    def _extract_frames(self):
        try:
            start_time = time.time()
            self.start_timer()
            self.update_timer()
            self.disable_buttons()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            os.makedirs("raw_frames", exist_ok=True)
            self.clean_directory('raw_frames')
            try:
                total_frames = int(self.total_frames)
            except Exception as e:
                total_frames = None
                self.operation_label["text"] = f"Error: {str(e)}"
            self.process = subprocess.Popen(["./bin/ffmpeg.exe", "-i", self.video_file, "-qscale:v", "3", "-qmin", "3", "-qmax", "3", "-vsync", "0", "raw_frames/frame%08d.jpg"])
            self.monitor_extract_frames(self.process, total_frames, start_time)
        finally:
            self.stop_timer()
            self.enable_buttons()
            if not self.process_stopped:
                self.operation_label["text"] = "Done Extracting!"
            self.stop_button.config(text="STOP", command=self.stop_process)
            if self.auto_var.get() == 1:
                self.upscale_frames()
            for button in [self.extract_button, self.merge_button]:
                button.config(state='disabled')
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def _upscale_frames(self):
        try:
            os.makedirs("upscaled_frames", exist_ok=True)
            self.clean_directory("upscaled_frames")
            self.start_timer()
            self.update_timer()
            self.disable_buttons()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            frame_total = len(glob.glob('raw_frames/*.jpg'))
            start_time = time.time()
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", "raw_frames", "-o", "upscaled_frames", "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"])
            self.monitor_upscale_frames(frame_total, start_time)
        except Exception as e:
            self.operation_label["text"] = f"Error: {str(e)}"
        finally:
            self.stop_timer()
            self.enable_buttons()
            self.stop_button.config(text="STOP", command=self.stop_process)
            for button in [self.extract_button, self.upscale_button]:
                button.config(state='disabled')
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")
        if self.keep_raw_var.get() == 0:
            self.clean_directory("raw_frames")
        if not self.process_stopped:
            self.operation_label["text"] = "Done Upscaling!"
        if self.auto_var.get() == 1:
            self.merge_frames()

    def _merge_frames(self):
        try:
            self.start_timer()
            self.disable_buttons()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            total_frames = len(os.listdir("upscaled_frames"))
            self.file_extension = os.path.splitext(self.video_file)[1]
            start_file_size = os.path.getsize(self.video_file)
            command, output_file_path = self.get_merge_frames_command()
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            start_time = time.time()
            frame_count = 0
            frame_count = self.monitor_merge_frames(process, frame_count, total_frames, start_time, start_file_size)
            process.stdout.close()
            process.wait()
            end_file_size = os.path.getsize(output_file_path)
            _, _, _, percent_change, start_file_size_MB, end_file_size_MB = self.calculate_metrics(frame_count, total_frames, start_time, start_file_size, end_file_size)
            self.stop_timer()
            if not self.process_stopped:
                self.operation_label["text"] = f"Done Merging!\nOriginal size: {start_file_size_MB:.2f}MB, Final size: {end_file_size_MB:.2f}MB, Change: {percent_change:.2f}%"
            if os.path.isfile("bin/palette001.png"):
                os.remove("bin/palette001.png")
            if not self.keep_upscaled_var.get():
                self.clean_directory("upscaled_frames")
            if not self.process_stopped:
                self.console_output_label["text"] = "Output:\n" + output_file_path
            self.stop_button.config(text="Open Output Folder", command=self.open_output_folder)
        except AttributeError as e:
            self.stop_timer()
            self.operation_label["text"] = f"Error: {str(e)}"
        finally:
            self.enable_buttons()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")
            for button in [self.extract_button, self.upscale_button, self.merge_button]:
                button.config(state='disabled')

##########################################################################################################################################################################
##########################################################################################################################################################################
#                     #
# Secondary Functions #
#                     #

    def show_thumbnail(self, middle_frame_time):
        _, duration, _, _, _ = self.collect_stream_info()
        if self.thumbnail_label is not None:
            self.thumbnail_label.destroy()

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
            self.thumbnail_label = tk.Label(image=photoImg)
            self.thumbnail_label.bind("<Double-1>", lambda e: self.open_output_folder())
            self.thumbnail_label.image = photoImg
            self.thumbnail_label.pack(side="bottom", expand=True, fill="both")
            ToolTip.create_tooltip(self.thumbnail_label, "Double click to open source folder", 1000, 0, -35)

            def update(index):
                frame = frames[index]
                photoImg.paste(frame)
                self.thumbnail_label.after(120, update, (index+1)%len(frames))

            self.thumbnail_label.after(120, update, 1)
        else:
            def update_thumbnail(e):
                nonlocal middle_frame_time
                middle_frame_time = (middle_frame_time + 2) % duration
                result = subprocess.run(["./bin/ffmpeg.exe", "-ss", str(middle_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                img = Image.open(io.BytesIO(result.stdout))
                photoImg = create_image(img)
                self.thumbnail_label.configure(image=photoImg)
                self.thumbnail_label.image = photoImg

            result = subprocess.run(["./bin/ffmpeg.exe", "-ss", str(middle_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            img = Image.open(io.BytesIO(result.stdout))
            photoImg = create_image(img)
            self.thumbnail_label = tk.Label(image=photoImg)
            self.thumbnail_label.bind("<Double-1>", lambda e: self.open_output_folder())
            self.thumbnail_label.bind("<Button-3>", update_thumbnail)
            self.thumbnail_label.image = photoImg
            self.thumbnail_label.pack(side="bottom", expand=True, fill="both")
            ToolTip.create_tooltip(self.thumbnail_label, "Double click to open source folder\nRight click to jump forward ~2sec", 1000, 0, -35)

    def get_merge_frames_command(self):
        frame_rate, _, _, _, _ = self.collect_stream_info()
        output_file_name = os.path.splitext(os.path.basename(self.video_file))[0] + "_UPSCALE"
        if self.output_format.get() in ['HQ gif', 'LQ gif']:
            output_file_name += "_" + self.output_format.get().split()[0]
        output_file_name += ('.gif' if self.output_format.get() in ['HQ gif', 'LQ gif'] else '.mp4')
        output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)
        if self.output_format.get() == 'HQ gif':
            palette_path = "bin/palette%03d.png"
            command_palettegen = ["./bin/ffmpeg.exe", "-y", "-i", "upscaled_frames/frame%08d.jpg", "-vf", "palettegen", palette_path]
            subprocess.call(command_palettegen)
            command = ["./bin/ffmpeg.exe", "-y", "-r", str(frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                       "-i", palette_path,
                       "-filter_complex", "paletteuse",
                       output_file_path]
        elif self.output_format.get() == 'LQ gif':
            command = ["./bin/ffmpeg.exe", "-y", "-r", str(frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                       "-c:v", 'gif',
                       output_file_path]
        else:
            command = ["./bin/ffmpeg.exe", "-y", "-r", str(frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                       "-i", self.video_file,
                       "-c:v", 'libx264',
                       output_file_path]
        if self.file_extension != '.gif':
            command.extend(["-c:a", "copy",
                           "-vsync", "0",
                           "-map", "0:v:0",
                           "-map", "1:a:0",
                           "-pix_fmt","yuv420p",
                           "-crf","18"])
        return command, output_file_path

    def update_scale_factor(self, *args):
        state = "normal" if self.upscale_model.get() == "realesr-animevideov3" else "disabled"
        self.scale_factor.set("2" if state == "normal" else "4")
        for i in range(4):
            self.scaleMenu.entryconfig(i, state=state)

    def run_ffprobe(self, args):
        return subprocess.run(["./bin/ffprobe.exe"] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode().strip()

##########################################################################################################################################################################
##########################################################################################################################################################################
#                       #
# Media Info Collection #
#                       #

    def select_video_get_media_info(self):
        self.total_frames = self.run_ffprobe(["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "default=nokey=1:noprint_wrappers=1", self.video_file])
        if not self.total_frames.isdigit():
            _, _, self.total_frames, _, _ = self.collect_stream_info()
            self.total_frames = int(self.total_frames) if self.total_frames else self.FALLBACK_FPS
        self.frame_rate = self.run_ffprobe(["-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file])
        numerator, denominator = map(int, self.frame_rate.split('/'))
        self.frame_rate = numerator / denominator

    def collect_stream_info(self):
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
        frame_rate, _, total_frames, dimensions, file_size_megabytes = self.collect_stream_info()
        scale_factor = int(self.scale_factor.get())
        coded_width, coded_height = map(int, dimensions.split('x'))
        new_dimensions = f"{coded_width*scale_factor}x{coded_height*scale_factor}"
        if total_frames:
            video_length_seconds = int(total_frames) / float(frame_rate)
            video_length_time_string = str(datetime.timedelta(seconds=int(video_length_seconds)))
            self.console_output_label["text"] = f"Video Dimensions: {dimensions}\n Upscaled:  x{scale_factor}, {new_dimensions}\n\nVideo Length: {video_length_time_string}\nTotal Frames: {total_frames}\nFile Size: {file_size_megabytes:.2f} MB"
        else:
            self.operation_label["text"] = f"Info collection failed... You can probably ignore this error."

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

##########################################################################################################################################################################
##########################################################################################################################################################################
#               #
# Upscale Image #
#               #

    def _select_and_upscale_image(self):
        try:
            self.filename_label["text"] = ""
            input_image = filedialog.askopenfilename()
            if input_image:
                try:
                    if input_image.lower().endswith('.gif'):
                        raise IOError
                    Image.open(input_image)
                except IOError:
                    self.filename_label["text"] = "Invalid, or not an image type!"
                    self.operation_label["text"] = self.sad_faces()
                    return
                filename_without_ext = os.path.splitext(input_image)[0]
                output_image = filename_without_ext + "_UP" + os.path.splitext(input_image)[1]
                final_output = filename_without_ext + "_UP.jpg"
                if os.path.exists(final_output):
                    result = messagebox.askquestion("File Exists", "The output file already exists. Do you want to overwrite it?", icon='warning')
                    if result == 'yes':
                        os.remove(final_output)
                    else:
                        self.filename_label["text"] = "Upscale Image: Canceled by user..."
                        self.operation_label["text"] = self.sad_faces()
                        return
                self.start_timer()
                self.select_video_button.config(state='disabled')
                for menu_item in ["Tools", "Options", "File"]:
                    self.menubar.entryconfig(menu_item, state="disabled")
                with subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", input_image, "-o", output_image, "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"]) as self.process:
                    self.process.wait()
                os.rename(output_image, final_output)
                self.filename_label["text"] = "Output:\n" + final_output
                self.operation_label["text"] = "Done Upscaling!"
                self.select_video_button.config(state='normal')
                for menu_item in ["Tools", "Options", "File"]:
                    self.menubar.entryconfig(menu_item, state="normal")
                time.sleep(0.1)
                os.startfile(final_output)
                self.stop_timer()
                self.stop_button.config(text="STOP", command=self.stop_process)
            else:
                self.filename_label["text"] = "No image selected..."
                self.operation_label["text"] = self.sad_faces()
        except Exception as e:
            self.operation_label["text"] = f"An error occurred: {str(e)}"
            self.select_video_button.config(state='normal')
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

##########################################################################################################################################################################
##########################################################################################################################################################################
#               #
# Batch Upscale #
#               #

    def select_source_folder(self):
        try:
            self.source_folder = filedialog.askdirectory()
            if not self.source_folder:
                self.operation_label["text"] = self.sad_faces()
                self.timer_label["text"] = ""
                raise ValueError("No source folder selected.")
            self.batchUpscaleMenu.entryconfig(self.source_folder_index, label="Source Folder ✔️")
            self.filename_label["text"] = "Input:\n" + self.source_folder
            self.timer_label["text"] = ""
        except Exception as e:
            self.console_output_label["text"] = str(e)

    def select_output_folder(self):
        try:
            self.output_folder = filedialog.askdirectory()
            if not self.output_folder:
                self.operation_label["text"] = self.sad_faces()
                self.timer_label["text"] = ""
                raise ValueError("No output folder selected.")
            self.batchUpscaleMenu.entryconfig(self.output_folder_index, label="Output Folder ✔️")
            self.console_output_label["text"] = "Output:\n" + self.output_folder
            self.timer_label["text"] = ""
        except Exception as e:
            self.console_output_label["text"] = str(e)

    def _batch_upscale(self):
        try:
            self.start_timer()
            self.update_timer()
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
            self.filename_label["text"] = "Output:\n" + self.output_folder
            image_files = [file for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp'] for file in glob.glob(f'{self.source_folder}/{ext}')]
            if not image_files:
                self.filename_label["text"] = "Error: No images found in the source folder."
                self.console_output_label["text"] = ""
                self.operation_label["text"] = self.sad_faces()
                self.stop_timer()
                self.timer_label["text"] = ""
                return
            frame_total = len(image_files)
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", self.source_folder, "-o", self.output_folder, "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"])
            self.monitor_batch_upscale(frame_total, start_time)
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")
            self.operation_label["text"] = "Done Upscaling!"
            self.stop_timer()
        except Exception as e:
            self.operation_label["text"] = f"Error:\n{str(e)}"
            self.stop_timer()
        finally:
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def clear_folder_choice(self):
        self.source_folder = None
        self.output_folder = None
        self.batchUpscaleMenu.entryconfig(self.source_folder_index, label="Source Folder")
        self.batchUpscaleMenu.entryconfig(self.output_folder_index, label="Output Folder")
        self.select_video_button.config(state='normal')
        self.filename_label["text"] = "Batch folder selection cleared."
        self.console_output_label["text"] = "..."
        self.operation_label["text"] = ""

##########################################################################################################################################################################
##########################################################################################################################################################################
#              #
# Scale Images #
#              #

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
                    result = messagebox.askquestion("Large Scale Factor", "You entered a large scale factor. Are you sure you want to continue?", icon='warning')
                    if result == 'yes':
                        self.resize_factor.set(resize_factor)
                        self.scale_frames()
                        break
                elif resize_factor > 0:
                    self.resize_factor.set(resize_factor)
                    self.scale_frames()
                    break

    def _scale_frames(self):
        try:
            self.start_timer()
            self.update_timer()
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
                image_total = len(glob.glob(f'{self.scale_path}/*.jpg'))
                if not os.listdir(self.scale_path):
                    self.operation_label["text"] = "No images found!"
                    return
                image_count = 0
            if ',' in self.resize_resolution.get():
                new_width, new_height = map(int, self.resize_resolution.get().split(','))
            else:
                resize_factor = int(self.resize_factor.get()) / 100
                new_width, new_height = None, None
            start_time = time.time()
            for filename in os.listdir(self.scale_path):
                img = Image.open(os.path.join(self.scale_path, filename))
                if new_width and new_height:
                    img = img.resize((new_width, new_height))
                else:
                    img = img.resize((int(img.size[0]*resize_factor), int(img.size[1]*resize_factor)))
                img.save(os.path.join(self.scale_path, filename), "JPEG", quality=100)
                image_count += 1
                elapsed_time = time.time() - start_time
                fps = image_count / elapsed_time
                eta_seconds = elapsed_time * (image_total - image_count) / image_count
                eta_hms = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
                percent_complete = (image_count / image_total) * 100
                self.console_output_label["text"] = f"Scaled {image_count:08d}, of {image_total:08d}, {percent_complete:.2f}%\n ETA {eta_hms}, FPS {fps:.2f}"
            self.operation_label["text"] = "Done Resizing!"
        except Exception as e:
            self.operation_label["text"] = f"Error:\n{str(e)}"
        finally:
            self.stop_timer()
            self.stop_button.config(text="STOP", command=self.stop_process)
            for menu_item in ["Tools", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

##########################################################################################################################################################################
##########################################################################################################################################################################
#       #
# Timer #
#       #

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

##########################################################################################################################################################################
##########################################################################################################################################################################
#                 #
# File Management #
#                 #

    def clean_directory(self, directory):
        for filename in os.listdir(directory):
            if os.path.isfile(f'{directory}/{filename}'):
                os.remove(f'{directory}/{filename}')

    def toolsmenu_clear_frames(self, directory):
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

##########################################################################################################################################################################
##########################################################################################################################################################################
#                #
# Misc Functions #
#                #

    def sad_faces(self):
        string_list = ("( ◎ _ ◎ )", "(╥╯ᗝ╰╥)", "(✖_✖)", "└[ ☉ ل͟ ☉ ]┘", "( ͡ ಠ ʖ̯ ͡ಠ)", "(-`д´-)", "๑(•̀_•́ )ﾉ", "ʕ ͡ಠ ‸ ͡ಠʔ", "[¬＿¬]", "(ಠ︹ಠ)",
                       "(*︵*)", "(ᵔ╭╮ᵔ)", "(-_-)", "(ಥ╭╮ಥ)", "(ᗒ༎︵༎ᗕ)", "(◞╭╮◟)", "(¬︹¬)", "┗(⊙_☉)┘", "(⊚_☉)", "(◈ дﾟ◈)",
                       "〘ఠ _ ఠ〙", "(҂◡╭╮◡)", "⤜(⚆︵⚆)⤏", "|⊙▂⊙|", "(ó︹ò ｡)", "(◡︵◡〞)", "•︵•", "(〃╯︵╰〃)", "(◞ ‸ ◟〟)", "ヽ(☉_☉ )〴"
                       "(ಥ﹏ಥ)", "(⏓﹏⏓)", "(ㆆ _ ㆆ)", "(> _ <)", "(⚆ᗝ⚆)", "⊙︿⊙", "˚‧º·(ᵒ﹏ᵒ)‧º·˚", "¯\_(⊙︿⊙)_/¯", "⁀⊙﹏☉⁀", "¯\_(⊙_ʖ⊙)_/¯"
                       "( ⚆ _ ⚆ )", "(╥﹏╥)", "( T ʖ̯ T)", "(ー_ーゞ", "( º﹃º )", "╮(╯_╰)╭", "(;⌣̀_⌣́)", "꒰•⌓•꒱", "(.づ◡﹏◡)づ.", "◕︵◕")
        pseudo_random_number = hash(str(time.time())) % len(string_list)
        return string_list[pseudo_random_number]

    def open_about_window(self):
        self.about_window = AboutWindow(self.master)

    def disable_buttons(self):
        self.select_video_button.config(state='disabled')
        self.extract_button.config(state='disabled')
        self.merge_button.config(state='disabled')
        self.upscale_button.config(state='disabled')

    def enable_buttons(self):
        self.select_video_button.config(state='normal')
        self.extract_button.config(state='normal')
        self.merge_button.config(state='normal')
        self.upscale_button.config(state='normal')

    def stop_process(self):
        if self.process:
            self.process.kill()
            self.process_stopped = True
            self.operation_label["text"] = "Process Stopped!"
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

##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Framework #
#           #

root = tk.Tk()
root.title('v1.11 - R-ESRGAN-AnimeVideo-UI')
root.geometry('520x600')
root.resizable(False, False)
app = reav_ui(master=root)
app.mainloop()

##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Changelog #
#           #

'''

v1.11 changes:

- New:
  - `Tools Menu`: This new menu is now where you access Batch and Single image upscale, along with Resize.
  - `clear folder`: Added a confirmation dialog to these File options.
  - `Batch Upscale`: Selecting an output folder is now optional. Images will output to "source/output" if no folder is selected.
  - You can now right click the thumbnail to progress the displayed frame by ~2sec.
  - Gif files are now animated in the UI, updated every 120ms (may not display at full speed).
  - When a video is selected, its size, current dimensions, the selected scale factor, and the upscaled dimensions are displayed.
  - Surprised or sad text faces are displayed for mild errors. (ó︹ò ｡) (e.g., no video selected, invalid file type).
  - `Keep Frames` options are now always available. Sometimes you may wish to change your mind during a long process
<br>

- Fixed:
  - Improved robustness of media info collection.
    - Total frames are now approximated for video streams that don't declare their total frames. This can lead to a slight discrepancy with the reported extracted frames. All frames will be extracted regardless.
  - Invisible tooltips no longer obstruct the checkboxes.
  - The chosen upscale model is now applied to both Batch and Single image upscale.
  - `Batch Upscale`: The elapsed timer now correctly updates in the UI.
  - `Resize`: No longer displays "Done Resizing!" immediately after running.
  - `Extract Frames`: This process can now be stopped.
  - Double-clicking is now required on the thumbnail to open the video directory.
    - This helps to prevent accidental openings when clicking the window.
  - Opening the video directory by clicking the thumbnail is less prone to issues.
    - The script now uses "os.startfile" instead of "subprocess.Popen 'explorer'", preventing multiple folder windows from opening when the folder is already open.
  - Stopping a process now properly updates the ui instead of stating "Done! ..."

'''

##########################################################################################################################################################################
##########################################################################################################################################################################
#      #
# todo #
#      #

'''

- Todo
  - Batch Upscale should be a new window popup.
  - The user should be able to pre-select a resize operation (raw_frames/upscaled_frames), so they can use auto and frame resize at the same time.

- Tofix
  - When merging: Basic timer sometimes stops working at some point. When the process is done, the timer correctly displays the time taken, but during operation, the timer displays 0.

'''
