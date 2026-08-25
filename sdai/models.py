""" Model Catalog: SD/XL/ANIMA Registries & Resolver | by ANXETY """

import re


SD = {
    'model': {
        'BluMix [Anime | V7] + INP': [
            {'url': 'https://civitai.red/api/download/models/361779', 'name': 'BluMix_V7.safetensors'}
        ],
        'Cetus-Mix [Anime | V4] + INP': [
            {'url': 'https://huggingface.co/fp16-guy/Cetus-Mix_v4_fp16_cleaned/resolve/main/cetusMix_v4_fp16.safetensors', 'name': 'CetusMix_V4.safetensors'}
        ],
        'Counterfeit [Anime | V3] + INP': [
            {'url': 'https://huggingface.co/fp16-guy/Counterfeit-V3.0_fp16_cleaned/resolve/main/CounterfeitV30_v30_fp16.safetensors', 'name': 'Counterfeit_V3.safetensors'}
        ],
        'CuteColor [Anime | V3]': [
            {'url': 'https://civitai.red/api/download/models/138754', 'name': 'CuteColor_V3.safetensors'}
        ],
        'Dark-Sushi-Mix [Anime]': [
            {'url': 'https://civitai.red/api/download/models/141866', 'name': 'DarkSushiMix_2_5D.safetensors'},
            {'url': 'https://civitai.red/api/download/models/56071', 'name': 'DarkSushiMix_colorful.safetensors'}
        ],
        'Meina-Mix [Anime | V12] + INP': [
            {'url': 'https://civitai.red/api/download/models/948574', 'name': 'MeinaMix_V12.safetensors'}
        ],
        'Mix-Pro [Anime | V4] + INP': [
            {'url': 'https://huggingface.co/fp16-guy/MIX-Pro-V4_fp16_cleaned/resolve/main/mixProV4_v4_fp16.safetensors', 'name': 'MixPro_V4.safetensors'},
            {'url': 'https://huggingface.co/fp16-guy/MIX-Pro-V4.5_fp16_cleaned/resolve/main/mixProV45Colorbox_v45_fp16.safetensors', 'name': 'MixPro_V4_5.safetensors'}
        ],
    },

    'vae': {
        'Anime.vae': [
            {'url': 'https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/kl-f8-anime2_fp16.safetensors', 'name': 'Anime-kl-f8.vae.safetensors'},
            {'url': 'https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/vae-ft-mse-840000-ema-pruned_fp16.safetensors', 'name': 'Anime-mse.vae.safetensors'}
        ],
        'Anything.vae': [{'url': 'https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/anything_fp16.safetensors', 'name': 'Anything.vae.safetensors'}],
        'Blessed2.vae': [{'url': 'https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/blessed2_fp16.safetensors', 'name': 'Blessed2.vae.safetensors'}],
        'ClearVae.vae': [{'url': 'https://huggingface.co/fp16-guy/anything_kl-f8-anime2_vae-ft-mse-840000-ema-pruned_blessed_clearvae_fp16_cleaned/resolve/main/ClearVAE_V2.3_fp16.safetensors', 'name': 'ClearVae_23.vae.safetensors'}],
        'WD.vae': [{'url': 'https://huggingface.co/NoCrypt/resources/resolve/main/VAE/wd.vae.safetensors', 'name': 'WD.vae.safetensors'}],
    },

    'controlnet': {
        'Openpose': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_openpose_fp16.yaml'}
        ],
        'Canny': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_canny_fp16.yaml'}
        ],
        'Depth': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1p_sd15_depth_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1p_sd15_depth_fp16.yaml'}
        ],
        'Lineart': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_lineart_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_lineart_fp16.yaml'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15s2_lineart_anime_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15s2_lineart_anime_fp16.yaml'}
        ],
        'ip2p': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_ip2p_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_ip2p_fp16.yaml'}
        ],
        'Shuffle': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11e_sd15_shuffle_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11e_sd15_shuffle_fp16.yaml'}
        ],
        'Inpaint': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_inpaint_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_inpaint_fp16.yaml'}
        ],
        'MLSD': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_mlsd_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_mlsd_fp16.yaml'}
        ],
        'Normalbae': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_normalbae_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_normalbae_fp16.yaml'}
        ],
        'Scribble': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_scribble_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_scribble_fp16.yaml'}
        ],
        'Seg': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_seg_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_seg_fp16.yaml'}
        ],
        'Softedge': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11p_sd15_softedge_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11p_sd15_softedge_fp16.yaml'}
        ],
        'Tile': [
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/resolve/main/control_v11f1e_sd15_tile_fp16.safetensors'},
            {'url': 'https://huggingface.co/ckpt/ControlNet-v1-1/raw/main/control_v11f1e_sd15_tile_fp16.yaml'}
        ],
    }
}

