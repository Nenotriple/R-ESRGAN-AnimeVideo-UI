# This script downloads all files required to run reav-ui

import os
import zipfile
import requests
from urllib.request import urlopen, urlretrieve

# URLs to download from
urls = [
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip",
    "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-6.0-essentials_build.zip"
]

# Files to extract and their destination paths
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
# Handles zip file download
def download_zip(count, block_size, total_size, filename):
    downloaded_mb = count * block_size / (1024 * 1024)
    total_mb = total_size / (1024 * 1024)
    print(f"\rDownloading: {filename} {downloaded_mb:.2f}MB / {total_mb:.2f}MB", end='')

for url, files in zip(urls, files_to_extract):
    # Check if all files exist
    all_files_exist = all(os.path.exists(os.path.join(destination, os.path.basename(file))) for file, destination in files)

    # If not all files exist, download and extract the zip file
    if not all_files_exist:
        # Print out missing files
        missing_files = [os.path.join(destination, os.path.basename(file)) for file, destination in files if not os.path.exists(os.path.join(destination, os.path.basename(file)))]
        print("\nMissing files:")
        for file in missing_files:
            print(file)

        # Download the zip file from the URL
        zip_file_path, _ = urlretrieve(url, filename=url.split('/')[-1], reporthook=lambda count, block_size, total_size: download_zip(count, block_size, total_size, url.split('/')[-1]))

        with zipfile.ZipFile(zip_file_path, 'r') as zfile:
            for file, destination in files:
                filename_only = os.path.basename(file)
                destination_path = os.path.join(destination, filename_only)

                # Check if the file already exists at the destination path
                if not os.path.exists(destination_path):
                    # Create directories if they don't exist
                    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

                    # Open each file and write its contents to the desired location
                    with zfile.open(file) as zf, open(destination_path, 'wb') as f:
                        f.write(zf.read())

        os.remove(zip_file_path)

# Handles individual file downloads
def download_file(url, path):
    filename = url.split("/")[-1]
    filepath = os.path.join(path, filename)

    # Check if file already exists
    if os.path.exists(filepath):
        return

    # Download the file
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

# List of files to download
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

# Check if all files exist
all_files_exist = all(os.path.exists(os.path.join(destination, os.path.basename(file))) for file, destination in files)

if not all_files_exist:
    # Print out missing files
    missing_files = [os.path.join(destination, os.path.basename(file)) for file, destination in files if not os.path.exists(os.path.join(destination, os.path.basename(file)))]
    print("\nMissing files:")
    for file in missing_files:
        print(file)

# Download all files
for url, path in files:
    download_file(url, path)
