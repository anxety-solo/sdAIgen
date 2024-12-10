# ~ download.py | by ANXETY ~

from json_utils import read_json, save_json, update_json    # JSON (main)
from webui_utils import handle_setup_timer                  # WEBUI
from CivitaiAPI import CivitAiAPI                           # CivitAI API

from IPython.display import clear_output
from IPython.utils import capture
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import zipfile
import shlex
import time
import sys
import re
import os

# Constants
HOME = Path.home()
SCR_PATH = Path(HOME / 'ANXETY')
SETTINGS_PATH = SCR_PATH / 'settings.json'
LANG = read_json(SETTINGS_PATH, 'ENVIRONMENT.lang')
ENV_NAME = read_json(SETTINGS_PATH, 'ENVIRONMENT.env_name')

UI = read_json(SETTINGS_PATH, 'WEBUI.current')
WEBUI = read_json(SETTINGS_PATH, 'WEBUI.webui_path')

SCRIPTS = SCR_PATH / 'scripts'

# ============ loading settings V5 =============
def load_settings(path):
    """Load settings from a JSON file."""
    try:
        return {
            **read_json(path, 'ENVIRONMENT'),
            **read_json(path, 'WIDGETS'),
            **read_json(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}

# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)

# ================ LIBRARIES V3 ================
def install_packages(install_lib):
    for index, (package, install_cmd) in enumerate(install_lib.items(), start=1):
        print(f"\r[{index}/{len(install_lib)}] \033[32m>>\033[0m Installing \033[33m{package}\033[0m..." + " "*35, end='')
        result = subprocess.run(install_cmd, shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"\n\033[31mError installing {package}: {result.stderr.decode()}\033[0m")

def download_additional_packages(SCR_PATH):
    commands = [
        'curl -s -Lo /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /usr/bin/cl',
        'curl -sLO https://github.com/openziti/zrok/releases/download/v0.4.32/zrok_0.4.32_linux_amd64.tar.gz && tar -xzf zrok_0.4.32_linux_amd64.tar.gz -C /usr/bin && rm -f zrok_0.4.32_linux_amd64.tar.gz'
    ]
    for command in commands:
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if not read_json(SETTINGS_PATH, 'ENVIRONMENT.install_deps'):
    print("💿 Установка библиотек, это займет какое-то время:")

    install_lib = {
        # "aria2": "apt -y install aria2",
        "aria2": "pip install aria2",
        "localtunnel": "npm install -g localtunnel",
    }
    if controlnet != 'none':
        install_lib["insightface"] = "pip install insightface"

    additional_libs = {
        "Google Colab": {
            "xformers": "pip install xformers==0.0.28.post1 --no-deps"
        },
        "Kaggle": {
            "openssl": "conda install -y openssh",
            "xformers": "pip install xformers==0.0.28.post3 --no-deps",
            "torch": "pip install torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121"
        }
    }

    if ENV_NAME in additional_libs:
        install_lib.update(additional_libs[ENV_NAME])

    install_packages(install_lib)
    download_additional_packages(SCR_PATH)

    clear_output()
    update_json(SETTINGS_PATH, 'ENVIRONMENT.install_deps', True)

    print("🍪 Библиотеки установлены!")
    time.sleep(2)
    clear_output()

# =================== WEBUI ===================
start_timer = read_json(SETTINGS_PATH, 'ENVIRONMENT.start_timer')

if not os.path.exists(WEBUI):
    start_install = time.time()
    print(f"⌚ Распаковка Stable Diffusion... | WEBUI: \033[34m{UI}\033[0m", end='')

    get_ipython().run_line_magic('run', f'{SCRIPTS}/UIs/{UI}.py')
    handle_setup_timer(WEBUI, start_timer)		# Setup timer (for ncpt timer-extensions)

    install_time = time.time() - start_install
    minutes, seconds = divmod(int(install_time), 60)
    print(f"\r🚀 Распаковка Завершена! За {minutes:02}:{seconds:02} ⚡" + " "*25)

else:
    print(f"🔧 Текущий WebUI: \033[34m{UI} \033[0m")
    print("🚀 Распаковка завершена. Пропуск. ⚡")

    timer_env = handle_setup_timer(WEBUI, start_timer)
    elapsed_time = str(timedelta(seconds=time.time() - timer_env)).split('.')[0]
    print(f"⌚️ Вы проводите эту сессию в течение - \033[33m{elapsed_time}\033[0m")


## Changes extensions and WebUi
if latest_webui or latest_extensions:
    action = "WebUI и Расширений" if latest_webui and latest_extensions else ("WebUI" if latest_webui else "Расширений")
    print(f"⌚️ Обновление {action}...", end='')
    with capture.capture_output():
        get_ipython().system('git config --global user.email "you@example.com"')
        get_ipython().system('git config --global user.name "Your Name"')

        ## Update Webui
        if latest_webui:
            get_ipython().run_line_magic('cd', '{WEBUI}')
            get_ipython().system('git restore .')
            get_ipython().system('git pull -X theirs --rebase --autostash')

        ## Update extensions
        if latest_extensions:
            get_ipython().system('{\'for dir in \' + WEBUI + \'/extensions/*/; do cd \\"$dir\\" && git reset --hard && git pull; done\'}')
    print(f"\r✨ Обновление {action} Завершено!")


# === FIXING EXTENSIONS ===
with capture.capture_output():
    # --- Umi-Wildcard ---
    get_ipython().system("sed -i '521s/open=\\(False\\|True\\)/open=False/' {WEBUI}/extensions/Umi-AI-Wildcards/scripts/wildcard_recursive.py  # Closed accordion by default")
    # --- Encrypt-Image ---
    get_ipython().system("sed -i '9,37d' {WEBUI}/extensions/Encrypt-Image/javascript/encrypt_images_info.js # Removes the weird text in webui")


## Version switching
if commit_hash:
    print('⏳ Активация машины времени...', end="")
    with capture.capture_output():
        get_ipython().run_line_magic('cd', '{WEBUI}')
        get_ipython().system('git config --global user.email "you@example.com"')
        get_ipython().system('git config --global user.name "Your Name"')
        get_ipython().system('git reset --hard {commit_hash}')
    print(f"\r⌛️ Машина времени активированна! Текущий коммит: \033[34m{commit_hash}\033[0m")


# Get XL or 1.5 models list
## model_list | vae_list | controlnet_list
model_files = '_xl-models-data.py' if XL_models else '_models-data.py'
with open(f'{SCRIPTS}/{model_files}') as f:
    exec(f.read())

## Downloading model and stuff | oh~ Hey! If you're freaked out by that code too, don't worry, me too!
print("📦 Скачивание моделей и прочего...", end='')

extension_repo = []
PREFIXES = {
    "model": model_dir,
    "vae": vae_dir,
    "lora": lora_dir,
    "embed": embed_dir,
    "extension": extension_dir,
    "control": control_dir,
    "upscale": upscale_dir,
    "adetailer": adetailer_dir,
    "config": WEBUI
}
for path in PREFIXES.values():
    os.makedirs(path, exist_ok=True)

''' Formatted Info Output '''

def format_output_line(line):
    """Format a line of output with ANSI color codes."""
    line = re.sub(r'\[', "\033[35m【\033[0m", line)
    line = re.sub(r'\]', "\033[35m】\033[0m", line)
    line = re.sub(r'(#)(\w+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(\(\d+%\))', r'\033[36m\1\033[0m', line)
    line = re.sub(r'(CN:)(\d+)', r'\1\033[34m\2\033[0m', line)
    line = re.sub(r'(DL:)(\d+\w+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(ETA:)(\d+\w+)', r'\1\033[33m\2\033[0m', line)
    return line

def handle_error_output(line, error_codes, error_messages):
    """Check and collect error messages from the output."""
    if 'errorCode' in line or 'Exception' in line:
        error_codes.append(line)
    if '|' in line and 'ERR' in line:
        formatted_line = re.sub(r'(\|\s*)(ERR)(\s*\|)', r'\1\033[31m\2\033[0m\3', line)
        error_messages.append(formatted_line)

def monitor_aria2_download(header, args, dst_dir, out, url):
    """Starts aria2c and intercepts the output to display the download progress."""
    try:
        command = f"aria2c {header} {args} -d {dst_dir} {out} '{url}'"
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        error_codes = []
        error_messages = []
        result = ""
        br = False

        while True:
            lines = process.stderr.readline()
            if lines == '' and process.poll() is not None:
                break

            if lines:
                result += lines

                for output_line in lines.splitlines():
                    handle_error_output(lines, error_codes, error_messages)

                    if re.match(r'\[#\w{6}\s.*\]', output_line):
                        formatted_line = format_output_line(output_line)
                        for line in lines:
                            print(f"\r{' ' * 180}\r{formatted_line}", end="")
                            sys.stdout.flush()
                        br = True
                        break

        # Print collected error messages
        for error in error_codes + error_messages:
            print(f" {error}")

        if br:
            print()

        # Print final status
        stripe = result.find("======+====+===========")
        if stripe != -1:
            for line in result[stripe:].splitlines():
                if '|' in line and 'OK' in line:
                    formatted_line = re.sub(r'(\|\s*)(OK)(\s*\|)', r'\1\033[32m\2\033[0m\3', line)
                    print(f" {formatted_line}")

        process.wait()

    except KeyboardInterrupt:
        print("\n\nDownload interrupted.")

def _center_text(text, terminal_width=45):
    padding = (terminal_width - len(text)) // 2
    return f"{' ' * padding}{text}{' ' * padding}"

def format_output(url, dst_dir, file_name, image_url=None, image_name=None):
    info = _center_text(f"[{file_name.split('.')[0]}]")
    sep_line = '---' * 20

    print(f"\n\033[32m{sep_line}\033[36;1m{info}\033[32m{sep_line}\033[0m")
    print(f"\033[33mURL: {url}")
    print(f"\033[33mSAVE DIR: \033[34m{dst_dir}")
    print(f"\033[33mFILE NAME: \033[34m{file_name}\033[0m")
    if 'civitai' in url and image_url:
        print(f"\033[32m[Preview]:\033[0m {image_name} -> {image_url}")
    print()

''' Main Download Code '''

def _strip_url(url):
    """Removes unnecessary parts from the URL for correct downloading."""
    if "huggingface.co" in url:
        url = url.replace('/blob/', '/resolve/')
        if '?' in url:
            url = url.split('?')[0]

    elif 'github.com' in url:
        return url.replace('/blob/', '/raw/')

    return url

def _unpack_zip_files():
    """Extracts all ZIP files in the directories specified in PREFIXES."""
    for directory in PREFIXES.values():
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".zip"):
                    zip_path = os.path.join(root, file)
                    extract_path = os.path.splitext(zip_path)[0]
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    os.remove(zip_path)

