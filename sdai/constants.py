""" Constants Module | by ANXETY """

from pathlib import Path
import os

osENV = os.environ
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}


# ~~ RUNTIME PATHS ~~
HOME_PATH     = PATHS['home_path']
PROJECT_PATH  = PATHS['project_path']
SETTINGS_PATH = PATHS['settings_path']
VENV_PATH     = PATHS['venv_path']

SCRIPTS_PATH = PROJECT_PATH / 'scripts'
ASSETS_PATH  = PROJECT_PATH / 'assets'

CSS_DIR_PATH = ASSETS_PATH / 'css'
JS_DIR_PATH  = ASSETS_PATH / 'js'


# ~~ REMOTE SOURCES ~~
GITHUB_BASE      = 'https://github.com'
GITHUB_RAW       = 'https://raw.githubusercontent.com'
GITHUB_API       = 'https://api.github.com'
HUGGINGFACE_BASE = 'https://huggingface.co'

CIVITAI_API      = 'https://civitai.com/api/v1'
CIVITAI_BASE     = 'https://civitai.red'
CIVITAI_DL       = f"{CIVITAI_BASE}/api/download/models"

HF_REPO_NAME     = 'NagisaNao/ANXETY'
HF_REPO_URL      = f"{HUGGINGFACE_BASE}/{HF_REPO_NAME}/resolve/main"


# ~~ Text Colors (\033) ~~
class COLORS:
    R  =  '\033[31m'    # Red
    G  =  '\033[32m'    # Green
    Y  =  '\033[33m'    # Yellow
    B  =  '\033[34m'    # Blue
    P  =  '\033[35m'    # Purple
    C  =  '\033[36m'    # Cyan
    lB =  '\033[36;1m'  # lightBlue + BOLD
    X  =  '\033[0m'     # Reset

COL = COLORS
