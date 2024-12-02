# ~ setup.py | by ANXETY ~

from IPython.display import display, HTML, clear_output
from urllib.parse import urljoin
from pathlib import Path
from tqdm import tqdm
import importlib.util
import importlib
import json
import time
import sys
import os

import argparse 

# Constants
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

# ================ BEAUTIFUL TEXT :3 ================
def display_info(env, scr_folder):
    content = f"""
    <div id="text-container">
      <span>A</span>
      <span>N</span>
      <span>X</span>
      <span>E</span>
      <span>T</span>
      <span>Y</span>
      <span>&nbsp;</span>
      <span>S</span>
      <span>D</span>
      <span>-</span>
      <span>W</span>
      <span>E</span>
      <span>B</span>
      <span>U</span>
      <span>I</span>
      <span>&nbsp;</span>
      <span>V</span>
      <span>2</span>
    </div>

    <div id="message-container">
      <span>Done! Now you can run the cells below. ☄️</span>
      <span>Runtime environment: <span class="env">{env}</span></span>
      <span>File Location: <span class="files-location">{scr_folder}</span></span>
    </div>

    <style>
    @import url('https://fonts.googleapis.com/css2?family=Righteous&display=swap');

    #text-container, #message-container {{
      display: flex;
      flex-direction: column;
      height: auto;
      font-family: "Righteous", sans-serif;
      margin: 0;
      padding: 5px 0;
      user-select: none;
    }}

    #text-container {{
      display: flex;
      flex-direction: row;
      align-items: center;
    }}

    #text-container > span {{
      font-size: 4vw;
      display: inline-block;
      color: #FF7A00;
      opacity: 0;
      transform: translateY(-50px);
      filter: blur(3px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    #text-container.loaded > span {{
      color: #FFFFFF;
      opacity: 1;
      transform: translateY(0);
      filter: blur(0);
    }}

    #message-container > span {{
      font-size: 2vw;
      color: #FF7A00;
      opacity: 0;
      transform: translateY(30px);
      filter: blur(3px);
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    #message-container.loaded > span {{
      color: #FFFFFF;
      opacity: 1;
      transform: translateY(0);
      filter: blur(0);
    }}

    .env {{
      color: #FFA500;
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}

    .files-location {{
      color: #FF99C2;
      transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }}
    </style>

    <script>
    function initAnimation() {{
        const textContainer = document.getElementById('text-container');
        const messageContainer = document.getElementById('message-container');
        const textSpans = textContainer.querySelectorAll('span');
        const messageSpans = messageContainer.querySelectorAll('span');

        // Set transition delay for each span in the text container
        textSpans.forEach((span, index) => {{
          span.style.transitionDelay = `${{index * 25}}ms`;
        }});

        // Set transition delay for each span in the message container
        messageSpans.forEach((span, index) => {{
          span.style.transitionDelay = `${{index * 50}}ms`;
        }});


        // Set a timeout to add the 'loaded' class to both containers after a short delay
        setTimeout(() => {{
          textContainer.classList.add('loaded');
          messageContainer.classList.add('loaded');
        }}, 250);
    }}
    initAnimation();
    </script>
    """

    display(HTML(content))

# ==================== ENVIRONMENT ====================

def detect_environment():
    environments = {
        'COLAB_GPU': 'Google Colab',
        'KAGGLE_URL_BASE': 'Kaggle'
    }
    for env_var, name in environments.items():
        if env_var in os.environ:
            return name
    raise EnvironmentError(f"Unsupported runtime environment. Supported: {', '.join(environments.values())}")

# ==================== MODULES ====================

def clear_module_cache(modules_folder):
    for module_name in list(sys.modules.keys()):
        module = sys.modules[module_name]
        if hasattr(module, '__file__') and module.__file__ and module.__file__.startswith(str(modules_folder)):
            del sys.modules[module_name]
    importlib.invalidate_caches()

def setup_module_folder(scr_folder):
    clear_module_cache(scr_folder)
    modules_folder = scr_folder / "modules"
    modules_folder.mkdir(parents=True, exist_ok=True)
    if str(modules_folder) not in sys.path:
        sys.path.append(str(modules_folder))

# ==================== FILE HANDLING ====================

def save_environment_to_json(data, scr_folder):
    file_path = scr_folder / 'settings.json'
    existing_data = {}
    
    if file_path.exists():
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)

    existing_data.update(data)

    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

def get_start_timer():
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, 'r') as f:
            settings = json.load(f)
            return settings.get('ENVIRONMENT', {}).get('start_timer', int(time.time() - 5))
    return int(time.time() - 5)

def create_environment_data(env, scr_folder, lang, branch):
    scr_folder.mkdir(parents=True, exist_ok=True)
    install_deps = importlib.util.find_spec('xformers') is not None
    start_timer = get_start_timer()

    return {
        'ENVIRONMENT': {
            'lang': lang,
            'branch': branch,
            'env_name': env,
            'install_deps': install_deps,
            'home_path': str(scr_folder.parent),
            'scr_path': str(scr_folder),
            'start_timer': start_timer,
            'public_ip': ''
        }
    }

def process_files(scr_path, files_dict, branch, parent_folder=''):
    file_list = []
    repo = 'sdAIgen'

    for folder, contents in files_dict.items():
        folder_path = scr_path / parent_folder / folder
        os.makedirs(folder_path, exist_ok=True)

        if isinstance(contents, list):
            for file in contents:
                file_url = urljoin(f"https://raw.githubusercontent.com/anxety-solo/{repo}/{branch}/", f"{parent_folder}{folder}/{file}")
                file_path = folder_path / file
                file_list.append((file_url, file_path))

        elif isinstance(contents, dict):
            file_list.extend(process_files(scr_path, contents, branch, parent_folder + folder + '/'))

    return file_list

async def download_file(session, url, path):
    async with session.get(url) as response:
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(await response.read())

async def download_files_async(scr_path, lang, branch):
    files_dict = {
        'CSS': ['main-widgets.css', 'download-result.css', 'auto-cleaner.css'],
        'JS': ['main-widgets.js'],
        'modules': ['json_utils.py', 'webui_utils.py', 'widget_factory.py', 'TunnelHub.py', 'CivitaiAPI.py'],
        'scripts': {
            'UIs': ['A1111.py', 'ReForge.py', 'ComfyUI.py', 'Forge.py'],
            lang: [f'widgets-{lang}.py', f'downloading-{lang}.py'],
            '': ['launch.py', 'auto-cleaner.py', 'download-result.py', '_models-data.py', '_xl-models-data.py']
        }
    }

    file_list = process_files(scr_path, files_dict, branch)
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for file_url, file_path in file_list:
            tasks.append(download_file(session, file_url, file_path))
        
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Downloading files", unit="file"):
            await future

    clear_output(wait=True)

# ======================= MAIN ======================

import aiohttp
import asyncio
import nest_asyncio
nest_asyncio.apply()

async def main_async():
    parser = argparse.ArgumentParser(description='Download script for ANXETY.')
    parser.add_argument('--lang', type=str, default='en', help='Language to be used (default: en)')
    parser.add_argument('--branch', type=str, default='main', help='Branch to download files from (default: main)')
    args = parser.parse_args()

    env = detect_environment()
    await download_files_async(SCR_PATH, args.lang, args.branch)    # download scripts files
    setup_module_folder(SCR_PATH)   # setup main dir -> modules

    env_data = create_environment_data(env, SCR_PATH, args.lang, args.branch)
    save_environment_to_json(env_data, SCR_PATH)

    display_info(env, SCR_PATH)   # display info text :3

if __name__ == "__main__":
    asyncio.run(main_async())