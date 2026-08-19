""" WebUI Metadata Module | by ANXETY """

# === SDAIGEN ===
from sdai.constants import HOME_PATH, VENV_PATH, HF_REPO_URL


# ~~ SHARED CONFIGS ~~

DEFAULT_VENV = 'python31018-venv-torch260-cu124-fa.tar.lz4'

DEFAULT_PYTHON   = '3.10'
DEFAULT_UI       = 'Neo'
DEFAULT_LAUNCHER = 'launch.py'
DEFAULT_PORT     = 7860

A1111_CONFIG = (
    ('{ui}/config.json', 'config.json'),
    ('{ui}/ui-config.json', 'ui-config.json'),
    ('_shared/styles.csv', 'styles.csv'),
    ('_shared/user.css', 'user.css'),
    ('_shared/card-no-preview.png', 'html/card-no-preview.png'),
    ('_shared/notification.mp3', 'notification.mp3'),
    ('_shared/gradio-tunneling.py', '{venv}/lib/python{pyver}/site-packages/gradio_tunneling/main.py'),
    ('_shared/tagcomplete-tags-parser.py', 'tagcomplete-tags-parser.py'),
)

CLASSIC_CONFIG = (
    ('{ui}/config.json', 'config.json'),
    ('{ui}/ui-config.json', 'ui-config.json'),
    ('_shared/styles.csv', 'styles.csv'),
    ('_shared/user.css', 'user.css'),
    ('_shared/card-no-preview.png', 'html/card-no-preview.jpg'),
    ('_shared/notification.mp3', 'notification.mp3'),
    ('_shared/gradio-tunneling.py', '{venv}/lib/python{pyver}/site-packages/gradio_tunneling/main.py'),
    ('_shared/tagcomplete-tags-parser.py', 'tagcomplete-tags-parser.py'),
)

COMFY_CONFIG = (
    ('{ui}/install-deps.py', 'install-deps.py'),
    ('{ui}/comfy.settings.json', 'user/default/comfy.settings.json'),
    ('{ui}/comfy-manager/config.ini', 'user/__manager/config.ini'),
    ('{ui}/workflows/anxety-workflow.json', 'user/default/workflows/anxety-workflow.json'),
    ('_shared/gradio-tunneling.py', '{venv}/lib/python{pyver}/site-packages/gradio_tunneling/main.py'),
)

# Folder tuple order: checkpoint, vae, lora, embed, extension, upscale, output
A1111_FOLDERS   = ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs')
CLASSIC_FOLDERS = ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'output')
COMFY_FOLDERS   = ('checkpoints', 'vae', 'loras', 'embeddings', 'custom_nodes', 'upscale_models', 'output')


# ~~ WEBUI REGISTRY ~~

WEBUIS = {
    'A1111': {
        'layout': 'a1111',
        'github_url': 'https://github.com/AUTOMATIC1111/stable-diffusion-webui',
        'branch': 'master',
        'branch_exclude': None,
        'python': DEFAULT_PYTHON,
        'venv': DEFAULT_VENV,
        'port': DEFAULT_PORT,
        'folders': A1111_FOLDERS,
        'config': A1111_CONFIG,
        'launcher': DEFAULT_LAUNCHER,
        'launch_args': '--xformers',
        'adetailer_cache': True,
    },
    'ComfyUI': {
        'layout': 'comfy',
        'github_url': 'https://github.com/comfyanonymous/ComfyUI',
        'branch': 'master',
        'branch_exclude': None,
        'python': '3.13',
        'venv': 'python31312-venv-torch2100-cu130-ComfyUI.tar.lz4',
        'port': 8188,
        'folders': COMFY_FOLDERS,
        'config': COMFY_CONFIG,
        'launcher': 'main.py',
        'launch_args': '--dont-print-server',
        'adetailer_cache': False,
    },
    'Forge': {
        'layout': 'a1111',
        'github_url': 'https://github.com/lllyasviel/stable-diffusion-webui-forge',
        'branch': 'main',
        'branch_exclude': None,
        'python': DEFAULT_PYTHON,
        'venv': DEFAULT_VENV,
        'port': DEFAULT_PORT,
        'folders': A1111_FOLDERS,
        'config': A1111_CONFIG,
        'launcher': DEFAULT_LAUNCHER,
        'launch_args': '--xformers --cuda-stream',
        'adetailer_cache': False,
    },
    'Classic': {
        'layout': 'haoming',
        'github_url': 'https://github.com/Haoming02/sd-webui-forge-classic',
        'branch': 'classic',
        'branch_exclude': ['neo'],
        'python': '3.11',
        'venv': 'python31113-venv-torch280-cu126-Classic.tar.lz4',
        'port': DEFAULT_PORT,
        'folders': CLASSIC_FOLDERS,
        'config': CLASSIC_CONFIG,
        'launcher': DEFAULT_LAUNCHER,
        'launch_args': '--xformers --cuda-stream --persistent-patches --skip-version-check',
        'adetailer_cache': False,
    },
    'Neo': {
        'layout': 'haoming',
        'github_url': 'https://github.com/Haoming02/sd-webui-forge-classic',
        'branch': 'neo',
        'branch_exclude': ['classic'],
        'python': '3.13',
        'venv': 'python31312-venv-torch2100-cu130-Neo.tar.lz4',
        'port': DEFAULT_PORT,
        'folders': CLASSIC_FOLDERS,
        'config': CLASSIC_CONFIG,
        'launcher': DEFAULT_LAUNCHER,
        'launch_args': '--xformers --cuda-malloc --cuda-stream  --persistent-patches --skip-version-check',
        'adetailer_cache': False,
    },
    'ReForge': {
        'layout': 'a1111',
        'github_url': 'https://github.com/Panchovix/stable-diffusion-webui-reForge',
        'branch': 'main',
        'branch_exclude': None,
        'python': '3.12',
        'venv': 'python31213-venv-torch2100-cu130-ReForge.tar.lz4',
        'port': DEFAULT_PORT,
        'folders': A1111_FOLDERS,
        'config': A1111_CONFIG,
        'launcher': DEFAULT_LAUNCHER,
        'launch_args': '--xformers',
        'adetailer_cache': False,
    },
    'SD-UX': {
        'layout': 'a1111',
        'github_url': 'https://github.com/anapnoe/stable-diffusion-webui-ux',
        'branch': 'master',
        'branch_exclude': None,
        'python': DEFAULT_PYTHON,
        'venv': DEFAULT_VENV,
        'port': DEFAULT_PORT,
        'folders': A1111_FOLDERS,
        'config': A1111_CONFIG,
        'launcher': DEFAULT_LAUNCHER,
        'launch_args': '--xformers',
        'adetailer_cache': True,
    },
}


