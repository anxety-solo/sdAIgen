""" Download Orchestrator: Venv, GDrive & Assets | by ANXETY """

import subprocess
import requests
import shutil
import shlex
import time
import sys
import re
import os

from IPython.display import clear_output
from collections.abc import Callable
from urllib.parse import urlparse
from IPython.utils import capture
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
from typing import Any

from os import chdir as CD

# === SDAIGEN ===
from sdai.constants import HOME_PATH, SETTINGS_PATH, VENV_PATH, SCRIPTS_PATH, GD_BASE, GD_FILES, GD_OUTPUTS, GD_CONFIGS, HF_REPO_URL, COL
from sdai.webui_meta import DEFAULT_VENV, WEBUIS, meta, build_urls
from sdai.utils.json import read, save, key_exists, load_settings
from sdai.services.manager import _normalize_url, download, clone
from sdai.models import find_model_by_partial_name, get_category
from sdai.utils.webui import _remove_path, handle_setup_timer
from sdai.api.civitai import CIVITAI_DOMAINS, CivitaiAPI
from sdai.translations import tr


ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

ENV_NAME   = read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI_NAME    = read(SETTINGS_PATH, 'WEBUI.current')
WEBUI_PATH = Path(read(SETTINGS_PATH, 'WEBUI.webui_path'))
EXTS_DIR   = Path(read(SETTINGS_PATH, 'WEBUI.extension_dir'))


# ~~ CLI ARGUMENTS ~~

SKIP_VENV  = '-s' in sys.argv or '--skip-install-venv' in sys.argv
GDRIVE_LOG = '-l' in sys.argv or '--gdrive-log' in sys.argv


# ~~ LOADING SETTINGS ~~

settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ~~ LIBRARIES | VENV ~~

def install_dependencies(commands: list[str]):
    """Run a list of installation commands"""
    for cmd in commands:
        try:
            subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def install_packages(install_lib: dict[str, str]):
    """Install packages from the provided library dictionary"""
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\r[{index}/{len(install_lib)}] {COL.G}>>{COL.X} {tr('lib_installing', package=f'{COL.Y}{package}{COL.X}')}..." + ' ' * 35, end='')
        try:
            result = subprocess.run(install_cmd, shell=True, capture_output=True)
            if result.returncode != 0:
                print(f"\n{COL.R}❌ Error installing {package}{COL.X}")
        except Exception:
            pass


def setup_venv(url: str):
    """Download and unpack the virtual environment, then wire it into PATH"""
    CD(HOME_PATH)
    fn = Path(url).name

    download(f"{url} {HOME_PATH} {fn}", verbose=True)

    # Install dependencies based on environment
    install_commands = ['sudo apt-get -y install lz4 pv']
    if ENV_NAME == 'Kaggle':
        install_commands.extend([
            'pip install ipywidgets jupyterlab_widgets --upgrade',
            'rm -f /usr/lib/python3.10/sitecustomize.py'
        ])

    install_dependencies(install_commands)

    # Unpack and clean
    ipySys(f"pv {fn} | lz4 -d | tar xf -")
    Path(fn).unlink()

    BIN    = str(VENV_PATH / 'bin')
    PY_VER = read(SETTINGS_PATH, 'WEBUI.python_version')
    PKG    = str(VENV_PATH / f"lib/python{PY_VER}/site-packages")

    os.environ.update({
        'PATH': f"{BIN}:{os.environ['PATH']}" if BIN not in os.environ['PATH'] else os.environ['PATH'],
        'PYTHONPATH': f"{PKG}:{os.environ['PYTHONPATH']}" if PKG not in os.environ['PYTHONPATH'] else os.environ['PYTHONPATH']
    })
    sys.path.insert(0, PKG)


