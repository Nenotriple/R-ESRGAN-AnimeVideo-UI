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
import requests
import zipfile
from io import BytesIO

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

class Downloader:
    def __init__(self, urls=None, files_to_extract=None, files=None):
        self.urls = urls
        self.files_to_extract = files_to_extract
        self.files = files

    def all_files_exist(self, files):
        missing_files = []
        for file in files:
            filename, path = file
            filepath = os.path.join(path, filename.split('/')[-1])
            if not os.path.exists(filepath):
                missing_files.append(filepath)
        return missing_files

    def download_and_extract_files(self):
        if self.urls and self.files_to_extract:
            for url, files in zip(self.urls, self.files_to_extract):
                missing_files = self.all_files_exist(files)
                if missing_files:
                    print(f"Missing files: {missing_files}")
                    self.download_and_extract_file(url, files)

    def download_and_extract_file(self, url, files):
        response = requests.get(url)
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            for file in files:
                filename, path = file
                filepath = os.path.join(path, filename.split('/')[-1])
                if not os.path.exists(filepath):
                    if filename in z.namelist():
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(z.read(filename))
                        print(f"Extracted {filename} to {filepath}")
                    else:
                        print(f"{filename} not found in the zip file")

    def download_files(self):
        if self.files:
            for url, path in self.files:
                filename = url.split("/")[-1]
                filepath = os.path.join(path, filename)
                if not os.path.exists(filepath):
                    print(f"Missing file: {filepath}")
                    self.download_file(url, path)

    def download_file(self, url, path):
        filename = url.split("/")[-1]
        filepath = os.path.join(path, filename)
        os.makedirs(path, exist_ok=True)
        response = requests.get(url)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename} to {filepath}")

downloader = Downloader(urls, files_to_extract, files)
downloader.download_and_extract_files()
downloader.download_files()
