<p align="center">
  <img src="https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/assets/70049990/22e22572-5cb3-4bf1-a7fc-bc871b855174" alt="reav-ui cover_small">
</p>

<h1 align="center">R-ESRGAN-AnimeVideo-UI (reav-ui)</h1>
<p align="center">Upscale your videos using the R-ESRGAN AnimeVideo model</p>

<p align="center">
  <img src="https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/assets/70049990/79130cc1-68b9-4976-9da6-9f8795b045d5)" alt="reav-ui app_sample">
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

Check out these [upscale comparisons](https://github.com/xinntao/Real-ESRGAN/blob/master/docs/anime_video_model.md).

## 🚩 Requirements

**Running the script will automatically fulfill all requirements.**

The `pillow` library will be downloaded and installed (if not already available) upon first launch.

`ffmpeg` and `ffprobe` will be downloaded upon first launch.

`realesrgan-ncnn-vulkan-20220424-windows.zip` will be downloaded upon first launch.


## 📜 Version History

v1.07 changes:

- Changed:
   - All videos are now output with .mp4 format, .gif output remains unchanged.
- New:
   - Auto mode: This automatically runs Upscale and Merge operations after Extracting or Upscaling frames.
   - Total video frames are now displayed in the ui while extracting. (for most filetypes)
   - Video length and frame count now visible after selecting a video. (for most filetypes)
   - Selecting a video now displays the middle most frame in the ui instead of the 20th frame. (for most filetypes)
- Fixed:
   - Fixed crash/hang when the app was expecting raw_frames and upscaled_frames folders when they don't exist.
   - Fixed a similar error when running upscale frames without a directory setup prior.
  
## 👥 **Credits**

ffmpeg-6.0-essentials - https://ffmpeg.org/

Real-ESRGAN_portable - https://github.com/xinntao/Real-ESRGAN#portable-executable-files-ncnn
