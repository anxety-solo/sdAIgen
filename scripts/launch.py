""" WebUI Launcher | by ANXETY """

from sdai.constants import HOME_PATH, SCRIPTS_PATH, SETTINGS_PATH, VENV_PATH, COL
from sdai.services.tunnel_hub import Tunnel
from sdai.translations import tr
from sdai.utils.json import read, save, update, key_exists

from IPython.display import clear_output
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import argparse
import logging
import shutil
import shlex
import time
import json
import yaml
import os
import re


osENV = os.environ
CD = os.chdir
ipySys = get_ipython().system

osENV['PYTHONWARNINGS'] = 'ignore'

ENV_NAME = read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = read(SETTINGS_PATH, 'WEBUI.webui_path')
EXTS = Path(read(SETTINGS_PATH, 'WEBUI.extension_dir'))


BIN = str(VENV_PATH / 'bin')
PYTHON_VERSION = read(SETTINGS_PATH, 'WEBUI.python_version')
PKG = str(VENV_PATH / f"lib/python{PYTHON_VERSION}/site-packages")

osENV.update({
    'PATH': f"{BIN}:{osENV['PATH']}" if BIN not in osENV['PATH'] else osENV['PATH'],
    'PYTHONPATH': f"{PKG}:{osENV['PYTHONPATH']}" if PKG not in osENV['PYTHONPATH'] else osENV['PYTHONPATH']
})


# Tag-CSV Mapping
TAGGER_MAP = {
    'm': 'merged', 'merged': 'merged',
    'e': 'e621', 'e621': 'e621',
    'd': 'danbooru', 'danbooru': 'danbooru'
}


# ~~ Load Settings ~~

