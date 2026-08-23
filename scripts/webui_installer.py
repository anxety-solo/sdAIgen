""" WebUI Installer | by ANXETY """

import subprocess
import requests
import asyncio
import sys

from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path

# === SDAIGEN ===
from sdai.webui_meta import meta, build_urls, build_config_urls, build_extensions_url
from sdai.constants import HOME_PATH, SETTINGS_PATH
from sdai.services.manager import download, clone
from sdai.utils.json import read


ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic


CLONE_UI = read(SETTINGS_PATH, 'WIDGETS.clone_ui', False)
UI_NAME  = read(SETTINGS_PATH, 'WEBUI.current')
ENV_NAME = read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
GITHUB   = read(SETTINGS_PATH, 'ENVIRONMENT.github')
BRANCH   = read(SETTINGS_PATH, 'ENVIRONMENT.branch')

WEBUI_PATH = Path(read(SETTINGS_PATH, 'WEBUI.webui_path'))
EXTS_DIR   = Path(read(SETTINGS_PATH, 'WEBUI.extension_dir'))
EMBED_DIR  = Path(read(SETTINGS_PATH, 'WEBUI.embed_dir'))
UPSC_DIR   = Path(read(SETTINGS_PATH, 'WEBUI.upscale_dir'))


# ~~ PARSE CLI ARGUMENTS ~~
SKIP_INSTALLING_UI = '-s' in sys.argv or '--skip-installing-ui' in sys.argv


# ~~ CONFIGURATION ~~

def get_extensions_list() -> list[str]:
    """Fetch the list of extensions from the config file"""
    try:
        resp = requests.get(build_extensions_url(UI_NAME, GITHUB, BRANCH), timeout=30)
        resp.raise_for_status()
        extensions = [
            line.strip() for line in resp.text.splitlines()
            if line.strip() and not line.startswith('#')
        ]
    except Exception as exc:
        print(f"Error fetching extensions list: {exc}")
        extensions = []

    # Environment-specific extensions
    if ENV_NAME == 'Kaggle':
        extensions.append(
            'https://github.com/anxety-solo/sd-encrypt-image Encrypt-Image'
            if UI_NAME != 'ComfyUI'
            else 'https://github.com/anxety-solo/comfyui-encrypt-image'
        )

    return extensions


async def download_configuration():
    """Download all configuration files for the current UI"""
    await asyncio.gather(*[
        _download_file(url, dest)
        for url, dest in build_config_urls(UI_NAME, GITHUB, BRANCH)
    ])


async def _download_file(url: str, dest: Path):
    """Download a single config file into its absolute destination path"""
    dest.parent.mkdir(parents=True, exist_ok=True)

    process = await asyncio.create_subprocess_shell(
        f"curl -sLo {dest} {url}",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    await process.communicate()


# ~~ EXTENSIONS ~~

async def install_extensions():
    """Install all required extensions"""
    EXTS_DIR.mkdir(parents=True, exist_ok=True)

    extensions = [ext.partition(' ') for ext in await asyncio.to_thread(get_extensions_list)]
    await asyncio.gather(*[
        asyncio.to_thread(clone, f"{url} {EXTS_DIR} {name}".rstrip())
        for url, _, name in extensions
    ])


# ~~ ARCHIVES ~~

async def process_archives():
    """Download and extract embed & upscaler archives"""
    await asyncio.gather(*[
        asyncio.to_thread(_download_archive, url, dest)
        for url, dest in (
            (build_urls(UI_NAME)['embeds'], EMBED_DIR),
            (build_urls(UI_NAME)['upscalers'], UPSC_DIR),
        )
    ])


def _download_archive(url: str, dest: Path):
    """Download an archive into WEBUI and extract it into the target directory"""
    archive = WEBUI_PATH / Path(url).name
    dest.mkdir(parents=True, exist_ok=True)

    download(f"{url} {WEBUI_PATH} {archive.name}")
    ipySys(f"unzip -q -o {archive} -d {dest} && rm -f {archive}")


# ~~ WEBUI SETUP & FIXES ~~

def unpack_webui():
    """Download and extract the WebUI archive"""
    download(f"{build_urls(UI_NAME)['webui']} {HOME_PATH} {UI_NAME}.zip", unzip=True)


def clone_webui():
    """Clone the WebUI repository from GitHub (with the meta branch)"""
    _m = meta(UI_NAME)
    clone(f"{_m['github_url']} {HOME_PATH} {UI_NAME}", branch=_m['branch'])


def run_tagcomplete_tag_parser():
    ipyRun('run', str(WEBUI_PATH / 'tagcomplete-tags-parser.py'))


# ~~ MAIN ~~

async def main():
    if not SKIP_INSTALLING_UI:
        clone_webui() if CLONE_UI else unpack_webui()

    await asyncio.gather(
        download_configuration(),
        install_extensions(),
        process_archives(),
    )

    if UI_NAME != 'ComfyUI':
        run_tagcomplete_tag_parser()


if __name__ == '__main__':
    with capture.capture_output():
        asyncio.run(main())
