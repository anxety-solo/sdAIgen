# ~ _core.py | by ANXETY ~

from Manager import m_download, m_clone    # Every Download | Clone
import json_utils as js                    # JSON

from typing import Optional, Callable, List
from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import os


CD = os.chdir
ipySys = get_ipython().system

# Constants
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'


class UICore:
    """Core class for UI installation and management"""

    def __init__(self, ui_name: str, url: str, git: bool = False):
        """
        Initialize UI Core

        ui_name: Name for UI directory
        url: Source URL for installation
        git: Use git clone instead of zip archive
        """
        # Load settings
        self.FORK_REPO = js.read(SETTINGS_PATH, 'ENVIRONMENT.fork')
        self.BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
        self.EXTS = js.read(SETTINGS_PATH, 'WEBUI.extension_dir')
        self.ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
        self.VENV = js.read(SETTINGS_PATH, 'ENVIRONMENT.venv_path')

        # UI configuration
        self.UI = ui_name
        self.WEBUI = HOME / ui_name
        self.source_url = url
        self.use_git = git

    async def _download_file(self, url: str, directory: str, filename: str) -> None:
        """Download single file asynchronously"""
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

    async def download_files(self, file_list: List[str]) -> None:
        """Batch download files with path customization"""
        tasks = []
        for file_info in file_list:
            parts = file_info.split(',')
            url = parts[0].strip()
            directory = parts[1].strip() if len(parts) > 1 else str(self.WEBUI)
            filename = parts[2].strip() if len(parts) > 2 else os.path.basename(url)
            tasks.append(self._download_file(url, directory, filename))
        await asyncio.gather(*tasks)

    async def clone_extensions(self, extensions_list: List[str], recursive: bool) -> None:
        """Clone extensions with optional submodules"""
        os.makedirs(self.EXTS, exist_ok=True)
        CD(self.EXTS)

        tasks = []
        for repo in extensions_list:
            cmd = f"git clone --depth 1 {'--recursive ' if recursive else ''}{repo}"
            tasks.append(asyncio.create_subprocess_shell(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            ))

        await asyncio.gather(*tasks)

    def unpack_webui(self) -> None:
        """Install base UI using specified method"""
        if self.use_git:
            CD(HOME)
            ipySys(f"git clone {self.source_url} {self.UI}")
        else:
            zip_name = os.path.basename(self.source_url)
            zip_path = f"{HOME}/{zip_name}"
            m_download(f"{self.source_url} {HOME} {zip_name}")
            ipySys(f"unzip -q -o {zip_path} -d {self.WEBUI}")
            ipySys(f"rm -rf {zip_path}")


def install_ui(
    core: UICore,
    config_files: Optional[List[str]] = None,
    extensions_list: Optional[List[str]] = None,
    recursive_extensions: bool = True,
    post_install: Optional[Callable[[UICore], None]] = None
) -> None:
    """
    Complete installation workflow

    core: Initialized UICore instance
    config_files: List of config files in 'URL,path,filename' format
    extensions_list: List of git repositories to clone
    recursive_extensions: Clone repositories with submodules
    post_install: Function to execute after installation
    """
    with capture.capture_output():
        # Base installation
        core.unpack_webui()

        # Configuration files
        if config_files:
            asyncio.run(core.download_files(config_files))

        # Extensions
        if extensions_list:
            asyncio.run(core.clone_extensions(extensions_list, recursive_extensions))

        # Post-install actions
        if post_install:
            post_install(core)