def load_settings(path):
    """Load settings from a JSON file"""
    try:
        return {
            **read(path, 'ENVIRONMENT'),
            **read(path, 'WIDGETS'),
            **read(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as exc:
        print(tr('settings_load_error', error=exc))
        return {}


# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ~~ Helper Functions ~~

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log', action='store_true', help='Show failed tunnel details')
    parser.add_argument(
        '-t', '--tagger',
        choices=['m', 'merged', 'e', 'e621', 'd', 'danbooru'],
        help='Select tagger type: m/merged, e/e621, d/danbooru'
    )
    return parser.parse_args()


def _trashing():
    dirs = ['A1111', 'ComfyUI', 'Forge', 'Classic', 'Neo', 'ReForge', 'SD-UX']
    paths = [Path(HOME_PATH) / name for name in dirs]

    for path in paths:
        cmd = f"find {path} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_latest_tag_file(target='danbooru'):
    """Find the latest tag file for specified target in TagComplete extension"""
    from datetime import datetime

    possible_names = {
        'a1111-sd-webui-tagcomplete',
        'sd-webui-tagcomplete',
        'webui-tagcomplete',
        'tag-complete',
        'tagcomplete',
    }

    # Find TagComplete extension directory
    tagcomplete_dir = next(
        (ext_dir for ext_dir in EXTS.iterdir() if ext_dir.is_dir() and ext_dir.name.lower() in possible_names),
        None
    )
    if not tagcomplete_dir:
        return None

    tags_dir = tagcomplete_dir / 'tags'
    if not tags_dir.exists():
        return None

    # Prepare patterns
    if target == 'merged':
        glob_pattern = '*_merged_*.csv'
        regex_pattern = r'.*_merged_(\d{4}-\d{2}-\d{2})\.csv$'
    else:
        glob_pattern = f"{target}_*.csv"
        regex_pattern = rf"{re.escape(target)}_(\d{{4}}-\d{{2}}-\d{{2}})\.csv$"

    # Find latest file
    latest_file = None
    latest_date = None

    for file_path in tags_dir.glob(glob_pattern):
        match = re.search(regex_pattern, file_path.name)
        if not match:
            continue
        try:
            file_date = datetime.strptime(match.group(1), '%Y-%m-%d')
        except ValueError:
            continue
        if latest_date is None or file_date > latest_date:
            latest_date, latest_file = file_date, file_path.name

    return latest_file


def _update_config_paths(tagger=None):
    """Update configuration paths in WebUI config file"""
    target_tagger = TAGGER_MAP.get(tagger, 'danbooru')

    config_mapping = {
        'tac_tagFile': find_latest_tag_file(target_tagger),
        'tagger_hf_cache_dir': f"{WEBUI}/models/interrogators/",
        'ad_extra_models_dir': adetailer_dir,
        # 'sd_vae': 'None'
    }

    config_file = f"{WEBUI}/config.json"
    for key, value in config_mapping.items():
        if key_exists(config_file, key):
            update(config_file, key, str(value))
        else:
            save(config_file, key, str(value))

    # Auto-sync VERSION_UID | Fix for NEO
    if UI == 'Neo':
        launch_utils_path = Path(WEBUI) / 'modules/launch_utils.py'
        if launch_utils_path.exists():
            content = launch_utils_path.read_text(encoding='utf-8')
            match = re.search(r'VERSION_UID:\s*Final\[str\]\s*=\s*["\'](.+?)["\']', content)
            if match:
                version_uid = match.group(1)
                if key_exists(config_file, 'VERSION_UID'):
                    update(config_file, 'VERSION_UID', version_uid)
                else:
                    save(config_file, 'VERSION_UID', version_uid)


def get_launch_command():
    """Construct launch command based on configuration"""
    base_args = commandline_arguments
    password = 'emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'

    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --skip-torch-cuda-test --theme dark'  # nah: --no-gradio-queue
    if ENV_NAME == 'Kaggle':
        common_args += f" --encrypt-pass={password}"

    # Accent Color For Anxety-Theme
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"

    if UI == 'ComfyUI':
        return f"python3 main.py {base_args}"
    else:
        return f"python3 launch.py {base_args}{common_args}"


# ~~ Tunneling ~~

def is_command_available(command: str) -> bool:
    """Check if command is available in PATH"""
    cmd_name = command.split()[0]
    return any(
        os.access(os.path.join(path, cmd_name), os.X_OK)
        for path in os.environ.get('PATH', '').split(os.pathsep)
    )


def get_public_ip() -> str:
    """Retrieve and cache public IPv4 address"""
    cached_ip = read(SETTINGS_PATH, 'ENVIRONMENT.public_ip')
    if cached_ip:
        return cached_ip

    try:
        response = requests.get('https://api64.ipify.org?format=json&ipv4=true', timeout=5)
        public_ip = response.json().get('ip', 'N/A')
        update(SETTINGS_PATH, 'ENVIRONMENT.public_ip', public_ip)
        return public_ip
    except Exception as exc:
        print(tr('ip_error', error=exc))
        return 'N/A'


def setup_tunnels(tunnel_port):
    """Setup tunnel configurations with command availability check"""
    public_ip = get_public_ip()

    services = [
        ('Gradio', {
            'command': f"gradio-tun {tunnel_port}",
            'pattern': r'[\w-]+\.gradio\.live'
        }),
        ('Pinggy', {
            'command': f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{tunnel_port} a.pinggy.io",
            'pattern': r'[\w-]+\.run\.pinggy-free\.link'
        }),
        ('Cloudflared', {
            'command': f"cl tunnel --url localhost:{tunnel_port}",
            'pattern': r'[\w-]+\.trycloudflare\.com'
        }),
        ('Localtunnel', {
            'command': f"lt --port {tunnel_port}",
            'pattern': r'[\w-]+\.loca\.lt',
            'note': f"| Password: {COL.G}{public_ip}{COL.X}"
        })
    ]

    # Zrok setup
    if zrok_token:
        env_path = HOME_PATH / '.zrok/environment.json'
        current_token = None

        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                current_token = json.load(f).get('zrok_token')

        if current_token != zrok_token:
            ipySys('zrok disable &> /dev/null')
            ipySys(f"zrok enable {zrok_token} &> /dev/null")

        services.append(('Zrok', {
            'command': f"zrok share public http://localhost:{tunnel_port}/ --headless",
            'pattern': r'[\w-]+\.share\.zrok\.io'
        }))

    # Ngrok setup
    if ngrok_token:
        config_path = HOME_PATH / '.config/ngrok/ngrok.yml'
        current_token = None

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                current_token = yaml.safe_load(f).get('agent', {}).get('authtoken')

        if current_token != ngrok_token:
            ipySys(f"ngrok config add-authtoken {ngrok_token}")

        services.append(('Ngrok', {
            'command': f"ngrok http http://localhost:{tunnel_port} --log stdout",
            'pattern': r'https://[\w-]+\.ngrok-free\.app'
        }))

    # Check command availability
    available_tunnels = []
    unavailable_tunnels = []

    print(f"{COL.Y}{tr('checking_tunnels')}{COL.X}")
    for name, config in services:
        print(f"- 🕒 {tr('checking_tunnel', name=f'{COL.lB}{name}{COL.X}')}...", end=' ')
        if is_command_available(config['command']):
            available_tunnels.append((name, config))
            print(f"{COL.G}✓{COL.X}")
        else:
            unavailable_tunnels.append(name)
            print(f"{COL.R}✗{COL.X}")

    return available_tunnels, len(services), len(available_tunnels), unavailable_tunnels


# ~~ Main ~~

if __name__ == '__main__':
    """Main execution flow"""
    args = parse_arguments()
    print(f"{tr('please_wait')}\n")

    osENV.setdefault('IIB_ACCESS_CONTROL', 'disable')
    osENV['UVICORN_LOG_LEVEL'] = 'error'
    # osENV.setdefault('IIB_SKIP_OPTIONAL_DEPS', '1')    # (thx: github.com/zanllp/sd-webui-infinite-image-browsing/issues/880)

    # Initialize tunnel manager
    tunnel_port = 8188 if UI == 'ComfyUI' else 7860
    available_tunnels, total, success, unavailable = setup_tunnels(tunnel_port)

    # Setup tunneling service
    tunneling_service = Tunnel(tunnel_port, check_command_available=False)
    tunneling_service.logger.setLevel(logging.DEBUG if args.log else logging.INFO)

    for name, config in available_tunnels:
        tunneling_service.add_tunnel(name=name, **config)

    clear_output(wait=True)

    # Launch sequence
    _trashing()
    _update_config_paths(args.tagger)
    LAUNCHER = get_launch_command()

    # Setup pinggy timer
    ipySys(f"echo -n {int(time.time())+(3600+20)} > {WEBUI}/static/timer-pinggy.txt")

    with tunneling_service:
        CD(WEBUI)

        if UI == 'ComfyUI':
            osENV['MPLBACKEND'] = 'agg'

            COMFYUI_SETTINGS_PATH = SCRIPTS_PATH / 'ComfyUI.json'
            if check_nodes_deps:
                ipySys('python3 install-deps.py')
                clear_output(wait=True)

            if not key_exists(COMFYUI_SETTINGS_PATH, 'install_req', True):
                print(tr('comfy_deps_installing'))
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                save(COMFYUI_SETTINGS_PATH, 'install_req', True)
                clear_output(wait=True)

            was_cfg_path = EXTS / 'was-node-suite-comfyui/was_suite_config.json'
            ffmpeg_path = shutil.which('ffmpeg')
            if was_cfg_path.exists() and ffmpeg_path:
                cfg = json.loads(was_cfg_path.read_text(encoding='utf-8'))
                cfg['ffmpeg_bin_path'] = ffmpeg_path
                was_cfg_path.write_text(json.dumps(cfg, indent=2), encoding='utf-8')

        print(f"{COL.B}{tr('tunnels_total', total=total)}{COL.X} | {COL.G}{tr('tunnels_available', count=success)}{COL.X} | {COL.R}{tr('tunnels_unavailable', count=len(unavailable))}{COL.X}\n")

        # Display unavailable tunnels if any
        if args.log and unavailable:
            print(f"{COL.R}{tr('unavailable_header')}{COL.X}")
            for name in unavailable:
                print(tr('cmd_not_found', name=name))
            print()

        # Display selected tagger if was used
        if UI != 'ComfyUI' and args.tagger:
            selected_tagger = TAGGER_MAP.get(args.tagger, args.tagger)
            tag_file = find_latest_tag_file(selected_tagger)

            if tag_file:
                print(f"{COL.B}{tr('selected_tagger', tagger=f'{COL.lB}{selected_tagger}{COL.X}', tag_file=tag_file)}\n")

        print(f"🔧 WebUI: {COL.B}{UI}{COL.X}")

        try:
            ipySys(LAUNCHER)
        except KeyboardInterrupt:
            pass

    # Post-execution cleanup
    if zrok_token:
        ipySys('zrok disable &> /dev/null')
        print(f"\n{tr('zrok_disabled')}")

    # Display session duration
    try:
        with open(f"{WEBUI}/static/timer.txt", encoding='utf-8') as f:
            timer = float(f.read())
            duration = timedelta(seconds=time.time() - timer)
            dur_str = f"{COL.Y}{str(duration).split('.')[0]}{COL.X}"
            print(f"\n{tr('session_duration', time=dur_str)}")
    except FileNotFoundError:
        pass
