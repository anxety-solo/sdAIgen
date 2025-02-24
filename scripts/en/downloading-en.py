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

def setup_venv():
    """Customize the virtual environment."""
    url = "https://huggingface.co/NagisaNao/ANXETY/resolve/main/python310-venv-torch251-cu121-C-fca.tar.lz4"
    fn = Path(url).name

    m_download(f'{url} {HOME} {fn}')

    # Install dependencies based on environment
    install_commands = []
    if ENV_NAME == 'Kaggle':
        install_commands.extend([
            "pip install ipywidgets jupyterlab_widgets --upgrade",
            "rm -f /usr/lib/python3.10/sitecustomize.py"
        ])
    # else:        
    #     install_commands.append("apt -y install python3.10-venv")

    install_commands.append("sudo apt-get -y install lz4 pv")
    install_dependencies(install_commands)

    # Unpack and clean
    CD(HOME)
    ipySys(f'pv {fn} | lz4 -d | tar xf -')
    Path(fn).unlink()
    # ipySys(f'rm -rf {VENV}/bin/pip* {VENV}/bin/python*')

    # Create a virtual environment
    # python_command = 'python3.10' if ENV_NAME == 'Google Colab' else 'python3'
    # venv_commands = [
    #     f'{python_command} -m venv {VENV}',
    #     f'{VENV}/bin/python3 -m pip install -U --force-reinstall pip',
    #     f'{VENV}/bin/python3 -m pip install ipykernel',
    #     f'{VENV}/bin/python3 -m pip uninstall -y ngrok pyngrok'
    # ]
    # if UI == 'Forge':
    #     venv_commands.append(f'{VENV}/bin/python3 -m pip uninstall -y transformers')

    # install_dependencies(venv_commands)

    BIN = str(VENV / 'bin')
    PKG = str(VENV / 'lib/python3.10/site-packages')

    if BIN not in os.environ["PATH"]:
        os.environ["PATH"] = BIN + ":" + os.environ["PATH"]

    if PKG not in os.environ["PYTHONPATH"]:
        os.environ["PYTHONPATH"] = PKG + ":" + os.environ["PYTHONPATH"]

    os.environ["PYTHONWARNINGS"] = "ignore"

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
if not VENV.exists(): 
    print("♻️ Installing VENV, this will take some time...")
    setup_venv()
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

if UI not in ['ComfyUI', 'Forge'] and not os.path.exists('/root/.cache/huggingface/hub/models--Bingsu--adetailer'):
    print('🚚 Unpacking ADetailer model cache...')

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
    print(f"⌚ Unpacking Stable Diffusion... | WEBUI: \033[34m{UI}\033[0m", end='')

    ipyRun('run', f'{SCRIPTS}/UIs/{UI}.py')
    handle_setup_timer(WEBUI, start_timer)		# Setup timer (for timer-extensions)

    install_time = time.time() - start_install
    minutes, seconds = divmod(int(install_time), 60)
    print(f"\r🚀 Unpacking \033[34m{UI}\033[0m is complete! {minutes:02}:{seconds:02} ⚡" + " "*25)

else:
    print(f"🔧 Current WebUI: \033[34m{UI}\033[0m")
    print("🚀 Unpacking is complete. Pass. ⚡")

    timer_env = handle_setup_timer(WEBUI, start_timer)
    elapsed_time = str(timedelta(seconds=time.time() - timer_env)).split('.')[0]
    print(f"⌚️ Session duration: \033[33m{elapsed_time}\033[0m")


## Changes extensions and WebUi
if latest_webui or latest_extensions:
    action = "WebUI and Extensions" if latest_webui and latest_extensions else ("WebUI" if latest_webui else "Extensions")
    print(f"⌚️ Update {action}...", end='')
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
                    subprocess.run(['git', 'reset', '--hard'], cwd=dir_path, check=True)
                    subprocess.run(['git', 'pull'], cwd=dir_path, check=True)

    print(f"\r✨ Update {action} Completed!")


# === FIXING EXTENSIONS ===
with capture.capture_output():
    # --- Umi-Wildcard ---
    ipySys("sed -i '521s/open=\\(False\\|True\\)/open=False/' {WEBUI}/extensions/Umi-AI-Wildcards/scripts/wildcard_recursive.py")    # Closed accordion by default


