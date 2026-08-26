""" Runtime Constants: Paths, GDrive & HF Endpoints | by ANXETY """

import os

from pathlib import Path


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


# ~~ GOOGLE DRIVE ~~

GD_BASE    = Path('/content/drive/MyDrive/sdAIgen')
GD_FILES   = GD_BASE / 'files'
GD_OUTPUTS = GD_BASE / 'outputs'
GD_CONFIGS = GD_BASE / 'configs'


# ~~ REMOTE SOURCES ~~

HUGGINGFACE_BASE = 'https://huggingface.co'

HF_REPO_NAME = 'NagisaNao/ANXETY'
HF_REPO_URL  = f"{HUGGINGFACE_BASE}/{HF_REPO_NAME}/resolve/main"


# ~~ TEXT COLORS ~~

class COL:
    R  =  '\033[31m'    # Red
    G  =  '\033[32m'    # Green
    Y  =  '\033[33m'    # Yellow
    B  =  '\033[34m'    # Blue
    P  =  '\033[35m'    # Purple
    C  =  '\033[36m'    # Cyan
    cB =  '\033[36;1m'  # Cyan + BOLD
    X  =  '\033[0m'     # Reset
