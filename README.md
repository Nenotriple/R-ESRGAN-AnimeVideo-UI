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
-  Select a video file that you want to upscale.
-  Follow the steps labeled in the UI.

**Note:** The `Upscale` and `Merge` operations delete the previous frames by default. If you want to keep the frames, make sure to enable the `Keep Frames` option.

After extracting/upscaling, you have the option to scale the frames to any size.

mp4, gif, avi, mkv, webm, mov, m4v, wmv, are supported.

Explore the options!

## 🤷 Why?

Why use this over an application like [Chainner](https://github.com/chaiNNer-org/chaiNNer), or [Topaz Video AI](https://www.topazlabs.com/)?

While both applications are undoubtedly more than capable, *(among others, I'm sure)* I found [xinntao's](https://github.com/xinntao) implementation is extremely fast compared to Chainner. And of course free is always better than Topaz Video AI's high cost.

Other upscale models are popular, but [realesr-animevideov3](https://github.com/xinntao/Real-ESRGAN/blob/master/docs/anime_video_model.md) remains a favorite of mine for multiple reasons.
- It's very fast. [Speed Tests](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/Speed-Tests)
- While it does have somewhat heavy smoothing, it doesn't totally destroy fine details like grain.
- In my opinion, it has superb line reconstruction compared to others like `RealESRGAN_x4plus_anime_6B`

Check out these [comparisons.✨](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/Comparisons)

## 🚩 Requirements

**You must have Python 3.10+ installed to the system PATH**

**Running the script will automatically fulfill all requirements.**

The `pillow` library will be downloaded and installed (if not already available) upon first launch.

`ffmpeg` and `ffprobe` will be downloaded upon first launch.

`realesrgan-ncnn-vulkan-20220424-windows.zip` and the required models will be downloaded upon launch.


## 📜 Version History

v1.10 changes:

- New:
  - You can now use other upscale models. `RealESRGAN_General_x4_v3, realesrgan-x4plus, realesrgan-x4plus-anime`
  - 1x scaling is now supported. Note: This is not recommended. [See comparison.](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/Comparisons)
  - You can now output any video as a gif and export high-quality or low-quality gifs. See [this section of the wiki](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/wiki/Gif-creation-and-settings) for details on getting the most out of this feature.
  - Percent, ETA, and FPS are now displayed during the image scaling process.
  - You can now resize extracted or upscaled frames by percentage or exact resolution.  
- Fixed:
  - Buttons are properly grayed out after merging.
  
## 👥 **Credits**

ffmpeg-6.0-essentials: https://ffmpeg.org/

Real-ESRGAN_portable: https://github.com/xinntao/Real-ESRGAN#portable-executable-files-ncnn
