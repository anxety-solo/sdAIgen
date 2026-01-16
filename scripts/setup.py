# ~ setup.py | by ANXETY ~

from typing import Dict, List, Tuple, Optional, Literal
from IPython.display import clear_output
from pathlib import Path
from tqdm import tqdm
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


nest_asyncio.apply()  # Async support for Jupyter


# === Remove default Colab sample_data ===
sample_data_path = Path('/content/sample_data')
if sample_data_path.exists() and sample_data_path.is_dir():
    shutil.rmtree(sample_data_path)


# ================= PATH & GLOBAL CONSTANTS ================

HOME = Path.home()

# Base project paths
SCR_PATH = HOME / 'ANXETY'
VENV_PATH = HOME / 'venv'
MODULES_FOLDER = SCR_PATH / 'modules'
SCRIPTS_FOLDER = SCR_PATH / 'scripts'
SETTINGS_PATH = SCR_PATH / 'settings.json'

# Add paths to the environment
os.environ.update({
    'home_path': str(HOME),
    'scr_path': str(SCR_PATH),
    'venv_path': str(VENV_PATH),
    'scripts_path': str(SCRIPTS_FOLDER),
    'modules_path': str(MODULES_FOLDER),
    'settings_path': str(SETTINGS_PATH)
})


# ====================== REMOTE SOURCES ====================

# GitHub configuration
DEFAULT_USER = 'anxety-solo'
DEFAULT_REPO = 'sdAIgen'
DEFAULT_BRANCH = 'main'
DEFAULT_LANG = 'en'

GITHUB_RAW = 'https://raw.githubusercontent.com'
GITHUB_API = 'https://api.github.com'
HUGGINGFACE_BASE = 'https://huggingface.co'

DEFAULT_HF_REPO = 'NagisaNao/ANXETY'

# Environments
SUPPORTED_ENVS = {
    'COLAB_GPU': ('Google Colab', '/content'),
    'KAGGLE_URL_BASE': ('Kaggle', '/kaggle/working')
}

# GitHub Source File (GSF)
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

# Another Source File (ASF)
ANOTHER_SOURCE_FILES: List[Dict] = []
"""
# SAMPLE:
ANOTHER_SOURCE_FILES = [
    {
        "url": "https://example.com/custom.py",
        "save_path": "custom/extra",
        "filename": "custom_file.py"  # optional
    }
]
"""


# =================== UTILITY FUNCTIONS ====================

def _install_deps() -> bool:
    """Check if all required dependencies are installed (aria2 and gdown)"""
    try:
        from shutil import which
        required_tools = ['aria2c', 'gdown']
        return all(which(tool) != None for tool in required_tools)
    except ImportError:
        return False

def _get_start_timer() -> int:
    """Get start timer from settings or return current time minus 5 seconds"""
    try:
        if SETTINGS_PATH.exists():
            settings = json.loads(SETTINGS_PATH.read_text())
            return settings.get('ENVIRONMENT', {}).get('start_timer', int(time.time() - 5))
    except (json.JSONDecodeError, OSError):
        pass
    return int(time.time() - 5)

def save_env_to_json(data: dict, filepath: Path) -> None:
    """Save environment data to JSON file, merging with existing content"""
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
    """Clear module cache for modules in specified folder or default modules folder"""
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
    """Set up module folder by clearing cache and adding to sys.path"""
    target_folder = Path(modules_folder) if modules_folder else MODULES_FOLDER
    target_folder.mkdir(parents=True, exist_ok=True)

    _clear_module_cache(target_folder)

    folder_str = str(target_folder)
    if folder_str not in sys.path:
        sys.path.insert(0, folder_str)


# =================== ENVIRONMENT SETUP ====================

