# ~ A1111.py | by ANXETY ~

from _core import UICore, install_ui

ipySys = get_ipython().system


UI = 'A1111'
ui_source = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"   # ZIP source or GIT
is_git = False

core = UICore(UI, ui_source, is_git)
config_url = f"https://raw.githubusercontent.com/{core.FORK_REPO}/{core.BRANCH}/__configs__"


# Config
config_files = [
    # settings
    f"{config_url}/{UI}/config.json",
    f"{config_url}/{UI}/ui-config.json",
    f"{config_url}/styles.csv",
    f"{config_url}/user.css",
    # other
    f"{config_url}/card-no-preview.png, {core.WEBUI}/html",
    f"{config_url}/notification.mp3"
]

# Extensions/Nodes
extensions_list = [
    ## ANXETY Edits
    'https://github.com/anxety-solo/webui_timer timer',
    'https://github.com/anxety-solo/anxety-theme',
    'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',

    ## Gutris1
    'https://github.com/gutris1/sd-image-viewer Image-Viewer',
    'https://github.com/gutris1/sd-image-info Image-Info',
    'https://github.com/gutris1/sd-hub SD-Hub',

    ## OTHER | ON
    'https://github.com/Bing-su/adetailer',

    ## OTHER | OFF
    # 'https://github.com/thomasasfk/sd-webui-aspect-ratio-helper Aspect-Ratio-Helper',
    # 'https://github.com/Mikubill/sd-webui-controlnet ControlNet',
    # 'https://github.com/zanllp/sd-webui-infinite-image-browsing Infinite-Image-Browsing',
    # 'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
    # 'https://github.com/ilian6806/stable-diffusion-webui-state State',
    # 'https://github.com/hako-mikan/sd-webui-supermerger Supermerger',
    # 'https://github.com/DominikDoom/a1111-sd-webui-tagcomplete TagComplete',
    # 'https://github.com/Tsukreya/Umi-AI-Wildcards',
    # 'https://github.com/picobyte/stable-diffusion-webui-wd14-tagger wd14-tagger'
]
if core.ENV_NAME == 'Kaggle':
    extensions_list.append('https://github.com/gutris1/sd-encrypt-image Encrypt-Image')


if __name__ == '__main__':
    install_ui(
        core=core,
        config_files=config_files,
        extensions_list=extensions_list
    )