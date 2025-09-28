# ~ setup.py | by ANXETY ~

from typing import Dict, List, Tuple, Optional
from IPython.display import clear_output
from pathlib import Path
from tqdm import tqdm
import nest_asyncio
import importlib
import argparse
import aiohttp
import asyncio
import time
import json
import sys
import os


nest_asyncio.apply()  # Async support for Jupyter


# ======================== CONSTANTS =======================

HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'
VENV_PATH = HOME / 'venv'
MODULES_FOLDER = SCR_PATH / 'modules'

# Add paths to the environment
os.environ.update({
    'home_path': str(HOME),
    'scr_path': str(SCR_PATH),
    'venv_path': str(VENV_PATH),
    'settings_path': str(SETTINGS_PATH)
})

# GitHub configuration
DEFAULT_USER = 'anxety-solo'
DEFAULT_REPO = 'sdAIgen'
DEFAULT_BRANCH = 'main'
DEFAULT_LANG = 'en'
BASE_GITHUB_URL = 'https://raw.githubusercontent.com'

# Environment detection
SUPPORTED_ENVS = {
    'COLAB_GPU': ('Google Colab', '/content'),
    'KAGGLE_URL_BASE': ('Kaggle', '/kaggle/working')
}

# File structure configuration
FILE_STRUCTURE = {
    'CSS': ['main-widgets.css', 'download-result.css', 'auto-cleaner.css'],
    'JS': ['main-widgets.js'],
    'modules': [
        'json_utils.py', 'webui_utils.py', 'widget_factory.py',
        'CivitaiAPI.py', 'Manager.py', 'TunnelHub.py', '_season.py'
    ],
    'scripts': {
        '{lang}': ['widgets-{lang}.py', 'downloading-{lang}.py'],
        '': [
            'webui-installer.py', 'launch.py', 'download-result.py', 'auto-cleaner.py',
            '_models-data.py', '_xl-models-data.py'
        ]
    }
}


# =================== UTILITY FUNCTIONS ====================

def _install_deps() -> bool:
    """Check if all required dependencies are installed (aria2 and gdown)."""
    try:
        from shutil import which
        required_tools = ['aria2c', 'gdown']
        return all(which(tool) != None for tool in required_tools)
    except ImportError:
        return False

def _get_start_timer() -> int:
    """Get start timer from settings or return current time minus 5 seconds."""
    try:
        if SETTINGS_PATH.exists():
            settings = json.loads(SETTINGS_PATH.read_text())
            return settings.get('ENVIRONMENT', {}).get('start_timer', int(time.time() - 5))
    except (json.JSONDecodeError, OSError):
        pass
    return int(time.time() - 5)

