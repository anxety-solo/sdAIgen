# ~ A1111.py | by ANXETY ~

from json_utils import read_json, update_json   # JSON (main)

from IPython.display import clear_output
from IPython.utils import capture
from pathlib import Path
import os

# Constants
UI = 'A1111'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
BRANCH = read_json(SETTINGS_PATH, 'ENVIRONMENT.branch')
EXTS = read_json(SETTINGS_PATH, 'WEBUI.extension_dir')

os.chdir(HOME)

# ==================== WEB UI OPERATIONS ====================

def _download_file(url, directory, filename):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    command = f"curl -sLo {file_path} {url}"
    os.system(command)

def download_files(file_list):
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory = parts[1].strip() if len(parts) > 1 else WEBUI   # Default Save Path
        filename = parts[2].strip() if len(parts) > 2 else os.path.basename(url)
        _download_file(url, directory, filename)

def download_configuration():
    ## FILES
    url_af = f'https://raw.githubusercontent.com/anxety-solo/sdAIgen/refs/heads/{BRANCH}/__configs__/'
    configs = [
        f'{url_af}/{UI}/config.json',
        f'{url_af}/{UI}/ui-config.json',
        f'{url_af}/styles.csv',
        f'{url_af}/user.css',
    ]
    download_files(configs)

    ## REPOS
    extensions_list = [
        "git clone https://github.com/anxety-solo/webui_timer timer"
    ]
    os.chdir(EXTS)

    for command in extensions_list:
        os.system(command)

def unpack_webui():
    with capture.capture_output():
        zip_path = f"{SCR_PATH}/{UI}.zip"
        get_ipython().system(f'aria2c --console-log-level=error -c -x 16 -s 16 -k 1M {REPO_URL} -d {SCR_PATH} -o {UI}.zip')
        get_ipython().system(f'unzip -q -o {zip_path} -d {WEBUI}')
        get_ipython().system(f'rm -rf {zip_path}')

# ==================== MAIN CODE ====================

if __name__ == "__main__":
    unpack_webui()
    download_configuration()