## Version switching
if commit_hash:
    print('🔄 Switching to the specified version...', end="")
    with capture.capture_output():
        CD(WEBUI)
        ipySys('git config --global user.email "you@example.com"')
        ipySys('git config --global user.name "Your Name"')
        ipySys('git reset --hard {commit_hash}')
        ipySys('git pull origin {commit_hash}')    # Get last changes in branch
    print(f"\r🔄 Switch complete! Current commit: \033[34m{commit_hash}\033[0m")


# Get XL or 1.5 models list
## model_list | vae_list | controlnet_list
model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
with open(f'{SCRIPTS}/{model_files}') as f:
    exec(f.read())

## Downloading model and stuff | oh~ Hey! If you're freaked out by that code too, don't worry, me too!
print("📦 Downloading models and stuff...", end='')

extension_repo = []
PREFIXES = {
    "model": model_dir,
    "vae": vae_dir,
    "lora": lora_dir,
    "embed": embed_dir,
    "extension": extension_dir,
    "adetailer": adetailer_dir,
    "control": control_dir,
    "upscale": upscale_dir,
    "clip": clip_dir,
    "unet": unet_dir,
    "config": WEBUI
}
SHORT_PREFIXES = {
    "model": "$ckpt",
    "embed": "$emb",
    "extension": "$ext",
    "adetailer": "$ad",
    "control": "$cnet",
    "upscale": "$ups",
    "config": "$cfg"
}
for path in PREFIXES.values():
    os.makedirs(path, exist_ok=True)

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

def _STRIP_URL(url):
    """Removes unnecessary parts from the URL for correct downloading."""
    if "huggingface.co" in url:
        url = url.replace('/blob/', '/resolve/')
        if '?' in url:
            url = url.split('?')[0]
    elif 'github.com' in url:
        return url.replace('/blob/', '/raw/')

    return url

def _get_file_name(url):
    file_name_match = re.search(r'\[(.*?)\]', url)
    if file_name_match:
        return file_name_match.group(1)

    file_name_parse = urlparse(url)
    if any(domain in file_name_parse.netloc for domain in ["civitai.com", "drive.google.com"]):
        return None

    return Path(file_name_parse.path).name

def _unpack_zips():
    """Extracts all ZIP files in the directories specified in PREFIXES."""
    for directory in PREFIXES.values():
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".zip"):
                    zip_path = Path(root) / file
                    extract_path = zip_path.with_suffix('')
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    zip_path.unlink()  # Using Path.unlink() to remove the file

def _handle_manual_download(link):
    """Handles downloads for URLs with prefixes."""
    prefix, path = link.split(':', 1)
    file_name = _get_file_name(path)
    path = re.sub(r'\[.*?\]', '', path)

    if prefix in PREFIXES:
        dir = PREFIXES[prefix]
        if prefix != "extension":
            try:
                manual_download(path, dir, file_name=file_name, prefix=prefix)
            except Exception as e:
                print(f"\nError downloading file: {e}")
        else:
            extension_repo.append((path, file_name))

def download(line):
    links = [link.strip() for link in line.split(',') if link.strip()]

    for link in links:
        link = _STRIP_URL(link)

        if any(link.lower().startswith(prefix) for prefix in PREFIXES):
            _handle_manual_download(link)
        else:
            url, dst_dir, file_name = link.split()
            manual_download(url, dst_dir, file_name)

    # Unpacking ZIPs files
    _unpack_zips()

def manual_download(url, dst_dir, file_name=None, prefix=None):
    clean_url = url
    image_url, image_name = None, None

    if 'civitai' in url:
        civitai = CivitAiAPI(civitai_token)
        data = civitai.fetch_data(url)

        if data is None or civitai.check_early_access(data):
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
            file_extension = clean_url.split('/')[-1].split('.', 1)[1]
            file_name = f"{file_name}.{file_extension}"
        if not file_name:
            file_name = clean_url.split("/")[-1]

    # Formatted info output
    format_output(clean_url, dst_dir, file_name, image_url, image_name)

    # Downloading
    # file_path = os.path.join(dst_dir, file_name)
    # if os.path.exists(file_path) and prefix == 'config':
    #     os.remove(file_path)

    m_download(f"{url} {dst_dir} {file_name if file_name else ''}", log=True)