def download(url):
    links_and_paths = [link_or_path.strip() for link_or_path in url.split(',') if link_or_path.strip()]

    for link_or_path in links_and_paths:
        if any(link_or_path.lower().startswith(prefix) for prefix in PREFIXES):
            _handle_manual_download(link_or_path)
        else:
            url, dst_dir, file_name = link_or_path.split()
            manual_download(url, dst_dir, file_name)

    # Unpacking ZIP files
    _unpack_zip_files()

def _handle_manual_download(url):
    """Handles downloads for URLs with prefixes."""
    url_parts = url.split(':', 1)
    prefix, path = url_parts[0], url_parts[1]

    file_name_match = re.search(r'\[(.*?)\]', path)
    file_name = file_name_match.group(1) if file_name_match else None
    if file_name:
        path = re.sub(r'\[.*?\]', '', path)

    if prefix in PREFIXES:
        dir = PREFIXES[prefix]
        if prefix != "extension":
            try:
                manual_download(path, dir, file_name=file_name, prefix=prefix)
            except Exception as e:
                print(f"Error downloading file: {e}")
        else:
            extension_repo.append((path, file_name))

def manual_download(url, dst_dir, file_name=None, prefix=None):
    hf_header = f"--header='Authorization: Bearer {huggingface_token}'" if huggingface_token else ""
    aria2_header = "--header='User-Agent: Mozilla/5.0' --allow-overwrite=true"
    aria2_args = "--optimize-concurrent-downloads --console-log-level=error --summary-interval=1 --stderr=true -c -x16 -s16 -k1M -j5"

    clean_url = _strip_url(url)

    if 'civitai' in url:
        civitai = CivitAiAPI(civitai_token)
        data = civitai.fetch_data(url)

        if data:
            model_type, model_name = civitai.get_model_info(data, url, file_name)
            download_url = civitai.get_download_url(data, url)
            clean_url, url = civitai.get_full_and_clean_download_url(download_url)
            image_url, image_name = civitai.get_image_info(data, model_name, model_type)
            # fix name error | split NoneType
            file_name = model_name
        
            # DL PREVIEW IMAGES | CIVITAI
            if image_url and image_name:
                command = ["aria2c"] + aria2_args.split() + ["-d", dst_dir, "-o", image_name, image_url]
                subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif 'github' in url or 'huggingface.co' in url:
        if file_name and '.' not in file_name:
            file_extension = f"{clean_url.split('/')[-1].split('.', 1)[1]}"
            file_name = f"{file_name}.{file_extension}"
        if not file_name:
            file_name = clean_url.split("/")[-1]

    ## Formatted info output
    try:
        format_output(clean_url, dst_dir, file_name, image_url, image_name)
    except UnboundLocalError:
        format_output(clean_url, dst_dir, file_name, None, None)

    ## fix token init in url
    if 'civitai' in url:
        clean_url = url

    _run_aria2c(prefix, clean_url, dst_dir, file_name, aria2_args, hf_header if 'huggingface' in url else aria2_header)

