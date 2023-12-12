"""
########################################
#                                      #
#         collect_requirements         #
#                                      #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################

Description:
-------------
This script downloads all files for reav-ui.

More info here: https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI

"""

import os
import sys
import zipfile
import requests
from urllib.request import urlretrieve
from tkinter import messagebox

files = [
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesr-animevideov3-x1.bin", "bin/models"),
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesr-animevideov3-x1.param", "bin/models"),
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/RealESRGAN_General_x4_v3.bin", "bin/models"),
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/RealESRGAN_General_x4_v3.param", "bin/models"),
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus-anime.bin", "bin/models"),
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus-anime.param", "bin/models"),
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus.bin", "bin/models"),
        ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus.param", "bin/models")
        ]

urls = [
        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip",
        "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-6.0-essentials_build.zip"
        ]

files_to_extract = [
                    [
                    ("realesrgan-ncnn-vulkan.exe", "bin"),
                    ("vcomp140d.dll", "bin"),
                    ("vcomp140.dll", "bin"),
                    ("models/realesr-animevideov3-x2.bin", "bin/models"),
                    ("models/realesr-animevideov3-x3.bin", "bin/models"),
                    ("models/realesr-animevideov3-x4.bin", "bin/models"),
                    ("models/realesr-animevideov3-x2.param", "bin/models"),
                    ("models/realesr-animevideov3-x3.param", "bin/models"),
                    ("models/realesr-animevideov3-x4.param", "bin/models")
                    ],
                    [
                    ("ffmpeg-6.0-essentials_build/bin/ffmpeg.exe", "bin"),
                    ("ffmpeg-6.0-essentials_build/bin/ffprobe.exe", "bin")
                    ]
                    ]

# Check if all files exist
all_files_exist = all(os.path.exists(os.path.join(destination, os.path.basename(file))) for file, destination in files)

# Check if all files to extract exist
all_files_to_extract_exist = all(os.path.exists(os.path.join(destination, os.path.basename(file))) for file_list in files_to_extract for file, destination in file_list)

# If not all files or files to extract exist, find the missing ones
if not all_files_exist or not all_files_to_extract_exist:
    missing_files = [os.path.basename(file) for file, destination in files if not os.path.exists(os.path.join(destination, os.path.basename(file)))]
    missing_files_to_extract = [os.path.basename(file) for file_list in files_to_extract for file, destination in file_list if not os.path.exists(os.path.join(destination, os.path.basename(file)))]
    print("\nMissing files:")
    for file in missing_files + missing_files_to_extract:
        print(file)
    missing_files_str = '\n'.join(missing_files + missing_files_to_extract)
    download_requirements = messagebox.askyesno("Download Required", f"The following files need to be downloaded.\n\n{missing_files_str}\n\nThe files will download in the background, and the app will open automatically when ready.")
    if not download_requirements:
        sys.exit()

# Function to download a zip file
def download_zip(count, block_size, total_size, filename):
    downloaded_mb = count * block_size / (1024 * 1024)
    total_mb = total_size / (1024 * 1024)
    print(f"\rDownloading: {filename} {downloaded_mb:.2f}MB / {total_mb:.2f}MB", end='')
# Loop over all urls and corresponding files to extract
for url, files in zip(urls, files_to_extract):
    all_files_exist = all(os.path.exists(os.path.join(destination, os.path.basename(file))) for file, destination in files)
    if not all_files_exist:
        missing_files = [os.path.join(destination, os.path.basename(file)) for file, destination in files if not os.path.exists(os.path.join(destination, os.path.basename(file)))]
        zip_file_path, _ = urlretrieve(url, filename=url.split('/')[-1], reporthook=lambda count, block_size, total_size: download_zip(count, block_size, total_size, url.split('/')[-1]))
        with zipfile.ZipFile(zip_file_path, 'r') as zfile:
            for file, destination in files:
                filename_only = os.path.basename(file)
                destination_path = os.path.join(destination, filename_only)
                if not os.path.exists(destination_path):
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                    with zfile.open(file) as zf, open(destination_path, 'wb') as f:
                        f.write(zf.read())
        os.remove(zip_file_path)

# Function to download a file
def download_file(url, path):
    filename = url.split("/")[-1]
    filepath = os.path.join(path, filename)
    if os.path.exists(filepath):
        return
    response = requests.get(url, stream=True)
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024
    total_mb = total_size_in_bytes / (1024 * 1024)
    with open(filepath, 'wb') as file:
        downloaded_mb = 0
        for data in response.iter_content(block_size):
            downloaded_mb += len(data) / (1024 * 1024)
            file.write(data)
            print(f"\rDownloading: {filename} {downloaded_mb:.2f}MB / {total_mb:.2f}MB", end='')
    print()

for url, path in files:
    download_file(url, path)
