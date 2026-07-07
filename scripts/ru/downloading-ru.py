# ~ download.py | by ANXETY ~

from Manager import m_download, m_clone             # Every Download | Clone
from CivitaiAPI import CivitAiAPI, CIVITAI_DOMAINS  # CivitAI API
from webui_utils import *                           # WEBUI
import json_utils as js                             # JSON

from IPython.display import clear_output
from IPython.utils import capture
from urllib.parse import urlparse
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import shutil
import shlex
import time
import json
import sys
import re
import os

# === Parse CLI arguments ===
SKIP_INSTALL_VENV = '-s' in sys.argv or '--skip-install-venv' in sys.argv
GDRIVE_LOG        = '-l' in sys.argv or '--gdrive-log' in sys.argv

osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

HF_REPO_URL = 'https://huggingface.co/NagisaNao/ANXETY/resolve/main'

# Auto-convert *_path env vars to Path
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, SCR_PATH, VENV, SETTINGS_PATH = (
    PATHS['home_path'], PATHS['scr_path'], PATHS['venv_path'], PATHS['settings_path']
)

ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
SCRIPTS = PATHS['scripts_path']

LANG = js.read(SETTINGS_PATH, 'ENVIRONMENT.lang')
UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = js.read(SETTINGS_PATH, 'WEBUI.webui_path')


# Text Colors (\033)
class COLORS:
    R  =  '\033[31m'    # Red
    G  =  '\033[32m'    # Green
    Y  =  '\033[33m'    # Yellow
    B  =  '\033[34m'    # Blue
    lB =  '\033[36;1m'  # lightBlue + BOLD
    X  =  '\033[0m'     # Reset

COL = COLORS


# ==================== LIBRARIES | VENV ====================

def install_dependencies(commands):
    """Run a list of installation commands"""
    for cmd in commands:
        try:
            subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def setup_venv(url):
    """Customize the virtual environment using the specified URL"""
    CD(HOME)
    fn = Path(url).name

    m_download(f"{url} {HOME} {fn}")

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

    BIN = str(VENV / 'bin')
    PYTHON_VERSION = js.read(SETTINGS_PATH, 'WEBUI.python_version')
    PKG = str(VENV / f"lib/python{PYTHON_VERSION}/site-packages")

    osENV.update({
        # 'PYTHONWARNINGS': 'ignore',
        'PATH': f"{BIN}:{osENV['PATH']}" if BIN not in osENV['PATH'] else osENV['PATH'],
        'PYTHONPATH': f"{PKG}:{osENV['PYTHONPATH']}" if PKG not in osENV['PYTHONPATH'] else osENV['PYTHONPATH']
    })
    sys.path.insert(0, PKG)

def install_packages(install_lib):
    """Install packages from the provided library dictionary"""
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\r[{index}/{len(install_lib)}] {COL.G}>>{COL.X} Installing {COL.Y}{package}{COL.X}..." + ' ' * 35, end='')
        try:
            result = subprocess.run(install_cmd, shell=True, capture_output=True)
            if result.returncode != 0:
                print(f"\n{COL.R}Error installing {package}{COL.X}")
        except Exception:
            pass