''' SubModels - Added URLs '''

# Separation of merged numbers
def _split_numbers(num_str, max_num):
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

def add_submodels(selection, num_selection, model_dict, dst_dir):
    """Add selected submodels based on user selection."""
    selected_models = []

    if selection == "none":
        return selected_models
    elif selection == "ALL":
        selected_models = sum(model_dict.values(), [])
    else:
        selected_models.extend(model_dict.get(selection, []))

        max_num = len(model_dict)
        unique_nums = _split_numbers(num_selection, max_num)

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

    return list(unique_models.values())

def handle_submodels(selection, num_selection, model_dict, dst_dir, url):
    """Handle the selection of submodels and construct the URL string."""
    submodels = add_submodels(selection, num_selection, model_dict, dst_dir)
    for submodel in submodels:
        if not inpainting_model and "inpainting" in submodel['name']:
            continue
        url += f"{submodel['url']} {submodel['dst_dir']} {submodel['name']}, "
    return url

line = ""
line = handle_submodels(model, model_num, model_list, model_dir, line)
line = handle_submodels(vae, vae_num, vae_list, vae_dir, line)
line = handle_submodels(controlnet, controlnet_num, controlnet_list, control_dir, line)

''' file.txt - added urls '''

def process_file_downloads(file_urls, prefixes, additional_lines=None):
    files_urls = ""
    unique_urls = set()

    if additional_lines:
        lines = additional_lines.splitlines()
    else:
        lines = []

    for file_url in file_urls:
        if file_url.startswith("http"):
            file_url = _STRIP_URL(file_url)
            response = requests.get(file_url)
            lines += response.text.splitlines()
        else:
            try:
                with open(file_url, 'r') as file:
                    lines += file.readlines()
            except FileNotFoundError:
                continue

    current_tag = None
    for line in lines:
        tag_line = line.strip().lower()
        for prefix in prefixes.keys():
            long_tag = f'# {prefix}'
            short_tag = SHORT_PREFIXES.get(prefix, None)
            
            if (long_tag.lower() in tag_line) or (short_tag and short_tag.lower() in tag_line):
                current_tag = prefix
                break

        urls = [url.split('#')[0].strip() for url in line.split(',')]
        for url in urls:
            filter_url = url.split('[')[0].strip()
            if url.startswith("http") and filter_url not in unique_urls:
                files_urls += f"{current_tag}:{url}, "
                unique_urls.add(filter_url)

    # Return string if no tag was found | FIX
    if current_tag is None:
        return ''

    return files_urls

file_urls = []

if custom_file_urls:
    file_urls = [f"{custom_file}.txt" if not custom_file.endswith('.txt') else custom_file 
                 for custom_file in custom_file_urls.replace(',', '').split()]

file_urls_result = process_file_downloads(file_urls, PREFIXES, empowerment_output)

# URL prefixing
urls = (Model_url, Vae_url, LoRA_url, Embedding_url, Extensions_url, ADetailer_url)
prefixed_urls = [
    f"{prefix}:{url.strip()}"
    for prefix, url in zip(PREFIXES.keys(), urls)
    if url for url in url.replace(',', '').split()
]
line += ", ".join(prefixed_urls) + ", " + file_urls_result.strip(', ')

if detailed_download == "on":
    print("\n\n\033[33m# ====== Detailed Download ====== #\n\033[0m")
    download(line)
    print("\n\033[33m# =============================== #\n\033[0m")
else:
    with capture.capture_output():
        download(line)

print("\r🏁 Download Complete!" + " "*15)


## Install of Custom extensions
def _clone_repository(repo, repo_name, extension_dir):
    """Clones the repository to the specified directory."""
    repo_name = repo_name or repo.split('/')[-1]
    command = f'cd {extension_dir} && git clone --depth 1 --recursive {repo} {repo_name} && cd {repo_name} && git fetch'
    ipySys(command)

extension_type = 'nodes' if UI == 'ComfyUI' else 'extensions'

if extension_repo:
    print(f"✨ Installing custom {extension_type}...", end='')
    with capture.capture_output():
        for repo, repo_name in extension_repo:
            _clone_repository(repo, repo_name, extension_dir)
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


## List Models and stuff
ipyRun('run', f'{SCRIPTS}/download-result.py')