XL = {
    'model': {
        'Flanime-IL [Anime | 4.0 | IL]': [
            {'url': 'https://civitai.red/api/download/models/2944197', 'name': 'FlanimeXL-illustrious_V4.safetensors'}
        ],
        'Hassaku-XL [Anime | V3.4 | IL]': [
            {'url': 'https://civitai.red/api/download/models/2615702', 'name': 'HassakuXL-illustrious_V3.4.safetensors'}
        ],
        'Nova-IL [Anime | V19 | IL]': [
            {'url': 'https://civitai.red/api/download/models/2940478', 'name': 'Nova-illustrious_V19.safetensors'}
        ],
        'NoobAI [Anime | VP-1.0 | NAI]': [
            {'url': 'https://civitai.red/api/download/models/1190596', 'name': 'NoobAI_VP1.safetensors'}
        ],
        'WAI-IL [Anime | V17 | IL]': [
            {'url': 'https://civitai.red/api/download/models/2883731', 'name': 'WAI-illustrious_V17.safetensors'}
        ],
    },

    'vae': {
        'sdxl.vae': [{'url': 'https://huggingface.co/madebyollin/sdxl-vae-fp16-fix/resolve/main/sdxl.vae.safetensors', 'name': 'sdxl.vae.safetensors'}],
    },

    'controlnet': {
        'Kohya Controllite XL Blur': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_blur.safetensors'},
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_blur_anime.safetensors'}
        ],
        'Kohya Controllite XL Canny': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_canny.safetensors'},
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_canny_anime.safetensors'}
        ],
        'Kohya Controllite XL Depth': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_depth.safetensors'},
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_depth_anime.safetensors'}
        ],
        'Kohya Controllite XL Openpose Anime': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_openpose_anime.safetensors'},
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_openpose_anime_v2.safetensors'}
        ],
        'Kohya Controllite XL Scribble Anime': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/kohya_controllllite_xl_scribble_anime.safetensors'}
        ],
        'T2I Adapter XL Canny': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_xl_canny.safetensors'}
        ],
        'T2I Adapter XL Openpose': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_xl_openpose.safetensors'}
        ],
        'T2I Adapter XL Sketch': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_xl_sketch.safetensors'}
        ],
        'T2I Adapter Diffusers XL Canny': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_canny.safetensors'}
        ],
        'T2I Adapter Diffusers XL Depth Midas': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_depth_midas.safetensors'}
        ],
        'T2I Adapter Diffusers XL Depth Zoe': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_depth_zoe.safetensors'}
        ],
        'T2I Adapter Diffusers XL Lineart': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_lineart.safetensors'}
        ],
        'T2I Adapter Diffusers XL Openpose': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_openpose.safetensors'}
        ],
        'T2I Adapter Diffusers XL Sketch': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/t2i-adapter_diffusers_xl_sketch.safetensors'}
        ],
        'IP Adapter SDXL': [
            {'url': 'https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter_sdxl.safetensors'}
        ],
        'IP Adapter SDXL VIT-H': [
            {'url': 'https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter_sdxl_vit-h.safetensors'}
        ],
        'Diffusers XL Canny Mid': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/diffusers_xl_canny_mid.safetensors'}
        ],
        'Diffusers XL Depth Mid': [
            {'url': 'https://huggingface.co/lllyasviel/sd_control_collection/resolve/main/diffusers_xl_depth_mid.safetensors'}
        ],
        'Controlnet Union SDXL 1.0': [
            {'url': 'https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/resolve/main/diffusion_pytorch_model.safetensors', 'name': 'controlnet-union-sdxl-1.0.safetensors'}
        ],
        'Controlnet Union SDXL Pro Max': [
            {'url': 'https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/resolve/main/diffusion_pytorch_model_promax.safetensors', 'name': 'controlnet-union-sdxl-promax.safetensors'}
        ],
    },
}

ANIMA = {
    'model': {
        'MiaoMiao Harem [Anime | Color V1]': [
            {'url': 'https://civitai.red/api/download/models/3203207', 'name': 'MiaoMiao-Harem-Color_V1.safetensors'}
        ],
    },

    'vae': {
        'Qwen2D VAE': [{'url': 'https://huggingface.co/Anzhc/Qwen2D-VAE/resolve/main/Qwen2D_VAE.safetensors'}],
        'Qwen Image VAE': [{'url': 'https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors'}],
    },

    'additional': {
        'qwen_3_06b_base': [
            {'url': 'https://huggingface.co/circlestone-labs/Anima/resolve/main/split_files/text_encoders/qwen_3_06b_base.safetensors', 'dst_dir': 'encoder_dir'}
        ],
    },
}


MODEL_CATEGORIES = {
    'SD':    SD,
    'XL':    XL,
    'ANIMA': ANIMA,
}


# ~~ HELPERS ~~


def find_model_by_partial_name(partial_name: str, model_dict: dict) -> str | None:
    """
    Find model in dictionary by partial name (case-insensitive)
    Returns the full key name if found, None otherwise.
    """
    if not partial_name or partial_name.lower() in {'none', 'all'}:
        return partial_name

    def normalize(name: str) -> str:
        return re.sub(r'^\d+\.\s*', '', name).lower()

    target = normalize(partial_name)
    return next((key for key in model_dict if target in normalize(key)), None)


def get_category(key: str) -> dict:
    return MODEL_CATEGORIES.get(key, SD)
