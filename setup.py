""" Setup sdAIgen Project Manager | by ANXETY """

import nest_asyncio
import importlib
import argparse
import aiohttp
import asyncio
import shutil
import time
import json
import sys
import os

from IPython.display import clear_output
from pathlib import Path
from tqdm import tqdm


nest_asyncio.apply()


# Remove Colab sample_data
sample_path = Path('/content/sample_data')
if sample_path.exists() and sample_path.is_dir():
    shutil.rmtree(sample_path)


# ~~ RUNTIME PATHS ~~

HOME_PATH     = Path.home()
PROJECT_PATH  = HOME_PATH / 'SDAIGEN'
SETTINGS_PATH = PROJECT_PATH / 'settings.json'
VENV_PATH     = HOME_PATH / 'venv'

SCRIPTS_PATH = PROJECT_PATH / 'scripts'
ASSETS_PATH  = PROJECT_PATH / 'assets'

os.environ.update({
    'home_path':     str(HOME_PATH),
    'project_path':  str(PROJECT_PATH),
    'settings_path': str(SETTINGS_PATH),
    'venv_path':     str(VENV_PATH),
})


# ~~ ENVIRONMENTS ~~

SUPPORTED_ENVIRONMENTS = {
    'COLAB_GPU': ('Google Colab', '/content'),
    'KAGGLE_URL_BASE': ('Kaggle', '/kaggle/working'),
}


# ~~ SOURCE FILES ~~

SOURCE_FILES = {
    'assets/css': [
        'auto-cleaner.css',
        'download-result.css',
        'main-widgets.css',
    ],
    'assets/js': ['main-widgets.js'],
    'sdai': [
        'constants.py',
        'factory.py',
        'models.py',
        'season.py',
        'webui_meta.py',
    ],
    'sdai/api': ['civitai.py'],
    'sdai/services': ['manager.py', 'tunnel_hub.py'],
    'sdai/translations': ['__init__.py', 'en.json', 'ru.json'],
    'sdai/utils': ['json.py', 'logger.py', 'webui.py'],
    'scripts': [
        '00-startup.py',
        'auto_cleaner.py',
        'download_result.py',
        'downloading.py',
        'launch.py',
        'webui_installer.py',
        'widgets.py',
    ],
}


# ~~ ENVIRONMENT DETECTION ~~

def detect_environment(force_env: str | None = None) -> tuple[str, str]:
    """Detect the runtime environment, optionally forcing one by name"""
    envs = {name for name, _ in SUPPORTED_ENVIRONMENTS.values()}
    if force_env:
        if force_env not in envs:
            raise EnvironmentError(
                f"Unsupported forced environment: {force_env}.\n"
                f"Supported: {', '.join(sorted(envs))}"
            )
        return force_env, ''

    for variable, (name, work_path) in SUPPORTED_ENVIRONMENTS.items():
        if variable in os.environ:
            return name, work_path

    raise EnvironmentError(f"Unsupported environment. Supported: {', '.join(sorted(envs))}")


def parse_github(value: str) -> str:
    """Normalize a GitHub fork value into user/repo format"""
    parts = value.split('/', 1)
    user  = parts[0]
    repo  = parts[1] if len(parts) > 1 else 'sdAIgen'

    if not (user or repo):
        raise ValueError('Invalid fork format. Expected user OR user/repo')

    return f"{user}/{repo}"


# ~~ SETTINGS ~~

def _check_install_deps() -> bool:
    """Check that required CLI tools (aria2c, gdown) are available"""
    return all(shutil.which(tool) for tool in ('aria2c', 'gdown'))


def _get_start_timer() -> int:
    """Return the saved start timer or the current time"""
    current_time = int(time.time() - 5)
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
        return settings.get('ENVIRONMENT', {}).get('start_timer', current_time)

    return current_time


def save_env_settings(data: dict):
    """Merge settings into the project settings.json file"""
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)

    existing = {}
    if SETTINGS_PATH.exists():
        try:
            existing = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            existing = {}

    existing.update(data)

    SETTINGS_PATH.write_text(
        json.dumps(existing, indent=4, ensure_ascii=False),
        encoding='utf-8',
    )


