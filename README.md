<p align="center">
  <img src="https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/assets/70049990/1bb2b8da-0f11-401d-a873-7d2f55883fa3" alt="app_cover">
</p>

<h1 align="center">R-ESRGAN-AnimeVideo-UI (reav-ui)</h1>
<p align="center">Upscale your videos using the R-ESRGAN AnimeVideo model</p>

<p align="center">
  <img src="https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/assets/70049990/8b6a27b7-07dc-4820-8455-477a3839fe62)" alt="app_sample">
</p>

## 📝 Usage

- Run the `R-ESRGAN-AnimeVideo-UI.pyw` script to launch the UI.
-  Select a video file that you want to upscale.
-  Follow the steps labeled in the UI.

**Note:** The `Upscale` and `Merge` operations delete the previous frames by default. If you want to keep the frames, make sure to enable the `Keep Frames` option.

After upscaling, you have the option to scale the frames back down to their original size.

mp4, gif, avi, mkv, webm, mov, m4v, wmv, are supported.

## 🤷 Why?

Why use this over an application like [Chainner](https://github.com/chaiNNer-org/chaiNNer), or [Topaz Video AI](https://www.topazlabs.com/)?

While both applications are undoubtedly more than capable, *(among others I'm sure)* I found [xinntao's](https://github.com/xinntao) implementation is extremely fast compared to Chainner. And of course free is always better than Topaz Video AI's high cost.

Other upscale models are popular, but [realesr-animevideov3](https://github.com/xinntao/Real-ESRGAN/blob/master/docs/anime_video_model.md) remains a favorite of mine for multiple reasons.
- It's very fast.
- While it does have somewhat heavy smoothing, it doesn't totally destroy fine details like grain.
- In my opinion it has superb line reconstruction compared to others like `RealESRGAN_x4plus_anime_6B`

Check out these [comparisons](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki). ✨

## 🚩 Requirements

**Running the script will automatically fulfill all requirements.**

The `pillow` library will be downloaded and installed (if not already available) upon first launch.

`ffmpeg` and `ffprobe` will be downloaded upon first launch.

`realesrgan-ncnn-vulkan-20220424-windows.zip` will be downloaded upon first launch.


## 📜 Version History

v1.09 changes:

- New:
    - FPS is now displayed during frame processing.
    - After merging, the STOP button changes function, allowing you to open the output folder.
    - After merging, the original and final file sizes, along with the percent change, are displayed.
    - You can now click on the video preview to open the source folder.
    - You can now output gif files as mp4 (default) or gif format, for a general increase in quality and reduced file size.
    - About menu/window where you can see the info text and open the link to this repo.

- Fixed:
    - The options menu is now accessible at all stages.
    - Issue where pressing stop while auto was enabled would still continue to the next steps.
    - Issue where subfolders present in raw_frames, upscaled_frames, and batch upscale output would cause an error.
    - Issue where details during batch upscale would be incorrect if images were already present in the selected output folder.
  
## 👥 **Credits**

ffmpeg-6.0-essentials: https://ffmpeg.org/

Real-ESRGAN_portable: https://github.com/xinntao/Real-ESRGAN#portable-executable-files-ncnn