# Check and install dependencies
if not js.key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    install_lib = {
        ## Libs
        'aria2': "pip install aria2",
        'gdown': "pip install gdown",
        ## Tunnels
        'localtunnel': "npm install -g localtunnel",
        'cloudflared': "wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod +x /usr/bin/cl",
        'zrok': "wget -qO zrok_1.1.10_linux_amd64.tar.gz https://github.com/openziti/zrok/releases/download/v1.1.10/zrok_1.1.10_linux_amd64.tar.gz; tar -xzf zrok_1.1.10_linux_amd64.tar.gz -C /usr/bin; rm -f zrok_1.1.10_linux_amd64.tar.gz",
        'ngrok': "wget -qO ngrok-v3-stable-linux-amd64.tgz https://bin.ngrok.com/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz; tar -xzf ngrok-v3-stable-linux-amd64.tgz -C /usr/bin; rm -f ngrok-v3-stable-linux-amd64.tgz"
    }

    print('💿 Установка библиотек займет немного времени.')
    install_packages(install_lib)
    clear_output()
    js.update(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

# Install VENV
current_ui = js.read(SETTINGS_PATH, 'WEBUI.current')
latest_ui = js.read(SETTINGS_PATH, 'WEBUI.latest')

# Determine whether to reinstall venv
venv_needs_reinstall = (
    not VENV.exists()  # venv is missing
    # Check UIs change (ComfyUI <-> other, Classic/Neo <-> other, ReForge <-> other)
    or (latest_ui == 'ComfyUI') != (current_ui == 'ComfyUI')
    or (latest_ui == 'Neo') != (current_ui == 'Neo')
    or (latest_ui == 'Classic') != (current_ui == 'Classic')
    or (latest_ui == 'ReForge') != (current_ui == 'ReForge')
)

if not SKIP_INSTALL_VENV and venv_needs_reinstall:
    if VENV.exists():
        print('🗑️ Удаление старого venv...')
        shutil.rmtree(VENV)
        clear_output()

    venv_config = {
        'ComfyUI': f"{HF_REPO_URL}/python31312-venv-torch2100-cu130-ComfyUI.tar.lz4",
        'Neo':     f"{HF_REPO_URL}/python31312-venv-torch2100-cu130-Neo.tar.lz4",
        'ReForge': f"{HF_REPO_URL}/python31213-venv-torch2100-cu130-ReForge.tar.lz4",
        'Classic': f"{HF_REPO_URL}/python31113-venv-torch280-cu126-Classic.tar.lz4",
        'default': f"{HF_REPO_URL}/python31018-venv-torch260-cu124-fa.tar.lz4",
    }
    venv_url = venv_config.get(current_ui, venv_config['default'])
    ui_name  = current_ui if current_ui in venv_config else 'Default'
    _m = re.search(r'python(\d{1})(\d{2})(\d{2})', venv_url)
    venv_version = f"{ui_name} • {int(_m[1])}.{int(_m[2])}.{int(_m[3])}" if _m else ui_name

    print(f"♻️ Установка VENV: {COL.B}{venv_version}{COL.X}, это может занять некоторое время...")
    setup_venv(venv_url)
    clear_output()

    # Update latest UI version...
    js.update(SETTINGS_PATH, 'WEBUI.latest', current_ui)


# =================== loading settings V5 ==================

def load_settings(path):
    """Load settings from a JSON file"""
    try:
        return {
            **js.read(path, 'ENVIRONMENT'),
            **js.read(path, 'WIDGETS'),
            **js.read(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}

# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ========================== WEBUI =========================

if UI in ['A1111', 'SD-UX']:
    cache_path = '/root/.cache/huggingface/hub/models--Bingsu--adetailer'
    if not os.path.exists(cache_path):
        print('🚚 Распаковка кэша моделей ADetailer...')

        name_zip = 'hf_cache_adetailer'
        chache_url = f"{HF_REPO_URL}/hf_cache_adetailer.zip"

        zip_path = HOME / f"{name_zip}.zip"
        parent_cache_dir = os.path.dirname(cache_path)
        os.makedirs(parent_cache_dir, exist_ok=True)

        m_download(f"{chache_url} {HOME} {name_zip}")
        ipySys(f"unzip -q -o {zip_path} -d {parent_cache_dir} && rm -rf {zip_path}")
        clear_output()

start_timer = js.read(SETTINGS_PATH, 'ENVIRONMENT.start_timer')

if not os.path.exists(WEBUI):
    start_install = time.time()
    print(f"⌚ Распаковка Stable Diffusion... | WEBUI: {COL.B}{UI}{COL.X}", end='')

    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
    handle_setup_timer(WEBUI, start_timer)		# Setup timer (for timer-extensions)

    install_time = time.time() - start_install
    minutes, seconds = divmod(int(install_time), 60)
    print(f"\r🚀 Распаковка {COL.B}{UI}{COL.X} Завершена! {minutes:02}:{seconds:02} ⚡" + ' '*25)

else:
    print(f"🔧 Текущий WebUI: {COL.B}{UI}{COL.X}")

    timer_env = handle_setup_timer(WEBUI, start_timer)
    elapsed_time = str(timedelta(seconds=time.time() - timer_env)).split('.')[0]
    print(f"⌚️ Продолжительность сеанса: {COL.Y}{elapsed_time}{COL.X}")


## Changes extensions and WebUi
if latest_webui or latest_extensions:
    action = 'WebUI и Расширений' if latest_webui and latest_extensions else ('WebUI' if latest_webui else 'Расширений')
    print(f"⌚️ Обновление {action}...", end='')
    with capture.capture_output():
        ipySys('git config --global user.email "you@example.com"')
        ipySys('git config --global user.name "Your Name"')

        ## Update Webui
        if latest_webui:
            CD(WEBUI)

            ipySys('git stash push --include-untracked')
            ipySys('git pull --rebase')
            ipySys('git stash pop')

        ## Update extensions
        if latest_extensions:
            for entry in os.listdir(f"{WEBUI}/extensions"):
                dir_path = f"{WEBUI}/extensions/{entry}"
                if os.path.isdir(dir_path):
                    subprocess.run(['git', 'reset', '--hard'], cwd=dir_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(['git', 'pull'], cwd=dir_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"\r✨ Обновление {action} Завершено!")


## Version or branch switching
def _git_branch_exists(branch: str) -> bool:
    result = subprocess.run(
        ['git', 'show-ref', '--verify', f"refs/heads/{branch}"],
        cwd=WEBUI,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

if commit_hash or branch != 'none':
    print('🔄 Switching to the specified commit or branch...', end='')
    with capture.capture_output():
        CD(WEBUI)
        ipySys('git config --global user.email "you@example.com"')
        ipySys('git config --global user.name "Your Name"')

        commit_hash = branch if branch != 'none' and not commit_hash else commit_hash

        # Check for local changes (in the working directory and staged)
        stash_needed = subprocess.run(['git', 'diff', '--quiet'], cwd=WEBUI).returncode != 0 \
                    or subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=WEBUI).returncode != 0

        if stash_needed:
            # Save local changes and untracked files
            ipySys('git stash push -u -m "Temporary stash"')

        is_commit = re.fullmatch(r"[0-9a-f]{7,40}", commit_hash) is not None

        if is_commit:
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
                cwd=WEBUI, stdout=subprocess.PIPE, text=True
            ).stdout.strip().splitlines()

            for f in conflicts:
                # Save the local version of the file (ours)
                ipySys(f"git checkout --ours -- \"{f}\"")

            if conflicts:
                ipySys(f"git add {' '.join(conflicts)}")
    print(f"\r✅ Переключение завершено! Текущий коммит/ветка: {COL.B}{commit_hash}{COL.X}")


# === Google Drive Mounting V2 | EXCLUSIVE for Colab ===
from google.colab import drive

# Read GDrive settings
_gdrive_cfg = js.read(SETTINGS_PATH, 'GDrive', {})

mountGDrive = _gdrive_cfg.get('mount')  # mount/unmount flag
GD_sync_files = _gdrive_cfg.get('gdrive_files')
GD_sync_outputs = _gdrive_cfg.get('gdrive_outputs')
GD_sync_configs = _gdrive_cfg.get('gdrive_configs')

GD_BASE = '/content/drive/MyDrive/sdAIgen'
GD_FILES = f"{GD_BASE}/files"
GD_OUTPUTS = f"{GD_BASE}/outputs"
GD_CONFIGS = f"{GD_BASE}/configs"

# --- Helpers ---
def _remove_path(path: Path):
    """Delete a file, symlink, or directory"""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)

def _merge_dirs(src: Path, dst: Path, label=''):
    """Move contents of *src* into *dst*, then delete *src*"""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name == '.ipynb_checkpoints':
            continue
        _remove_path(dst / item.name)
        shutil.move(str(item), str(dst))
    shutil.rmtree(src)
    if GDRIVE_LOG and label:
        print(f"{COL.Y}📦 {label}: {COL.lB}{src}{COL.X} → {COL.G}{dst}{COL.X}")

def _cleanup_ipynb_checkpoints(base_path):
    """Recursively remove all .ipynb_checkpoints directories under *base_path*"""
    for root, dirs, _ in os.walk(base_path):
        if '.ipynb_checkpoints' in dirs:
            shutil.rmtree(Path(root) / '.ipynb_checkpoints', ignore_errors=True)

# --- Сonfiguration ---
def _build_sync_config(ui: str) -> dict:
    """Build configuration dict with file, output, and config symlink items for given UI"""
    is_comfy = ui == 'ComfyUI'

    # Files structure | Local <-> GDrive
    # > local_dir, gdrive_subdir, flat_link
    files_base = [
        (model_dir,     'Checkpoints', False),
        (vae_dir,       'VAE',         True),
        (lora_dir,      'Lora',        False),
        (embed_dir,     'Embeddings',  False),
        (control_dir,   'ControlNet',  False),
        (upscale_dir,   'Upscale',     False),
        (adetailer_dir, 'Adetailer',   False),
        (clip_dir,      'Clip',        False),
        (unet_dir,      'Unet',        False),
        (vision_dir,    'Vision',      False),
        (encoder_dir,   'Encoder',     False),
        (diffusion_dir, 'Diffusion',   False),
    ]
    files = [
        {'local': local, 'gdrive': f"{GD_FILES}/{gdir}", 'flat': flat}
        for local, gdir, flat in files_base
    ]
    files.append({
        'local': extension_dir,
        'gdrive': f"{GD_FILES}/{'Custom-Nodes' if is_comfy else 'Extensions'}"
    })

    # Output structure
    outputs = [{
        'local': output_dir,
        'gdrive': f"{GD_OUTPUTS}/{ui}",
        'direct': True
    }]

    # Config structure
    configs_base = f"{GD_CONFIGS}/{ui}"
    if is_comfy:
        user_default = f"{WEBUI}/user/default"
        user_manager = f"{WEBUI}/user/__manager"
        configs = [
            {'local': f"{user_default}/comfy.settings.json", 'gdrive': f"{configs_base}/comfy.settings.json",
                'type': 'file', 'name': 'ComfyUI Settings'},
            {'local': f"{user_manager}/config.ini", 'gdrive': f"{configs_base}/comfy-manager-config.ini",
                'type': 'file', 'name': 'Comfy Manager Config'},
            {'local': f"{user_default}/workflows", 'gdrive': f"{configs_base}/workflows",
                'type': 'dir', 'name': 'Workflows'},
        ]
    else:
        configs = [
            {'local': f"{WEBUI}/config.json", 'gdrive': f"{configs_base}/config.json",
                'type': 'file', 'name': 'WebUI Config'},
            {'local': f"{WEBUI}/ui-config.json", 'gdrive': f"{configs_base}/ui-config.json",
                'type': 'file', 'name': 'UI Config'},
        ]

    return {'files': files, 'outputs': outputs, 'configs': configs}

# --- Remove symlinks function ---
def _remove_symlink(item, restore=False, category='files'):
    """Remove symlink(s) defined by item, optionally restore from GDrive; return count removed"""
    local = Path(item['local'])
    gdrive = Path(item['gdrive'])
    count = 0

    # Special file handling (flat and GDrive subfolder)
    if category == 'files':
        if item.get('flat', False):
            if local.exists():
                gdrive_resolved = str(gdrive.resolve())
                for file in local.iterdir():
                    if file.is_symlink() and str(file.resolve()).startswith(gdrive_resolved):
                        file.unlink()
                        count += 1
                        if GDRIVE_LOG:
                            print(f"{COL.R}🗑️ Unlinked: {COL.lB}{file}{COL.X}")
        else:
            symlink_path = local / 'GDrive'
            if symlink_path.is_symlink():
                symlink_path.unlink()
                count += 1
                if GDRIVE_LOG:
                    print(f"{COL.R}🗑️ Removed symlink: {COL.lB}{symlink_path}{COL.X}")

        return count

    # General logic for outputs and configs
    if not local.is_symlink():
        return count

    is_dir = (category == 'outputs') or (item.get('type') == 'dir')
    name = item.get('name', category.capitalize())

    local.unlink()
    count += 1

    # Restore from GDrive if necessary and if the file/folder exists
    if restore and gdrive.exists():
        if is_dir:
            shutil.copytree(gdrive, local, dirs_exist_ok=True)
        else:
            shutil.copy2(gdrive, local)
        if GDRIVE_LOG:
            icon = '📁' if is_dir else '📄'
            print(f"{COL.Y}{icon} Restored [{name}]: {COL.lB}{local.name}{COL.X} ← {COL.B}GDrive{COL.X}")
    else:
        if GDRIVE_LOG:
            type_label = 'output' if category == 'outputs' else 'config'
            print(f"{COL.R}🗑️ Removed {type_label} symlink: {COL.lB}{local}{COL.X}")

    return count

# --- Сreate symlinks functions ---
def _create_files_symlink(item):
    """Create flat or GDrive-subfolder symlinks for model files/extensions"""
    local = Path(item['local'])
    gdrive = Path(item['gdrive'])
    local.mkdir(parents=True, exist_ok=True)
    gdrive.mkdir(parents=True, exist_ok=True)

    if item.get('flat', False):
        for file in gdrive.iterdir():
            if file.name == '.ipynb_checkpoints':
                continue
            target = local / file.name
            if target.is_symlink():
                target.unlink()
            elif target.exists():
                continue
            target.symlink_to(file)
            if GDRIVE_LOG:
                print(f"{COL.G}🔗 Linked: {COL.lB}{target}{COL.X} → {COL.G}{file}{COL.X}")
    else:
        symlink_path = local / 'GDrive'
        if symlink_path.exists() and not symlink_path.is_symlink():
            _merge_dirs(symlink_path, gdrive, label='Migrated')
        _remove_path(symlink_path)
        local.mkdir(parents=True, exist_ok=True)
        if not symlink_path.exists():
            symlink_path.symlink_to(gdrive, target_is_directory=True)
            if GDRIVE_LOG:
                print(f"{COL.G}🔗 Symlink: {COL.lB}{symlink_path}{COL.X} → {COL.G}{gdrive}{COL.X}")

def _create_outputs_symlink(item):
    """Create a direct symlink from output_dir to GDrive outputs folder, migrating existing content"""
    local = Path(item['local'])
    gdrive = Path(item['gdrive'])
    local.parent.mkdir(parents=True, exist_ok=True)
    gdrive.parent.mkdir(parents=True, exist_ok=True)

    if local.exists() and not local.is_symlink():
        _merge_dirs(local, gdrive, label='Migrated')
    _remove_path(local)
    if not local.exists():
        local.symlink_to(gdrive, target_is_directory=True)
        if GDRIVE_LOG:
            print(f"{COL.G}🔗 Direct symlink: {COL.lB}{local}{COL.X} → {COL.G}{gdrive}{COL.X}")

def _create_config_symlink(item):
    """Create a symlink for a config file or folder, backing up local file if GDrive missing"""
    local = Path(item['local'])
    gdrive = Path(item['gdrive'])
    local.parent.mkdir(parents=True, exist_ok=True)
    gdrive.parent.mkdir(parents=True, exist_ok=True)

    ctype = item.get('type', 'file')
    name = item.get('name', 'Config')

    if ctype == 'file':
        if local.exists() and local.is_file() and not gdrive.exists():
            shutil.copy2(local, gdrive)
            if GDRIVE_LOG:
                print(f"{COL.Y}📄 Backed up [{name}]: {COL.lB}{local.name}{COL.X} → {COL.G}GDrive{COL.X}")
        _remove_path(local)
    else:
        if local.exists() and not local.is_symlink():
            _merge_dirs(local, gdrive, label=f"Merged [{name}]")
        else:
            _remove_path(local)
    if not local.exists():
        local.symlink_to(gdrive, target_is_directory=(ctype == 'dir'))
        if GDRIVE_LOG:
            icon = '📁' if ctype == 'dir' else '📄'
            print(f"{COL.G}{icon} Config symlink [{name}]: {COL.lB}{local.name}{COL.X} → {COL.G}GDrive{COL.X}")

# --- Main entry ---
def _sync_category(items, selected, create_func, remove_func, restore_on_remove=True, category='files'):
    """Apply create_func if selected, else remove_func with restore flag; return count of removals"""
    count = 0
    if selected:
        for item in items:
            create_func(item)
    else:
        for item in items:
            count += remove_func(item, restore=restore_on_remove, category=category)
    return count

def handle_gdrive(mount_flag, ui='A1111', *, sync_files=False, sync_outputs=False, sync_configs=False):
    """Mount/unmount GDrive and manage symlinks for selected categories"""
    _cleanup_ipynb_checkpoints(GD_BASE)
    drive_mounted = os.path.exists('/content/drive/MyDrive')

    config = _build_sync_config(ui)

    # Unmount logic
    if not mount_flag:
        if drive_mounted:
            try:
                print(f"{COL.Y}⏳ Отключение Google Drive...{COL.X}", end='')
                if GDRIVE_LOG:
                    print()
                removed_files   = _sync_category(config['files'],   False, None, _remove_symlink, restore_on_remove=False, category='files')
                removed_outputs = _sync_category(config['outputs'], False, None, _remove_symlink, restore_on_remove=True,  category='outputs')
                removed_configs = _sync_category(config['configs'], False, None, _remove_symlink, restore_on_remove=True,  category='configs')
                total_removed = removed_files + removed_outputs + removed_configs
                with capture.capture_output():
                    drive.flush_and_unmount()
                    os.system('rm -rf /content/drive')
                print(f"\r{COL.G}✅ Google Drive успешно отключен!{COL.X}")
                if total_removed:
                    print(f"{COL.B}💾 Конфигурации восстановлены, удалено {total_removed} симлинков{COL.X}")
            except Exception as e:
                print(f"\r{COL.R}❌ Unmount error:{COL.X} {str(e)}")
        return

    # Mount logic
    if not drive_mounted:
        try:
            print(f"{COL.Y}⏳ Подключение Google Drive...{COL.X}", end='')
            with capture.capture_output():
                drive.mount('/content/drive')
            print(f"\r{COL.G}💿 Google Drive успешно подключен!{COL.X}")
        except Exception as e:
            print(f"\r{COL.R}❌ Mounting failed:{COL.X} {str(e)}")
            return
    else:
        print(f"{COL.G}🎉 Google Drive подключен~{COL.X}")

    try:
        # Create base directories
        dirs_to_create = [GD_BASE]
        if sync_files:   dirs_to_create.append(GD_FILES)
        if sync_outputs: dirs_to_create.append(GD_OUTPUTS)
        if sync_configs: dirs_to_create.append(GD_CONFIGS)
        for dir in dirs_to_create:
            Path(dir).mkdir(parents=True, exist_ok=True)

        # Active/Inactive summary
        active   = [n for flag, n in [(sync_files, 'Files'), (sync_outputs, 'Outputs'), (sync_configs, 'Configs')] if flag]
        inactive = [n for flag, n in [(sync_files, 'Files'), (sync_outputs, 'Outputs'), (sync_configs, 'Configs')] if not flag]
        if active:
            active_str   = ', '.join(f"{COL.G}{n}{COL.X}" for n in active)
            inactive_str = ', '.join(f"{COL.Y}{n}{COL.X}" for n in inactive) if inactive else ''
            print(f"{COL.B}📋 GDrive Синхронизация — активно: {active_str}" + (f" | неактивно: {inactive_str}" if inactive else '') + COL.X)
        else:
            print(f"{COL.Y}⚠️ GDrive подключен, но категории не выбраны — ничего не будет связано.{COL.X}")
            return

        # Sync each category
        _sync_category(config['files'],   sync_files,   _create_files_symlink,   _remove_symlink, restore_on_remove=False, category='files')
        _sync_category(config['outputs'], sync_outputs, _create_outputs_symlink, _remove_symlink, restore_on_remove=True,  category='outputs')
        _sync_category(config['configs'], sync_configs, _create_config_symlink,  _remove_symlink, restore_on_remove=True,  category='configs')

        print(f"{COL.G}✅ Синхронизация завершена!{COL.X}")
    except Exception as e:
        print(f"{COL.R}❌ Sync error:{COL.X} {e}")

handle_gdrive(
    mountGDrive, UI,
    sync_files=GD_sync_files,
    sync_outputs=GD_sync_outputs,
    sync_configs=GD_sync_configs
)


# ======================= DOWNLOADING ======================

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f">> An error occurred in {func.__name__}: {str(e)}")
    return wrapper