def _run_aria2c(prefix, url, dst_dir, file_name=None, args="", header=""):
    """Starts the download using aria2c."""
    file_path = os.path.join(dst_dir, file_name)
    if os.path.exists(file_path) and prefix == 'config':
        os.remove(file_path)

    out = f"-o '{file_name}'" if file_name else ""
    # get_ipython().system(f"aria2c {header} {args} -d {dst_dir} {out} '{url}'")
    monitor_aria2_download(header, args, dst_dir, out, url)

''' SubModels - Added URLs '''

# Separation of merged numbers
def split_numbers(num_str, max_num):
    unique_numbers = set()
    nums_str = num_str.replace(',', ' ').strip()

    i = 0
    while i < len(nums_str):
        found = False
        for length in range(2, 0, -1):
            if i + length <= len(nums_str):
                part = int(nums_str[i:i + length])
                if part <= max_num:
                    unique_numbers.add(part)
                    i += length
                    found = True
                    break
        if not found:
            break

    return sorted(unique_numbers)

def add_submodels(selection, num_selection, model_dict, dst_dir):
    if selection == "none":
        return []
    selected_models = []

    if selection == "ALL":
        selected_models = sum(model_dict.values(), [])
    else:
        selected_models.extend(model_dict.get(selection, []))

        max_num = len(model_dict)
        unique_nums = split_numbers(num_selection, max_num)

        for num in unique_nums:
            if 1 <= num <= max_num:
                name = list(model_dict.keys())[num - 1]
                selected_models.extend(model_dict[name])

    unique_models = {}
    for model in selected_models:
        if 'name' not in model and 'huggingface.co' in model['url']:
            model['name'] = os.path.basename(model['url'])
        model['dst_dir'] = dst_dir
        unique_models[model['name']] = model

    return list(unique_models.values())

