# ~ Classic.py | by ANXETY ~

from _core import *
from IPython.utils import capture
import asyncio

# Configuration
UI = 'Classic'
REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
WEBUI = HOME / UI

CONFIGS = [
    # Settings
    f"{UI}/config.json",
    f"{UI}/ui-config.json",
    "styles.csv",
    "user.css",
    # Other files
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
    # 'https://github.com/ilian6806/stable-diffusion-webui-state State',
    # 'https://github.com/DominikDoom/a1111-sd-webui-tagcomplete TagComplete',
    # 'https://github.com/Tsukreya/Umi-AI-Wildcards'
]

def fix_cmd_args(webui_path):
    """Apply specific fixes for Classic UI modules"""
    path = webui_path / "modules/cmd_args.py"
    if not path.exists():
        return

    marker = '# Arguments added by ANXETY'
    with open(path, 'r+', encoding='utf-8') as f:
        if marker in f.read():
            return

        f.write(f"\n\n{marker}\n")
        f.write('parser.add_argument("--hypernetwork-dir", type=normalized_filepath, '
               'default=os.path.join(models_path, \'hypernetworks\'), help="hypernetwork directory")')

async def install_classic():
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

    # Apply Classic-specific fixes
    fix_cmd_args(WEBUI)

if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(install_classic())