# ~ webui-installer.py | by ANXETY ~

from Manager import m_download    # Every Download
import json_utils as js           # JSON

from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import requests
import os


osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# Auto-convert *_path env vars to Path
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, VENV, SCR_PATH, SETTINGS_PATH = (
    PATHS['home_path'], PATHS['venv_path'], PATHS['scr_path'], PATHS['settings_path']
)

UI         = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI      = HOME / UI
EXTS       = Path(js.read(SETTINGS_PATH, 'WEBUI.extension_dir'))
EMBED      = Path(js.read(SETTINGS_PATH, 'WEBUI.embed_dir'))
UPSC       = Path(js.read(SETTINGS_PATH, 'WEBUI.upscale_dir'))

ENV_NAME   = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
FORK_REPO  = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
BRANCH     = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')

CONFIG_URL = f"https://raw.githubusercontent.com/{FORK_REPO}/{BRANCH}/__configs__"

CD(HOME)


# ==================== WEBUI OPERATIONS ====================

def get_extensions_list():
    """Fetch list of extensions from config repo."""
    ext_file_url = f"{CONFIG_URL}/{UI}/_extensions.txt"
    extensions = []

    try:
        resp = requests.get(ext_file_url, timeout=10)
        if resp.status_code == 200:
            extensions = [
                line.strip()
                for line in resp.text.splitlines()
                if line.strip() and not line.startswith('#')
            ]
    except Exception as e:
        print(f"Error fetching extensions list: {e}")

    # Add environment-specific extensions
    if ENV_NAME == 'Kaggle' and UI != 'ComfyUI':
        extensions.append('https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image')

    return extensions


# ================= CONFIGURATION HANDLING =================

CONFIG_MAP = {
    'A1111': [
        f"{CONFIG_URL}/{UI}/config.json",
        f"{CONFIG_URL}/{UI}/ui-config.json",
        f"{CONFIG_URL}/styles.csv",
        f"{CONFIG_URL}/user.css",
        f"{CONFIG_URL}/card-no-preview.png, {WEBUI}/html",
        f"{CONFIG_URL}/notification.mp3",
        f"{CONFIG_URL}/gradio-tunneling.py, {VENV}/lib/python3.10/site-packages/gradio_tunneling, main.py",
        f"{CONFIG_URL}/tagcomplete-tags-parser.py"
    ],
    'ComfyUI': [
        f"{CONFIG_URL}/{UI}/install-deps.py",
        f"{CONFIG_URL}/{UI}/comfy.settings.json, {WEBUI}/user/default",
        f"{CONFIG_URL}/{UI}/Comfy-Manager/config.ini, {WEBUI}/user/default/ComfyUI-Manager",
        f"{CONFIG_URL}/{UI}/workflows/anxety-workflow.json, {WEBUI}/user/default/workflows",
        f"{CONFIG_URL}/gradio-tunneling.py, {VENV}/lib/python3.10/site-packages/gradio_tunneling, main.py"
    ],
    'Classic': [
        f"{CONFIG_URL}/{UI}/config.json",
        f"{CONFIG_URL}/{UI}/ui-config.json",
        f"{CONFIG_URL}/styles.csv",
        f"{CONFIG_URL}/user.css",
        f"{CONFIG_URL}/card-no-preview.png, {WEBUI}/html, card-no-preview.jpg",
        f"{CONFIG_URL}/notification.mp3",
        f"{CONFIG_URL}/gradio-tunneling.py, {VENV}/lib/python3.11/site-packages/gradio_tunneling, main.py",
        f"{CONFIG_URL}/tagcomplete-tags-parser.py"
    ]
}


def download_configuration():
    """Download all configuration files for current UI."""
    configs = CONFIG_MAP.get(UI, CONFIG_MAP['A1111'])
    for config in configs:
        m_download(config, log=True)


# ================= EXTENSIONS INSTALLATION ================

def install_extensions():
    """Install all required extensions."""
    extensions = get_extensions_list()
    EXTS.mkdir(parents=True, exist_ok=True)
    CD(EXTS)

    for ext in extensions:
        subprocess.run(
            f"git clone --depth 1 {ext}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


# =================== WEBUI SETUP & FIXES ==================

REPO_MAP = {
    'A1111':   'https://github.com/AUTOMATIC1111/stable-diffusion-webui',
    'ComfyUI': 'https://github.com/comfyanonymous/ComfyUI',
    'Forge':   'https://github.com/lllyasviel/stable-diffusion-webui-forge',
    'Classic': 'https://github.com/Haoming02/sd-webui-forge-classic',
    'ReForge': 'https://github.com/Panchovix/stable-diffusion-webui-reForge',
    'SD-UX':   'https://github.com/anapnoe/stable-diffusion-webui-ux'
}


def clone_webui():
    """Clone WebUI repository instead of downloading archive."""
    repo_url = REPO_MAP.get(UI)
    process = subprocess.run(
        f"git clone --depth 1 {repo_url} {WEBUI}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    if process.returncode != 0:
        raise RuntimeError(f"Failed to clone {UI} repository")


def apply_classic_fixes():
    """Apply specific fixes for Classic UI."""
    if UI != 'Classic':
        return

    cmd_args_path = WEBUI / 'modules/cmd_args.py'
    if not cmd_args_path.exists():
        return

    marker = '# === Arguments added by ANXETY ==='
    with cmd_args_path.open('r+', encoding='utf-8') as f:
        content = f.read()
        if marker in content:
            return
        f.write(f"\n\n{marker}\n")
        f.write('parser.add_argument("--hypernetwork-dir", type=normalized_filepath, '
                'default=os.path.join(models_path, \'hypernetworks\'), '
                'help="hypernetwork directory")')


def run_tagcomplete_tag_parser():
    if (WEBUI / "tagcomplete-tags-parser.py").exists():
        ipyRun('run', f"{WEBUI}/tagcomplete-tags-parser.py")


# =================== ARCHIVES HANDLING ====================

def process_archives():
    """Download and extract embeds & upscalers archives."""
    archives = [
        f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/embeds.zip, {EMBED}",
        f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/upscalers.zip, {UPSC}"
    ]
    for archive in archives:
        m_download(archive, log=True, unzip=True)


# ======================== MAIN CODE =======================

def main():
    clone_webui()
    download_configuration()
    install_extensions()
    process_archives()

    # if UI == 'Classic':
    #     apply_classic_fixes()

    if UI != 'ComfyUI':
        run_tagcomplete_tag_parser()


if __name__ == '__main__':
    with capture.capture_output():
        main()