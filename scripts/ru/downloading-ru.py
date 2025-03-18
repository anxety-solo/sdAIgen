# ~ download.py | by ANXETY ~

from webui_utils import handle_setup_timer    # WEBUI
from CivitaiAPI import CivitAiAPI             # CivitAI API
from Manager import m_download                # Every Download
import json_utils as js                       # JSON

from IPython.display import clear_output
from IPython.utils import capture
from urllib.parse import urlparse
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import zipfile
import shutil
import shlex
import time
import json
import sys
import re
import os


CD = os.chdir
ipySys = get_ipython().system
ipyRun = get_ipython().run_line_magic

# Constants
HOME = Path.home()
VENV = HOME / 'venv'
SCR_PATH = Path(HOME / 'ANXETY')
SCRIPTS = SCR_PATH / 'scripts'
SETTINGS_PATH = SCR_PATH / 'settings.json'

LANG = js.read(SETTINGS_PATH, 'ENVIRONMENT.lang')
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = js.read(SETTINGS_PATH, 'WEBUI.webui_path')


## =================== LIBRARIES | VENV ==================

def install_dependencies(commands):
    """Run a list of installation commands."""
    for cmd in commands:
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def setup_venv(url):
    """Customize the virtual environment using the specified URL."""
    CD(HOME)
    fn = Path(url).name

    m_download(f'{url} {HOME} {fn}')

    # Install dependencies based on environment
    install_commands = []
    if ENV_NAME == 'Kaggle':
        install_commands.extend([
            "pip install ipywidgets jupyterlab_widgets --upgrade",
            "rm -f /usr/lib/python3.10/sitecustomize.py"
        ])

    install_commands.append("sudo apt-get -y install lz4 pv")
    install_dependencies(install_commands)

    # Unpack and clean
    ipySys(f'pv {fn} | lz4 -d | tar xf -')
    Path(fn).unlink()

    BIN = str(VENV / 'bin')
    PKG = str(VENV / 'lib/python3.10/site-packages')

    os.environ["PYTHONWARNINGS"] = "ignore"
    if BIN not in os.environ["PATH"]:
        os.environ["PATH"] = BIN + ":" + os.environ["PATH"]
    if PKG not in os.environ["PYTHONPATH"]:
        os.environ["PYTHONPATH"] = PKG + ":" + os.environ["PYTHONPATH"]