def detect_environment(force_env=None):
    """Detect runtime environment, optionally forcing an emulated environment"""
    envs = [env_info[0] for env_info in SUPPORTED_ENVS.values()]

    if force_env:
        if force_env not in envs:
            raise EnvironmentError(f"Unsupported forced environment: {force_env}. Supported: {', '.join(envs)}")
        os.environ['home_work_path'] = ''
        return force_env

    for var, env_info in SUPPORTED_ENVS.items():
        if var in os.environ:
            name, work_path = env_info
            os.environ['home_work_path'] = work_path
            return name

    raise EnvironmentError(f"Unsupported environment. Supported: {', '.join(envs)}")

def parse_fork_arg(fork_arg):
    """Parse fork argument into user/repo"""
    if not fork_arg:
        return DEFAULT_USER, DEFAULT_REPO
    parts = fork_arg.split('/', 1)
    return parts[0], (parts[1] if len(parts) > 1 else DEFAULT_REPO)

def create_environment_data(env, lang, fork_user, fork_repo, branch):
    """Create environment data dictionary"""
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


# ==================== DOWNLOAD HELPERS ====================

def _format_lang_path(path: str, lang: str) -> str:
    """Format path with language placeholder"""
    return path.format(lang=lang) if '{lang}' in path else path

def generate_github_file_list(structure: Dict, base_url: str, lang: str) -> List[Tuple[str, Path]]:
    """Generate flat list of (url, path) from nested structure"""
    def walk(struct: Dict, path_parts: List[str]) -> List[Tuple[str, Path]]:
        items = []
        for key, value in struct.items():
            current_key = _format_lang_path(key, lang)
            current_path = [*path_parts, current_key] if current_key else path_parts

            if isinstance(value, dict):
                items.extend(walk(value, current_path))
            else:
                url_path = '/'.join(current_path)
                for file in value:
                    formatted_file = _format_lang_path(file, lang)
                    url = f"{base_url}/{url_path}/{formatted_file}" if url_path else f"{base_url}/{formatted_file}"
                    file_path = SCR_PATH / '/'.join(current_path) / formatted_file
                    items.append((url, file_path))
        return items

    return walk(structure, [])

def normalize_another_source_files(files: List[Dict]) -> List[Tuple[str, Path]]:
    """Converts another_source to a uniform format (URL, Path)

    - If save_path is absolute -> use it directly
    - If save_path is relative -> default to relative to SCR_PATH
    - If rooted=True is specified -> also save outside SCR_PATH
    - If save_path is not specified -> save next to setup.py
    """
    result = []

    for item in files:
        url = item.get('url')
        if not url:
            continue

        filename = item.get('filename') or url.rsplit('/', 1)[-1]
        save_path = item.get('save_path')
        rooted = item.get('rooted', False)

        if save_path is None:
            base_path = Path(__file__).parent
        else:
            p = Path(save_path)
            base_path = p if (p.is_absolute() or rooted) else SCR_PATH / p

        result.append((url, base_path / filename))

    return result

# ===================== ASYNC DOWNLOAD =====================

async def _download_file(session: aiohttp.ClientSession, url: str, path: Path) -> Tuple[bool, str, Path, Optional[str]]:
    """Download and save single file with error handling"""
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

async def download_files_async(lang, fork_user, fork_repo, branch, log):
    """Main download executor"""
    base_url = f"{GITHUB_RAW}/{fork_user}/{fork_repo}/{branch}"

    github_files = generate_github_file_list(FILE_STRUCTURE, base_url, lang)
    extra_files = normalize_another_source_files(ANOTHER_SOURCE_FILES)

    all_files = github_files + extra_files

    async with aiohttp.ClientSession() as session:
        tasks = [_download_file(session, url, path) for url, path in all_files]
        errors = []

        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc='Downloading files', unit='file'):
            success, url, path, error = await future
            if not success:
                errors.append((url, path, error))

        clear_output()

        if log and errors:
            print('\nErrors occurred during download:')
            for url, path, error in errors:
                print(f"URL: {url}\nPath: {path}\nError: {error}\n")


# ===================== MAIN EXECUTION =====================

async def main(args=None):
    parser = argparse.ArgumentParser(description='SDAIGEN Setup Manager')
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
    asyncio.run(main())