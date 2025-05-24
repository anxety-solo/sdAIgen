# ~ ReForge.py | by ANXETY ~

from Manager import m_download, m_clone    # Every Download | Clone
import json_utils as js                    # JSON

from IPython.display import clear_output
from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import os


CD = os.chdir
ipySys = get_ipython().system

# Constants
UI = 'ReForge'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
EXTS = js.read(SETTINGS_PATH, 'WEBUI.extension_dir')

CD(HOME)


## ================== WEB UI OPERATIONS ==================

async def _download_file(url, directory, filename):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    process = await asyncio.create_subprocess_shell(
        f"curl -sLo {file_path} {url}",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    await process.communicate()

async def download_files(file_list):
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory = parts[1].strip() if len(parts) > 1 else WEBUI   # Default Save Path
        filename = parts[2].strip() if len(parts) > 2 else os.path.basename(url)
        tasks.append(_download_file(url, directory, filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    ## FILES
    url_cfg = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
    configs = [
        # settings
        f"{url_cfg}/{UI}/config.json",
        f"{url_cfg}/{UI}/ui-config.json",
        f"{url_cfg}/styles.csv",
        f"{url_cfg}/user.css",
        # other
        f"{url_cfg}/card-no-preview.png, {WEBUI}/html",
        f"{url_cfg}/notification.mp3"
    ]
    await download_files(configs)

    ## REPOS
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
        # 'https://github.com/zanllp/sd-webui-infinite-image-browsing Infinite-Image-Browsing',
        # 'https://github.com/hako-mikan/sd-webui-regional-prompter Regional-Prompter',
        # 'https://github.com/ilian6806/stable-diffusion-webui-state State',
        # 'https://github.com/hako-mikan/sd-webui-supermerger Supermerger',
        # 'https://github.com/DominikDoom/a1111-sd-webui-tagcomplete TagComplete',
        # 'https://github.com/Tsukreya/Umi-AI-Wildcards',
        # 'https://github.com/picobyte/stable-diffusion-webui-wd14-tagger wd14-tagger'
    ]
    if ENV_NAME == 'Kaggle':
        extensions_list.append('https://github.com/gutris1/sd-encrypt-image Encrypt-Image')

    os.makedirs(EXTS, exist_ok=True)
    CD(EXTS)

    tasks = []
    for command in extensions_list:
        tasks.append(asyncio.create_subprocess_shell(
            f"git clone --depth 1 {command}",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ))

    await asyncio.gather(*tasks)

def unpack_webui():
    zip_path = f"{HOME}/{UI}.zip"
    m_download(f"{REPO_URL} {HOME} {UI}.zip")
    ipySys(f"unzip -q -o {zip_path} -d {WEBUI}")
    ipySys(f"rm -rf {zip_path}")

## ====================== MAIN CODE ======================
if __name__ == '__main__':
    with capture.capture_output():
        unpack_webui()
        asyncio.run(download_configuration())