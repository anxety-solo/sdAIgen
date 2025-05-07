# ~ ComfyUI.py | by ANXETY ~

from _core import UICore, install_ui    # UI-Core

ipySys = get_ipython().system


UI = 'ComfyUI'
ui_source = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"   # ZIP source or GIT
is_git = False

core = UICore(UI, ui_source, is_git)
config_url = f"https://raw.githubusercontent.com/{core.FORK_REPO}/{core.BRANCH}/__configs__"

def post_install(core: UICore):
    ipySys('pip install gradio-tunneling')


# Config
config_files=[
    # settings
    f"{config_url}/{UI}/install-deps.py",
    f"{config_url}/{UI}/comfy.settings.json, {core.WEBUI}/user/default",                        # ComfyUI settings
    f"{config_url}/{UI}/Comfy-Manager/config.ini, {core.WEBUI}/user/default/ComfyUI-Manager",   # ComfyUI-Manager settings
    # workflows
    f"{config_url}/{UI}/workflows/anxety-workflow.json, {core.WEBUI}/user/default/workflows",
    # other | tunneling
    f"{config_url}/{UI}/gradio-tunneling.py, {core.VENV}/lib/python3.10/site-packages/gradio_tunneling, main.py"    # Replace py-Script
]

# Extensions/Nodes
extensions_list=[
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


if __name__ == '__main__':
    install_ui(
        core=core,
        config_files=config_files,
        extensions_list=extensions_list,
        post_install=post_install
    )