def save_env_to_json(data: dict, filepath: Path) -> None:
    """Save environment data to JSON file, merging with existing content."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data if file exists
    existing_data = {}
    if filepath.exists():
        try:
            existing_data = json.loads(filepath.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    # Merge new data with existing
    merged_data = {**existing_data, **data}
    filepath.write_text(json.dumps(merged_data, indent=4))


# =================== MODULE MANAGEMENT ====================

def _clear_module_cache(modules_folder=None):
    """Clear module cache for modules in specified folder or default modules folder."""
    target_folder = Path(modules_folder) if modules_folder else MODULES_FOLDER
    target_folder = target_folder.resolve()  # Full absolute path

    for module_name, module in list(sys.modules.items()):
        if hasattr(module, '__file__') and module.__file__:
            module_path = Path(module.__file__).resolve()
            try:
                if target_folder in module_path.parents:
                    del sys.modules[module_name]
            except (ValueError, RuntimeError):
                continue

    importlib.invalidate_caches()

def setup_module_folder(modules_folder=None):
    """Set up module folder by clearing cache and adding to sys.path."""
    target_folder = Path(modules_folder) if modules_folder else MODULES_FOLDER
    target_folder.mkdir(parents=True, exist_ok=True)

    _clear_module_cache(target_folder)

    folder_str = str(target_folder)
    if folder_str not in sys.path:
        sys.path.insert(0, folder_str)


# =================== ENVIRONMENT SETUP ====================

def detect_environment(force_env=None):
    """Detect runtime environment, optionally forcing an emulated environment."""
    envs = [env_info[0] for env_info in SUPPORTED_ENVS.values()]

    if force_env:
        if force_env not in envs:
            raise EnvironmentError(f"Unsupported forced environment: {force_env}. Supported: {', '.join(envs)}")
        os.environ['home_work_path'] = ''
        return force_env

    for var, env_info in SUPPORTED_ENVS.items():
        if var in os.environ:
            # Set home_work_path for detected environment
            name, work_path = env_info
            os.environ['home_work_path'] = work_path
            return name

    raise EnvironmentError(f"Unsupported environment. Supported: {', '.join(envs)}")

def parse_fork_arg(fork_arg):
    """Parse fork argument into user/repo."""
    if not fork_arg:
        return DEFAULT_USER, DEFAULT_REPO
    parts = fork_arg.split('/', 1)
    return parts[0], (parts[1] if len(parts) > 1 else DEFAULT_REPO)

def create_environment_data(env, lang, fork_user, fork_repo, branch):
    """Create environment data dictionary."""
    install_deps = _install_deps()
    start_timer = _get_start_timer()

    return {
        'ENVIRONMENT': {
            'home_work_path': os.environ['home_work_path'],
            'env_name': env,
            'install_deps': install_deps,
            'fork': f"{fork_user}/{fork_repo}",
            'branch': branch,
            'lang': lang,
            'home_path': os.environ['home_path'],
            'scr_path': os.environ['scr_path'],
            'venv_path': os.environ['venv_path'],
            'settings_path': os.environ['settings_path'],
            'start_timer': start_timer,
            'public_ip': ''
        }
    }


# ===================== DOWNLOAD LOGIC =====================

def _format_lang_path(path: str, lang: str) -> str:
    """Format path with language placeholder."""
    return path.format(lang=lang) if '{lang}' in path else path

def generate_file_list(structure: Dict, base_url: str, lang: str) -> List[Tuple[str, Path]]:
    """Generate flat list of (url, path) from nested structure."""
    def walk(struct: Dict, path_parts: List[str]) -> List[Tuple[str, Path]]:
        items = []
        for key, value in struct.items():
            # Handle language-specific paths
            current_key = _format_lang_path(key, lang)
            current_path = [*path_parts, current_key] if current_key else path_parts

            if isinstance(value, dict):
                items.extend(walk(value, current_path))
            else:
                url_path = '/'.join(current_path)
                for file in value:
                    # Handle language-specific files
                    formatted_file = _format_lang_path(file, lang)
                    url = f"{base_url}/{url_path}/{formatted_file}" if url_path else f"{base_url}/{formatted_file}"
                    file_path = SCR_PATH / '/'.join(current_path) / formatted_file
                    items.append((url, file_path))
        return items

    return walk(structure, [])

async def download_file(session: aiohttp.ClientSession, url: str, path: Path) -> Tuple[bool, str, Path, Optional[str]]:
    """Download and save single file with error handling."""
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(await resp.read())
            return (True, url, path, None)
    except aiohttp.ClientResponseError as e:
        return (False, url, path, f"HTTP error {e.status}: {e.message}")
    except Exception as e:
        return (False, url, path, f"Error: {str(e)}")

async def download_files_async(lang, fork_user, fork_repo, branch, log_errors):
    """Main download executor with error logging."""
    base_url = f"{BASE_GITHUB_URL}/{fork_user}/{fork_repo}/{branch}"
    file_list = generate_file_list(FILE_STRUCTURE, base_url, lang)

    async with aiohttp.ClientSession() as session:
        tasks = [download_file(session, url, path) for url, path in file_list]
        errors = []

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='Downloading files', unit='file'):
            success, url, path, error = await future
            if not success:
                errors.append((url, path, error))

        clear_output()

        if log_errors and errors:
            print('\nErrors occurred during download:')
            for url, path, error in errors:
                print(f"URL: {url}\nPath: {path}\nError: {error}\n")


# ===================== MAIN EXECUTION =====================

async def main_async(args=None):
    """Entry point."""
    parser = argparse.ArgumentParser(description='ANXETY Download Manager')
    parser.add_argument('--lang', default=DEFAULT_LANG, help=f"Language to be used (default: {DEFAULT_LANG})")
    parser.add_argument('--branch', default=DEFAULT_BRANCH, help=f"Branch to download files from (default: {DEFAULT_BRANCH})")
    parser.add_argument('--fork', default=None, help='Specify project fork (user or user/repo)')
    parser.add_argument('-s', '--skip-download', action='store_true', help='Skip downloading files')
    parser.add_argument('-l', '--log', action='store_true', help='Enable logging of download errors')
    parser.add_argument('-e', '--force-env', default=None, help=f"Force emulated environment (only supported: {', '.join([env_info[0] for env_info in SUPPORTED_ENVS.values()])})")

    args, _ = parser.parse_known_args(args)

    env = detect_environment(force_env=args.force_env)
    user, repo = parse_fork_arg(args.fork)  # GitHub: user/repo

    # Download scripts files
    if not args.skip_download:
        await download_files_async(args.lang, user, repo, args.branch, args.log)

    setup_module_folder()
    env_data = create_environment_data(env, args.lang, user, repo, args.branch)
    save_env_to_json(env_data, SETTINGS_PATH)

    # Display info after setup
    from _season import display_info
    display_info(
        env=env,
        scr_folder=os.environ['scr_path'],
        branch=args.branch,
        lang=args.lang,
        fork=args.fork
    )


if __name__ == '__main__':
    asyncio.run(main_async())