def install_packages(install_lib):
    """Install packages from the provided library dictionary."""
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\r[{index}/{len(install_lib)}] \033[32m>>\033[0m Installing \033[33m{package}\033[0m..." + " " * 35, end='')
        result = subprocess.run(install_cmd, shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"\n\033[31mError installing {package}: {result.stderr.decode()}\033[0m")

# Check and install dependencies
if not js.key_exists(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True):
    install_lib = {
        ## Libs
        "aria2": "pip install aria2",
        "gdown": "pip install gdown",
        ## Tunnels
        "localtunnel": "npm install -g localtunnel",
        "cloudflared": "wget -qO /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64; chmod +x /usr/bin/cl",
        "zrok": "wget -qO zrok_0.4.44_linux_amd64.tar.gz https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz; tar -xzf zrok_0.4.44_linux_amd64.tar.gz -C /usr/bin; rm -f zrok_0.4.44_linux_amd64.tar.gz",
        "ngrok": "wget -qO ngrok-v3-stable-linux-amd64.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz; tar -xzf ngrok-v3-stable-linux-amd64.tgz -C /usr/bin; rm -f ngrok-v3-stable-linux-amd64.tgz"
    }

    print("💿 Installing the libraries will take a bit of time.")
    install_packages(install_lib)
    clear_output()
    js.update(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

# Check and setup virtual environment
current_ui = js.read(SETTINGS_PATH, 'WEBUI.current')
venv_ui_path = SCR_PATH / '.venv_ui'

# Determine whether to reinstall venv
venv_needs_reinstall = (
    not VENV.exists()  # venv is missing
    or not venv_ui_path.exists()  # file marker is missing
     # Check category change (ReForge <-> other)
    or (venv_ui_path.read_text().strip() == 'ReForge') != (current_ui == 'ReForge')
)

if venv_needs_reinstall:
    if VENV.exists():
        print("🗑️ Удаление старого venv...")
        shutil.rmtree(VENV)
        clear_output()

    if current_ui == 'ReForge':
        venv_url = "https://huggingface.co/NagisaNao/ANXETY/resolve/main/python310-venv-torch251-cu121-C-ReForge.tar.lz4"
    else:
        venv_url = "https://huggingface.co/NagisaNao/ANXETY/resolve/main/python310-venv-torch251-cu121-C-fca.tar.lz4"

    print(f"♻️ Установка {'ReForge VENV' if UI == 'ReForge' else 'VENV'}, это займет некоторое время...")
    setup_venv(venv_url)

    # Create a marker for the current UI
    (SCR_PATH / '.venv_ui').write_text(current_ui)
    clear_output()

## ================ loading settings V5 ==================
def load_settings(path):
    """Load settings from a JSON file."""
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

## ======================== WEBUI ========================

if UI not in ['ComfyUI', 'Forge', 'ReForge'] and not os.path.exists('/root/.cache/huggingface/hub/models--Bingsu--adetailer'):
    print('🚚 Распаковка кэша моделей ADetailer...')

    name_zip = 'hf_cache_adetailer'
    chache_url = 'https://huggingface.co/NagisaNao/ANXETY/resolve/main/hf_chache_adetailer.zip'

    zip_path = f'{HOME}/{name_zip}.zip'
    m_download(f'{chache_url} {HOME} {name_zip}')
    ipySys(f'unzip -q -o {zip_path} -d /')
    ipySys(f'rm -rf {zip_path}')

    clear_output()

start_timer = js.read(SETTINGS_PATH, 'ENVIRONMENT.start_timer')

if not os.path.exists(WEBUI):
    start_install = time.time()
    print(f"⌚ Распаковка Stable Diffusion... | WEBUI: \033[34m{UI}\033[0m", end='')

    ipyRun('run', f'{SCRIPTS}/UIs/{UI}.py')
    handle_setup_timer(WEBUI, start_timer)		# Setup timer (for timer-extensions)

    install_time = time.time() - start_install
    minutes, seconds = divmod(int(install_time), 60)
    print(f"\r🚀 Распаковка \033[34m{UI}\033[0m Завершена! {minutes:02}:{seconds:02} ⚡" + " "*25)

else:
    print(f"🔧 Текущий WebUI: \033[34m{UI}\033[0m")
    print("🚀 Распаковка завершена. Пропуск. ⚡")

    timer_env = handle_setup_timer(WEBUI, start_timer)
    elapsed_time = str(timedelta(seconds=time.time() - timer_env)).split('.')[0]
    print(f"⌚️ Продолжительность сеанса: \033[33m{elapsed_time}\033[0m")


## Changes extensions and WebUi
if latest_webui or latest_extensions:
    action = "WebUI и Расширений" if latest_webui and latest_extensions else ("WebUI" if latest_webui else "Расширений")
    print(f"⌚️ Обновление {action}...", end='')
    with capture.capture_output():
        ipySys('git config --global user.email "you@example.com"')
        ipySys('git config --global user.name "Your Name"')

        ## Update Webui
        if latest_webui:
            CD(WEBUI)
            # ipySys('git restore .')
            # ipySys('git pull -X theirs --rebase --autostash')

            ipySys('git stash')
            ipySys('git pull --rebase')
            ipySys('git stash pop')

        ## Update extensions
        if latest_extensions:
            # ipySys('{\'for dir in \' + WEBUI + \'/extensions/*/; do cd \\"$dir\\" && git reset --hard && git pull; done\'}')
            for entry in os.listdir(f'{WEBUI}/extensions'):
                dir_path = f'{WEBUI}/extensions/{entry}'
                if os.path.isdir(dir_path):
                    subprocess.run(['git', 'reset', '--hard'], cwd=dir_path)
                    subprocess.run(['git', 'pull'], cwd=dir_path)

    print(f"\r✨ Обновление {action} Завершено!")


# === FIXING EXTENSIONS ===
with capture.capture_output():
    # --- Umi-Wildcard ---
    ipySys("sed -i '521s/open=\\(False\\|True\\)/open=False/' {WEBUI}/extensions/Umi-AI-Wildcards/scripts/wildcard_recursive.py")    # Closed accordion by default


## Version switching
if commit_hash:
    print('🔄 Переключаемся на указанную версию...', end="")
    with capture.capture_output():
        CD(WEBUI)
        ipySys('git config --global user.email "you@example.com"')
        ipySys('git config --global user.name "Your Name"')
        ipySys('git reset --hard {commit_hash}')
        ipySys('git pull origin {commit_hash}')    # Get last changes in branch
    print(f"\r🔄 Переключение завершено! Текущий коммит: \033[34m{commit_hash}\033[0m")


# Get XL or 1.5 models list
## model_list | vae_list | controlnet_list
model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
with open(f'{SCRIPTS}/{model_files}') as f:
    exec(f.read())

## Downloading model and stuff | oh~ Hey! If you're freaked out by that code too, don't worry, me too!
print("📦 Скачивание моделей и прочего...", end='')

extension_repo = []
PREFIX_MAP = {
    # prefix : (dir_path , short-tag)
    "model": (model_dir, "$ckpt"),
    "vae": (vae_dir, None),
    "lora": (lora_dir, None),
    "embed": (embed_dir, "$emb"),
    "extension": (extension_dir, "$ext"),
    "adetailer": (adetailer_dir, "$ad"),
    "control": (control_dir, "$cnet"),
    "upscale": (upscale_dir, "$ups"),
    # Other
    "clip": (clip_dir, None),
    "unet": (unet_dir, None),
    "vision": (vision_dir, None),
    "encoder": (encoder_dir, "$enc"),
    "diffusion": (diffusion_dir, "$diff"),
    "config": (config_dir, "$cfg")
}
for dir_path, _ in PREFIX_MAP.values():
    os.makedirs(dir_path, exist_ok=True)

''' Formatted Info Output '''

def _center_text(text, terminal_width=45):
    padding = (terminal_width - len(text)) // 2
    return f"{' ' * padding}{text}{' ' * padding}"

def format_output(url, dst_dir, file_name, image_url=None, image_name=None):
    info = "[ NONE ]"
    if file_name:
        info = _center_text(f"[{file_name.split('.')[0]}]")
    if not file_name and 'drive.google.com' in url:
      info = _center_text("[ GDrive ]")

    sep_line = '---' * 20

    print(f"\n\033[32m{sep_line}\033[36;1m{info}\033[32m{sep_line}\033[0m")
    print(f"\033[33mURL: \033[0m{url}")
    print(f"\033[33mSAVE DIR: \033[34m{dst_dir}")
    print(f"\033[33mFILE NAME: \033[34m{file_name}\033[0m")
    if 'civitai' in url and image_url:
        print(f"\033[32m[Preview]:\033[0m {image_name} -> {image_url}")
    print()

''' Main Download Code '''

def _clean_url(url):
    if "huggingface.co" in url:
        return url.replace('/blob/', '/resolve/').split('?')[0]
    if 'github.com' in url:
        return url.replace('/blob/', '/raw/')
    return url

def _extract_filename(url):
    if match := re.search(r'\[(.*?)\]', url):
        return match.group(1)

    parsed = urlparse(url)
    if any(d in parsed.netloc for d in ["civitai.com", "drive.google.com"]):
        return None

    return Path(parsed.path).name

def _unpack_zips():
    for dir_path, _ in PREFIX_MAP.values():
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".zip"):
                    zip_path = Path(root) / file
                    extract_path = zip_path.with_suffix('')
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    zip_path.unlink()

# Download Core

def _process_download_link(link):
    link = _clean_url(link)
    if ':' in link:
        prefix, path = link.split(':', 1)
        if prefix in PREFIX_MAP:
            return prefix, re.sub(r'\[.*?\]', '', path), _extract_filename(path)
    return None, link, None

def download(line):
    for link in (l.strip() for l in line.split(',') if l.strip()):
        prefix, url, filename = _process_download_link(link)

        if prefix:
            dir_path, _ = PREFIX_MAP[prefix]
            if prefix == "extension":
                extension_repo.append((url, filename))
            else:
                try:
                    manual_download(url, dir_path, filename, prefix)
                except Exception as e:
                    print(f"\n> Error downloading file: {e}")
        else:
            url, dst_dir, file_name = url.split()
            manual_download(url, dst_dir, file_name)

    _unpack_zips()

def manual_download(url, dst_dir, file_name=None, prefix=None):
    clean_url = url
    image_url, image_name = None, None

    if 'civitai' in url:
        civitai = CivitAiAPI(civitai_token)
        if not (data := civitai.fetch_data(url)) or civitai.check_early_access(data):
            return  # Terminate if no data or requires payment

        model_type, file_name = civitai.get_model_info(data, url, file_name)
        download_url = civitai.get_download_url(data, url)
        clean_url, url = civitai.get_full_and_clean_download_url(download_url)
        image_url, image_name = civitai.get_image_info(data, file_name, model_type)

        # Download preview images
        if image_url and image_name:
            m_download(f"{image_url} {dst_dir} {image_name}")

    elif 'github' in url or 'huggingface.co' in url:
        if file_name and '.' not in file_name:
            file_name += f".{clean_url.split('.')[-1]}"

    # Formatted info output
    format_output(clean_url, dst_dir, file_name, image_url, image_name)

    # Downloading
    m_download(f"{url} {dst_dir} {file_name or ''}", log=True)

''' SubModels - Added URLs '''

# Separation of merged numbers
def _parse_selection_numbers(num_str, max_num):
    """Split a string of numbers into unique integers."""
    num_str = num_str.replace(',', ' ').strip()
    unique_numbers = set()

    # Handling space-separated and concatenated numbers
    for part in num_str.split():
        if part.isdigit():
            part_int = int(part)
            if part_int <= max_num:
                unique_numbers.add(part_int)

    # Handle the case where numbers can be written as concatenates
    for i in range(len(num_str)):
        for length in range(2, 0, -1):
            if i + length <= len(num_str):
                substring = num_str[i:i + length]
                if substring.isdigit():
                    part = int(substring)
                    if part <= max_num:
                        unique_numbers.add(part)
                        break

    return sorted(unique_numbers)

def handle_submodels(selection, num_selection, model_dict, dst_dir, base_url):
    selected_models = []

    if selection != "none":
        if selection == "ALL":
            selected_models = sum(model_dict.values(), [])
        else:
            if selection in model_dict:
                selected_models.extend(model_dict[selection])

            if num_selection:
                max_num = len(model_dict)
                unique_nums = _parse_selection_numbers(num_selection, max_num)
                for num in unique_nums:
                    if 1 <= num <= max_num:
                        name = list(model_dict.keys())[num - 1]
                        selected_models.extend(model_dict[name])

    unique_models = {}
    for model in selected_models:
        model_name = model.get('name') or os.path.basename(model['url'])
        model['name'] = model_name
        model['dst_dir'] = model.get('dst_dir', dst_dir)
        unique_models[model_name] = model

    # Filter inpainting
    for model in unique_models.values():
        if not inpainting_model and "inpainting" in model['name']:
            continue
        base_url += f"{model['url']} {model['dst_dir']} {model['name']}, "

    return base_url

line = ""
line = handle_submodels(model, model_num, model_list, model_dir, line)
line = handle_submodels(vae, vae_num, vae_list, vae_dir, line)
line = handle_submodels(controlnet, controlnet_num, controlnet_list, control_dir, line)

''' file.txt - added urls '''

def _process_lines(lines):
    current_tag = None
    unique_urls = set()
    files_urls = ""

    for line in lines:
        tag_line = line.strip().lower()
        for prefix, (_, short_tag) in PREFIX_MAP.items():
            if (f'# {prefix}'.lower() in tag_line) or (short_tag and short_tag.lower() in tag_line):
                current_tag = prefix
                break

        for url_part in [u.split('#')[0].strip() for u in line.split(',')]:
            filter_url = url_part.split('[')[0].strip()
            if current_tag is not None:
                if url_part.startswith("http") and filter_url not in unique_urls:
                    files_urls += f"{current_tag}:{url_part}, "
                    unique_urls.add(filter_url)

    # Return string if no tag was found | FIX
    if current_tag is None:
        return ''

    return files_urls

def process_file_downloads(file_urls, additional_lines=None):
    lines = additional_lines.splitlines() if additional_lines else []

    for source in file_urls:
        if source.startswith("http"):
            lines += requests.get(_clean_url(source)).text.splitlines()
        else:
            try:
                with open(source, 'r') as f:
                    lines += f.readlines()
            except FileNotFoundError:
                continue

    return _process_lines(lines)

# File URLs processing
urls_sources = (Model_url, Vae_url, LoRA_url, Embedding_url, Extensions_url, ADetailer_url)
file_urls = [f"{f}.txt" if not f.endswith('.txt') else f for f in custom_file_urls.replace(',', '').split()] if custom_file_urls else []

# p -> prefix ; u -> url | Remember: don't touch the prefix!
prefixed_urls = [f"{p}:{u}" for p, u in zip(PREFIX_MAP, urls_sources) if u for u in u.replace(',', '').split()]
line += ", ".join(prefixed_urls + [process_file_downloads(file_urls, empowerment_output)])

if detailed_download == "on":
    print("\n\n\033[33m# ====== Подробная Загрузка ====== #\n\033[0m")
    download(line)
    print("\n\033[33m# =============================== #\n\033[0m")
else:
    with capture.capture_output():
        download(line)

print("\r🏁 Скачивание Завершено!" + " "*15)


## Install of Custom extensions
def _clone_repository(repo, repo_name, extension_dir):
    """Clones the repository to the specified directory."""
    repo_name = repo_name or repo.split('/')[-1]
    command = f'cd {extension_dir} && git clone --depth 1 --recursive {repo} {repo_name} && cd {repo_name} && git fetch'
    ipySys(command)

extension_type = 'нодов' if UI == 'ComfyUI' else 'расширений'

if extension_repo:
    print(f"✨ Установка кастомных {extension_type}...", end='')
    with capture.capture_output():
        for repo, repo_name in extension_repo:
            _clone_repository(repo, repo_name, extension_dir)
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


## List Models and stuff
ipyRun('run', f'{SCRIPTS}/download-result.py')
