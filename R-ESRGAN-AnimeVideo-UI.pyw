##########################
#                        #
# R-ESRGAN-AnimeVideo-UI #
#         reav-ui        #
#      Version 1.10      #
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
import datetime
import threading
import mimetypes
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Tk
from subprocess import TimeoutExpired

try:
    from PIL import ImageTk, Image
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
    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("About")
        self.geometry("450x550")
        self.maxsize(450, 560)
        self.minsize(450, 560)

        self.button = tk.Button(self, text="Open: github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI", fg="blue", command=self.open_url)
        self.button.pack(fill="x")

        self.info_label = tk.Label(self, text="Info", font=("Arial", 14))
        self.info_label.pack(pady=5)

        info_text = (
        "\nSelect a video:\n"
        "   - mp4, gif, avi, mkv, webm, mov, m4v, wmv\n"

        "\nNOTE: The Upscale and Merge operations delete the previous frames by default.\n"
        "   - If you want to keep the frames, make sure to enable the Keep Frames option.\n"
        "   - The resize operation overwrites frames.\n"

        "\nUpscale Frames:\n"
        "   - Select a scaling factor in the options menu. Default= x2 \n"

        "\nBatch Upscale:\n"
        "   - Upscales all images in a folder. The source images are not deleted.\n"

        "\nUpscale Image:\n"
        "   - Upscale a single image. The source image is not deleted.\n"

        "\nYou can right-click grayed-out buttons to enable them out of sequence.\n"
        "   - Only use if you know what you're doing!\n"

        "\nThis program will open several command prompts during operation.\n"
        "   - (ffmpeg, realesrgan)"
        )

        self.info_text = tk.Label(self, text=info_text, width=100, anchor='w', justify='left')
        self.info_text.pack(pady=5)

        self.separator = tk.Label(self, height=1)
        self.separator.pack()

        self.credits_label = tk.Label(self, text="Credits", font=("Arial", 14))
        self.credits_label.pack(pady=5)

        self.info_label = tk.Label(self, text="(2023) Created by: Nenotriple", font=("Arial", 10))
        self.info_label.pack(pady=5)

        self.credits_text = tk.Label(self, text="ffmpeg-6.0-essentials: ffmpeg.org\nReal-ESRGAN_portable: github.com/xinntao/Real-ESRGAN\n Thank you!", width=50)
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
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, tip_text):
        "Display text in a tooltip window"
        if self.tip_window or not tip_text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
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

def create_tooltip(widget, text):
    tool_tip = ToolTip(widget)
    def enter(event):
        tool_tip.show_tip(text)
    def leave(event):
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
        self.pack(fill=tk.BOTH, expand=1)
        self.create_interface()
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.process = None
        self.extract_button.config(state='disabled')
        self.merge_button.config(state='disabled')
        self.upscale_button.config(state='disabled')

        # This script collects ffmpeg, realesrgan, models
        subprocess.run(["python", "bin/collect_requirements.py"])

    def create_interface(self):