def handle_submodels(selection, num_selection, model_dict, dst_dir, url):
    submodels = add_submodels(selection, num_selection, model_dict, dst_dir)
    for submodel in submodels:
        if not inpainting_model and "inpainting" in submodel['name']:
            continue
        url += f"{submodel['url']} {submodel['dst_dir']} {submodel['name']}, "
    return url

url = ""
url = handle_submodels(model, model_num, model_list, model_dir, url)
url = handle_submodels(vae, vae_num, vae_list, vae_dir, url)
url = handle_submodels(controlnet, controlnet_num, controlnet_list, control_dir, url)

''' file.txt - added urls '''

def process_file_download(file_url, prefixes, unique_urls):
    files_urls = ""
    current_tag = None

    if file_url.startswith("http"):
        file_url = file_url.replace("/blob/", "/raw/")
        response = requests.get(file_url)
        lines = response.text.split('\n')
    else:
        with open(file_url, 'r') as file:
            lines = file.readlines()

    for line in lines:
        line = line.strip()

        # if any(f'# {tag}' in line.lower() for tag in prefixes):
        #     current_tag = next((tag for tag in prefixes if tag in line.lower()), None)

        for prefix in prefixes.keys():
            if f'# {prefix}'.lower() in line.lower():
                current_tag = prefix
                break

        urls = [url.split('#')[0].strip() for url in line.split(',')]
        for url in urls:
            filter_url = url.split('[')[0].strip()    # Take out the unnecessary parts of the URL

            # Check if the URL is unique
            if url.startswith("http") and filter_url not in unique_urls:
                files_urls += f"{current_tag}:{url}, "
                unique_urls.add(filter_url)

    return files_urls