# Get XL or 1.5 models list
## model_list | vae_list | controlnet_list
model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
with open(f"{SCRIPTS}/{model_files}") as f:
    exec(f.read())

## Downloading model and stuff | oh~ Hey! If you're freaked out by that code too, don't worry, me too!
print('📦 Скачивание моделей и прочего...', end='')

extension_repo = []
PREFIX_MAP = {
    # prefix : (dir_path , short-tag)
    'model': (model_dir, '$ckpt'),
    'vae': (vae_dir, '$vae'),
    'lora': (lora_dir, '$lora'),
    'embed': (embed_dir, '$emb'),
    'extension': (extension_dir, '$ext'),
    'adetailer': (adetailer_dir, '$ad'),
    'control': (control_dir, '$cnet'),
    'upscale': (upscale_dir, '$ups'),
    # Other
    'clip': (clip_dir, '$clip'),
    'unet': (unet_dir, '$unet'),
    'vision': (vision_dir, '$vis'),
    'encoder': (encoder_dir, '$enc'),
    'diffusion': (diffusion_dir, '$diff'),
    'config': (config_dir, '$cfg')
}
for dir_path, _ in PREFIX_MAP.values():
    os.makedirs(dir_path, exist_ok=True)

''' Formatted Info Output '''

def _center_text(text, terminal_width=45):
    padding = (terminal_width - len(text)) // 2
    return f"{' ' * padding}{text}{' ' * padding}"

