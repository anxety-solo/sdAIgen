## MODEL

model_list = {
    "1.Anime (by XpucT) + INP": [
        {"url": "https://huggingface.co/XpucT/Anime/resolve/main/Anime_v2.safetensors", "name": "Anime_V2.safetensors"},
        {"url": "https://huggingface.co/XpucT/Anime/resolve/main/Anime_v2-inpainting.safetensors", "name": "Anime_V2-inpainting.safetensors"}
    ],
    "2.BluMix [Anime] [V7] + INP": [
        {"url": "https://civitai.com/api/download/models/361779", "name": "BluMix_V7.safetensors"},
        {"url": "https://civitai.com/api/download/models/363850", "name": "BluMix_V7-inpainting.safetensors"}
    ],
    "3.Cetus-Mix [Anime] [V4] + INP": [
        {"url": "https://huggingface.co/fp16-guy/Cetus-Mix_v4_fp16_cleaned/resolve/main/cetusMix_v4_fp16.safetensors", "name": "CetusMix_V4.safetensors"},
        {"url": "https://huggingface.co/fp16-guy/Cetus-Mix_v4_fp16_cleaned/resolve/main/cetusMix_v4_inp_fp16.safetensors", "name": "CetusMix_V4-inpainting.safetensors"}
    ],
    "4.Counterfeit [Anime] [V3] + INP": [
        {"url": "https://huggingface.co/fp16-guy/Counterfeit-V3.0_fp16_cleaned/resolve/main/CounterfeitV30_v30_fp16.safetensors", "name": "Counterfeit_V3.safetensors"},
        {"url": "https://huggingface.co/fp16-guy/Counterfeit-V3.0_fp16_cleaned/resolve/main/CounterfeitV30_v30_inp_fp16.safetensors", "name": "Counterfeit_V3-inpainting.safetensors"}
    ],
    "5.CuteColor [Anime] [V3]": [
        {"url": "https://civitai.com/api/download/models/138754", "name": "CuteColor_V3.safetensors"}
    ],
    "6.Dark-Sushi-Mix [Anime]": [
        {"url": "https://civitai.com/api/download/models/101640", "name": "DarkSushiMix_2_5D.safetensors"},
        {"url": "https://civitai.com/api/download/models/56071", "name": "DarkSushiMix_colorful.safetensors"}
    ],
    "7.Meina-Mix [Anime] [V11] + INP": [
        {"url": "https://civitai.com/api/download/models/119057", "name": "MeinaMix_V11.safetensors"},
        {"url": "https://civitai.com/api/download/models/120702", "name": "MeinaMix_V11-inpainting.safetensors"}
    ],
    "8.Mix-Pro [Anime] [V4] + INP": [
        {"url": "https://huggingface.co/fp16-guy/MIX-Pro-V4_fp16_cleaned/resolve/main/mixProV4_v4_fp16.safetensors", "name": "MixPro_V4.safetensors"},
        {"url": "https://huggingface.co/fp16-guy/MIX-Pro-V4_fp16_cleaned/resolve/main/mixProV4_v4_inp_fp16.safetensors", "name": "MixPro_V4-inpainting.safetensors"},
        {"url": "https://huggingface.co/fp16-guy/MIX-Pro-V4.5_fp16_cleaned/resolve/main/mixProV45Colorbox_v45_fp16.safetensors", "name": "MixPro_V4_5.safetensors"},
        {"url": "https://huggingface.co/fp16-guy/MIX-Pro-V4.5_fp16_cleaned/resolve/main/mixProV45Colorbox_v45_inp_fp16.safetensors", "name": "MixPro_V4_5-inpainting.safetensors"}
    ]
}

## VAE

vae_list = {
    "1.Anime.vae": [
      {"url": "https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/kl-f8-anime2_fp16.safetensors", "name": "Anime-kl-f8.vae.safetensors"},
      {"url": "https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/vae-ft-mse-840000-ema-pruned_fp16.safetensors", "name": "Anime-mse.vae.safetensors"}
    ],
    "2.Anything.vae": [{"url": "https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/anything_fp16.safetensors", "name": "Anything.vae.safetensors"}],
    "3.Blessed2.vae": [{"url": "https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/blessed2_fp16.safetensors", "name": "Blessed2.vae.safetensors"}],
    "4.ClearVae.vae": [{"url": "https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/ClearVAE_V2.3_fp16.safetensors", "name": "ClearVae_23.vae.safetensors"}],
    "5.WD.vae": [{"url": "https://huggingface.co/NoCrypt/resources/resolve/main/VAE/wd.vae.safetensors", "name": "WD.vae.safetensors"}]
}

## CONTROLNET

controlnet_list = {
    "1.Openpose": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_openpose_fp16.yaml"}
    ],
    "2.Canny": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_canny_fp16.yaml"}
    ],
    "3.Depth": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1p_sd15_depth_fp16.yaml"}
    ],
    "4.Lineart": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_lineart_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_lineart_fp16.yaml"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15s2_lineart_anime_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15s2_lineart_anime_fp16.yaml"}
    ],
    "5.ip2p": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_ip2p_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_ip2p_fp16.yaml"}
    ],
    "6.Shuffle": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_shuffle_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_shuffle_fp16.yaml"}
    ],
    "7.Inpaint": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_inpaint_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_inpaint_fp16.yaml"}
    ],
    "8.MLSD": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_mlsd_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_mlsd_fp16.yaml"}
    ],
    "9.Normalbae": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_normalbae_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_normalbae_fp16.yaml"}
    ],
    "10.Scribble": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_scribble_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_scribble_fp16.yaml"}
    ],
    "11.Seg": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_seg_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_seg_fp16.yaml"}
    ],
    "12.Softedge": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_softedge_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_softedge_fp16.yaml"}
    ],
    "13.Tile": [
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors"},
        {"url": "https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1e_sd15_tile_fp16.yaml"}
    ]
}