##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Menubar #
#         #

        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        self.fileMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label="Open: Extracted Frames", command=lambda: os.startfile('raw_frames'))
        self.fileMenu.add_command(label="Open: Upscaled Frames", command=lambda: os.startfile('upscaled_frames'))
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Clear: Extracted Frames", command=lambda: [os.remove(os.path.join('raw_frames', file)) for file in os.listdir('raw_frames')])
        self.fileMenu.add_command(label="Clear: Upscaled Frames", command=lambda: [os.remove(os.path.join('upscaled_frames', file)) for file in os.listdir('upscaled_frames')])

        self.optionsMenu = tk.Menu(self.menubar, tearoff=0)
        self.upscale_model = tk.StringVar(value="realesr-animevideov3")
        self.modelMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Upscale Model", menu=self.modelMenu)
        for model in ["realesr-animevideov3", "RealESRGAN_General_x4_v3", "realesrgan-x4plus", "realesrgan-x4plus-anime"]:
            self.modelMenu.add_radiobutton(label=model, variable=self.upscale_model, value=model)

        self.output_format = tk.StringVar(value="mp4")
        self.formatMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Output Format", menu=self.formatMenu)
        for format in ["mp4", "HQ gif", "LQ gif"]:
            self.formatMenu.add_radiobutton(label=format, variable=self.output_format, value=format)

        self.optionsMenu.add_separator()

        self.scale_factor = tk.StringVar(value="2")
        self.scaleMenu = tk.Menu(self.optionsMenu, tearoff=0)
        self.optionsMenu.add_cascade(label="Upscale Factor", menu=self.scaleMenu)
        for i in ["1", "2", "3", "4"]:
            self.scaleMenu.add_radiobutton(label=i, variable=self.scale_factor, value=i)
        self.menubar.add_cascade(label="Options", menu=self.optionsMenu)

        def update_scale_factor(*args):
            state = "normal" if self.upscale_model.get() == "realesr-animevideov3" else "disabled"
            self.scale_factor.set("2" if state == "normal" else "4")
            for i in range(4):
                self.scaleMenu.entryconfig(i, state=state)
        self.upscale_model.trace('w', update_scale_factor)

        self.optionsMenu.add_command(label="Resize: Extracted Frames", command=lambda: self.confirm_scale("raw_frames"))
        self.optionsMenu.add_command(label="Resize: Upscaled Frames", command=lambda: self.confirm_scale("upscaled_frames"))

        self.batchUpscaleMenu = tk.Menu(self.menubar, tearoff=0)
        self.source_folder_index = 0
        self.output_folder_index = 1
        self.clear_folder_choice_index = 2
        self.menubar.add_cascade(label="Batch Upscale", menu=self.batchUpscaleMenu)
        self.batchUpscaleMenu.add_command(label="Source Folder", command=self.select_source_folder)
        self.batchUpscaleMenu.add_command(label="Output Folder", command=self.select_output_folder)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Clear Folder Choice", command=self.clear_folder_choice)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Run", command=self.batch_upscale)

        self.menubar.add_command(label="Upscale Image", command=self.select_and_upscale_image)

        self.menubar.add_command(label="About", command=self.open_about_window)

##########################################################################################################################################################################
##########################################################################################################################################################################
#        #
# Labels #
#        #

        self.filename_label = tk.Label(self)
        self.filename_label["text"] = "Select a video to begin!"
        self.filename_label['wraplength'] = 500
        self.filename_label.pack(side="top", fill=tk.X)

        self.console_output_label = tk.Label(self)
        self.console_output_label["text"] = ""
        self.console_output_label["wraplength"] = 500
        self.console_output_label.pack(side="top", fill=tk.X)

        self.operation_label = tk.Label(self)
        self.filename_label['wraplength'] = 500
        self.operation_label.pack(side="top", fill=tk.X)

        self.start_time = time.time()
        self.timer_label = tk.Label(self)
        self.timer_label.pack(side="top", fill=tk.X)
        self.timer_running = False

