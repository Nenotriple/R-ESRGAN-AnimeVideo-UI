##########################
#                        #
# R-ESRGAN-AnimeVideo-UI #
#         reav-ui        #
#      Version 1.05      #
#                        #
##########################
# Requirements: #
# ffmpeg        # Included
# ffprobe       # Included
# pillow        # Included: Auto-install
##########################################################################################################################################################################
##########################################################################################################################################################################
#         #
# Imports #
#         #

import os
import io
import time
import glob
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

        # This script collects ffmpeg, realesrgan
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
        self.fileMenu.add_command(label="Open raw_frames", command=lambda: os.startfile('raw_frames'))
        self.fileMenu.add_command(label="Open upscaled_frames", command=lambda: os.startfile('upscaled_frames'))
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Clear raw_frames", command=lambda: [os.remove(os.path.join('raw_frames', file)) for file in os.listdir('raw_frames')])
        self.fileMenu.add_command(label="Clear upscaled_frames", command=lambda: [os.remove(os.path.join('upscaled_frames', file)) for file in os.listdir('upscaled_frames')])

        self.optionsMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Options", menu=self.optionsMenu)
        self.optionsMenu.add_command(label="Scale output frames to match input frames", command=self.confirm_scale)

        self.source_folder_index = 0
        self.output_folder_index = 1
        self.clear_folder_choice_index = 2
        self.batchUpscaleMenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Batch Upscale", menu=self.batchUpscaleMenu)        
        self.batchUpscaleMenu.add_command(label="Source Folder", command=self.select_source_folder)
        self.batchUpscaleMenu.add_command(label="Output Folder", command=self.select_output_folder)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Clear Folder Choice", command=self.clear_folder_choice)
        self.batchUpscaleMenu.add_separator()
        self.batchUpscaleMenu.add_command(label="Run", command=self.batch_upscale)

        self.menubar.add_command(label="Upscale Image", command=self.select_and_upscale_image)              

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
            "\nSelect a video:\n"
            "   - mp4, gif, avi, mkv, webm, mov, m4v, wmv\n"

            "\nUpscale Frames:\n"
            "   - After upscaling video frames you can scale them down to the original size.\n"
            "       Options > Scale output frames to match input frames.\n"

            "\nUpscale Image:\n"
            "   - Select a single image to upscale.\n"

            "\nNOTE: The Upscale and Merge operations delete the previous frames by default.\n"
            "   - If you want to keep the frames, make sure to enable the Keep Frames option.\n"            

            "\nYou can right click greyed out buttons to enable them out of sequence.\n"
            "   - (Only use if you know what you're doing!).\n" 

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
        result = subprocess.run(["./bin/ffprobe.exe", "-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.frame_rate = result.stdout.decode().strip()
        numerator, denominator = map(int, self.frame_rate.split('/'))
        self.frame_rate = numerator / denominator
        tenth_frame_time = 20 / float(self.frame_rate)
        result = subprocess.run(["./bin/ffmpeg.exe", "-ss", str(tenth_frame_time), "-i", self.video_file, "-vframes", "1", "-f", "image2pipe", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            os.makedirs("raw_frames", exist_ok=True)
            for filename in os.listdir('raw_frames'):
                os.remove(f'raw_frames/{filename}')
            self.process = subprocess.Popen(["./bin/ffmpeg.exe", "-i", self.video_file, "-qscale:v", "3", "-qmin", "3", "-qmax", "3", "-vsync", "0", "raw_frames/frame%08d.jpg"])
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
            for button in [self.extract_button, self.merge_button]:
                button.config(state='disabled')            
            for menu_item in ["Batch Upscale", "Upscale Image", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def _upscale_frames(self):
        try:
            for file in os.listdir("upscaled_frames"):
                os.remove(os.path.join("upscaled_frames", file))
            self.start_timer()
            self.update_timer()
            self._disable_buttons()
            for menu_item in ["Batch Upscale", "Options", "Upscale Image", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            os.makedirs("upscaled_frames", exist_ok=True)
            frame_total = len(glob.glob('raw_frames/*.jpg'))
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", "raw_frames", "-o", "upscaled_frames", "-n", "realesr-animevideov3", "-s", "2", "-f", "jpg"])
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
            for button in [self.extract_button, self.upscale_button]:
                button.config(state='disabled')            
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def _merge_frames(self):
        try:
            self.start_timer()
            self._disable_buttons()
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            command = ["./bin/ffprobe.exe", "-v", "0", "-of", "compact=p=0:nk=1", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", self.video_file]
            output, _ = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True).communicate()
            num, denom = map(int, output.strip().split('/'))
            self.source_frame_rate = num / denom
            self.file_extension = os.path.splitext(self.video_file)[1]
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
            if self.file_extension == '.gif':
                command = ["./bin/ffmpeg.exe", "-y", "-r", str(self.frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                           "-i", self.video_file,
                           "-c:v", 'gif',
                           output_file_path]
            else:
                command = ["./bin/ffmpeg.exe", "-y", "-r", str(self.frame_rate), "-i", "upscaled_frames/frame%08d.jpg",
                           "-i", self.video_file,
                           "-c:v", 'libx264',
                           "-c:a", "copy",
                           "-vsync", "0",
                           "-map", "0:v:0",
                           "-map", "1:a:0",
                           "-pix_fmt","yuv420p",
                           "-crf","18",
                           output_file_path]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            for line in iter(process.stdout.readline, ""):
                self.console_output_label["text"] = line.replace("time=", "").replace("dup=", "").replace("drop=", "").strip()
            process.stdout.close()
            process.wait()
            self.stop_timer()
            self.operation_label["text"] = "Done Merging!"
            if not self.keep_upscaled_var.get():
                for file in os.listdir("upscaled_frames"):
                    os.remove(os.path.join("upscaled_frames", file))           
            self.console_output_label["text"] = "Output:\n" + output_file_path
        except AttributeError as e:
            self.stop_timer()
            self.console_output_label["text"] = "No video_file"
        finally:
            self._enable_buttons()
            for button in [self.extract_button, self.merge_button, self.upscale_button]:
                button.config(state='disabled')
            for menu_item in ["Batch Upscale", "Upscale Image", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

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
                with subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", input_image, "-o", output_image, "-n", "realesr-animevideov3", "-s", "2", "-f", "jpg"]) as self.process:
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
            self.start_timer()
            self.update_timer()
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
            self.filename_label["text"] = "Output:\n" + self.output_folder
            image_files = [file for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp'] for file in glob.glob(f'{self.source_folder}/{ext}')]
            if not image_files:
                self.filename_label["text"] = "Error: No images found in the source folder."
                self.operation_label["text"] = ""
                return
            frame_total = len(image_files)
            self.process = subprocess.Popen(["./bin/realesrgan-ncnn-vulkan.exe", "-i", self.source_folder, "-o", self.output_folder, "-n", "realesr-animevideov3", "-s", "2", "-f", "jpg"])
            while self.process.poll() is None:
                frame_count = len(glob.glob(f'{self.output_folder}/*.jpg'))
                self.console_output_label["text"] = f"Upscaled {frame_count:08d}, of {frame_total:08d}"
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")
                time.sleep(.1)
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

    def _scale_frames(self):
        try:
            self.start_timer()
            self.update_timer()
            self._disable_buttons()
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="disabled")
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
            self.operation_label["text"] = f"Error:\n{str(e)}"
        finally:
            self.stop_timer()
            self._enable_buttons()
            self.extract_button.config(state='disabled')
            self.upscale_button.config(state='disabled')
            for menu_item in ["Batch Upscale", "Upscale Image", "Options", "File"]:
                self.menubar.entryconfig(menu_item, state="normal")

    def confirm_scale(self):
        result = messagebox.askquestion("Scale Images", "This operation will resize images in the 'upscaled_frames' folder by half.\n\nThis is a destructive process, the old images will be deleted!", icon='warning')
        if result == 'yes':
            self.scale_frames()          

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
                if os.path.isfile(os.path.join("raw_frames", file)):
                    os.remove(os.path.join("raw_frames", file))
        if not self.keep_upscaled_var.get():
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
root.title('v1.05 - R-ESRGAN-AnimeVideo-UI')
root.geometry('520x600')
root.resizable(False, False)
app = reav_ui(master=root)
app.mainloop()

##########################################################################################################################################################################
##########################################################################################################################################################################

#v1.05 changes:
#
#- New:
#    - All requirements are now downloaded upon launch instead of packaged together with the script.
#    - Upscale Image. Upscales single image, saves with "_UP" appended to filename, opens in default image viewer when complete.
#    - Added support for: gif, webm, mov, m4v, wmv.
#- Fixed:
#    - Audio is now directly copied from source, not re-encoded. This improves quality and speeds up the merging process.
#    - an error when a subfolder was present in either "raw_frames" or "upscaled_frames" when closing the application.
#    - ffprobe now properlly called.
#- Batch Upscale updates:
#    - Provides upscale details, runs in threaded process for smoother UI.
#    - Batch Upscale updates: Added error handling/guidance.
#    - Batch Upscale updates: Fixed "bad menu entry index" error when choosing folder path twice.
