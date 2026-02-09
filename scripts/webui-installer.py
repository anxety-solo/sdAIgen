# ~ webui-installer.py | by ANXETY ~

from Manager import m_download  # Every Download
import json_utils as js         # JSON

from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import aiohttp
import os


osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# Auto-convert *_path env vars to Path
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, SCR_PATH, VENV, SETTINGS_PATH = (
    PATHS['home_path'], PATHS['scr_path'], PATHS['venv_path'], PATHS['settings_path']
)

UI    = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = HOME / UI
EXTS  = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir'))
EMBED = Path(js.read(SETTINGS_PATH, 'WEBUI.embed_dir'))
UPSC  = Path(js.read(SETTINGS_PATH, 'WEBUI.upscale_dir'))

ENV_NAME  = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH    = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')

# === Common Repo Base ===
HF_REPO_URL = 'https://huggingface.co/NagisaNao/ANXETY/resolve/main'

REPO_URL   = f"{HF_REPO_URL}/{UI}.zip"
CONFIG_URL = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"
ARIA_FLAGS = '--allow-overwrite=true --console-log-level=error --stderr=true -c -x16 -s16 -k1M -j5'

CD(HOME)


# ==================== WEBUI OPERATIONS ====================

async def _download_file(url, directory=WEBUI, filename=None):
    """Download single file"""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    file_path = directory / (filename or Path(url).name)

    if file_path.exists():
        file_path.unlink()

    process = await asyncio.create_subprocess_shell(
        f"curl -sLo {file_path} {url}",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    await process.communicate()

async def get_extensions_list():
    """Fetch list of extensions from config file"""
    ext_file_url = f"{CONFIG_URL}/{UI}/_extensions.txt"
    extensions = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ext_file_url) as response:
                if response.status == 200:
                    extensions = [
                        line.strip() for line in (await response.text()).splitlines()
                        if line.strip() and not line.startswith('#')  # Skip empty lines and comments
                    ]
    except Exception as e:
        print(f"Error fetching extensions list: {e}")

    # Add environment-specific extensions
    if ENV_NAME == 'Kaggle' and UI != 'ComfyUI':
        extensions.append('https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image')

    return extensions

# ================= CONFIGURATION HANDLING =================

# For Forge/ReForge/SD-UX - default is used: A1111
CONFIG_MAP = {
    'A1111': [
        f"{CONFIG_URL}/{UI}/config.json",
        f"{CONFIG_URL}/{UI}/ui-config.json",
        f"{CONFIG_URL}/styles.csv",
        f"{CONFIG_URL}/user.css",
        f"{CONFIG_URL}/card-no-preview.png, {WEBUI}/html",
        f"{CONFIG_URL}/notification.mp3",
        # Special Scripts
        f"{CONFIG_URL}/gradio-tunneling.py, {VENV}/lib/python3.10/site-packages/gradio_tunneling, main.py",
        f"{CONFIG_URL}/tagcomplete-tags-parser.py"
    ],
    'ComfyUI': [
        f"{CONFIG_URL}/{UI}/install-deps.py",
        f"{CONFIG_URL}/{UI}/comfy.settings.json, {WEBUI}/user/default",
        f"{CONFIG_URL}/{UI}/Comfy-Manager/config.ini, {WEBUI}/user/__manager",
        f"{CONFIG_URL}/{UI}/workflows/anxety-workflow.json, {WEBUI}/user/default/workflows",
        # Special Scripts
        f"{CONFIG_URL}/gradio-tunneling.py, {VENV}/lib/python3.10/site-packages/gradio_tunneling, main.py"
    ],
    'Classic': [
        f"{CONFIG_URL}/{UI}/config.json",
        f"{CONFIG_URL}/{UI}/ui-config.json",
        f"{CONFIG_URL}/styles.csv",
        f"{CONFIG_URL}/user.css",
        f"{CONFIG_URL}/card-no-preview.png, {WEBUI}/html, card-no-preview.jpg",
        f"{CONFIG_URL}/notification.mp3",
        # Special Scripts
        f"{CONFIG_URL}/gradio-tunneling.py, {VENV}/lib/python3.11/site-packages/gradio_tunneling, main.py",
        f"{CONFIG_URL}/tagcomplete-tags-parser.py"
    ]
}
# 🔁 Alias
CONFIG_MAP['Neo'] = CONFIG_MAP['Classic']

async def download_configuration():
    """Download all configuration files for current UI"""
    configs = CONFIG_MAP.get(UI, CONFIG_MAP['A1111'])
    await asyncio.gather(*[
        _download_file(*map(str.strip, config.split(',')))
        for config in configs
    ])

# ================= EXTENSIONS INSTALLATION ================

async def install_extensions():
    """Install all required extensions"""
    extensions = await get_extensions_list()
    EXTS.mkdir(parents=True, exist_ok=True)
    CD(EXTS)

    tasks = [
        asyncio.create_subprocess_shell(
            f"git clone --depth 1 {ext}",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) for ext in extensions
    ]
    await asyncio.gather(*tasks)

# =================== ARCHIVES HANDLING ====================

async def process_archives():
    """Download and extract embed & upscaler archives via aria2"""
    archives = [
        (f"{HF_REPO_URL}/embeds.zip", EMBED),
        (f"{HF_REPO_URL}/upscalers.zip", UPSC)
    ]

    async def download_and_extract(url, extract_to):
        archive_path = WEBUI / Path(url).name
        extract_to.mkdir(parents=True, exist_ok=True)

        # Download archive
        cmd = f"aria2c {ARIA_FLAGS} -d {WEBUI} -o '{archive_path.name}' '{url}'"
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        await process.communicate()

        # Extract and cleanup
        ipySys(f"unzip -q -o {archive_path} -d {extract_to} && rm -f {archive_path}")

    await asyncio.gather(*[
        download_and_extract(url, path) for url, path in archives
    ])

# =================== WEBUI SETUP & FIXES ==================

def unpack_webui():
    """Download and extract WebUI archive"""
    zip_path = HOME / f"{UI}.zip"
    m_download(f"{REPO_URL} {HOME} {UI}.zip")
    ipySys(f"unzip -q -o {zip_path} -d {WEBUI} && rm -rf {zip_path}")

def apply_comfyui_cleanup():
    """Remove 'SD' folder inside EMBED directory after unpack"""
    sd_dir = EMBED / 'SD'
    if sd_dir.exists() and sd_dir.is_dir():
        subprocess.run(['rm', '-rf', str(sd_dir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_tagcomplete_tag_parser():
    ipyRun('run', f"{WEBUI}/tagcomplete-tags-parser.py")

# ======================== MAIN CODE =======================

async def main():
    # Main Func
    unpack_webui()
    await asyncio.gather(
        download_configuration(),
        install_extensions(),
        process_archives()
    )

    # Special Func
    if UI == 'ComfyUI':
        apply_comfyui_cleanup()

    if UI != 'ComfyUI':
        run_tagcomplete_tag_parser()


if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(main())