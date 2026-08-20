""" WebUI Launcher | by ANXETY """

import subprocess
import argparse
import requests
import logging
import shutil
import shlex
import json
import time
import yaml
import os
import re

from datetime import datetime, timedelta
from IPython.display import clear_output
from collections.abc import Callable
from IPython import get_ipython
from pathlib import Path

from os import chdir as CD

# === SDAIGEN ===
from sdai.constants import COL, HOME_PATH, SCRIPTS_PATH, SETTINGS_PATH, VENV_PATH
from sdai.utils.json import key_exists, load_settings, read, save, update
from sdai.services.tunnel_hub import Tunnel
from sdai.webui_meta import WEBUIS, meta
from sdai.translations import tr


# ~~ SETUP ~~

osENV  = os.environ
ipySys = get_ipython().system

osENV['PYTHONWARNINGS'] = 'ignore'

ENV_NAME   = read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI_NAME    = read(SETTINGS_PATH, 'WEBUI.current')
WEBUI_PATH = Path(read(SETTINGS_PATH, 'WEBUI.webui_path'))
EXTS_DIR   = Path(read(SETTINGS_PATH, 'WEBUI.extension_dir'))

PY_VER = read(SETTINGS_PATH, 'WEBUI.python_version')
BIN    = str(VENV_PATH / 'bin')
PKG    = str(VENV_PATH / f"lib/python{PY_VER}/site-packages")

osENV.update({
    'PATH': f"{BIN}:{osENV['PATH']}" if BIN not in osENV['PATH'] else osENV['PATH'],
    'PYTHONPATH': f"{PKG}:{osENV['PYTHONPATH']}" if PKG not in osENV['PYTHONPATH'] else osENV['PYTHONPATH'],
})

# ~~ LOADING SETTINGS ~~

settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ~~ TUNNELS ~~

def _sync_token(config_path: Path, parse: Callable[[str], str | None], commands: list[str], token: str):
    """Apply token commands when the stored token differs"""
    stored = parse(config_path.read_text(encoding='utf-8')) if config_path.exists() else None
    if stored != token:
        for cmd in commands:
            ipySys(cmd)


def get_public_ip() -> str:
    """Get the public IPv4 address, cached in settings"""
    cached_ip = read(SETTINGS_PATH, 'ENVIRONMENT.public_ip')
    if cached_ip:
        return cached_ip

    try:
        response  = requests.get('https://api64.ipify.org?format=json&ipv4=true', timeout=5)
        public_ip = response.json().get('ip', 'N/A')
        update(SETTINGS_PATH, 'ENVIRONMENT.public_ip', public_ip)
        return public_ip
    except Exception as exc:
        print(tr('ip_error', error=exc))
        return 'N/A'