def create_env_settings(env_name: str, home_work_path: str, github: str, branch: str, lang: str) -> dict:
    """Build the environment settings dict for the current session"""
    return {
        'ENVIRONMENT': {
            'env_name':       env_name,
            'home_work_path': home_work_path,
            'install_deps':   _check_install_deps(),
            'github':         github,
            'branch':         branch,
            'lang':           lang,
            'home_path':      str(HOME_PATH),
            'project_path':   str(PROJECT_PATH),
            'settings_path':  str(SETTINGS_PATH),
            'venv_path':      str(VENV_PATH),
            'start_timer':    _get_start_timer(),
            'public_ip':      '',
        }
    }


# ~~ DOWNLOAD ~~

def _build_download_list(github: str, branch: str) -> list[tuple[str, Path]]:
    """Build (url, dest_path) pairs for all project source files"""
    base_url = f"https://raw.githubusercontent.com/{github}/{branch}"

    return [
        (f"{base_url}/{folder}/{file}", PROJECT_PATH / folder / file)
        for folder, files in SOURCE_FILES.items()
        for file in files
    ]


async def _download_file(session: aiohttp.ClientSession, url: str, path: Path) -> tuple[bool, str, Path, str | None]:
    """Download a single file, returning success status with error info"""
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(await resp.read())
            return True, url, path, None
    except aiohttp.ClientResponseError as exc:
        return False, url, path, f"HTTP error {exc.status}: {exc.message}"
    except Exception as exc:
        return False, url, path, f"Error: {exc}"


async def download_files_async(github: str, branch: str, log: bool):
    """Download all project files concurrently and optionally log errors"""
    files  = _build_download_list(github, branch)
    errors = []

    async with aiohttp.ClientSession() as session:
        tasks = [_download_file(session, url, path) for url, path in files]

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='Downloading scripts', unit='file'):
            success, url, path, error = await future
            if not success:
                errors.append((url, path, error))

    clear_output()

    if log and errors:
        print('\nErrors occurred during download:')
        for url, path, error in errors:
            print(f"URL: {url}\nPath: {path}\nError: {error}\n")


# ~~ STARTUP RECOVERY ~~

def install_startup():
    """Install IPython auto-recovery script (runs on every kernel start)"""
    source = SCRIPTS_PATH / '00-startup.py'
    if not source.exists():
        return

    startup_dir = HOME_PATH / '.ipython' / 'profile_default' / 'startup'
    startup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, startup_dir / '00-startup.py')


# ~~ IMPORTS ~~

def setup_imports():
    """Make the project package (sdai) importable and drop cached modules from previous runs"""
    path_str = str(PROJECT_PATH)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

    for name, module in list(sys.modules.items()):
        module_path = getattr(module, '__file__', None)
        if not module_path:
            continue

        try:
            if PROJECT_PATH in Path(module_path).resolve().parents:
                del sys.modules[name]
        except (ValueError, RuntimeError):
            continue

    importlib.invalidate_caches()


# ~~ ARGUMENTS ~~

def parse_arguments() -> argparse.Namespace:
    """Parse and return the CLI arguments for the setup manager"""
    envs = ', '.join(sorted(name for name, _ in SUPPORTED_ENVIRONMENTS.values()))

    parser = argparse.ArgumentParser(description='sdAIgen Setup Manager')

    parser.add_argument('--github', required=True, help='Specify GitHub fork (user OR user/repo)')
    parser.add_argument('--branch', required=True, help='Specify branch name of the fork')
    parser.add_argument('--lang',   required=True, help='Specify interface language')
    parser.add_argument('-s', '--skip-download', action='store_true', help='Skip file download')
    parser.add_argument('-f', '--force-env', default=None, help=f"Force emulated environment (Supported: {envs})")
    parser.add_argument('-l', '--log', action='store_true', help='Enable logging of download errors')

    return parser.parse_args()


# ~~ MAIN ~~

async def main():
    args = parse_arguments()

    env_name, home_work_path = detect_environment(args.force_env)

    github = parse_github(args.github)
    branch = args.branch
    lang   = args.lang

    save_env_settings(
        create_env_settings(
            env_name,
            home_work_path,
            github,
            branch,
            lang,
        ),
    )

    if not args.skip_download:
        await download_files_async(github, branch, args.log)

    install_startup()

    # Reset sdai modules
    setup_imports()

    # Display info after full setup
    from sdai.season import display_info
    display_info(
        env_name=env_name,
        project_path=PROJECT_PATH,
        github=github,
        branch=branch,
        lang=lang,
    )


if __name__ == '__main__':
    asyncio.run(main())
