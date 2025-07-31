# ~ webui-installer.py | by ANXETY ~

from Manager import m_download   # Every Download
import json_utils as js          # JSON

from IPython.display import clear_output
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

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
VENV = PATHS['venv_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = HOME / UI
EXTS = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir'))
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
CONFIG_URL = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"

CD(HOME)


# ==================== WEBUI OPERATIONS ====================

async def _download_file(url, directory=WEBUI, filename=None):
    """Download single file."""
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
    """Fetch list of extensions from config file."""
    ext_file_url = f"{CONFIG_URL}/{UI}/_extensions.txt"
    extensions = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ext_file_url) as response:
                if response.status == 200:
                    extensions = [
                        line.strip() for line in (await response.text()).splitlines()
                        if line.strip() and not line.startswith('#')    # Skip empty lines and comments
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
        f"{CONFIG_URL}/{UI}/Comfy-Manager/config.ini, {WEBUI}/user/default/ComfyUI-Manager",
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

async def download_configuration():
    """Download all configuration files for current UI"""
    configs = CONFIG_MAP.get(UI, CONFIG_MAP['A1111'])
    await asyncio.gather(*[
        _download_file(*map(str.strip, config.split(',')))
        for config in configs
    ])

# ================= EXTENSIONS INSTALLATION ================

async def install_extensions():
    """Install all required extensions."""
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


# =================== WEBUI SETUP & FIXES ==================

def unpack_webui():
    """Download and extract WebUI archive."""
    zip_path = HOME / f"{UI}.zip"
    m_download(f"{REPO_URL} {HOME} {UI}.zip")
    ipySys(f"unzip -q -o {zip_path} -d {WEBUI} && rm -rf {zip_path}")

def apply_classic_fixes():
    """Apply specific fixes for Classic UI."""
    cmd_args_path = WEBUI / 'modules/cmd_args.py'
    if not cmd_args_path.exists():
        return

    marker = '# Arguments added by ANXETY'
    with cmd_args_path.open('r+', encoding='utf-8') as f:
        if marker in f.read():
            return
        f.write(f"\n\n{marker}\n")
        f.write('parser.add_argument("--hypernetwork-dir", type=normalized_filepath, '
               'default=os.path.join(models_path, \'hypernetworks\'), help="hypernetwork directory")')

def run_tagcomplete_tag_parser():
    ipyRun('run', f"{WEBUI}/tagcomplete-tags-parser.py")


# ======================== MAIN CODE =======================

async def main():
    # Main Func
    unpack_webui()
    await download_configuration()
    await install_extensions()

    # Special Func
    if UI == 'Classic':
        apply_classic_fixes()

    if UI != 'ComfyUI':
        run_tagcomplete_tag_parser()


if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(main())