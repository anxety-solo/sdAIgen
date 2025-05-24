# ~ _core.py | by ANXETY ~

from Manager import m_download, m_clone    # Every Download | Clone
import json_utils as js                    # JSON

from IPython.display import clear_output
from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import os


class Core:
    """Core class for UI installation with accessible constants"""
    
    def __init__(self, ui_name=None):
        # Initialize paths and constants
        self.HOME = Path.home()
        self.SCR_PATH = self.HOME / 'ANXETY'
        self.SETTINGS_PATH = self.SCR_PATH / 'settings.json'
        
        # Load settings from JSON
        self.ENV_NAME = js.read(self.SETTINGS_PATH, 'ENVIRONMENT.env_name')
        self.FORK_REPO = js.read(self.SETTINGS_PATH, 'ENVIRONMENT.fork')
        self.BRANCH = js.read(self.SETTINGS_PATH, 'ENVIRONMENT.branch')
        self.EXTS = js.read(self.SETTINGS_PATH, 'WEBUI.extension_dir')
        self.VENV = self.HOME / 'venv'
        
        # Set UI name if provided
        self.UI = ui_name
        if ui_name:
            self.WEBUI = self.HOME / ui_name
        
        # Shortcut functions
        self.CD = os.chdir
        self.ipySys = get_ipython().system

    async def _download_file(self, url, directory, filename):
        """Download a single file asynchronously."""
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

    async def download_files(self, file_list, base_dir=None):
        """
        Download multiple files asynchronously.
        
        Args:
            file_list: List of file entries in format "url, [directory], [filename]"
            base_dir: Default directory if not specified in file_list
        """
        if base_dir is None:
            base_dir = self.WEBUI if hasattr(self, 'WEBUI') else self.HOME
            
        tasks = []
        for file_info in file_list:
            parts = [p.strip() for p in file_info.split(',')]
            url = parts[0]
            directory = parts[1] if len(parts) > 1 else base_dir
            filename = parts[2] if len(parts) > 2 else os.path.basename(url)
            tasks.append(self._download_file(url, directory, filename))
        await asyncio.gather(*tasks)

    async def clone_extensions(self, extensions_list):
        """
        Clone multiple git repositories asynchronously.
        
        Args:
            extensions_list: List of git repositories in format "url [folder_name]"
        """
        os.makedirs(self.EXTS, exist_ok=True)
        self.CD(self.EXTS)

        tasks = []
        for command in extensions_list:
            tasks.append(asyncio.create_subprocess_shell(
                f"git clone --depth 1 {command}",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            ))

        await asyncio.gather(*tasks)

    def install_ui(self, source, mode='zip'):
        """
        Install the UI from either zip archive or git repository.
        
        Args:
            source: URL to zip archive or git repository
            mode: Installation mode ('zip' or 'git')
        """
        if not hasattr(self, 'WEBUI'):
            raise ValueError("UI name not set. Initialize Core with ui_name or set self.UI first")
            
        if mode == 'zip':
            # Zip archive installation
            zip_path = f"{self.HOME}/{self.UI}.zip"
            m_download(f"{source} {self.HOME} {self.UI}.zip")
            self.ipySys(f"unzip -q -o {zip_path} -d {self.WEBUI}")
            self.ipySys(f"rm -rf {zip_path}")
        elif mode == 'git':
            # Git repository installation
            self.ipySys(f"git clone --depth 1 {source} {self.WEBUI}")
        else:
            raise ValueError(f"Unsupported installation mode: {mode}")

    async def core_install(self, source, configs=None, extensions=None, mode='zip'):
        """
        Core installation function for any UI.
        
        Args:
            source: URL to zip archive or git repository
            configs: List of configuration files to download
            extensions: List of extensions to clone
            mode: Installation mode ('zip' or 'git')
        """
        with capture.capture_output():
            # Step 1: Install the base UI
            self.install_ui(source, mode)
            
            # Step 2: Download configurations if provided
            if configs:
                await self.download_files(configs)
            
            # Step 3: Clone extensions if provided
            if extensions:
                await self.clone_extensions(extensions)


# Create a default instance for direct constant access
core = Core()