##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Buttons #
#         #

        self.select_button = tk.Button(self)
        self.select_button["text"] = "1) Select Video\t\t\t"
        self.select_button["command"] = self.select_video
        self.select_button.pack(side="top", fill=tk.X)

        self.button_frame1 = tk.Frame(self)
        self.button_frame1.pack(anchor='center')

        self.extract_button = tk.Button(self.button_frame1, text="2) Extract Frames  ", command=self.extract_frames, width=59, height=1)
        self.extract_button.grid(row=0, column=0, pady=3)
        self.extract_button.bind('<Button-3>', lambda event: self.extract_button.config(state='normal'))

        self.keep_raw_var = tk.IntVar(value=0)
        self.keep_raw_check = tk.Checkbutton(self.button_frame1, text="Keep Frames", variable=self.keep_raw_var)
        self.keep_raw_check.grid(row=0, column=1, pady=3)
        create_tooltip(self.keep_raw_check, "Enable this before Upscaling or closing the window to save Raw Frames.")

        self.button_frame2 = tk.Frame(self)
        self.button_frame2.pack(anchor='center')

        self.upscale_button = tk.Button(self.button_frame2, width=59, height=1)
        self.upscale_button["text"] = "3) Upscale Frames"
        self.upscale_button["command"] = self.upscale_frames
        self.upscale_button.grid(row=0, column=0)
        self.upscale_button.bind('<Button-3>', lambda event: self.upscale_button.config(state='normal'))

        self.keep_upscaled_var = tk.IntVar(value=0)
        self.keep_upscaled_check = tk.Checkbutton(self.button_frame2, text="Keep Frames", variable=self.keep_upscaled_var)
        self.keep_upscaled_check.grid(row=0, column=1, pady=3)
        create_tooltip(self.keep_upscaled_check, "Enable this before Merging or closing the window to save Upscaled Frames.")

        self.button_frame3 = tk.Frame(self)
        self.button_frame3.pack(anchor='center')

        self.merge_button = tk.Button(self.button_frame3, text="4) Merge Frames ", command=self.merge_frames, width=59)
        self.merge_button.grid(row=0, column=0)
        self.merge_button.bind('<Button-3>', lambda event: self.merge_button.config(state='normal'))

        self.auto_var = tk.IntVar(value=0)
        self.auto_check = tk.Checkbutton(self.button_frame3, text="Auto\t       ", variable=self.auto_var, width=10)
        self.auto_check.grid(row=0, column=1, pady=3)
        create_tooltip(self.auto_check, "Enable this to automatically Upscale/Merge Frames after Extracting/Upscaling.")

        self.process_stopped = False
        self.stop_button = tk.Button(self, text="STOP", command=self.stop_process)
        self.stop_button.pack(side="top", fill=tk.X)

