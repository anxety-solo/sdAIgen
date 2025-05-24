# ~ ComfyUI.py | by ANXETY ~

from _core import *
from IPython.utils import capture
import asyncio

# Configuration
UI = 'ComfyUI'
REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
WEBUI = HOME / UI
VENV = HOME / 'venv'

CONFIGS = [
    # Settings
    f"{UI}/install-deps.py",
    f"{UI}/comfy.settings.json, user/default",
    f"{UI}/Comfy-Manager/config.ini, user/default/ComfyUI-Manager",
    # Workflows
    f"{UI}/workflows/anxety-workflow.json, user/default/workflows",
    # Tunneling
    f"{UI}/gradio-tunneling.py, {VENV}/lib/python3.10/site-packages/gradio_tunneling, main.py"
]

EXTENSIONS = [
    'https://github.com/Fannovel16/comfyui_controlnet_aux',
    'https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet',
    'https://github.com/hayden-fr/ComfyUI-Model-Manager',
    'https://github.com/jags111/efficiency-nodes-comfyui',
    'https://github.com/ltdrdata/ComfyUI-Impact-Pack',
    'https://github.com/ltdrdata/ComfyUI-Impact-Subpack',
    'https://github.com/ltdrdata/ComfyUI-Manager',
    'https://github.com/pythongosssss/ComfyUI-Custom-Scripts',
    'https://github.com/pythongosssss/ComfyUI-WD14-Tagger',
    'https://github.com/ssitu/ComfyUI_UltimateSDUpscale',
    'https://github.com/WASasquatch/was-node-suite-comfyui'
]

async def install_comfyui():
    # Download and extract WebUI
    install_zip(REPO_URL, WEBUI)

    # Install additional dependencies
    ipySys('pip install gradio-tunneling')

    # Download configs
    base_url = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    await asyncio.gather(*[
        download_file(f"{base_url}/{cfg}", WEBUI)
        for cfg in CONFIGS
    ])

    # Install extensions (with --recursive for ComfyUI)
    os.makedirs(EXTS, exist_ok=True)
    await asyncio.gather(*[
        git_clone(repo, depth=1) for repo in EXTENSIONS
    ])

if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(install_comfyui())