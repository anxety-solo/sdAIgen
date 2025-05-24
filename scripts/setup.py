# ~ setup.py | by ANXETY ~

from IPython.display import display, HTML, clear_output
from urllib.parse import urljoin
from pathlib import Path
from tqdm import tqdm
import nest_asyncio
import importlib
import argparse
import asyncio
import aiohttp
import time
import json
import sys
import os


# Constants
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

nest_asyncio.apply()  # Async support for Jupyter


# ===================== UTILITIES (JSON/FILE OPERATIONS) =====================

def key_exists(filepath, key=None, value=None):
    """Check key/value in JSON file."""
    if not filepath.exists():
        return False
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return False

    if key:
        keys = key.split('.')
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return False
        return (data == value) if value else True
    return False

def save_environment_to_json(SETTINGS_PATH, data):
    """Save environment data to a JSON file."""
    existing_data = {}

    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, 'r') as json_file:
            existing_data = json.load(json_file)

    existing_data.update(data)

    with open(SETTINGS_PATH, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

def get_start_timer():
    """Get the start timer from settings or default to current time minus 5 seconds."""
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, 'r') as f:
            settings = json.load(f)
            return settings.get('ENVIRONMENT', {}).get('start_timer', int(time.time() - 5))
    return int(time.time() - 5)


## ======================= MODULES =======================

def clear_module_cache(modules_folder):
    """Clear the module cache for modules in the specified folder."""
    for module_name in list(sys.modules.keys()):
        module = sys.modules[module_name]
        if hasattr(module, '__file__') and module.__file__ and module.__file__.startswith(str(modules_folder)):
            del sys.modules[module_name]
    importlib.invalidate_caches()

def setup_module_folder(scr_folder):
    """Set up the module folder by clearing the cache and adding it to sys.path."""
    clear_module_cache(scr_folder)
    modules_folder = scr_folder / 'modules'
    modules_folder.mkdir(parents=True, exist_ok=True)
    if str(modules_folder) not in sys.path:
        sys.path.append(str(modules_folder))


# ===================== ENVIRONMENT SETUP =====================

def detect_environment():
    """Detect runtime environment."""
    envs = {'COLAB_GPU': 'Google Colab', 'KAGGLE_URL_BASE': 'Kaggle'}
    for var, name in envs.items():
        if var in os.environ:
            return name
    raise EnvironmentError(f"Unsupported environment. Supported: {', '.join(envs.values())}")

def get_fork_info(fork_arg):
    """Parse fork argument into user/repo."""
    if not fork_arg:
        return 'anxety-solo', 'sdAIgen'
    parts = fork_arg.split('/', 1)
    return parts[0], (parts[1] if len(parts) > 1 else 'sdAIgen')

def create_environment_data(env, scr_folder, lang, fork_user, fork_repo, branch):
    """Create a dictionary with environment data."""
    install_deps = key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)
    start_timer = get_start_timer()

    return {
        'ENVIRONMENT': {
            'lang': lang,
            'fork': f"{fork_user}/{fork_repo}",
            'branch': branch,
            'env_name': env,
            'install_deps': install_deps,
            'home_path': str(scr_folder.parent),
            'venv_path': str(scr_folder.parent / 'venv'),
            'scr_path': str(scr_folder),
            'start_timer': start_timer,
            'public_ip': ''
        }
    }


# ===================== DOWNLOAD LOGIC =====================

def generate_file_list(structure, base_url, base_path):
    """Generate flat list of (url, path) from nested structure"""
    def walk(struct, path_parts):
        items = []
        for key, value in struct.items():
            current_path = [*path_parts, key] if key else path_parts
            if isinstance(value, dict):
                items.extend(walk(value, current_path))
            else:
                url_path = '/'.join(current_path)
                for file in value:
                    url = f"{base_url}/{url_path}/{file}" if url_path else f"{base_url}/{file}"
                    file_path = base_path / '/'.join(current_path) / file
                    items.append((url, file_path))
        return items

    return walk(structure, [])

async def download_file(session, url, path):
    """Download and save single file with error handling"""
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            content = await resp.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return (True, url, path, None)
    except aiohttp.ClientResponseError as e:
        return (False, url, path, f"HTTP error {e.status}: {e.message}")
    except Exception as e:
        return (False, url, path, f"Error: {str(e)}")

async def download_files_async(scr_path, lang, fork_user, fork_repo, branch, log_errors):
    """Main download executor with error logging"""
    files_structure = {
        'CSS': ['main-widgets.css', 'download-result.css', 'auto-cleaner.css'],
        'JS': ['main-widgets.js'],
        'modules': ['json_utils.py', 'webui_utils.py', 'widget_factory.py', 
                   'TunnelHub.py', 'CivitaiAPI.py', 'Manager.py', '__season.py'],
        'scripts': {
            'UIs': ['A1111.py', 'ComfyUI.py', 'Forge.py', 'Classic.py', 'ReForge.py', 'SD-UX.py'],
            lang: [f"widgets-{lang}.py", f"downloading-{lang}.py"],
            '': ['launch.py', 'auto-cleaner.py', 'download-result.py', 
                '_models-data.py', '_xl-models-data.py']
        }
    }

    base_url = f"https://raw.githubusercontent.com/{fork_user}/{fork_repo}/{branch}"
    file_list = generate_file_list(files_structure, base_url, scr_path)

    async with aiohttp.ClientSession() as session:
        tasks = [download_file(session, url, path) for url, path in file_list]

        errors = []
        futures = asyncio.as_completed(tasks)
        for future in tqdm(futures, total=len(tasks), desc="Downloading files", unit="file"):
            result = await future
            success, url, path, error = result
            if not success:
                errors.append((url, path, error))

        clear_output()

        if log_errors and errors:
            print("\nErrors occurred during download:")
            for url, path, error in errors:
                print(f"URL: {url}")
                print(f"Path: {path}")
                print(f"Error: {error}\n")


# ===================== MAIN EXECUTION =====================

async def main_async(args=None):
    """Entry point."""
    parser = argparse.ArgumentParser(description='ANXETY Download Manager')
    parser.add_argument('-l', '--lang', type=str, default='en', help='Language to be used (default: en)')
    parser.add_argument('-b', '--branch', type=str, default='main', help='Branch to download files from (default: main)')
    parser.add_argument('-f', '--fork', type=str, default=None, help='Specify project fork (user or user/repo)')
    parser.add_argument('-s', '--skip-download', action='store_true', help='Skip downloading files and just update the directory and modules')
    parser.add_argument('-L', '--log', action='store_true', help='Enable logging of download errors')

    args, _ = parser.parse_known_args(args)

    env = detect_environment()
    user, repo = get_fork_info(args.fork)   # gitLogin , gitRepoName

    if not args.skip_download:
        await download_files_async(SCR_PATH, args.lang, user, repo, args.branch, args.log)    # download scripts files

    setup_module_folder(SCR_PATH)   # setup main dir -> modules

    env_data = create_environment_data(env, SCR_PATH, args.lang, user, repo, args.branch)
    save_environment_to_json(SETTINGS_PATH, env_data)

    # display info text | MODULES
    from __season import display_info

    display_info(
        env=env,
        scr_folder=str(SCR_PATH),
        branch=args.branch,
        lang=args.lang,
        fork=args.fork
    )

if __name__ == '__main__':
    asyncio.run(main_async())