def format_output(url, dst_dir, file_name, image_url=None, image_name=None):
    """Formats and prints download details with colored text"""
    info = '[NONE]'
    if file_name:
        info = _center_text(f"[{file_name.rsplit('.', 1)[0]}]")
    if not file_name and 'drive.google.com' in url:
      info = _center_text('[GDrive]')

    sep_line = '───' * 20

    print()
    print(f"{COL.G}{sep_line}{COL.lB}{info}{COL.G}{sep_line}{COL.X}")
    print(f"{COL.Y}{'URL:':<12}{COL.X}{url}")
    print(f"{COL.Y}{'SAVE DIR:':<12}{COL.B}{dst_dir}")
    print(f"{COL.Y}{'FILE NAME:':<12}{COL.B}{file_name}{COL.X}")
    if 'civitai' in url and image_url:
        # print(f"{COL.G}{'[Preview]:':<12}{COL.X}{image_name} → {image_url}")
        print(f"{COL.G}{'[Preview]:':<12}{COL.X}{image_url}")
    print()

''' Main Download Code '''

def _clean_url(url):
    url_cleaners = {
        'huggingface.co': lambda u: u.replace('/blob/', '/resolve/').split('?')[0],
        'github.com': lambda u: u.replace('/blob/', '/raw/')
    }
    for domain, cleaner in url_cleaners.items():
        if domain in url:
            return cleaner(url)
    return url

