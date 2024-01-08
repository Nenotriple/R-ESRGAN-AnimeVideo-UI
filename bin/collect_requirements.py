
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
import urllib.request
from urllib.parse import urlparse
import zipfile
import tempfile
import shutil
import time


print("File Check: Starting...")


def all_files_exist(file_list):
    for file in file_list:
        if not os.path.exists(os.path.join(file[1], os.path.basename(file[0]))):
            return False
    return True


def download_file(url, save_path):
    download_complete = False
    last_update = 0
    def reporthook(blocknum, blocksize, totalsize):
        nonlocal download_complete, last_update
        readsofar = blocknum * blocksize
        if totalsize > 0:
            if readsofar >= totalsize or blocksize > totalsize:
                if not download_complete:
                    if totalsize / 1024 / 1024 < 2:
                        print(f"\rFile Check: 100% - {totalsize / 1024:.2f} KB - Download complete\n")
                    else:
                        print(f"\rFile Check: 100% - {totalsize / 1024 / 1024:.2f} MB - Download complete\n")
                    download_complete = True
            else:
                percent = readsofar * 1e2 / totalsize
                if time.time() - last_update > 0.1:
                    if totalsize / 1024 / 1024 < 2:
                        status = f"\rDownload:{percent:5.1f}%, {readsofar / 1024 :>{len(str(int(totalsize / 1024)))}.2f} / {totalsize / 1024:.2f} KB"
                    else:
                        status = f"\rDownload:{percent:5.1f}%, {readsofar / 1024 / 1024 :>{len(str(int(totalsize / 1024 / 1024)))}.2f} / {totalsize / 1024 / 1024:.2f} MB"
                    print(status, end='')
                    last_update = time.time()
        else:
            print(f"File Check: read - {readsofar}\n", end='')
    if not os.path.exists(save_path):
        file_name = os.path.basename(urlparse(url).path)
        print(f"File Check: Downloading - {file_name}")
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            urllib.request.urlretrieve(url, tmp_file.name, reporthook)
        shutil.move(tmp_file.name, save_path)


def extract_files(zip_path, file_list):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in file_list:
            if not os.path.exists(file[1]):
                os.makedirs(file[1])
            if not os.path.exists(os.path.join(file[1], os.path.basename(file[0]))):
                print(f"File Check: Extracting - {file[0]} to {file[1]}")
                zip_ref.extract(file[0])
                os.rename(file[0], os.path.join(file[1], os.path.basename(file[0])))
            else:
                print(f"File Check: File - {os.path.join(file[1], os.path.basename(file[0]))} already exists. Skipping extraction.")
    os.remove(zip_path)
    for root, dirs, files in os.walk(".", topdown=False):
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                pass


zip_file_url_resrgan  = ["https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip"]
zip_file_url_ffmpeg   = ["https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-6.0-essentials_build.zip"]


zip_file_list_resrgan = [
                        ("realesrgan-ncnn-vulkan.exe",           "bin"),
                        ("vcomp140d.dll",                        "bin"),
                        ("vcomp140.dll",                         "bin"),
                        ("models/realesr-animevideov3-x2.bin",   "bin/models"),
                        ("models/realesr-animevideov3-x3.bin",   "bin/models"),
                        ("models/realesr-animevideov3-x4.bin",   "bin/models"),
                        ("models/realesr-animevideov3-x2.param", "bin/models"),
                        ("models/realesr-animevideov3-x3.param", "bin/models"),
                        ("models/realesr-animevideov3-x4.param", "bin/models")
                        ]


zip_file_list_ffmpeg  = [
                        ("ffmpeg-6.0-essentials_build/bin/ffmpeg.exe",  "bin"),
                        ("ffmpeg-6.0-essentials_build/bin/ffprobe.exe", "bin")
                        ]


file_url =  [
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesr-animevideov3-x1.bin",    "bin/models"),
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesr-animevideov3-x1.param",  "bin/models"),
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/RealESRGAN_General_x4_v3.bin",   "bin/models"),
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/RealESRGAN_General_x4_v3.param", "bin/models"),
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus-anime.bin",    "bin/models"),
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus-anime.param",  "bin/models"),
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus.bin",          "bin/models"),
            ("https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/raw/main/bin/models/realesrgan-x4plus.param",        "bin/models")
            ]


if not all_files_exist(zip_file_list_resrgan):
    for url in zip_file_url_resrgan:
        download_file(url, os.path.basename(url))
        extract_files(os.path.basename(url), zip_file_list_resrgan)


if not all_files_exist(zip_file_list_ffmpeg):
    for url in zip_file_url_ffmpeg:
        download_file(url, os.path.basename(url))
        extract_files(os.path.basename(url), zip_file_list_ffmpeg)


for url, path in file_url:
    if not os.path.exists(path):
        os.makedirs(path)
    download_file(url, os.path.join(path, os.path.basename(url)))


print("File Check: All Files verified!")