##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Info_Text #
#           #

        info_text = (
        "\nSelect a video:\n"
        "   - mp4, gif, avi, mkv, webm, mov, m4v, wmv\n"

        "\nNOTE: The Upscale and Merge operations delete the previous frames by default.\n"
        "   - If you want to keep the frames, make sure to enable the Keep Frames option.\n"
        "   - The resize operation overwrites frames.\n"

        "\nUpscale Frames:\n"
        "   - Select a scaling factor in the options menu. Default= x2 \n"

        "\nBatch Upscale:\n"
        "   - Upscales all images in a folder. The source images are not deleted.\n"

        "\nUpscale Image:\n"
        "   - Upscale a single image. The source image is not deleted.\n"

        "\nYou can right-click grayed-out buttons to enable them out of sequence.\n"
        "   - Only use if you know what you're doing!\n"

        "\nThis program will open several command prompts during operation.\n"
        "   - (ffmpeg, realesrgan)"
        )
        self.infotext_label = tk.Label(self, text=info_text, anchor='w', justify=tk.LEFT, wraplength=500)
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
#                   #
# Primary Functions #
#                   #

    def select_video(self):
        self._disable_buttons()
        self.infotext_label.pack_forget()
        self.console_output_label["text"] = ""
        self.operation_label["text"] = ""
        mimetypes.add_type("video/mkv", ".mkv")
        mimetypes.add_type("video/webm", ".webm")
        self.video_file = filedialog.askopenfilename()
        self.filename_label["text"] = os.path.basename(self.video_file)
        video_type = mimetypes.guess_type(self.video_file)[0]
        if video_type not in ["video/mp4", "video/avi", "video/mkv", "video/mov", "video/m4v", "video/wmv", "video/webm", "image/gif"]:
            self.select_button.config(state='normal')
            self.filename_label["text"] = "Unsupported filetype or no file selected"
            return
        self.file_extension = os.path.splitext(self.video_file)[1]
        result = subprocess.run(["./bin/ffprobe.exe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames", "-of", "default=nokey=1:noprint_wrappers=1", self.video_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        total_frames = None
        try:
            total_frames = int(result.stdout.decode().strip())
            middle_frame_number = total_frames // 2
        except ValueError:
            middle_frame_number = 20
        result = subprocess.run(["./bin/ffprobe.exe", "-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.frame_rate = result.stdout.decode().strip()
        numerator, denominator = map(int, self.frame_rate.split('/'))
        self.frame_rate = numerator / denominator
        middle_frame_time = middle_frame_number / float(self.frame_rate)
        result = subprocess.run(["./bin/ffmpeg.exe", "-ss", str(middle_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        img = Image.open(io.BytesIO(result.stdout))
        max_size = (512, 512)
        aspect_ratio = img.width / img.height
        if aspect_ratio > 1:
            new_width = max_size[0]
            new_height = int(max_size[0] / aspect_ratio)
        else:
            new_height = max_size[1]
            new_width = int(max_size[1] * aspect_ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        photoImg = ImageTk.PhotoImage(img)
        if hasattr(self, 'thumbnail_label'):
            self.thumbnail_label['image'] = photoImg
            self.thumbnail_label.image = photoImg
            self.thumbnail_label.bind("<Button-1>", lambda e: self.open_output_folder())
        else:
            self.thumbnail_label = tk.Label(image=photoImg)
            self.thumbnail_label.bind("<Button-1>", lambda e: self.open_output_folder())
            self.thumbnail_label.image = photoImg
            self.thumbnail_label.pack(side="bottom", expand=True, fill="both")
        if total_frames is not None:
            video_length_seconds = total_frames / float(self.frame_rate)
            video_length_time_string = str(datetime.timedelta(seconds=int(video_length_seconds)))
            self.operation_label["text"] = f"Video Length: {video_length_time_string}, Total Frames: {total_frames}"
        else:
            self.operation_label["text"] = f"Info collection failed... You can probably ignore this error."
        self.timer_label["text"] = ""
        self.select_button.config(state='normal')
        self.extract_button.config(state='normal')
        self.stop_button.config(text="STOP", command=self.stop_process)

    def _extract_frames(self):
        try:
            start_time = time.time()
            self.start_timer()
            self.update_timer()
            self._disable_buttons()
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            os.makedirs("raw_frames", exist_ok=True)
            for filename in os.listdir('raw_frames'):
                if os.path.isfile(f'raw_frames/{filename}'):
                    os.remove(f'raw_frames/{filename}')
            try:
                total_frames = int(subprocess.check_output(['./bin/ffprobe.exe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'default=nokey=1:noprint_wrappers=1', self.video_file]).decode('utf-8').strip())
            except Exception as e:
                total_frames = None
            self.process = subprocess.Popen(["./bin/ffmpeg.exe", "-i", self.video_file, "-qscale:v", "3", "-qmin", "3", "-qmax", "3", "-vsync", "0", "raw_frames/frame%08d.jpg"])
            while self.process.poll() is None:
                frame_count = len(glob.glob('raw_frames/*.jpg'))
                if total_frames is not None:
                    elapsed_time = time.time() - start_time
                    fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                    eta = (total_frames / frame_count - 1) * elapsed_time if frame_count > 0 else 0
                    eta_str = str(datetime.timedelta(seconds=int(eta)))
                    percentage_complete = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                    self.console_output_label["text"] = f"Extracted {frame_count:08d} of {total_frames:08d}, {percentage_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
                else:
                    self.console_output_label["text"] = f"Extracted {frame_count:08d} frames"
            frame_count = len(glob.glob('raw_frames/*.jpg'))
            if total_frames is not None:
                elapsed_time = time.time() - start_time
                fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                eta_str = str(datetime.timedelta(seconds=int(eta)))
                percentage_complete = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                self.console_output_label["text"] = f"Extracted {frame_count:08d} of {total_frames:08d}, {percentage_complete:.2f}%\nETA: {eta_str}, FPS: {fps:.2f}"
        finally:
            self.stop_timer()
            self._enable_buttons()
            self.operation_label["text"] = "Done Extracting!"
            self.stop_button.config(text="STOP", command=self.stop_process)
            if self.auto_var.get() == 1:
                self.upscale_frames()
            for button in [self.extract_button, self.merge_button]:
                button.config(state='disabled')
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def _upscale_frames(self):
        try:
            os.makedirs("upscaled_frames", exist_ok=True)
            for file in os.listdir("upscaled_frames"):
                if os.path.isfile(os.path.join("upscaled_frames", file)):
                    os.remove(os.path.join("upscaled_frames", file))
            self.start_timer()
            self.update_timer()
            self._disable_buttons()
            for menu_item in ["Batch Upscale", "Options", "Upscale Image", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            frame_total = len(glob.glob('raw_frames/*.jpg'))
            start_time = datetime.datetime.now()
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", "raw_frames", "-o", "upscaled_frames", "-n", self.upscale_model.get(), "-s", self.scale_factor.get(), "-f", "jpg"])
            while self.process.poll() is None:
                frame_count = len(glob.glob('upscaled_frames/*.jpg'))
                if frame_count > 0:
                    elapsed_time = datetime.datetime.now() - start_time
                    fps = frame_count / elapsed_time.total_seconds()
                    eta = (elapsed_time / frame_count) * (frame_total - frame_count)
                    eta_seconds = int(round(eta.total_seconds()))
                    eta_formatted = str(datetime.timedelta(seconds=eta_seconds))
                    percentage_complete = (frame_count / frame_total) * 100
                    self.console_output_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percentage_complete:.2f}%\nETA: {eta_formatted}, FPS: {fps:.2f}"
                time.sleep(.1)
            if self.keep_raw_var.get() == 0:
                for file in os.listdir("raw_frames"):
                    if os.path.isfile(os.path.join("raw_frames", file)):
                        os.remove(os.path.join("raw_frames", file))
            self.operation_label["text"] = "Done Upscaling!"
            if self.auto_var.get() == 1:
                self.merge_frames()
        except Exception as e:
            self.operation_label["text"] = f"Error: {str(e)}"
        finally:
            self.stop_timer()
            self._enable_buttons()
            self.stop_button.config(text="STOP", command=self.stop_process)
            for button in [self.extract_button, self.upscale_button]:
                button.config(state='disabled')
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def _merge_frames(self):
        try:
            self.start_timer()
            self._disable_buttons()
            total_frames = len(os.listdir("upscaled_frames"))
            self.file_extension = os.path.splitext(self.video_file)[1]
            output_file_name = os.path.splitext(os.path.basename(self.video_file))[0] + "_UPSCALE"
            if self.output_format.get() in ['HQ gif', 'LQ gif']:
                output_file_name += "_" + self.output_format.get().split()[0]
            output_file_name += ('.gif' if self.output_format.get() in ['HQ gif', 'LQ gif'] else '.mp4')
            output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)
            start_file_size = os.path.getsize(self.video_file)
            if self.output_format.get() == 'HQ gif':
                palette_path = "bin/palette%03d.png"
                command_palettegen = ["./bin/ffmpeg.exe", "-y", "-i", "upscaled_frames/frame%08d.jpg", "-vf", "palettegen", palette_path]
                subprocess.call(command_palettegen)
                command = ["./bin/ffmpeg.exe", "-y", "-r", str(self.frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                           "-i", palette_path,
                           "-filter_complex", "paletteuse",
                           output_file_path]
            elif self.output_format.get() == 'LQ gif':
                command = ["./bin/ffmpeg.exe", "-y", "-r", str(self.frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                           "-c:v", 'gif',
                           output_file_path]
            else:
                command = ["./bin/ffmpeg.exe", "-y", "-r", str(self.frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
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
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            start_time = time.time()
            for line in iter(process.stdout.readline, ""):
                frame_number_search = re.search(r'frame=\s*(\d+)', line)
                fps_search = re.search(r'fps=\s*(\d+)', line)
                if frame_number_search:
                    frame_number = int(frame_number_search.group(1))
                    elapsed_time = time.time() - start_time
                    eta_seconds = elapsed_time * (total_frames - frame_number) / frame_number if frame_number != 0 else 0
                    eta_time = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
                    percentage_complete = (frame_number / total_frames) * 100
                    if fps_search:
                        fps = int(fps_search.group(1))
                        self.console_output_label["text"] = f"Frame: {frame_number}/{total_frames}, {percentage_complete:.2f}%\nETA: {eta_time}, FPS: {fps}"
                    else:
                        self.console_output_label["text"] = f"Frame: {frame_number}/{total_frames}, {percentage_complete:.2f}%\nETA: {eta_time}"
            process.stdout.close()
            process.wait()
            end_file_size = os.path.getsize(output_file_path)
            percent_change = ((end_file_size - start_file_size) / start_file_size) * 100
            start_file_size_MB = start_file_size / (1024 * 1024)
            end_file_size_MB = end_file_size / (1024 * 1024)
            self.stop_timer()
            self.operation_label["text"] = f"Done Merging!\nOriginal size: {start_file_size_MB:.2f}MB, Final size: {end_file_size_MB:.2f}MB, Change: {percent_change:.2f}%"
            if os.path.isfile("bin/palette001.png"):
                os.remove("bin/palette001.png")
            if not self.keep_upscaled_var.get():
                for file in os.listdir("upscaled_frames"):
                    if os.path.isfile(os.path.join("upscaled_frames", file)):
                        os.remove(os.path.join("upscaled_frames", file))
            self.console_output_label["text"] = "Output:\n" + output_file_path
            self.stop_button.config(text="Open Output Folder", command=self.open_output_folder)
        except AttributeError as e:
            self.stop_timer()
            self.console_output_label["text"] = "No video_file"
        finally:
            self._enable_buttons()
            for button in [self.extract_button, self.upscale_button, self.merge_button]:
                button.config(state='disabled')

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
                filename_without_ext = os.path.splitext(input_image)[0]
                output_image = filename_without_ext + "_UP" + os.path.splitext(input_image)[1]
                final_output = filename_without_ext + "_UP.jpg"
                if os.path.exists(final_output):
                    result = messagebox.askquestion("File Exists", "The output file already exists. Do you want to overwrite it?", icon='warning')
                    if result == 'yes':
                        os.remove(final_output)
                    else:
                        self.filename_label["text"] = "Upscale Image: Canceled by user..."
                        self.operation_label["text"] = ""
                        return
                self.start_timer()
                self.select_button.config(state='disabled')
                for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                    self.menubar.entryconfig(menu_item, state="disabled")
                with subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", input_image, "-o", output_image, "-n", "realesr-animevideov3", "-s", self.scale_factor.get(), "-f", "jpg"]) as self.process:
                    self.process.wait()
                os.rename(output_image, final_output)
                self.filename_label["text"] = "Output:\n" + final_output
                self.operation_label["text"] = "Done Upscaling!"
                self.select_button.config(state='normal')
                for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                    self.menubar.entryconfig(menu_item, state="normal")
                time.sleep(0.1)
                os.startfile(final_output)
                self.stop_timer()
                self.stop_button.config(text="STOP", command=self.stop_process)
            else:
                self.filename_label["text"] = "No image selected..."
                self.operation_label["text"] = ""
        except Exception as e:
            self.operation_label["text"] = f"An error occurred: {str(e)}"
            self.select_button.config(state='normal')
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
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
                raise ValueError("No source folder selected.")
            self.batchUpscaleMenu.entryconfig(self.source_folder_index, label="Source Folder ✔️")
            self.filename_label["text"] = "Input:\n" + self.source_folder
        except Exception as e:
            self.console_output_label["text"] = str(e)

    def select_output_folder(self):
        try:
            self.output_folder = filedialog.askdirectory()
            if not self.output_folder:
                raise ValueError("No output folder selected.")
            self.batchUpscaleMenu.entryconfig(self.output_folder_index, label="Output Folder ✔️")
            self.console_output_label["text"] = "Output:\n" + self.output_folder
        except Exception as e:
            self.console_output_label["text"] = str(e)

    def _batch_upscale(self):
        try:
            if not self.output_folder:
                self.filename_label["text"] = "Error: No output folder selected."
                return
            for filename in os.listdir(self.output_folder):
                file_path = os.path.join(self.output_folder, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            start_time = time.time()
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            self.filename_label["text"] = "Output:\n" + self.output_folder
            image_files = [file for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp'] for file in glob.glob(f'{self.source_folder}/{ext}')]
            if not image_files:
                self.filename_label["text"] = "Error: No images found in the source folder."
                self.operation_label["text"] = ""
                return
            frame_total = len(image_files)
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", self.source_folder, "-o", self.output_folder, "-n", "realesr-animevideov3", "-s", self.scale_factor.get(), "-f", "jpg"])
            while self.process.poll() is None:
                frame_count = len(glob.glob(f'{self.output_folder}/*.jpg'))
                percent_complete = (frame_count / frame_total) * 100 if frame_total else 0
                elapsed_time = time.time() - start_time
                eta = (elapsed_time / frame_count) * (frame_total - frame_count) if frame_count else 0
                fps = frame_count / elapsed_time if elapsed_time else 0
                self.console_output_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}, {percent_complete:.2f}%\nETA: {time.strftime('%H:%M:%S', time.gmtime(eta))}, FPS: {fps:.2f}"
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")
            self.operation_label["text"] = "Done Upscaling!"
        except Exception as e:
            self.operation_label["text"] = f"Error:\n{str(e)}"
        finally:
            self.stop_timer()
            self.menubar.entryconfig("Batch Upscale", state="normal")

    def clear_folder_choice(self):
        self.source_folder = None
        self.output_folder = None
        self.batchUpscaleMenu.entryconfig(self.source_folder_index, label="Source Folder")
        self.batchUpscaleMenu.entryconfig(self.output_folder_index, label="Output Folder")
        self.select_button.config(state='normal')
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
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
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
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
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
#                #
# Misc Functions #
#                #

    def open_about_window(self):
        self.about_window = AboutWindow(self.master)

    def open_output_folder(self):
        output_file_name = os.path.splitext(os.path.basename(self.video_file))[0] + "_UPSCALE" + self.file_extension
        output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)
        output_folder = os.path.dirname(output_file_path)
        subprocess.Popen(f'explorer {os.path.realpath(output_folder)}')
        time.sleep(1)
        self.stop_button.config(text="STOP", command=self.stop_process)

    def _disable_buttons(self):
        self.select_button.config(state='disabled')
        self.extract_button.config(state='disabled')
        self.merge_button.config(state='disabled')
        self.upscale_button.config(state='disabled')
        self.keep_raw_check.config(state='disabled')
        self.keep_upscaled_check.config(state='disabled')

    def _enable_buttons(self):
        self.select_button.config(state='normal')
        self.extract_button.config(state='normal')
        self.merge_button.config(state='normal')
        self.upscale_button.config(state='normal')
        self.keep_raw_check.config(state='normal')
        self.keep_upscaled_check.config(state='normal')

    def stop_process(self):
        if self.process:
            self.process.kill()
            self.process_stopped = True
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
        if not self.keep_raw_var.get():
            if os.path.exists("raw_frames"):
                for file in os.listdir("raw_frames"):
                    if os.path.isfile(os.path.join("raw_frames", file)):
                        os.remove(os.path.join("raw_frames", file))
        if not self.keep_upscaled_var.get():
            if os.path.exists("upscaled_frames"):
                for file in os.listdir("upscaled_frames"):
                    if os.path.isfile(os.path.join("upscaled_frames", file)):
                        os.remove(os.path.join("upscaled_frames", file))
        root.destroy()

##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Framework #
#           #

root = tk.Tk()
root.title('v1.10 - R-ESRGAN-AnimeVideo-UI')
root.geometry('520x600')
root.resizable(False, False)
app = reav_ui(master=root)
app.mainloop()

##########################################################################################################################################################################
##########################################################################################################################################################################
#v1.10 changes:
#
#- New:
#  - You can now use other upscale models. `RealESRGAN_General_x4_v3, realesrgan-x4plus, realesrgan-x4plus-anime`
#  - 1x scaling is now supported. Note: This is not recommended. [See comparison.](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/Comparisons)
#  - You can now output any video as a gif and export high-quality or low-quality gifs. See [this section of the wiki](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/Gif-creation-and-settings) for details on getting the most out of this feature.
#  - Percent, ETA, and FPS are now displayed during the image scaling process.
#  - You can now resize extracted or upscaled frames by percentage or exact resolution.
#- Fixed:
#  - Buttons are properly grayed out after merging.