# Check and install dependencies
if not key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    install_lib = {
        # Libs
        'aria2': 'pip install aria2',
        'gdown': 'pip install gdown',
        # Tunnels
        'localtunnel': 'npm install -g localtunnel',
        'cloudflared': 'wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod +x /usr/bin/cl',
        'zrok2':       'wget -qO zrok_2.0.4_linux_amd64.tar.gz https://github.com/openziti/zrok/releases/download/v2.0.4/zrok_2.0.4_linux_amd64.tar.gz; tar -xzf zrok_2.0.4_linux_amd64.tar.gz -C /usr/bin; rm -f zrok_2.0.4_linux_amd64.tar.gz',
        'ngrok':       'wget -qO ngrok-v3-stable-linux-amd64.tgz https://bin.ngrok.com/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz; tar -xzf ngrok-v3-stable-linux-amd64.tgz -C /usr/bin; rm -f ngrok-v3-stable-linux-amd64.tgz'
    }

    print(f"💿 {tr('deps_installing')}")
    install_packages(install_lib)
    clear_output()
    save(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

# Install VENV (only when missing or when the UI switched to a different venv)
latest_ui = read(SETTINGS_PATH, 'WEBUI.latest', None)
venv_needs_reinstall = (
    not VENV_PATH.exists()  # venv is missing
    or latest_ui != UI_NAME and meta(latest_ui)['venv'] != meta(UI_NAME)['venv']
)

if not SKIP_VENV and venv_needs_reinstall:
    if VENV_PATH.exists():
        print(f"🗑️ {tr('venv_removing')}")
        shutil.rmtree(VENV_PATH)
        clear_output()

    venv_url = build_urls(UI_NAME)['venv'] if UI_NAME in WEBUIS else f"{HF_REPO_URL}/{DEFAULT_VENV}"
    ui_name  = UI_NAME if UI_NAME in WEBUIS else 'Default'
    m = re.search(r'python(\d)(\d{2})(\d{2})', venv_url)
    venv_version = f"{ui_name} • {int(m[1])}.{int(m[2])}.{int(m[3])}" if m else ui_name

    print(f"♻️ {tr('venv_installing', venv=f'{COL.B}{venv_version}{COL.X}')}")
    setup_venv(venv_url)
    clear_output()

    # Update latest UI version in settings.json
    save(SETTINGS_PATH, 'WEBUI.latest', UI_NAME)


# ~~ WEBUI Installation ~~

# --- ADetailer cache (A1111 / SD-UX only) ---
if (cache_url := build_urls(UI_NAME).get('adetailer_cache')):
    cache_path = '/root/.cache/huggingface/hub/models--Bingsu--adetailer'
    if not os.path.exists(cache_path):
        print(f"🚚 {tr('adetailer_unpacking')}")

        zip_path = HOME_PATH / 'hf_cache_adetailer.zip'
        parent_cache_dir = os.path.dirname(cache_path)
        os.makedirs(parent_cache_dir, exist_ok=True)

        download(f"{cache_url} {HOME_PATH} hf_cache_adetailer")
        ipySys(f"unzip -q -o {zip_path} -d {parent_cache_dir} && rm -rf {zip_path}")
        clear_output()

start_timer = read(SETTINGS_PATH, 'ENVIRONMENT.start_timer')

if not WEBUI_PATH.exists():
    method = tr('method_cloning' if clone_ui else 'method_unpacking')

    print(f"⌚ {tr('webui_installing', method=method, ui=f'{COL.B}{UI_NAME}{COL.X}')}", end='')
    ipyRun('run', str(SCRIPTS_PATH / 'webui_installer.py'))

    handle_setup_timer(WEBUI_PATH, start_timer) # Setup timer (for timer-extension)

    print(f"\r🚀 {tr('webui_installed', method=method, ui=f'{COL.B}{UI_NAME}{COL.X}')}" + ' '*20)
else:
    print(f"🔧 {tr('webui_current', ui=f'{COL.B}{UI_NAME}{COL.X}')}")

    timer_env = handle_setup_timer(WEBUI_PATH, start_timer)
    elapsed_time = str(timedelta(seconds=time.time() - timer_env)).split('.')[0]
    print(f"⌚️ {tr('session_duration', time=f'{COL.Y}{elapsed_time}{COL.X}')}")

# --- Extensions and WebUI update ---

def _setup_git_identity():
    ipySys('git config --global user.email "you@example.com"')
    ipySys('git config --global user.name "Your Name"')


if update_scope != 'none' and not clone_ui:
    do_webui = update_scope.lower() in ('ui', 'all')
    do_ext   = update_scope.lower() in ('extensions', 'all')

    action = tr('update_webui_exts') if do_webui and do_ext else ('WebUI' if do_webui else tr('update_exts'))
    print(f"⌚️ {tr('update_action', action=action)}", end='')
    with capture.capture_output():
        _setup_git_identity()

        ## Update Webui
        if do_webui:
            CD(WEBUI_PATH)

            ipySys('git stash push --include-untracked')
            ipySys('git pull --rebase')
            ipySys('git stash pop')

        ## Update extensions
        if do_ext:
            for entry in os.listdir(EXTS_DIR):
                dir_path = EXTS_DIR / entry
                if dir_path.is_dir():
                    subprocess.run(['git', 'reset', '--hard'], cwd=dir_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(['git', 'pull'], cwd=dir_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"\r✨ {tr('update_done', action=action)}")

# --- Version or branch switching ---

def _git_branch_exists(branch: str) -> bool:
    return subprocess.run(
        ['git', 'show-ref', '--verify', f"refs/heads/{branch}"],
        cwd=WEBUI_PATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0


if commit_hash or branch != 'none':
    print(f"🔄 {tr('switching_branch')}", end='')
    with capture.capture_output():
        CD(WEBUI_PATH)
        _setup_git_identity()

        commit_hash = branch if branch != 'none' and not commit_hash else commit_hash

        # Check for local changes (in the working directory and staged)
        stash_needed = subprocess.run(['git', 'diff', '--quiet'], cwd=WEBUI_PATH).returncode != 0 \
                    or subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=WEBUI_PATH).returncode != 0

        if stash_needed:
            # Save local changes and untracked files
            ipySys('git stash push -u -m "Temporary stash"')

        if re.fullmatch(r'[0-9a-f]{7,40}', commit_hash):
            ipySys(f"git checkout {commit_hash}")
        else:
            ipySys(f"git fetch origin {commit_hash}")

            if _git_branch_exists(commit_hash):
                ipySys(f"git checkout {commit_hash}")
            else:
                ipySys(f"git checkout -b {commit_hash} origin/{commit_hash}")

            ipySys('git pull')

        if stash_needed:
            # Apply stash, saving the index
            ipySys('git stash pop --index || true')

            # In case of conflicts, resolve them while preserving local changes
            conflicts = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=U'],
                cwd=WEBUI_PATH, stdout=subprocess.PIPE, text=True
            ).stdout.strip().splitlines()

            for f in conflicts:
                # Save the local version of the file (ours)
                ipySys(f"git checkout --ours -- \"{f}\"")

            if conflicts:
                ipySys(f"git add {' '.join(conflicts)}")

    print(f"\r✅ {tr('switch_done', commit=f'{COL.B}{commit_hash}{COL.X}')}")


# ~~ GOOGLE DRIVE MOUNTING (Colab only) ~~

# Read gdrive settings
_gdrive_cfg  = read(SETTINGS_PATH, 'GDRIVE', {})
gdrive_mount = _gdrive_cfg.get('mount', False)  # mount/unmount flag
sync_files   = _gdrive_cfg.get('gdrive_files', False)
sync_outputs = _gdrive_cfg.get('gdrive_outputs', False)
sync_configs = _gdrive_cfg.get('gdrive_configs', False)


# --- Helpers ---

def merge_dirs(src: Path, dst: Path, label='', log=False):
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name == '.ipynb_checkpoints':
            continue
        _remove_path(dst / item.name)
        shutil.move(item, dst)
    shutil.rmtree(src)
    if log:
        print(f"{COL.Y}📦 {label}: {COL.cB}{src}{COL.X} → {COL.G}{dst}{COL.X}")


def cleanup_ipynb_checkpoints(base_path: Path):
    for root, dirs, _ in os.walk(base_path):
        if '.ipynb_checkpoints' in dirs:
            chk = Path(root) / '.ipynb_checkpoints'
            shutil.rmtree(chk, ignore_errors=True)

# --- Main Logic ---

def build_symlink_config(ui: str) -> dict:
    """Build symlink configuration based on UI type"""
    is_comfy = meta(ui)['layout'] == 'comfy'

    # base_files: (local_dir, gdrive_folder_name)
    base_files = [
        (model_dir,     'Checkpoints'),
        (vae_dir,       'VAE'),
        (lora_dir,      'LoRa'),
        (embed_dir,     'Embeddings'),
        (control_dir,   'ControlNet'),
        (upscale_dir,   'Upscale'),
        # Others
        (adetailer_dir, 'Adetailer'),
        (clip_dir,      'Clip'),
        (unet_dir,      'Unet'),
        (vision_dir,    'Vision'),
        (encoder_dir,   'Encoder'),
        (diffusion_dir, 'Diffusion'),
    ]
    _files = [
        {'local': local, 'gdrive': str(GD_FILES / gdir)}
        for local, gdir in base_files
    ]
    ext_folder = 'Custom-Nodes' if is_comfy else 'Extensions'
    _files.append({
        'local':  extension_dir,
        'gdrive': str(GD_FILES / ext_folder)
    })

    _outputs = [{
        'local': output_dir,
        'gdrive': str(GD_OUTPUTS / ui),
        'direct_link': True
    }]

    # Config structure
    config_base = GD_CONFIGS / ui
    if is_comfy:
        # ComfyUI specific config structure
        user_default = WEBUI_PATH / 'user' / 'default'
        user_manager = WEBUI_PATH / 'user' / '__manager'
        _configs = [
            {'local': str(user_default / 'comfy.settings.json'), 'gdrive': str(config_base / 'comfy.settings.json'),
                'type': 'file', 'name': 'ComfyUI Settings'},
            {'local': str(user_manager / 'config.ini'), 'gdrive': str(config_base / 'comfy-manager-config.ini'),
                'type': 'file', 'name': 'Comfy Manager Config'},
            {'local': str(user_default / 'workflows'), 'gdrive': str(config_base / 'workflows'),
                'type': 'dir', 'name': 'Workflows'}
        ]
    else:
        # A1111/Forge config structure
        _configs = [
            {'local': str(WEBUI_PATH / 'config.json'), 'gdrive': str(config_base / 'config.json'),
                'type': 'file', 'name': 'WebUI Config'},
            {'local': str(WEBUI_PATH / 'ui-config.json'), 'gdrive': str(config_base / 'ui-config.json'),
                'type': 'file', 'name': 'UI Config'}
        ]

    return {'files': _files, 'outputs': _outputs, 'configs': _configs}


def create_symlink(src: str | Path, dst: str | Path, symlink_name='GDrive', direct_link=False, log=False):
    """Create symlink with optional migration of existing content"""
    try:
        src = Path(src)
        dst = Path(dst)
        dst.mkdir(parents=True, exist_ok=True)

        if direct_link:
            # Direct link mode: replace entire directory with symlink
            if src.exists() and src.is_dir() and not src.is_symlink():
                merge_dirs(src, dst, label=tr('gd_merge_migrated'), log=log)

            if src.is_symlink():
                src.unlink()
            src.parent.mkdir(parents=True, exist_ok=True)

            # Create direct symlink
            if not src.exists():
                src.symlink_to(dst, target_is_directory=True)
                if log:
                    print(f"{COL.G}🔗 {tr('gd_direct_symlink')} {COL.cB}{src}{COL.X} → {COL.G}{dst}{COL.X}")
        else:
            # Subfolder mode: create GDrive folder inside src
            symlink_path = src / symlink_name

            # Migrate contents if GDrive subfolder exists and is real dir
            if symlink_path.exists() and not symlink_path.is_symlink():
                merge_dirs(symlink_path, dst, label=tr('gd_merge_migrated'), log=log)
            _remove_path(symlink_path)
            src.mkdir(parents=True, exist_ok=True)

            # Create subfolder symlink
            if not symlink_path.exists():
                symlink_path.symlink_to(dst, target_is_directory=True)
                if log:
                    print(f"{COL.G}🔗 {tr('gd_symlink_created')} {COL.cB}{symlink_path}{COL.X} → {COL.G}{dst}{COL.X}")
    except Exception as exc:
        print(f"{COL.R}❌ {tr('gd_symlink_error')}{COL.X} {src} - {exc}")


def create_config_symlink(local_path: str | Path, gdrive_path: str | Path, config_type='file', config_name='Config', log=False):
    """Create symlink for config files or directories"""
    try:
        local_path  = Path(local_path)
        gdrive_path = Path(gdrive_path)
        gdrive_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if config_type == 'file':
            # For files: backup local to gdrive if gdrive doesn't exist
            if local_path.exists() and local_path.is_file() and not gdrive_path.exists():
                shutil.copy2(local_path, gdrive_path)
                if log:
                    print(f"{COL.Y}📄 {tr('gd_backed_up', config_name=config_name, name=f'{COL.cB}{local_path.name}{COL.X}')} → {COL.G}GDrive{COL.X}")

            if local_path.exists():
                local_path.unlink()
        else:
            # For directories: merge content to gdrive
            if local_path.exists() and local_path.is_dir() and not local_path.is_symlink():
                merge_dirs(
                    local_path, gdrive_path,
                    label=tr('gd_merge_merged', config_name=config_name), log=log
                )
            elif local_path.exists() and not local_path.is_symlink():
                _remove_path(local_path)

        if local_path.is_symlink():
            local_path.unlink()

        # Create new symlink
        if not local_path.exists():
            is_dir = (config_type == 'dir')
            local_path.symlink_to(gdrive_path, target_is_directory=is_dir)
            if log:
                icon = '📁' if is_dir else '📄'
                print(f"{COL.G}{icon} {tr('gd_config_symlink', config_name=config_name, name=f'{COL.cB}{local_path.name}{COL.X}')} → {COL.G}GDrive{COL.X}")
    except Exception as exc:
        print(f"{COL.R}❌ {tr('gd_config_error', config_name=config_name)}{COL.X} {local_path.name} - {exc}")


def restore_from_symlink(local_path: str | Path, gdrive_path: str | Path, config_type='file', config_name='Config', log=False):
    """Restore local files/directories from Google Drive before unmounting"""
    try:
        local_path  = Path(local_path)
        gdrive_path = Path(gdrive_path)

        # Only restore if local is symlink and gdrive exists
        if not local_path.is_symlink() or not gdrive_path.exists():
            return
        local_path.unlink()

        is_dir = (config_type == 'dir')
        if (gdrive_path.is_dir() if is_dir else gdrive_path.is_file()):
            (shutil.copytree if is_dir else shutil.copy2)(gdrive_path, local_path)
            if log:
                icon = '📁' if is_dir else '📄'
                print(f"{COL.Y}{icon} {tr('gd_restored', config_name=config_name, name=f'{COL.cB}{local_path.name}{COL.X}')} ← {COL.B}GDrive{COL.X}")
    except Exception as exc:
        print(f"{COL.R}❌ {tr('gd_restore_error', config_name=config_name)}{COL.X} {exc}")


def _clear_category_symlinks(config_list: list, category: str, restore=False, log=False) -> int:
    """Remove symlinks for a single category, optionally restoring files first"""
    removed = 0
    for cfg in config_list:
        if category == 'files':
            p = Path(cfg['local']) / 'GDrive'
            if p.is_symlink():
                p.unlink()
                removed += 1
                if log:
                    print(f"{COL.R}🗑️ {tr('gd_removed')} {COL.cB}{p}{COL.X}")
        else:
            local = Path(cfg['local'])
            gdrive = Path(cfg['gdrive'])
            if local.is_symlink():
                if restore:
                    ctype = cfg.get('type', 'dir' if category == 'outputs' else 'file')
                    name = cfg.get('name', category.capitalize())
                    restore_from_symlink(local, gdrive, config_type=ctype, config_name=name, log=log)
                else:
                    local.unlink()
                removed += 1
    return removed


def remove_all_symlinks(ui='A1111', restore_configs=False, log=False) -> int:
    """Remove ALL symlinks (every category)"""
    config  = build_symlink_config(ui)
    removed = _clear_category_symlinks(config['files'],    'files',   log=log)
    removed += _clear_category_symlinks(config['outputs'], 'outputs', restore=restore_configs, log=log)
    removed += _clear_category_symlinks(config['configs'], 'configs', restore=restore_configs, log=log)
    return removed


def handle_gdrive(mount_flag: bool, ui='A1111', log=False, sync_files=False, sync_outputs=False, sync_configs=False):
    """Mount/unmount GDrive and sync symlinks for selected categories.

    On mount (or re-run with drive already mounted):
      1. Restore + remove symlinks for DESELECTED categories.
      2. Create / refresh symlinks for SELECTED categories.
    On unmount: restore+remove ALL categories, then unmount.
    """
    from google.colab import drive

    cleanup_ipynb_checkpoints(GD_BASE)  # Remove Jupyter checkpoints
    drive_mounted = os.path.exists('/content/drive/MyDrive')

    # Unmount logic
    if not mount_flag:
        if drive_mounted:
            try:
                print(f"⏳ {tr('gd_unmounting')}", end='')
                if log: print()

                removed = remove_all_symlinks(ui, restore_configs=True, log=log)

                with capture.capture_output():
                    drive.flush_and_unmount()
                    os.system('rm -rf /content/drive')

                print(f"\r✅ {tr('gd_unmounted')}")
                if removed:
                    print(f"💾 {tr('gd_restore_summary', count=removed)}")
            except Exception as exc:
                print(f"\r{COL.R}❌ {tr('gd_unmount_error')}{COL.X} {exc}")
        return

    # Mount logic
    if not drive_mounted:
        try:
            print(f"⏳ {tr('gd_mounting')}", end='')
            with capture.capture_output():
                drive.mount('/content/drive')
            print(f"\r💿 {tr('gd_mounted')}")
        except Exception as exc:
            print(f"\r{COL.R}❌ {tr('gd_mount_error')}{COL.X} {exc}")
            return
    else:
        print(f"🎉 {tr('gd_connected')}")

    # categories: (key, enabled, restore_on_deselect, display_name, section_header)
    categories = [
        ('files',   sync_files,   False, tr('gd_files_label'),   tr('gd_header_files')),
        ('outputs', sync_outputs, True,  tr('gd_outputs_label'), tr('gd_header_outputs')),
        ('configs', sync_configs, True,  tr('gd_configs_label'), tr('gd_header_configs')),
    ]
    active   = [name for _, enabled, _, name, _ in categories if enabled]
    inactive = [name for _, enabled, _, name, _ in categories if not enabled]

    if not active:
        print(f"⚠️ {tr('gd_no_categories')}")
        return

    active_str   = ', '.join(f"{COL.G}{n}{COL.X}" for n in active)
    inactive_str = ', '.join(f"{COL.Y}{n}{COL.X}" for n in inactive)
    print(f"{COL.B}📋 {tr('gd_sync_summary', active=active_str)}{tr('gd_sync_inactive', inactive=inactive_str) if inactive else ''}{COL.X}")

    try:
        # Create base directories
        for base, enabled in ((GD_BASE, True), (GD_FILES, sync_files), (GD_OUTPUTS, sync_outputs), (GD_CONFIGS, sync_configs)):
            if enabled:
                os.makedirs(base, exist_ok=True)

        config = build_symlink_config(ui)

        # Step 1: restore + remove DESELECTED categories
        for key, enabled, restore, _, _ in categories:
            if not enabled:
                _clear_category_symlinks(config[key], key, restore=restore, log=log)

        # Step 2: create / refresh SELECTED categories
        for key, enabled, _, _, header in categories:
            if not enabled:
                continue
            if log:
                print(f"\n{COL.B}━━━ {header} ━━━{COL.X}")
            for cfg in config[key]:
                if key == 'configs':
                    create_config_symlink(
                        cfg['local'], cfg['gdrive'],
                        cfg.get('type', 'file'),
                        cfg.get('name', 'Config'),
                        log=log
                    )
                else:
                    create_symlink(
                        cfg['local'], cfg['gdrive'],
                        direct_link=cfg.get('direct_link', False),
                        log=log
                    )

        print(f"✅ {tr('gd_sync_done')}")
    except Exception as exc:
        print(f"{COL.R}❌ {tr('gd_setup_error')}{COL.X} {exc}")


handle_gdrive(
    gdrive_mount, UI_NAME, GDRIVE_LOG,
    sync_files=sync_files,
    sync_outputs=sync_outputs,
    sync_configs=sync_configs
)


# ~~ DOWNLOADING ~~

def handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            print(f">> An error occurred in {func.__name__}: {exc}")
    return wrapper


# Get model lists (SD / XL / ANIMA) by selected type
model_type = settings.get('model_type', 'XL')
model_data = get_category(model_type)
model_list, vae_list, controlnet_list, additional_list = (model_data.get(k, {}) for k in ('model', 'vae', 'controlnet', 'additional'))

# --- Downloading models ---
print(f"📦 {tr('dl_start')}", end='')

extension_repo = []
# prefix | (dir_path, short_tag)
PREFIX_MAP = {
    # prefix : (dir_path, short_tag)
    'model':     (model_dir, '$ckpt'),
    'vae':       (vae_dir, '$vae'),
    'lora':      (lora_dir, '$lora'),
    'embed':     (embed_dir, '$emb'),
    'extension': (extension_dir, '$ext'),
    'adetailer': (adetailer_dir, '$ad'),
    'control':   (control_dir, '$cnet'),
    'upscale':   (upscale_dir, '$ups'),
    # Other
    'clip':      (clip_dir, '$clip'),
    'unet':      (unet_dir, '$unet'),
    'vision':    (vision_dir, '$vis'),
    'encoder':   (encoder_dir, '$enc'),
    'diffusion': (diffusion_dir, '$diff'),
    'config':    (config_dir, '$cfg')
}
for dir_path, _ in PREFIX_MAP.values():
    os.makedirs(dir_path, exist_ok=True)


# ~~ FORMATTED INFO OUTPUT ~~

def _center_text(text: str, terminal_width=45) -> str:
    padding = (terminal_width - len(text)) // 2
    return f"{' ' * padding}{text}{' ' * padding}"


def format_output(url: str, dst_dir: str, file_name: str, image_url: str = None):
    """Formats and prints download details with colored text"""
    info = '[NONE]'
    if file_name:
        info = _center_text(f"[{file_name.rsplit('.', 1)[0]}]")
    elif 'drive.google.com' in url:
        info = _center_text('[GDrive]')

    sep_line = '───' * 20

    print()
    print(f"{COL.G}{sep_line}{COL.cB}{info}{COL.G}{sep_line}{COL.X}")
    print(f"{COL.Y}{'URL:':<12}{COL.X}{url}")
    print(f"{COL.Y}{'SAVE DIR:':<12}{COL.B}{dst_dir}")
    print(f"{COL.Y}{'FILE NAME:':<12}{COL.B}{file_name}{COL.X}")
    if 'civitai' in url and image_url:
        print(f"{COL.G}{'[Preview]:':<12}{COL.X}{image_url}")
    print()


# ~~ DOWNLOAD CORE ~~

def _extract_filename(url: str) -> str | None:
    if match := re.search(r'\[(.*?)\]', url):
        return match.group(1)
    if any(d in urlparse(url).netloc for d in [*CIVITAI_DOMAINS, 'drive.google.com']):
        return None
    return Path(urlparse(url).path).name


def _process_download_link(link: str) -> tuple[str | None, str, str | None]:
    """Processes a download link, splitting prefix, URL, and filename"""
    link = _normalize_url(link)
    if ':' in link:
        prefix, path = link.split(':', 1)
        if prefix in PREFIX_MAP:
            return prefix, re.sub(r'\[.*?\]', '', path), _extract_filename(path)
    return None, link, None


@handle_errors
def run_downloads(line: str):
    """Downloads files from comma-separated links, processes prefixes, and unpacks zips post-download"""
    for link in filter(None, map(str.strip, line.split(','))):
        prefix, url, filename = _process_download_link(link)

        if prefix:
            dir_path, _ = PREFIX_MAP[prefix]

            if prefix == 'extension':
                extension_repo.append((url, filename))
                continue
            try:
                manual_download(url, dir_path, filename)
            except Exception as exc:
                print(f"\n> Download error: {exc}")
        else:
            parts = url.split(maxsplit=2)
            if len(parts) < 2:
                print(f"\n> Skipping malformed download link: {url}")
            else:
                manual_download(*parts)


@handle_errors
def manual_download(url: str, dst_dir: str, file_name: str = None):
    image_url = None

    if 'modelVersionId=' in url or any(f"{d}/models/" in url for d in CIVITAI_DOMAINS):
        api = CivitaiAPI(civitai_token)
        if not (data := api.validate_download(url, file_name)):
            return

        url, file_name = data.download_url, data.file_name          # Download_URL, File_Name
        image_url = data.image_url                                  # Image_URL

        # Download preview images (only for ComfyUI)
        if UI_NAME == 'ComfyUI' and image_url and data.image_name:
            download(f"{image_url} {dst_dir} {data.image_name}")

    # Formatted info output
    format_output(url.split('?')[0], dst_dir, file_name, image_url)

    # Downloading Files | With Logs and Auto Unpacking ZIP Archives
    download(f"{url} {dst_dir} {file_name or ''}", verbose=True, unzip=True)


# ~~ SUBMODELS ~~

# Separation of merged numbers
def _parse_selection_numbers(num_str: str, max_num: int) -> list[int]:
    """Split a string of numbers into unique integers, considering max_num as the upper limit"""
    num_str = num_str.replace(',', ' ').strip()
    unique_numbers = set()
    max_length = len(str(max_num))

    for part in num_str.split():
        if not part.isdigit():
            continue

        # Check if the entire part is a valid number
        part_int = int(part)
        if part_int <= max_num:
            unique_numbers.add(part_int)
            continue  # No need to split further

        # Split the part into valid numbers starting from the longest possible
        current_position = 0
        part_len = len(part)
        while current_position < part_len:
            found = False
            # Try lengths from max_length down to 1
            for length in range(min(max_length, part_len - current_position), 0, -1):
                substring = part[current_position:current_position + length]
                if substring.isdigit():
                    num = int(substring)
                    if num <= max_num and num != 0:
                        unique_numbers.add(num)
                        current_position += length
                        found = True
                        break
            if not found:
                # Move to the next character if no valid number found
                current_position += 1

    return sorted(unique_numbers)


def handle_submodels(selection: str, num_selection: str, model_dict: dict, dst_dir: str, base_url: str) -> str:
    selected = []

    def _resolve_dst(path_str: str) -> str:
        if '/' in path_str or '\\' in path_str:
            return path_str
        return globals().get(path_str, path_str)

    keys = list(model_dict)
    numbered = {f"{i}. {k}": v for i, (k, v) in enumerate(model_dict.items(), 1)}

    def add_by_key(key: str):
        if key in model_dict:
            selected.extend(model_dict[key])

    # Selection
    if selection.lower() != 'none':
        if selection.lower() == 'all':
            selected = sum(model_dict.values(), [])
        else:
            found = find_model_by_partial_name(selection, numbered) or selection
            add_by_key(re.sub(r'^\d+\.\s*', '', found))

        if num_selection:
            for num in _parse_selection_numbers(num_selection, len(keys)):
                add_by_key(keys[num - 1])

    # Deduplicate
    unique = {}
    for m in selected:
        name = m.get('name') or os.path.basename(m['url'])
        unique[name] = {    # Note: `name` is an optional parameter
            'url': m['url'],
            'dst_dir': _resolve_dst(m.get('dst_dir', dst_dir)),
            'name': name
        }

    # Build result
    suffix = ''.join(
        f"{m['url']} {m['dst_dir']} {m['name']}, "
        for m in unique.values()
    )

    return base_url + suffix


line = ''
line = handle_submodels(model, model_num, model_list, model_dir, line)
line = handle_submodels(vae, vae_num, vae_list, vae_dir, line)
line = handle_submodels(controlnet, controlnet_num, controlnet_list, control_dir, line)
line = handle_submodels('all', '', additional_list, '', line)


# ~~ FILE SOURCES ~~

def _process_lines(lines: list[str]) -> str:
    """Processes text lines, extracts valid URLs with tags/filenames, and ensures uniqueness"""
    current_tag = None
    processed_entries = set()  # Store (tag, clean_url) to check uniqueness
    result_urls = []

    for line in lines:
        clean_line = line.strip().lower()

        # Update the current tag when detected
        for prefix, (_, short_tag) in PREFIX_MAP.items():
            if (f"# {prefix}".lower() in clean_line) or (short_tag and short_tag.lower() in clean_line):
                current_tag = prefix
                break

        if not current_tag:
            continue

        # Normalise the delimiters and process each URL
        normalized_line = re.sub(r'[\s,]+', ',', line.strip())
        for url_entry in normalized_line.split(','):
            url = url_entry.split('#')[0].strip()
            if not url.startswith('http'):
                continue

            clean_url = re.sub(r'\[.*?\]', '', url)
            entry_key = (current_tag, clean_url)    # Uniqueness is determined by a pair (tag, URL)

            if entry_key not in processed_entries:
                filename = _extract_filename(url_entry)
                formatted_url = f"{current_tag}:{clean_url}"
                if filename:
                    formatted_url += f"[{filename}]"

                result_urls.append(formatted_url)
                processed_entries.add(entry_key)

    return ', '.join(result_urls)


def process_file_downloads(file_urls: list[str], additional_lines: str = None) -> str:
    """Reads URLs from files/HTTP sources"""
    lines = []

    if additional_lines:
        lines.extend(additional_lines.splitlines())

    for source in file_urls:
        if source.startswith('http'):
            try:
                response = requests.get(_normalize_url(source))
                response.raise_for_status()
                lines.extend(response.text.splitlines())
            except requests.RequestException:
                continue
        else:
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    lines.extend(f.readlines())
            except FileNotFoundError:
                continue

    return _process_lines(lines)


# File URLs processing
urls_sources = (model_urls, vae_urls, lora_urls, embedding_urls, extensions_urls, adetailer_urls)
file_urls = [f"{f}.txt" if not f.endswith('.txt') else f for f in re.split(r'[\s,]+', custom_file_urls) if f] if custom_file_urls else []

# p -> prefix ; u -> url | Remember: don't touch the prefix!
prefixed_urls = [f"{p}:{u}" for p, u in zip(PREFIX_MAP, urls_sources) if u for u in u.replace(',', '').split()]
line += ', '.join(prefixed_urls + [process_file_downloads(file_urls, empowerment_input)])

if detailed_download == 'on':
    print(f"\n\n{COL.Y}# ====== Detailed Download ====== #{COL.X}")
    run_downloads(line)
    print(f"\n{COL.Y}# =============================== #\n{COL.X}")
else:
    with capture.capture_output():
        run_downloads(line)

print(f"\r🏁 {tr('dl_done')}" + ' '*15)


# ~~ CUSTOM EXTENSIONS ~~

extension_type = tr('ext_type_nodes') if UI_NAME == 'ComfyUI' else tr('ext_type_extensions')

if extension_repo:
    print(f"✨ {tr('ext_installing', type=extension_type)}", end='')
    with capture.capture_output():
        for repo_url, repo_name in extension_repo:
            clone(f"{repo_url} {EXTS_DIR} {repo_name}")
    print(f"\r📦 {tr('ext_installed', count=len(extension_repo), type=extension_type)}")


# ~~ SPECIAL ~~

# --- ADetailer sorting (bbox / segm) | ComfyUI only ---
if UI_NAME == 'ComfyUI':
    adetailer_dir = Path(adetailer_dir)

    for sub in ('bbox', 'segm'):
        (adetailer_dir / sub).mkdir(exist_ok=True)

    for path in adetailer_dir.glob('*.pt'):
        sub = 'segm' if path.name.endswith('-seg.pt') else 'bbox'
        dest = adetailer_dir / sub / path.name

        if dest.exists():
            path.unlink()
        else:
            shutil.move(path, dest)

# --- Symlink `diffusion_dir/model` → `model_dir` | ComfyUI only ---
model_symlink = Path(diffusion_dir) / 'ckpts'
if UI_NAME == 'ComfyUI':
    if not model_symlink.exists():
        model_symlink.symlink_to(model_dir, target_is_directory=True)
elif model_symlink.is_symlink():
    model_symlink.unlink()

# --- Copy dir from GDrive to extension_dir (if enabled) ---
if gdrive_mount and sync_files:
    gdrive_path = EXTS_DIR / 'GDrive'
    if gdrive_path.is_dir():
        for folder in os.listdir(gdrive_path):
            src = gdrive_path / folder
            dst = EXTS_DIR / folder
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        _remove_path(gdrive_path)


# --- List Models and stuff ---
ipyRun('run', str(SCRIPTS_PATH / 'download_result.py'))
