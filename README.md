<p align="center">
  <img src="https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/assets/70049990/1bb2b8da-0f11-401d-a873-7d2f55883fa3" alt="app_cover">
</p>

<h1 align="center">R-ESRGAN-AnimeVideo-UI (reav-ui)</h1>
<p align="center">Upscale your videos using the R-ESRGAN AnimeVideo model</p>

<p align="center">
  <img src="https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/assets/70049990/e3554a6b-fbb8-4606-9caf-8da2cd065a88" alt="app_sample">
</p>

## 📝 Usage

- Run the portable executable file or the `R-ESRGAN-AnimeVideo-UI.pyw` script to launch the UI.
- Wait for the required files to downloaded. ~200mb - ffmpeg, ffprobe realesrgan-ncnn-vulkan-20220424-windows, models from this repo.
- Select a video file that you want to upscale.
- Follow the steps labeled in the UI.

**Note:** The `Upscale` and `Merge` operations delete the previous frames by default. If you want to keep the frames, make sure to enable the `Keep Frames` option.

After Extracting or Upscaling, you have the option to scale the frames to any size, either by percent or exact resolution.

`mp4`, `gif`, `avi`, `mkv`, `webm`, `mov`, `m4v`, `wmv`, are supported.

- Other Uses:
  - Batch Upscale a folder of images.
  - Upscale a single image.
  - You can also use these models for upscaling: `RealESRGAN_General_x4_3`, `realesrgan-x4plus`, `realesrgan-x4plus-anime`
  - Output any video as a gif, and/or output gif as mp4.


## 🤷 Why?

Why use this over an application like [Chainner](https://github.com/chaiNNer-org/chaiNNer), or [Topaz Video AI](https://www.topazlabs.com/)?

While both applications are undoubtedly more than capable, *(among others, I'm sure)* I found [xinntao's](https://github.com/xinntao) implementation is extremely fast compared to Chainner. And of course free is always better than Topaz Video AI's high cost.

Other upscale models are popular, but [realesr-animevideov3](https://github.com/xinntao/Real-ESRGAN/blob/master/docs/anime_video_model.md) remains a favorite of mine for multiple reasons.
- It's very fast. [Speed Tests⏱️](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/%E2%8F%B1%EF%B8%8FSpeed-Tests)
- While it does have somewhat heavy smoothing, it doesn't totally destroy fine details like grain.
- In my opinion, it has superb line reconstruction compared to others like `RealESRGAN_x4plus_anime_6B`

Check out these [comparisons.✨](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/%E2%9A%96%EF%B8%8F-Comparisons)

## 🚩 Requirements

You don't need to worry about anything if you're using the [portable/executable](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/releases?q=executable&expanded=true) version.

___

**You must have Python 3.10+ installed to the system PATH**

**Running the script will automatically fulfill all requirements.**

The `pillow` library will be downloaded and installed (if not already available) upon first launch.

`ffmpeg` and `ffprobe` will be downloaded upon first launch.

`realesrgan-ncnn-vulkan-20220424-windows.zip` and the required models will be downloaded upon launch.


## 📜 Version History

[v1.17 changes:](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/releases/tag/v1.16)

- New:
  - A terminal window now opens with the app to display various info/errors etc.
    - This is really helpful during the initial startup while downloading files, and checking previous completed processes, etc.
  - An [hstack][hstack] video is now created during the "Create Sample" process.
  - You can now set an audio bitrate.
  - You can now enter an exact audio or video bitrate value.
  -  New preset for Audio/Video Bitrate options, `Auto From Source`.
    - Regular "Auto" mode allows FFmpeg to choose a bitrate when merging. This generally results in lower quality video and audio.
    - When you select "Auto From Source" for "Video Bitrate", it will use source video bitrate and add 1500.
    - When you select "Auto From Source" for "Audio Bitrate", it will use the source audio bitrate.
  - `Batch Resize Image` Added to the "Image" tab. From here you can select a folder and resize images to any resolution.
    - There's also an option to resize a single image.
  - You can now define a start time for creating the preview sample,
  - Output videos are now encoded with a keyframe every 10 video frames. This results in much smoother seeking. but larger file size.
  - You can now skip the upscale process. This is useful if you just want to resize a video


<br>


- Fixed:
  - Video frame rate info collection is now more robust.
  - Fix an issue where the app would remain running if closed during "auto > upscale"
  - Handle an error when "Toggle Animated Thumbnail" doesn't work.
  - Fixed error preventing multipliers like "x0.25", "x4" from working as a resize input.
  - Fixed error that would occur after first selecting an invalid filetype, then selecting a valid filetype.


- Other changes:
  - `Batch Image Upscale` Added back to the Tools menu. This just opens the Image tab.
  - Renamed "R-ESRGAN-AnimeVideo-UI.pyw" to "R-ESRGAN-AnimeVideo-UI.py"
  - Moved "icon.ico" to "bin" folder.


[hstack]: https://ffmpeg.org/ffmpeg-filters.html#hstack-1
  
## 👥 **Credits**

ffmpeg-6.0-essentials: https://ffmpeg.org/

Real-ESRGAN_portable: https://github.com/xinntao/Real-ESRGAN#portable-executable-files-ncnn
