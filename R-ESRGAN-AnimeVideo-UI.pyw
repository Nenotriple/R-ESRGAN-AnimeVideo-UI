###################################
#                                 #
# RealESRGAN Anime-Video Upscaler #
#                                 #
###################################
# Requirements: #
# ffmpeg        # Included
# ffprobe       # Included
# pillow        # Included: Auto-install
#################

##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Imports #
#         #

import os
import io
import time
import glob
import zipfile
import threading
import mimetypes
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, Tk
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
#                  #
# ArchiveExtractor #
#                  #

class ArchiveExtractor:
    def __init__(self, archive_files):
        self.archive_files = archive_files

    def extract_and_delete(self):
        if not os.path.isfile(self.archive_files[0]):
            return
        with open("ffmpeg.zip", "wb") as output_file:
            for archive_file in self.archive_files:
                with open(archive_file, "rb") as input_file:
                    output_file.write(input_file.read())
        with zipfile.ZipFile("ffmpeg.zip", "r") as zip_ref:
            zip_ref.extractall()
        for archive_file in self.archive_files:
            os.remove(archive_file)
        os.remove("ffmpeg.zip")

archive_files = ["ffmpeg.zip.001", "ffmpeg.zip.002", "ffmpeg.zip.003"]
extractor = ArchiveExtractor(archive_files)
extractor.extract_and_delete()

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

class Application(tk.Frame):
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
        self.fileMenu.add_command(label="Open raw_frames", command=lambda: os.startfile('raw_frames'))
        self.fileMenu.add_command(label="Open upscaled_frames", command=lambda: os.startfile('upscaled_frames'))
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Clear raw_frames", command=lambda: [os.remove(os.path.join('raw_frames', file)) for file in os.listdir('raw_frames')])
        self.fileMenu.add_command(label="Clear upscaled_frames", command=lambda: [os.remove(os.path.join('upscaled_frames', file)) for file in os.listdir('upscaled_frames')])

        self.optionsMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Options", menu=self.optionsMenu)
        self.optionsMenu.add_command(label="Scale output frames to match input frames", command=self.confirm_scale)

        self.batchUpscaleMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Batch Upscale", menu=self.batchUpscaleMenu)
        self.source_folder_index = 0
        self.output_folder_index = 1
        self.clear_folder_choice_index = 2
        self.batchUpscaleMenu.add_command(label="Source Folder", command=self.select_source_folder)
        self.batchUpscaleMenu.add_command(label="Output Folder", command=self.select_output_folder)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Clear Folder Choice", command=self.clear_folder_choice)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Run", command=self.run_upscale)

##########################################################################################################################################################################
##########################################################################################################################################################################
#        #
# Labels #
#        #

        self.filename_label = tk.Label(self)
        self.filename_label["text"] = "Select a video to begin!"
        self.filename_label.pack(side="top", fill=tk.X)

        self.console_output_label = tk.Label(self)
        self.console_output_label["text"] = ""
        self.console_output_label["wraplength"] = 500
        self.console_output_label.pack(side="top", fill=tk.X)       

        self.operation_label = tk.Label(self)
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

        self.merge_button = tk.Button(self, text="4) Merge Frames\t\t\t", command=self.merge_frames)
        self.merge_button.pack(side="top", fill=tk.X)
        self.merge_button.bind('<Button-3>', lambda event: self.merge_button.config(state='normal'))

        self.stop_button = tk.Button(self, text="STOP", command=self.stop_process)
        self.stop_button.pack(side="top", fill=tk.X)

