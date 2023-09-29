# R-ESRGAN-AnimeVideo-UI
Upscale your videos using the R-ESRGAN AnimeVideo model

![R-ESRGAN-AnimeVideo-UI_coverB](https://github.com/Nenotriple/R-ESRGAN-AnimeVideo-UI/assets/70049990/79130cc1-68b9-4976-9da6-9f8795b045d5)

## Usage

- Run the `R-ESRGAN-AnimeVideo-UI.pyw` script to launch the UI.
-  Select a video file that you want to upscale.
-  Follow the steps labeled in the UI.

**Note:** The `Upscale` and `Merge` operations delete the previous frames by default. If you want to keep the frames, make sure to enable the `Keep Frames` option.

After upscaling, you have the option to scale the frames back down to their original size.

Currently only mp4, avi, mkv, are supported.

## Why?

Why use this over an application like [Chainner](https://github.com/chaiNNer-org/chaiNNer), or [Topaz Video AI](https://www.topazlabs.com/)?

While both applications are undoubtedly more than capable, *(among others I'm sure)* I found [xinntao's](https://github.com/xinntao) implementation is extremely fast compared to Chainner. And of course free is always better than Topaz Video AI's high cost.

Other upscale models are popular, but [realesr-animevideov3](realesr-animevideov3) remains a favorite of mine for multiple reasons.
- It's very fast.
- While it does have somewhat heavy smoothing, it doesn't totally destroy fine details like grain.
- In my opinion it has superb line reconstruction compared to others like `RealESRGAN_x4plus_anime_6B`

## Requirements

**Running the script will automatically fulfill all requirements.**

The `pillow` library will be downloaded and installed (if not already available) upon first launch.

`ffmpeg` and `ffprobe` are included in the package and will be extracted upon first launch.

## **Credits**

ffmpeg - https://ffmpeg.org/

Real-ESRGAN - https://github.com/xinntao/Real-ESRGAN