def _extract_filename(url):
    if match := re.search(r'\[(.*?)\]', url):
        return match.group(1)
    if any(d in urlparse(url).netloc for d in [*CIVITAI_DOMAINS, 'drive.google.com']):
        return None
    return Path(urlparse(url).path).name

# Download Core

def _process_download_link(link):
    """Processes a download link, splitting prefix, URL, and filename"""
    link = _clean_url(link)
    if ':' in link:
        prefix, path = link.split(':', 1)
        if prefix in PREFIX_MAP:
            return prefix, re.sub(r'\[.*?\]', '', path), _extract_filename(path)
    return None, link, None

@handle_errors
def download(line):
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
            except Exception as e:
                print(f"\n> Download error: {e}")
        else:
            url, dst_dir, file_name = url.split()
            manual_download(url, dst_dir, file_name)

@handle_errors
def manual_download(url, dst_dir, file_name=None):
    image_url, image_name = None, None

    if 'civitai' in url:
        api = CivitAiAPI(civitai_token)
        if not (data := api.validate_download(url, file_name)):
            return

        url, file_name = data.download_url, data.file_name          # Download_URL, File_Name
        image_url, image_name = data.image_url, data.image_name     # Image_URL, Image_Name

        ## Preview will be downloaded automatically via [CivitAI-Extension]
        # Download preview images (only for ComfyUI)
        if UI == 'ComfyUI' and image_url and image_name:
            m_download(f"{image_url} {dst_dir} {image_name}")

    # Formatted info output
    format_output(url.split('?')[0], dst_dir, file_name, image_url, image_name)

    # Downloading Files | With Logs and Auto Unpacking ZIP Archives
    m_download(f"{url} {dst_dir} {file_name or ''}", verbose=True, debug=False, unzip=True)