##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Info_Text #
#           #        

        info_text = (
            "\nSelect a video - mp4, avi, mkv\n"
            "\nExtract frames - Enable 'Keep Frames' or they will be deleted at the next step!\n"
            "\nUpscale Frames:\nEnable 'Keep Frames' or they will be deleted at the next step!\n"
            "Options > Scale output frames to match input frames.\n"
            "(Do this before merging for the same size video!)\n"
            "\nYou can right click greyed out buttons to enable them out of sequence.\n"
            "(Only use if you know what you're doing!).\n"
            "\nThis program will open several command prompts during operation.\n"
            "(ffmpeg, realesrgan)"
        )
        self.infotext_label = tk.Label(self, text=info_text, anchor='w', justify=tk.LEFT)
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

    def scale_images(self):
        self.operation_label["text"] = "Resizing... This may take a while..."
        thread = threading.Thread(target=self._scale_images)
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
        mimetypes.add_type("video/x-matroska", ".mkv")
        self.video_file = filedialog.askopenfilename()
        self.filename_label["text"] = os.path.basename(self.video_file)
        video_type = mimetypes.guess_type(self.video_file)[0]
        if video_type not in ["video/mp4", "video/avi", "video/x-matroska"]:
            self.select_button.config(state='normal')
            self.filename_label["text"] = "Unsupported filetype or no file selected"
            return
        self.file_extension = os.path.splitext(self.video_file)[1]
        result = subprocess.run(["ffprobe", "-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.frame_rate = result.stdout.decode().strip()
        numerator, denominator = map(int, self.frame_rate.split('/'))
        self.frame_rate = numerator / denominator
        tenth_frame_time = 20 / float(self.frame_rate)
        result = subprocess.run(["./ffmpeg.exe", "-ss", str(tenth_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        else:
            self.thumbnail_label = tk.Label(image=photoImg)
            self.thumbnail_label.image = photoImg
            self.thumbnail_label.pack(side="bottom", expand=True, fill="both")
        self.operation_label["text"] = ""
        self.timer_label["text"] = ""
        self.select_button.config(state='normal')
        self.extract_button.config(state='normal')
        self.menubar.entryconfig("Options", state="disabled")

    def _extract_frames(self):
        try:
            self.start_timer()
            self.update_timer()
            self._disable_buttons()
            self.menubar.entryconfig("Batch Upscale", state="disabled")
            os.makedirs("raw_frames", exist_ok=True)
            for filename in os.listdir('raw_frames'):
                os.remove(f'raw_frames/{filename}')
            self.process = subprocess.Popen(["./ffmpeg.exe", "-i", self.video_file, "-qscale:v", "3", "-qmin", "3", "-qmax", "3", "-vsync", "0", "raw_frames/frame%08d.jpg"])
            while self.process.poll() is None:
                frame_count = len(glob.glob('raw_frames/*.jpg'))
                self.console_output_label["text"] = f"Extracted {frame_count:08d}"
                time.sleep(.01)
            self.operation_label["text"] = "Done Extracting!"
        except Exception as e:
            self.operation_label["text"] = f"Error: {str(e)}"
        finally:
            self.stop_timer()
            self._enable_buttons()
            self.extract_button.config(state='disabled')
            self.merge_button.config(state='disabled')
            self.menubar.entryconfig("Batch Upscale", state="normal")

    def _upscale_frames(self):
        try:
            for file in os.listdir("upscaled_frames"):
                os.remove(os.path.join("upscaled_frames", file))
            self.start_timer()
            self.update_timer()
            self._disable_buttons()
            self.menubar.entryconfig("Batch Upscale", state="disabled")
            os.makedirs("upscaled_frames", exist_ok=True)
            frame_total = len(glob.glob('raw_frames/*.jpg'))
            self.process = subprocess.Popen(["./realesrgan.exe", "-i", "raw_frames", "-o", "upscaled_frames", "-n", "realesr-animevideov3", "-s", "2", "-f", "jpg"])
            while self.process.poll() is None:
                frame_count = len(glob.glob('upscaled_frames/*.jpg'))
                self.console_output_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}"
                time.sleep(.1)
            if self.keep_raw_var.get() == 0:
                for file in os.listdir("raw_frames"):
                    os.remove(os.path.join("raw_frames", file))
            self.operation_label["text"] = "Done Upscaling!"
        except Exception as e:
            self.operation_label["text"] = f"Error: {str(e)}"
        finally:
            self.stop_timer()
            self._enable_buttons()
            self.upscale_button.config(state='disabled')
            self.extract_button.config(state='disabled')
            self.menubar.entryconfig("Options", state="normal")
            self.menubar.entryconfig("Batch Upscale", state="normal")

    def _merge_frames(self):
        try:
            self.start_timer()
            self._disable_buttons()
            self.menubar.entryconfig("Batch Upscale", state="disabled")
            command = ["ffprobe", "-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file]
            output, _ = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).communicate()
            num, denom = map(int, output.strip().split('/'))
            self.source_frame_rate = num / denom
            output_file_name = os.path.splitext(os.path.basename(self.video_file))[0] + "_UPSCALE" + self.file_extension
            output_file_path = os.path.join(os.path.dirname(self.video_file), output_file_name)    
            self.stop_timer()
            root = tk.Tk()
            root.withdraw()
            if os.path.exists(output_file_path) and messagebox.askquestion("Warning!", "File exists. Overwrite?", icon='warning') != 'yes':
                self.operation_label["text"] = "Operation canceled."
                self._enable_buttons()
                self.stop_timer()
                return
            audio_file = "audio.wav"
            command1 = ["./ffmpeg.exe", "-i", self.video_file, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", audio_file]
            command2 = ["./ffmpeg.exe", "-y", "-r", str(self.frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                       "-i", audio_file,
                       "-c:v", 'libx264',
                       "-c:a", "aac",
                       "-vsync", "0",
                       "-map", "0:v:0",
                       "-map", "1:a:0",
                       "-pix_fmt","yuv420p",
                       "-crf","18",
                       output_file_path]
            for command in [command1, command2]:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
                for line in iter(process.stdout.readline, ""):
                    self.console_output_label["text"] = line.replace("time=", "").replace("dup=", "").replace("drop=", "").strip()
                process.stdout.close()
                process.wait()
            if os.path.exists(audio_file):
                os.remove(audio_file)
            if not self.keep_upscaled_var.get():
                for file in os.listdir("upscaled_frames"):
                    os.remove(os.path.join("upscaled_frames", file))           
            self.operation_label["text"] = "Done Merging!"
            self.console_output_label["text"] = ""
        except AttributeError as e:
            self.stop_timer()
            self.console_output_label["text"] = "No video_file"
        finally:
            self.stop_timer()
            self._enable_buttons()
            self.extract_button.config(state='disabled')
            self.merge_button.config(state='disabled')
            self.upscale_button.config(state='disabled')
            self.menubar.entryconfig("Options", state="disabled")
            self.menubar.entryconfig("Batch Upscale", state="normal")

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
            self.batchUpscaleMenu.entryconfig("Source Folder", label="Source Folder ✔️")
            self.filename_label["text"] = "Input:", self.source_folder
            self.filename_label['wraplength'] = 500
        except Exception as e:
            self.console_output_label["text"] = str(e)
            self.console_output_label['wraplength'] = 500

    def select_output_folder(self):
        try:
            self.output_folder = filedialog.askdirectory()
            if not self.output_folder:
                raise ValueError("No output folder selected.")
            self.batchUpscaleMenu.entryconfig("Output Folder", label="Output Folder ✔️")
            self.console_output_label["text"] = "Output:", self.output_folder
            self.console_output_label['wraplength'] = 500
        except Exception as e:
            self.console_output_label["text"] = str(e)
            self.console_output_label['wraplength'] = 500
    
    def run_upscale(self):
        try:
            if not self.source_folder or not self.output_folder:
                raise ValueError("Source or output folder not selected.")
            command = ["./realesrgan.exe", "-i", self.source_folder, "-o", self.output_folder, "-n", "realesr-animevideov3", "-s", "2", "-f", "jpg"]
            self.process = subprocess.Popen(command)
            self.batchUpscaleMenu.entryconfig("Source Folder", label="Source Folder")
            self.batchUpscaleMenu.entryconfig("Output Folder", label="Output Folder")
        except Exception as e:
            self.console_output_label["text"] = str(e)
    
    def clear_folder_choice(self):
        self.source_folder = None
        self.output_folder = None
        self.batchUpscaleMenu.entryconfig(self.source_folder_index, label="Source Folder")
        self.batchUpscaleMenu.entryconfig(self.output_folder_index, label="Output Folder")
        self.select_button.config(state='normal')
        self.console_output_label["text"] = "..."
        self.filename_label["text"] = "..."

##########################################################################################################################################################################
##########################################################################################################################################################################
#              #
# Scale Images #
#              #

    def _scale_images(self):
        try:
            self.start_timer()
            self.update_timer()
            self._disable_buttons()
            self.menubar.entryconfig("Batch Upscale", state="disabled")
            image_total = len(glob.glob('upscaled_frames/*.jpg'))
            if not os.listdir("upscaled_frames"):
                self.operation_label["text"] = "No images found!"
                return
            image_count = 0
            for filename in os.listdir("upscaled_frames"):
                img = Image.open(os.path.join("upscaled_frames", filename))
                img = img.resize((img.size[0]//2, img.size[1]//2))
                img.save(os.path.join("upscaled_frames", filename), "JPEG", quality=100)
                image_count += 1
                self.console_output_label["text"] = f"Scaled {image_count:08d}, of {image_total:08d}"
            self.operation_label["text"] = "Done Resizing!"
        except Exception as e:
            self.operation_label["text"] = f"Error: {str(e)}"
        finally:
            self.stop_timer()
            self._enable_buttons()
            self.extract_button.config(state='disabled')
            self.upscale_button.config(state='disabled')
            self.menubar.entryconfig("Batch Upscale", state="normal")

    def confirm_scale(self):
        result = messagebox.askquestion("Scale Images", "This operation will resize images in the 'upscaled_frames' folder by half.\n\nThis is a destructive process, the old images will be deleted!", icon='warning')
        if result == 'yes':
            self.scale_images()            

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

    def _is_codec_available(self, codec):
        command = ['./ffmpeg.exe', '-codecs']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        available_codecs = out.decode('utf-8')
        return codec in available_codecs

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

    def on_closing(self):
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.communicate(timeout=5)
            except TimeoutExpired:
                self.process.kill()
                self.process.communicate()
        if not self.keep_raw_var.get():
            for file in os.listdir("raw_frames"):
                os.remove(os.path.join("raw_frames", file))
        if not self.keep_upscaled_var.get():
            for file in os.listdir("upscaled_frames"):
                os.remove(os.path.join("upscaled_frames", file))
        root.destroy()

##########################################################################################################################################################################
##########################################################################################################################################################################
#           #
# Framework #
#           #

root = tk.Tk()
root.title('v1.0 - R-ESRGAN-AnimeVideo-UI')
root.geometry('520x600')
root.resizable(False, False)
app = Application(master=root)
app.mainloop()
