# ~ download.py | by ANXETY ~

from Manager import m_download, m_clone   # Every Download | Clone
from CivitaiAPI import CivitAiAPI         # CivitAI API
from webui_utils import *                 # WEBUI
import json_utils as js                   # JSON

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
    PYTHON_VERSION = '3.11' if UI in ['Classic', 'Neo'] else '3.10'
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
        'ngrok': "wget -qO ngrok-v3-stable-linux-amd64.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz; tar -xzf ngrok-v3-stable-linux-amd64.tgz -C /usr/bin; rm -f ngrok-v3-stable-linux-amd64.tgz"
    }

    print('💿 Installing the libraries will take a bit of time.')
    install_packages(install_lib)
    clear_output()
    js.update(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

# Install VENV
current_ui = js.read(SETTINGS_PATH, 'WEBUI.current')
latest_ui = js.read(SETTINGS_PATH, 'WEBUI.latest')

# Determine whether to reinstall venv
venv_needs_reinstall = (
    not VENV.exists()  # venv is missing
    # Check UIs change (Classic/Neo <-> other, ComfyUI <-> other)
    or (latest_ui == 'Neo') != (current_ui == 'Neo')
    or (latest_ui == 'Classic') != (current_ui == 'Classic')
    or (latest_ui == 'ComfyUI') != (current_ui == 'ComfyUI')
)

if not SKIP_INSTALL_VENV and venv_needs_reinstall:
    if VENV.exists():
        print('🗑️ Remove old venv...')
        shutil.rmtree(VENV)
        clear_output()

    venv_config = {
        'Neo':     (f"{HF_REPO_URL}/python31312-venv-torch2100-cu128-C-Neo.tar.lz4", 'Neo • 3.13.12'),
        'Classic': (f"{HF_REPO_URL}/python31113-venv-torch260-cu124-C-Classic.tar.lz4", 'Classic • 3.11.13'),
        'ComfyUI': (f"{HF_REPO_URL}/python31018-venv-torch260-cu124-C-ComfyUI.tar.lz4", 'ComfyUI • 3.10.18'),
        'default': (f"{HF_REPO_URL}/python31018-venv-torch260-cu124-C-fa.tar.lz4", 'Default • 3.10.18')
    }
    venv_url, venv_version = venv_config.get(current_ui, venv_config['default'])

    print(f"♻️ Installing VENV: {COL.B}{venv_version}{COL.X}, this may take a while...")
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
        print('🚚 Unpacking ADetailer model cache...')

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
    print(f"⌚ Unpacking Stable Diffusion... | WEBUI: {COL.B}{UI}{COL.X}", end='')

    ipyRun('run', f"{SCRIPTS}/webui-installer.py")
    handle_setup_timer(WEBUI, start_timer)		# Setup timer (for timer-extensions)

    install_time = time.time() - start_install
    minutes, seconds = divmod(int(install_time), 60)
    print(f"\r🚀 Unpacking {COL.B}{UI}{COL.X} complete! {minutes:02}:{seconds:02} ⚡" + ' '*25)

else:
    print(f"🔧 Current WebUI: {COL.B}{UI}{COL.X}")

    timer_env = handle_setup_timer(WEBUI, start_timer)
    elapsed_time = str(timedelta(seconds=time.time() - timer_env)).split('.')[0]
    print(f"⌚️ Session duration: {COL.Y}{elapsed_time}{COL.X}")


## Changes extensions and WebUi
if latest_webui or latest_extensions:
    action = 'WebUI and Extensions' if latest_webui and latest_extensions else ('WebUI' if latest_webui else 'Extensions')
    print(f"⌚️ Update {action}...", end='')
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

    print(f"\r✨ Update {action} Completed!")


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
    print(f"\r✅ Switch complete! Now at: {COL.B}{commit_hash}{COL.X}")


# === Google Drive Mounting | EXCLUSIVE for Colab ===
from google.colab import drive

mountGDrive = js.read(SETTINGS_PATH, 'mountGDrive')  # mount/unmount flag
GD_BASE = '/content/drive/MyDrive/sdAIgen'
GD_FILES = f"{GD_BASE}/files"
GD_OUTPUTS = f"{GD_BASE}/outputs"
GD_CONFIGS = f"{GD_BASE}/configs"

# Helper Functions
def fs_remove(path: Path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)

def merge_dirs(src, dst, label='', log=False):
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name == '.ipynb_checkpoints':
            continue
        fs_remove(dst / item.name)
        shutil.move(str(item), str(dst))
    shutil.rmtree(src)

    if log:
        print(f"{COL.Y}📦 {label}: {COL.lB}{src}{COL.X} → {COL.G}{dst}{COL.X}")

def cleanup_ipynb_checkpoints(base_path):
    for root, dirs, _ in os.walk(base_path):
        if '.ipynb_checkpoints' in dirs:
            chk = Path(root) / '.ipynb_checkpoints'
            shutil.rmtree(chk, ignore_errors=True)

# Main Logic
def build_symlink_config(ui: str) -> dict:
    """Build symlink configuration based on UI type"""
    is_comfy = ui == 'ComfyUI'

    # Files structure | Local <-> GDrive
    base_files = [
        (model_dir,     'Checkpoints'),
        (vae_dir,       'VAE'),
        (lora_dir,      'Lora'),
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
        {'local': local, 'gdrive': f"{GD_FILES}/{gdir}"}
        for local, gdir in base_files
    ]
    _files.append({
        'local': extension_dir,
        'gdrive': f"{GD_FILES}/{'Custom-Nodes' if is_comfy else 'Extensions'}"
    })

    # Output structure
    outputs_base = f"{GD_OUTPUTS}/{ui}"
    _outputs = [{
        'local': output_dir,
        'gdrive': outputs_base,
        'direct_link': True
    }]

    # Config structure
    config_base = f"{GD_CONFIGS}/{ui}"
    if is_comfy:
        # ComfyUI specific config structure
        user_default = f"{WEBUI}/user/default"
        user_manager = f"{WEBUI}/user/__manager"
        _configs = [
            {
                'local': f"{user_default}/comfy.settings.json",
                'gdrive': f"{config_base}/comfy.settings.json",
                'type': 'file',
                'name': 'ComfyUI Settings'
            },
            {
                'local': f"{user_manager}/config.ini",
                'gdrive': f"{config_base}/comfy-manager-config.ini",
                'type': 'file',
                'name': 'Comfy Manager Config'
            },
            {
                'local': f"{user_default}/workflows",
                'gdrive': f"{config_base}/workflows",
                'type': 'dir',
                'name': 'Workflows'
            }
        ]
    else:
        # A1111/Forge config structure
        _configs = [
            {
                'local': f"{WEBUI}/config.json",
                'gdrive': f"{config_base}/config.json",
                'type': 'file',
                'name': 'WebUI Config'
            },
            {
                'local': f"{WEBUI}/ui-config.json",
                'gdrive': f"{config_base}/ui-config.json",
                'type': 'file',
                'name': 'UI Config'
            }
        ]

    return {
        'files': _files,
        'outputs': _outputs,
        'configs': _configs
    }

def create_symlink(src, dst, symlink_name='GDrive', direct_link=False, log=False):
    """Create symlink with optional migration of existing content"""
    try:
        src = Path(src)
        dst = Path(dst)
        dst.mkdir(parents=True, exist_ok=True)

        if direct_link:
            # Direct link mode: replace entire directory with symlink
            if src.exists() and src.is_dir() and not src.is_symlink():
                merge_dirs(src, dst, label='Migrated', log=log)

            if src.is_symlink():
                src.unlink()
            src.parent.mkdir(parents=True, exist_ok=True)

            # Create direct symlink
            if not src.exists():
                src.symlink_to(dst, target_is_directory=True)
                if log:
                    print(f"{COL.G}🔗 Direct symlink: {COL.lB}{src}{COL.X} → {COL.G}{dst}{COL.X}")
        else:
            # Subfolder mode: create GDrive folder inside src
            symlink_path = src / symlink_name

            # Migrate contents if GDrive subfolder exists and is real dir
            if symlink_path.exists() and not symlink_path.is_symlink():
                merge_dirs(symlink_path, dst, label='Migrated', log=log)

            fs_remove(symlink_path)
            src.mkdir(parents=True, exist_ok=True)

            # Create subfolder symlink
            if not symlink_path.exists():
                symlink_path.symlink_to(dst, target_is_directory=True)
                if log:
                    print(f"{COL.G}🔗 Symlink: {COL.lB}{symlink_path}{COL.X} → {COL.G}{dst}{COL.X}")
    except Exception as e:
        print(f"{COL.R}❌ Error creating symlink:{COL.X} {src} - {str(e)}")

def create_config_symlink(local_path, gdrive_path, config_type='file', config_name='Config', log=False):
    """Create symlink for config files or directories"""
    try:
        local_path = Path(local_path)
        gdrive_path = Path(gdrive_path)
        gdrive_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if config_type == 'file':
            # For files: backup local to gdrive if gdrive doesn't exist
            if local_path.exists() and local_path.is_file() and not gdrive_path.exists():
                shutil.copy2(local_path, gdrive_path)
                if log:
                    print(f"{COL.Y}📄 Backed up [{config_name}]: {COL.lB}{local_path.name}{COL.X} → {COL.G}GDrive{COL.X}")

            if local_path.exists():
                local_path.unlink()
        else:
            # For directories: merge content to gdrive
            if local_path.exists() and local_path.is_dir() and not local_path.is_symlink():
                merge_dirs(
                    local_path, gdrive_path,
                    label=f"Merged [{config_name}]", log=log
                )
            elif local_path.exists() and not local_path.is_symlink():
                fs_remove(local_path)

        if local_path.is_symlink():
            local_path.unlink()

        # Create new symlink
        if not local_path.exists():
            is_dir = (config_type == 'dir')
            local_path.symlink_to(gdrive_path, target_is_directory=is_dir)
            if log:
                icon = '📁' if is_dir else '📄'
                print(f"{COL.G}{icon} Config symlink [{config_name}]: {COL.lB}{local_path.name}{COL.X} → {COL.G}GDrive{COL.X}")
    except Exception as e:
        print(f"{COL.R}❌ Error [{config_name}]:{COL.X} {local_path.name} - {str(e)}")

def restore_from_symlink(local_path, gdrive_path, config_type='file', config_name='Config', log=False):
    """Restore local files/directories from Google Drive before unmounting"""
    try:
        local_path = Path(local_path)
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
                print(f"{COL.Y}{icon} Restored [{config_name}]: {COL.lB}{local_path.name}{COL.X} ← {COL.B}GDrive{COL.X}")
    except Exception as e:
        print(f"{COL.R}❌ Error restoring [{config_name}]:{COL.X} {str(e)}")

def remove_all_symlinks(ui='A1111', restore_configs=False, log=False):
    """Remove all symlinks created by handle_gdrive"""
    config = build_symlink_config(ui)
    removed = 0

    def _remove(path, name=None):
        nonlocal removed
        if path.is_symlink():
            path.unlink()
            removed += 1
            if log:
                label = f" [{name}]" if name else ''
                print(f"{COL.R}🗑️ Removed{label}: {COL.lB}{path}{COL.X}")

    # Remove files symlinks (GDrive folders)
    for cfg in config['files']:
        _remove(Path(cfg['local']) / 'GDrive')

    # Restore and remove output symlinks
    for cfg in config['outputs']:
        local = Path(cfg['local'])
        gdrive = Path(cfg['gdrive'])

        if restore_configs:
            restore_from_symlink(
                local,
                gdrive,
                config_type='dir',
                config_name='Outputs',
                log=log
            )
        else:
            _remove(local)

    # Restore and remove config symlinks
    for cfg in config['configs']:
        local = Path(cfg['local'])
        gdrive = Path(cfg['gdrive'])
        ctype = cfg.get('type', 'file')
        name  = cfg.get('name', 'Config')

        if restore_configs:
            restore_from_symlink(
                local,
                gdrive,
                config_type=ctype,
                config_name=name,
                log=log
            )
        else:
            _remove(local)

    return removed

def handle_gdrive(mount_flag, ui='A1111', log=False):
    """Main handler for Google Drive mounting and symlink setup"""
    def _ensure_dirs(*paths):
        for p in paths:
            os.makedirs(p, exist_ok=True)

    cleanup_ipynb_checkpoints(GD_BASE)   # Remove Jupyter shits

    if not mount_flag:
        # Unmount logic
        if os.path.exists('/content/drive/MyDrive'):
            try:
                print(f"{COL.Y}⏳ Unmounting Google Drive...{COL.X}", end='')
                if log: print()

                removed = remove_all_symlinks(ui, restore_configs=True, log=log)

                with capture.capture_output():
                    drive.flush_and_unmount()
                    os.system('rm -rf /content/drive')

                print(f"\r{COL.G}✅ Google Drive unmounted successfully!{COL.X}")
                if removed:
                    print(f"{COL.B}💾 Configs restored and {removed} symlinks removed{COL.X}")
            except Exception as e:
                print(f"\r{COL.R}❌ Unmount error:{COL.X} {str(e)}")
        return

    # Mount logic
    if not os.path.exists('/content/drive/MyDrive'):
        try:
            print(f"{COL.Y}⏳ Mounting Google Drive...{COL.X}", end='')
            with capture.capture_output():
                drive.mount('/content/drive')
            print(f"\r{COL.G}💿 Google Drive mounted successfully!{COL.X}")
        except Exception as e:
            print(f"\r{COL.R}❌ Mounting failed:{COL.X} {str(e)}")
            return
    else:
        print(f"{COL.G}🎉 Google Drive is connected~{COL.X}")

    try:
        # Create base directories
        _ensure_dirs(GD_BASE, GD_FILES, GD_OUTPUTS, GD_CONFIGS)

        config = build_symlink_config(ui)

        # Create files symlinks
        if log:
            print(f"\n{COL.B}━━━ Files Symlinks ━━━{COL.X}")
        for cfg in config['files']:
            create_symlink(
                cfg['local'],
                cfg['gdrive'],
                log=log
            )

        # Create output symlinks (direct)
        if log:
            print(f"\n{COL.B}━━━ Output Symlinks ━━━{COL.X}")
        for cfg in config['outputs']:
            create_symlink(
                cfg['local'],
                cfg['gdrive'],
                direct_link=cfg.get('direct_link', True),
                log=log
            )

        # Create config symlinks
        if log:
            print(f"\n{COL.B}━━━ Config Symlinks ━━━{COL.X}")
        for cfg in config['configs']:
            create_config_symlink(
                cfg['local'],
                cfg['gdrive'],
                cfg.get('type', 'file'),
                cfg.get('name', 'Config'),
                log=log
            )

        print(f"{COL.G}✅ All symlinks created successfully!{COL.X}")
    except Exception as e:
        print(f"{COL.R}❌ Setup error:{COL.X} {str(e)}")

handle_gdrive(mountGDrive, ui=UI, log=GDRIVE_LOG)


# ======================= DOWNLOADING ======================

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f">>An error occurred in {func.__name__}: {str(e)}")
    return wrapper

