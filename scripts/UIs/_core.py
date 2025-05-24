# ~ _core.py | by ANXETY ~

from Manager import m_download, m_clone    # Every Download | Clone
import json_utils as js                    # JSON

from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import os

# Global constants (can be imported directly)
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

# Read settings once when module loads
try:
    ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
    FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
    BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
    EXTS = js.read(SETTINGS_PATH, 'WEBUI.extension_dir')
except:
    ENV_NAME = FORK_REPO = BRANCH = EXTS = None

# Utilities (can be used directly)
CD = os.chdir
ipySys = get_ipython().system

async def download_file(url, directory, filename=None):
    """Simple file download"""
    filename = filename or os.path.basename(url)
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

async def git_clone(repo_url, target_dir=None, depth=1):
    """Clone repository"""
    target_dir = target_dir or EXTS
    os.makedirs(target_dir, exist_ok=True)

    process = await asyncio.create_subprocess_shell(
        f"git clone --depth {depth} {repo_url}",
        cwd=target_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    await process.communicate()

def install_zip(url, extract_to):
    """Install from zip archive"""
    zip_name = os.path.basename(url)
    zip_path = f"{HOME}/{zip_name}"

    m_download(f"{url} {HOME} {zip_name}")
    ipySys(f"unzip -q -o {zip_path} -d {extract_to}")
    ipySys(f"rm -rf {zip_path}")