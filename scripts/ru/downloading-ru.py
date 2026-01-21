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
    PKG = str(VENV / f'lib/{PYTHON_VERSION }/site-packages')

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
    # Check UIs change (Classic/Neo <-> other, ComfyUI <-> other)
    or (latest_ui == 'Neo') != (current_ui == 'Neo')
    or (latest_ui == 'Classic') != (current_ui == 'Classic')
    or (latest_ui == 'ComfyUI') != (current_ui == 'ComfyUI')
)

if not SKIP_INSTALL_VENV and venv_needs_reinstall:
    if VENV.exists():
        print('🗑️ Удаление старого venv...')
        shutil.rmtree(VENV)
        clear_output()

    venv_config = {
        'Neo':     (f"{HF_REPO_URL}/python31113-venv-torch280-cu126-C-Neo.tar.lz4", 'Neo • 3.11.13'),
        'Classic': (f"{HF_REPO_URL}/python31113-venv-torch260-cu124-C-Classic.tar.lz4", 'Classic • 3.11.13'),
        'ComfyUI': (f"{HF_REPO_URL}/python31018-venv-torch260-cu124-C-ComfyUI.tar.lz4", 'ComfyUI • 3.10.18'),
        'default': (f"{HF_REPO_URL}/python31018-venv-torch260-cu124-C-fa.tar.lz4", 'Default • 3.10.18')
    }
    venv_url, venv_version = venv_config.get(current_ui, venv_config['default'])

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


# === Google Drive Mounting | EXCLUSIVE for Colab ===
from google.colab import drive

mountGDrive = js.read(SETTINGS_PATH, 'mountGDrive')  # mount/unmount flag
GD_BASE = '/content/drive/MyDrive/sdAIgen'

def build_symlink_config(ui: str) -> list[dict]:
    """Build symlink configuration based on UI type"""
    is_comfy = ui == 'ComfyUI'
    return [
        {'local': model_dir,      'gdrive': 'Checkpoints'},
        {'local': vae_dir,        'gdrive': 'VAE'},
        {'local': lora_dir,       'gdrive': 'Lora'},
        {'local': embed_dir,      'gdrive': 'Embeddings'},
        {'local': extension_dir,  'gdrive': 'CustomNodes' if is_comfy else 'Extensions'},
        {'local': control_dir,    'gdrive': 'ControlNet'},
        {'local': upscale_dir,    'gdrive': 'Upscale'},
        # Others
        {'local': adetailer_dir,  'gdrive': 'Adetailer'},
        {'local': clip_dir,       'gdrive': 'Clip'},
        {'local': unet_dir,       'gdrive': 'Unet'},
        {'local': vision_dir,     'gdrive': 'Vision'},
        {'local': encoder_dir,    'gdrive': 'Encoder'},
        {'local': diffusion_dir,  'gdrive': 'Diffusion'},
    ]

def create_symlink(src, dst, log=False):
    """Create symlink with optional migration of existing content"""
    try:
        # Migrate contents if src is a real dir
        if os.path.isdir(src) and os.path.islink(src) != True and os.path.exists(dst):
            for item in os.listdir(src):
                shutil.move(os.path.join(src, item), dst)
            shutil.rmtree(src)
            if log:
                print(f"📦 Moved contents: {src} → {dst}")

        # Remove old link or file
        if os.path.islink(src) or os.path.isfile(src):
            os.remove(src)

        # Create new symlink
        if not os.path.exists(src):
            os.symlink(dst, src)
            if log:
                print(f"🔗 Symlink: {src} → {dst}")

    except Exception as e:
        print(f"❌ Error processing {src}: {str(e)}")

def handle_gdrive(mount_flag, ui='A1111', log=False):
    """Main handler for Google Drive mounting and symlink setup"""
    if not mount_flag:
        # Unmount logic
        if os.path.exists('/content/drive/MyDrive'):
            try:
                print('⏳ Отсоединение Google Drive...', end='')
                with capture.capture_output():
                    drive.flush_and_unmount()
                    os.system('rm -rf /content/drive')
                print('\r✅ Google Drive отсоединён и очищен!')

                # Remove symlinks
                for cfg in build_symlink_config(ui):
                    link_path = os.path.join(cfg['local'], 'GDrive')
                    if os.path.islink(link_path):
                        os.unlink(link_path)

                print('🗑️ Симлинки успешно удалены!')
            except Exception as e:
                print(f"\r❌ Unmount error: {str(e)}")
        return

    # Mount logic
    if not os.path.exists('/content/drive/MyDrive'):
        try:
            print('⏳ Подключение Google Drive...', end='')
            with capture.capture_output():
                drive.mount('/content/drive')
            print('\r🚀 Google Drive успешно подключён!')
        except Exception as e:
            # clear_output()
            print(f"\r❌ Mounting failed: {str(e)}")
            return
    else:
        print('🎉 Google Drive уже подключён~')

    try:
        os.makedirs(GD_BASE, exist_ok=True)

        # Create structure in Drive and symlinks
        for cfg in build_symlink_config(ui):
            dst = os.path.join(GD_BASE, cfg['gdrive'])
            src = os.path.join(cfg['local'], 'GDrive')
            os.makedirs(dst, exist_ok=True)
            os.makedirs(os.path.dirname(src), exist_ok=True)
            create_symlink(src, dst, log)

        print('✅ Симлинки успешно созданы!')

    except Exception as e:
        print(f"❌ Setup error: {str(e)}")

    # Cleanup notebook checkpoints
    subprocess.run(
        shlex.split(f"find {GD_BASE} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

handle_gdrive(mountGDrive, ui=UI)


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

    # text selection
    if selection.lower() != 'none':
        if selection == 'ALL':
            selected = sum(model_dict.values(), [])
        else:
            found = find_model_by_partial_name(selection, numbered) or selection
            original = re.sub(r'^\d+\.\s*', '', found)
            add_by_key(original)

    # numeric selection
    if num_selection:
        for num in _parse_selection_numbers(num_selection, len(keys)):
            if 1 <= num <= len(keys):
                add_by_key(keys[num - 1])

    # deduplicate + filter
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

    # build result
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
    print(f"\n\n{COL.Y}# ====== Подробная Загрузка ====== #\n{COL.X}")
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
if mountGDrive:
    gdrive_path = os.path.join(extension_dir, 'GDrive')
    if os.path.isdir(gdrive_path):
        for folder in os.listdir(gdrive_path):
            src = os.path.join(gdrive_path, folder)
            dst = os.path.join(extension_dir, folder)
            if os.path.isdir(src):
                # Copy directory tree; if dst exists, merge contents
                if os.path.exists(dst):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copytree(src, dst)


## List Models and stuff
ipyRun('run', f"{SCRIPTS}/download-result.py")