''' SubModels - Added URLs '''

# Separation of merged numbers
def _parse_selection_numbers(num_str, max_num):
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

def handle_submodels(selection, num_selection, model_dict, dst_dir, base_url, inpainting_model=False):
    selected = []

    keys = list(model_dict)
    numbered = {f"{i}. {k}": v for i, (k, v) in enumerate(model_dict.items(), 1)}

    def add_by_key(key):
        if key in model_dict:
            selected.extend(model_dict[key])

    # Selection
    if selection.lower() != 'none':
        if selection == 'ALL':
            selected = sum(model_dict.values(), [])
        else:
            found = find_model_by_partial_name(selection, numbered) or selection
            original = re.sub(r'^\d+\.\s*', '', found)
            add_by_key(original)

        if num_selection:
            for num in _parse_selection_numbers(num_selection, len(keys)):
                if 1 <= num <= len(keys):
                    add_by_key(keys[num - 1])

    # Deduplicate + Filter
    unique = {}
    for m in selected:
        name = m.get('name') or os.path.basename(m['url'])
        if not inpainting_model and 'inpainting' in name:
            continue
        unique[name] = {    # Note: `name` is an optional parameter
            'url': m['url'],
            'dst_dir': m.get('dst_dir', dst_dir),
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

''' File.txt - added urls '''

def _process_lines(lines):
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

    return ', '.join(result_urls) if result_urls else ''

def process_file_downloads(file_urls, additional_lines=None):
    """Reads URLs from files/HTTP sources"""
    lines = []

    if additional_lines:
        lines.extend(additional_lines.splitlines())

    for source in file_urls:
        if source.startswith('http'):
            try:
                response = requests.get(_clean_url(source))
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
urls_sources = (Model_url, Vae_url, LoRA_url, Embedding_url, Extensions_url, ADetailer_url)
file_urls = [f"{f}.txt" if not f.endswith('.txt') else f for f in custom_file_urls.replace(',', '').split()] if custom_file_urls else []

# p -> prefix ; u -> url | Remember: don't touch the prefix!
prefixed_urls = [f"{p}:{u}" for p, u in zip(PREFIX_MAP, urls_sources) if u for u in u.replace(',', '').split()]
line += ', '.join(prefixed_urls + [process_file_downloads(file_urls, empowerment_output)])

if detailed_download == 'on':
    print(f"\n\n{COL.Y}# ====== Подробная Загрузка ====== #{COL.X}")
    download(line)
    print(f"\n{COL.Y}# =============================== #\n{COL.X}")
else:
    with capture.capture_output():
        download(line)

print('\r🏁 Скачивание Завершено!' + ' '*15)


## Install of Custom extensions
extension_type = 'нодов' if UI == 'ComfyUI' else 'расширений'

if extension_repo:
    print(f"✨ Установка кастомных {extension_type}...", end='')
    with capture.capture_output():
        for repo_url, repo_name in extension_repo:
            m_clone(f"{repo_url} {extension_dir} {repo_name}")
    print(f"\r📦 Установлено '{len(extension_repo)}' кастомных {extension_type}!")


# === SPECIAL ===
## Sorting models `bbox` and `segm` | Only ComfyUI
if UI == 'ComfyUI':
    dirs = {'segm': '-seg.pt', 'bbox': None}
    for d in dirs:
        os.makedirs(os.path.join(adetailer_dir, d), exist_ok=True)

    for filename in os.listdir(adetailer_dir):
        src = os.path.join(adetailer_dir, filename)

        if os.path.isfile(src) and filename.endswith('.pt'):
            dest_dir = 'segm' if filename.endswith('-seg.pt') else 'bbox'
            dest = os.path.join(adetailer_dir, dest_dir, filename)

            if os.path.exists(dest):
                os.remove(src)
            else:
                shutil.move(src, dest)

## Copy dir from GDrive to extension_dir (if enabled)
if mountGDrive and GD_sync_files:
    gdrive_path = os.path.join(extension_dir, 'GDrive')
    if os.path.isdir(gdrive_path):
        for folder in os.listdir(gdrive_path):
            src = os.path.join(gdrive_path, folder)
            dst = os.path.join(extension_dir, folder)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        os.unlink(gdrive_path)


## List Models and stuff
ipyRun('run', f"{SCRIPTS}/download-result.py")