def setup_tunnels(tunnel_port: int, tunneling_service: Tunnel) -> tuple[list[tuple[str, dict]], int, int, list[str]]:
    """Configure tunnel tokens and check command availability"""
    public_ip = get_public_ip()

    services = [
        ('Gradio',      {'command': f"gradio-tun {tunnel_port}",                          'pattern': r'[\w-]+\.gradio\.live'}),
        ('Pinggy',      {'command': f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{tunnel_port} a.pinggy.io", 'pattern': r'[\w-]+\.run\.pinggy-free\.link'}),
        ('Cloudflared', {'command': f"cl tunnel --url localhost:{tunnel_port}",           'pattern': r'[\w-]+\.trycloudflare\.com'}),
        ('Localtunnel', {'command': f"lt --port {tunnel_port}",                           'pattern': r'[\w-]+\.loca\.lt', 'note': f"| Password: {COL.G}{public_ip}{COL.X}"}),
    ]

    if zrok2_token:
        _sync_token(
            HOME_PATH / '.zrok2/environment.json',
            lambda data: json.loads(data).get('zrok_token'),
            ['zrok2 disable &> /dev/null', f"zrok2 enable {zrok2_token} &> /dev/null"],
            zrok2_token,
        )
        services.append(('Zrok', {'command': f"zrok2 share public localhost:{tunnel_port} --headless", 'pattern': r'[\w-]+\.shares\.zrok\.io'}))

    if ngrok_token:
        _sync_token(
            HOME_PATH / '.config/ngrok/ngrok.yml',
            lambda data: yaml.safe_load(data).get('agent', {}).get('authtoken'),
            [f"ngrok config add-authtoken {ngrok_token}"],
            ngrok_token,
        )
        services.append(('Ngrok', {'command': f"ngrok http http://localhost:{tunnel_port} --log stdout", 'pattern': r'https://[\w-]+\.ngrok-free\.app'}))

    print(f"{COL.Y}{tr('tunnels_checking')}{COL.X}")
    available, unavailable = [], []
    for name, config in services:
        print(f"- 🕒 {tr('tunnel_checking', name=f'{COL.lB}{name}{COL.X}')}...", end=' ')
        if tunneling_service.is_command_available(config['command']):
            available.append((name, config))
            print(f"{COL.G}✓{COL.X}")
        else:
            unavailable.append(name)
            print(f"{COL.R}✗{COL.X}")

    return available, len(services), len(available), unavailable


# ~~ TAG COMPLETE ~~

TAGGER_MAP = {
    'm':        'merged',
    'merged':   'merged',
    'e':        'e621',
    'e621':     'e621',
    'd':        'danbooru',
    'danbooru': 'danbooru',
}

TAGCOMPLETE_NAMES = ('a1111-sd-webui-tagcomplete', 'sd-webui-tagcomplete', 'webui-tagcomplete', 'tag-complete', 'tagcomplete')

CONFIG_FILE = WEBUI_PATH / 'config.json'


def find_latest_tag_file(target: str = 'danbooru') -> str | None:
    """Find the latest tag file for the target in the TagComplete extension"""
    tagcomplete_dir = next(
        (ext for ext in EXTS_DIR.iterdir() if ext.is_dir() and ext.name.lower() in TAGCOMPLETE_NAMES),
        None,
    )
    tags_dir = tagcomplete_dir / 'tags' if tagcomplete_dir else None
    if not tags_dir or not tags_dir.exists():
        return None

    if target == 'merged':
        glob_pattern  = '*_merged_*.csv'
        regex_pattern = r'.*_merged_(\d{4}-\d{2}-\d{2})\.csv$'
    else:
        glob_pattern  = f"{target}_*.csv"
        regex_pattern = rf"{re.escape(target)}_(\d{{4}}-\d{{2}}-\d{{2}})\.csv$"

    latest_file = latest_date = None
    for path in tags_dir.glob(glob_pattern):
        match = re.search(regex_pattern, path.name)
        if not match:
            continue
        try:
            file_date = datetime.strptime(match.group(1), '%Y-%m-%d')
        except ValueError:
            continue
        if latest_date is None or file_date > latest_date:
            latest_date, latest_file = file_date, path.name

    return latest_file


def _set_config(key: str, value: str | None):
    """Set a config key, saving it when missing"""
    value = str(value)
    if key_exists(CONFIG_FILE, key):
        update(CONFIG_FILE, key, value)
    else:
        save(CONFIG_FILE, key, value)


def _sync_version_uid():
    """Sync VERSION_UID from launch_utils.py into the WebUI config"""
    launch_utils = WEBUI_PATH / 'modules/launch_utils.py'
    if not launch_utils.exists():
        return

    match = re.search(r'VERSION_UID:\s*Final\[str\]\s*=\s*["\'](.+?)["\']', launch_utils.read_text(encoding='utf-8'))
    if match:
        _set_config('VERSION_UID', match.group(1))


def _update_config_paths(tagger: str | None = None):
    """Update tagger and ADetailer paths in the WebUI config"""
    _set_config('tac_tagFile', find_latest_tag_file(TAGGER_MAP.get(tagger, 'danbooru')))
    _set_config('tagger_hf_cache_dir', f"{WEBUI_PATH}/models/interrogators/")
    _set_config('ad_extra_models_dir', adetailer_dir)

    # Auto-sync VERSION_UID | Fix for NEO
    if UI_NAME == 'Neo':
        _sync_version_uid()


# ~~ LAUNCHER ~~

ENCRYPT_PASS = 'emoy4cnkm6imbysp84zmfiz1opahooblh7j34sgh'
PINGGY_TIMER = 3620  # Free tier lasts 1 hour, +20s margin


def _trashing():
    """Remove .ipynb_checkpoints directories from all WebUI roots"""
    for ui in WEBUIS:
        cmd = f"find {HOME_PATH / ui} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_launch_command() -> str:
    """Construct the launch command from settings"""
    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --skip-torch-cuda-test --theme dark'

    if ENV_NAME == 'Kaggle':
        common_args += f" --encrypt-pass={ENCRYPT_PASS}"
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"

    launcher = meta(UI_NAME)['launcher']

    if UI_NAME == 'ComfyUI':
        return f"python3 {launcher} {commandline_arguments}"
    return f"python3 {launcher} {commandline_arguments}{common_args}"


def _setup_comfyui():
    """Prepare ComfyUI: node deps, requirements and ffmpeg config"""
    osENV['MPLBACKEND'] = 'agg'

    if check_nodes_deps:
        ipySys('python3 install-deps.py')
        clear_output(wait=True)

    comfyui_settings = SCRIPTS_PATH / 'ComfyUI.json'
    if not key_exists(comfyui_settings, 'install_req', True):
        print(tr('comfy_deps_installing'))
        subprocess.run(['pip', 'install', '-r', 'requirements.txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        save(comfyui_settings, 'install_req', True)
        clear_output(wait=True)

    was_config = EXTS_DIR / 'was-node-suite-comfyui/was_suite_config.json'
    ffmpeg     = shutil.which('ffmpeg')
    if was_config.exists() and ffmpeg:
        config = json.loads(was_config.read_text(encoding='utf-8'))
        config['ffmpeg_bin_path'] = ffmpeg
        was_config.write_text(json.dumps(config, indent=2), encoding='utf-8')


def _print_selected_tagger(tagger: str):
    """Print the selected tagger and its latest tag file"""
    target   = TAGGER_MAP.get(tagger, tagger)
    tag_file = find_latest_tag_file(target)
    if tag_file:
        print(f"{COL.B}{tr('selected_tagger', tagger=f'{COL.lB}{target}{COL.X}', tag_file=tag_file)}\n")


def _print_session_duration():
    """Print the session duration from the saved timer"""
    try:
        timer    = float((WEBUI_PATH / 'static/timer.txt').read_text(encoding='utf-8'))
        duration = timedelta(seconds=time.time() - timer)
        time_str = f"{COL.Y}{str(duration).split('.')[0]}{COL.X}"
        print(f"\n{tr('session_duration', time=time_str)}")
    except FileNotFoundError:
        pass


# ~~ MAIN ~~

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log', action='store_true', help='Show failed tunnel details')
    parser.add_argument('-t', '--tagger', choices=TAGGER_MAP, help='Select tagger type: m/merged, e/e621, d/danbooru')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    print(f"{tr('please_wait')}\n")

    osENV.setdefault('IIB_ACCESS_CONTROL', 'disable')
    osENV['UVICORN_LOG_LEVEL'] = 'error'

    tunnel_port = meta(UI_NAME)['port']

    tunneling_service = Tunnel(tunnel_port, check_command_available=False)
    tunneling_service.logger.setLevel(logging.DEBUG if args.log else logging.INFO)

    available_tunnels, total, success, unavailable = setup_tunnels(tunnel_port, tunneling_service)

    for name, config in available_tunnels:
        tunneling_service.add_tunnel(name=name, **config)

    clear_output(wait=True)

    _trashing()
    _update_config_paths(args.tagger)
    launcher = get_launch_command()

    ipySys(f"echo -n {int(time.time()) + PINGGY_TIMER} > {WEBUI_PATH}/static/timer-pinggy.txt")

    with tunneling_service:
        CD(WEBUI_PATH)

        if UI_NAME == 'ComfyUI':
            _setup_comfyui()

        print(f"{COL.B}{tr('tunnels_total', total=total)}{COL.X} | {COL.G}{tr('tunnels_available', count=success)}{COL.X} | {COL.R}{tr('tunnels_unavailable', count=len(unavailable))}{COL.X}\n")

        if args.log and unavailable:
            print(f"{COL.R}{tr('unavailable_header')}{COL.X}")
            for name in unavailable:
                print(tr('cmd_not_found', name=name))
            print()

        if UI_NAME != 'ComfyUI' and args.tagger:
            _print_selected_tagger(args.tagger)

        print(f"🔧 WebUI: {COL.B}{UI_NAME}{COL.X}")

        try:
            ipySys(launcher)
        except KeyboardInterrupt:
            pass

    if zrok2_token:
        ipySys('zrok2 disable &> /dev/null')
        print(f"\n{tr('zrok_disabled')}")

    _print_session_duration()