file_urls = ""
unique_urls = set()

if custom_file_urls:
    for custom_file_url in custom_file_urls.replace(',', '').split():
        if not custom_file_url.endswith('.txt'):
            custom_file_url += '.txt'

        try:
            file_urls += process_file_download(custom_file_url, PREFIXES, unique_urls)
        except FileNotFoundError:
            pass

# URL prefixing
urls = (Model_url, Vae_url, LoRA_url, Embedding_url, Extensions_url)
prefixed_urls = [
    f"{prefix}:{url.strip()}"
    for prefix, url in zip(PREFIXES.keys(), urls)
    if url for url in url.replace(',', '').split()
]
url += ", ".join(prefixed_urls) + ", " + file_urls

if detailed_download == "on":
    print("\n\n\033[33m# ====== Подробная Загрузка ====== #\n\033[0m")
    download(url)
    print("\n\033[33m# =============================== #\n\033[0m")
else:
    with capture.capture_output():
        download(url)

print("\r🏁 Скачивание Завершено!" + " "*15)


## Install of Custom extensions
def _clone_repository(repo, repo_name, extension_dir):
    """Clones the repository to the specified directory."""
    repo_name = repo_name or repo.split('/')[-1]
    command = f'cd {extension_dir} && git clone --depth 1 --recursive {repo} {repo_name} && cd {repo_name} && git fetch'
    get_ipython().system(command)
    
extension_type = 'нодов' if UI == 'ComfyUI' else 'расширений'

if extension_repo:
    print(f"✨ Установка кастомных {extension_type}...", end='')
    with capture.capture_output():
        for repo, repo_name in extension_repo:
            _clone_repository(repo, repo_name, extension_dir)
    print(f"\r📦 Установлено '{len(extension_repo)}' кастомных {extension_type}!")

## List Models and stuff
get_ipython().run_line_magic('run', f'{SCRIPTS}/download-result.py')