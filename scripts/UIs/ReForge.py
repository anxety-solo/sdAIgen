# ~ ReForge.py | by ANXETY ~

from _core import *
from IPython.utils import capture
import asyncio

# Configuration
UI = 'ReForge'
REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
WEBUI = HOME / UI

CONFIGS = [
    # Settings
    f"{UI}/config.json",
    f"{UI}/ui-config.json",
    "styles.csv",
    "user.css",
    # Other files
    "card-no-preview.png, html",
    "notification.mp3"
]

EXTENSIONS = [
    # ANXETY Edits
    'https://github.com/anxety-solo/webui_timer timer',
    'https://github.com/anxety-solo/anxety-theme',
    'https://github.com/anxety-solo/sd-civitai-browser-plus Civitai-Browser-Plus',

    # Gutris1
    'https://github.com/gutris1/sd-image-viewer Image-Viewer',
    'https://github.com/gutris1/sd-image-info Image-Info',
    'https://github.com/gutris1/sd-hub SD-Hub',

    # OTHER | ON
    'https://github.com/Bing-su/adetailer',

    # OTHER | OFF
    # 'https://github.com/thomasasfk/sd-webui-aspect-ratio-helper Aspect-Ratio-Helper',
    # 'https://github.com/zanllp/sd-webui-infinite-image-browsing Infinite-Image-Browsing',
    # 'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
    # 'https://github.com/ilian6806/stable-diffusion-webui-state State',
    # 'https://github.com/hako-mikan/sd-webui-supermerger Supermerger',
    # 'https://github.com/DominikDoom/a1111-sd-webui-tagcomplete TagComplete',
    # 'https://github.com/Tsukreya/Umi-AI-Wildcards',
    # 'https://github.com/picobyte/stable-diffusion-webui-wd14-tagger wd14-tagger'
]

async def install_reforge():
    # Download and extract WebUI
    install_zip(REPO_URL, WEBUI)

    # Download configs
    base_url = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    await asyncio.gather(*[
        download_file(f"{base_url}/{cfg}", WEBUI)
        for cfg in CONFIGS
    ])

    # Install extensions
    if ENV_NAME == 'Kaggle':
        EXTENSIONS.append('https://github.com/gutris1/sd-encrypt-image Encrypt-Image')

    await asyncio.gather(*[
        git_clone(repo) for repo in EXTENSIONS
    ])

if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(install_reforge())