# Get XL or 1.5 models list
## model_list | vae_list | controlnet_list
model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
with open(f"{SCRIPTS}/{model_files}") as f:
    exec(f.read())

## Downloading model and stuff | oh~ Hey! If you're freaked out by that code too, don't worry, me too!
print('📦 Downloading models and stuff...', end='')

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
        print(f"{COL.G}{'[Preview]:':<12}{COL.X}{image_name} → {image_url}")
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
    if any(d in urlparse(url).netloc for d in ['civitai.com', 'drive.google.com']):
        return None
    return Path(urlparse(url).path).name

# Download Core

@handle_errors
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
    clean_url = url
    image_url, image_name = None, None

    if 'civitai' in url:
        api = CivitAiAPI(civitai_token)
        if not (data := api.validate_download(url, file_name)):
            return

        model_type, file_name = data.model_type, data.model_name    # Model_Type, Model_Name
        clean_url, url = data.clean_url, data.download_url          # Clean_URL, Download_URL
        image_url, image_name = data.image_url, data.image_name     # Image_URL, Image_Name

        ## Preview will be downloaded automatically via [CivitAI-Extension]
        # Download preview images (Only  for ComfyUI)
        if UI == 'ComfyUI' and image_url and image_name:
            m_download(f"{image_url} {dst_dir} {image_name}")

    elif any(s in url for s in ('github', 'huggingface.co')):
        if file_name and '.' not in file_name:
            file_name += f".{clean_url.split('.')[-1]}"

    # Formatted info output
    format_output(clean_url, dst_dir, file_name, image_url, image_name)

    # Downloading Files | With Logs and Auto Unpacking ZIP Archives
    m_download(f"{url} {dst_dir} {file_name or ''}", log=True, unzip=True)

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
    print(f"\n\n{COL.Y}# ====== Detailed Download ====== #{COL.X}")
    download(line)
    print(f"\n{COL.Y}# =============================== #\n{COL.X}")
else:
    with capture.capture_output():
        download(line)

print('\r🏁 Download Complete!' + ' '*15)


## Install of Custom extensions
extension_type = 'nodes' if UI == 'ComfyUI' else 'extensions'

if extension_repo:
    print(f"✨ Installing custom {extension_type}...", end='')
    with capture.capture_output():
        for repo_url, repo_name in extension_repo:
            m_clone(f"{repo_url} {extension_dir} {repo_name}")
    print(f"\r📦 Installed '{len(extension_repo)}' custom {extension_type}!")


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
if mountGDrive:
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