# ~~ HELPERS ~~

def resolve(ui: str) -> str:
    """Return the UI key or the default UI for unknown values"""
    return ui if ui in WEBUIS else DEFAULT_UI


def meta(ui: str) -> dict:
    """Get metadata dict for UI, falling back to default"""
    return WEBUIS[resolve(ui)]


# ~~ URL BUILDERS ~~

def build_urls(ui: str) -> dict:
    """Build all archive URLs for the given UI"""
    _m = meta(ui)

    urls = {
        'webui':     f"{HF_REPO_URL}/{resolve(ui)}.zip",
        'venv':      f"{HF_REPO_URL}/{_m['venv']}",
        'embeds':    f"{HF_REPO_URL}/embeds.zip",
        'upscalers': f"{HF_REPO_URL}/upscalers.zip",
    }

    if _m.get('adetailer_cache'):
        urls['adetailer_cache'] = f"{HF_REPO_URL}/hf_cache_adetailer.zip"

    return urls


def build_config_urls(ui: str, github: str, branch: str) -> list:
    """Build (url, dest_path) pairs for all config files of the UI"""
    _m = meta(ui)
    ui_key = resolve(ui)

    webui_root  = HOME_PATH / ui_key
    configs_url = f"https://raw.githubusercontent.com/{github}/{branch}/configs"

    return [
        (
            f"{configs_url}/{src.format(ui=ui_key)}",
            webui_root / dest.format(venv=str(VENV_PATH), pyver=_m['python'])
        )
        for src, dest in _m['config']
    ]


def build_extensions_url(ui: str, github: str, branch: str) -> str:
    """URL of the UI's extensions list file"""
    return f"https://raw.githubusercontent.com/{github}/{branch}/configs/{resolve(ui)}/extensions.txt"


# ~~ PATH BUILDERS ~~

def build_paths(ui: str) -> dict:
    """Build all WebUI directories for the given UI from meta"""
    _m = meta(ui)

    webui_root  = HOME_PATH / resolve(ui)
    models_root = webui_root / 'models'

    checkpoint, vae, lora, embed, extension, upscale, output = _m['folders']

    is_comfy   = _m['layout'] == 'comfy'
    is_haoming = _m['layout'] == 'haoming'

    control_dir = 'controlnet' if is_comfy else 'ControlNet'
    embed_root  = models_root if (is_comfy or is_haoming) else webui_root
    config_root = webui_root / 'user/default' if is_comfy else webui_root

    return {
        # Main Directories
        'model_dir':     models_root / checkpoint,
        'vae_dir':       models_root / vae,
        'lora_dir':      models_root / lora,
        'embed_dir':     embed_root / embed,
        'extension_dir': webui_root / extension,
        'control_dir':   models_root / control_dir,
        'upscale_dir':   models_root / upscale,
        'output_dir':    webui_root / output,
        'config_dir':    config_root,
        # Additional Directories
        'adetailer_dir': models_root / ('ultralytics' if is_comfy else 'adetailer'),
        'clip_dir':      models_root / ('clip' if is_comfy else 'text_encoder'),
        'unet_dir':      models_root / ('unet' if is_comfy else 'text_encoder'),
        'vision_dir':    models_root / 'clip_vision',
        'encoder_dir':   models_root / ('text_encoders' if is_comfy else 'text_encoder'),
        'diffusion_dir': models_root / 'diffusion_models',
    }
