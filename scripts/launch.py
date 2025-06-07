# ~ launch.py | by ANXETY ~

from TunnelHub import Tunnel    # Tunneling
import json_utils as js         # JSON

from IPython.display import clear_output
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import nest_asyncio
import subprocess
import requests
import argparse
import logging
import asyncio
import shlex
import time
import json
import yaml
import sys
import os
import re


CD = os.chdir
ipySys = get_ipython().system

# Constants
HOME = Path.home()
VENV = HOME / 'venv'
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = js.read(SETTINGS_PATH, 'WEBUI.webui_path')

nest_asyncio.apply()  # Async support for Jupyter

BIN = str(VENV / 'bin')
PKG = str(VENV / 'lib/python3.10/site-packages')

if BIN not in os.environ['PATH']:
    os.environ['PATH'] = BIN + ':' + os.environ['PATH']
if PKG not in os.environ['PYTHONPATH']:
    os.environ['PYTHONPATH'] = PKG + ':' + os.environ['PYTHONPATH']


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

## ====================== Helpers ========================

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--log', action='store_true', help='Show failed tunnel details')
    return parser.parse_args()

def _trashing():
    dirs = ['A1111', 'ComfyUI', 'Forge', 'Classic', 'ReForge', 'SD-UX']
    paths = [Path(HOME) / name for name in dirs]

    for path in paths:
        cmd = f"find {path} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _update_config_paths():
    """Update configuration paths in WebUI config file"""
    config_mapping = {
        'tagger_hf_cache_dir': f"{WEBUI}/models/interrogators/",
        'ad_extra_models_dir': adetailer_dir,
        # 'sd_checkpoint_hash': '',
        # 'sd_model_checkpoint': '',
        'sd_vae': 'None'
    }

    config_file = f"{WEBUI}/config.json"
    for key, value in config_mapping.items():
        if js.key_exists(config_file, key):
            js.update(config_file, key, str(value))
        else:
            js.save(config_file, key, str(value))

def get_launch_command():
    """Construct launch command based on configuration"""
    base_args = commandline_arguments
    password = 'ha4ez7147b5vdlu5u8f8flrllgn61kpbgbh6emil'

    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --theme dark'
    if ENV_NAME == 'Kaggle':
        common_args += f" --encrypt-pass={password}"

    # Accent Color For Anxety-Theme
    if theme_accent != 'anxety':
        common_args += f" --anxety {theme_accent}"

    if UI == 'ComfyUI':
        return f"python3 main.py {base_args}"
    else:
        return f"python3 launch.py {base_args}{common_args}"

## ===================== Tunneling =======================

class TunnelManager:
    """Class for managing tunnel services"""

    def __init__(self, tunnel_port):
        self.tunnel_port = tunnel_port
        self.tunnels = []
        self.error_reasons = []
        self.public_ip = self._get_public_ip()
        self.checking_queue = asyncio.Queue()
        self.timeout = 10

    def _get_public_ip(self) -> str:
        """Retrieve and cache public IPv4 address"""
        cached_ip = js.read(SETTINGS_PATH, 'ENVIRONMENT.public_ip')
        if cached_ip:
            return cached_ip

        try:
            response = requests.get('https://api64.ipify.org?format=json&ipv4=true', timeout=5)
            public_ip = response.json().get('ip', 'N/A')
            js.update(SETTINGS_PATH, 'ENVIRONMENT.public_ip', public_ip)
            return public_ip
        except Exception as e:
            print(f"Error getting public IP address: {e}")
            return 'N/A'

    async def _print_status(self):
        """Async status printer"""
        print('\033[33m>> Tunnels:\033[0m')
        while True:
            service_name = await self.checking_queue.get()
            print(f"- 🕒 Checking \033[36m{service_name}\033[0m...")
            self.checking_queue.task_done()

    async def _test_tunnel(self, name, config):
        """Async tunnel testing"""
        await self.checking_queue.put(name)
        try:
            process = await asyncio.create_subprocess_exec(
                *shlex.split(config['command']),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            start_time = time.time()
            output = []
            pattern_found = False
            check_interval = 0.5

            while time.time() - start_time < self.timeout:
                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=check_interval
                    )
                    if not line:
                        continue

                    line = line.decode().strip()
                    output.append(line)

                    if config['pattern'].search(line):
                        pattern_found = True
                        break

                except asyncio.TimeoutError:
                    continue

            if process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=2)
                except:
                    pass

            if pattern_found:
                return True, None

            error_msg = '\n'.join(output[-3:]) or 'No output received'
            return False, f"{error_msg[:300]}..."

        except Exception as e:
            return False, f"Process error: {str(e)}"

    async def setup_tunnels(self):
        """Async tunnel configuration"""
        services = [
            ('Gradio', {
                'command': f"gradio-tun {self.tunnel_port}",
                'pattern': re.compile(r'[\w-]+\.gradio\.live')
            }),
            ('Serveo', {
                'command': f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{self.tunnel_port} serveo.net",
                'pattern': re.compile(r'[\w-]+\.serveo\.net')
            }),
            ('Pinggy', {
                'command': f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{self.tunnel_port} a.pinggy.io",
                'pattern': re.compile(r'[\w-]+\.a\.free\.pinggy\.link')
            }),
            ('Cloudflared', {
                'command': f"cl tunnel --url localhost:{self.tunnel_port}",
                'pattern': re.compile(r'[\w-]+\.trycloudflare\.com')
            }),
            ('Localtunnel', {
                'command': f"lt --port {self.tunnel_port}",
                'pattern': re.compile(r'[\w-]+\.loca\.lt'),
                'note': f"Password: \033[32m{self.public_ip}\033[0m"
            })
        ]

        if zrok_token:
            env_path = HOME / '.zrok/environment.json'
            current_token = None

            if env_path.exists():
                with open(env_path, 'r') as f:
                    current_token = json.load(f).get('zrok_token')

            if current_token != zrok_token:
                ipySys('zrok disable &> /dev/null')
                ipySys(f"zrok enable {zrok_token} &> /dev/null")

            services.append(('Zrok', {
                'command': f"zrok share public http://localhost:{self.tunnel_port}/ --headless",
                'pattern': re.compile(r'[\w-]+\.share\.zrok\.io')
            }))

        if ngrok_token:
            config_path = HOME / '.config/ngrok/ngrok.yml'
            current_token = None

            if config_path.exists():
                with open(config_path, 'r') as f:
                    current_token = yaml.safe_load(f).get('agent', {}).get('authtoken')

            if current_token != ngrok_token:
                ipySys(f"ngrok config add-authtoken {ngrok_token}")

            services.append(('Ngrok', {
                'command': f"ngrok http http://localhost:{self.tunnel_port} --log stdout",
                'pattern': re.compile(r'https://[\w-]+\.ngrok-free\.app')
            }))

        # Create status printer task
        printer_task = asyncio.create_task(self._print_status())

        # Run all tests concurrently
        tasks = []
        for name, config in services:
            tasks.append(self._test_tunnel(name, config))

        results = await asyncio.gather(*tasks)

        # Cancel status printer
        printer_task.cancel()
        try:
            await printer_task
        except asyncio.CancelledError:
            pass

        # Process results
        for (name, config), (success, error) in zip(services, results):
            if success:
                self.tunnels.append({**config, 'name': name})
            else:
                self.error_reasons.append({'name': name, 'reason': error})

        return (
            self.tunnels,
            len(services),
            len(self.tunnels),
            len(self.error_reasons)
        )

## ========================= Main ========================

if __name__ == '__main__':
    """Main execution flow"""
    args = parse_arguments()
    print('Please Wait...\n')

    os.environ['PYTHONWARNINGS'] = 'ignore'

    # Initialize tunnel manager and services
    tunnel_port = 8188 if UI == 'ComfyUI' else 7860
    tunnel_mgr = TunnelManager(tunnel_port)

    # Run async setup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tunnels, total, success, errors = loop.run_until_complete(tunnel_mgr.setup_tunnels())

    # Set up tunneling service
    tunnelingService = Tunnel(tunnel_port)
    tunnelingService.logger.setLevel(logging.DEBUG)

    for tunnel in tunnels:
        tunnelingService.add_tunnel(**tunnel)

    clear_output(wait=True)

    # Launch sequence
    _trashing()
    _update_config_paths()
    LAUNCHER = get_launch_command()

    # Setup pinggy timer
    ipySys(f"echo -n {int(time.time())+(3600+20)} > {WEBUI}/static/timer-pinggy.txt")

    with tunnelingService:
        CD(WEBUI)

        if UI == 'ComfyUI':
            COMFYUI_SETTINGS_PATH = SCR_PATH / 'ComfyUI.json'
            if check_custom_nodes_deps:
                ipySys('python3 install-deps.py')
                clear_output(wait=True)

            if not js.key_exists(COMFYUI_SETTINGS_PATH, 'install_req', True):
                print('Installing ComfyUI dependencies...')
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                js.save(COMFYUI_SETTINGS_PATH, 'install_req', True)
                clear_output(wait=True)

        print(f"\033[34m>> Total Tunnels:\033[0m {total} | \033[32mSuccess:\033[0m {success} | \033[31mErrors:\033[0m {errors}\n")

        # Display error details if any
        if args.log and errors > 0:
            print('\033[31m>> Failed Tunnels:\033[0m')
            for error in tunnel_mgr.error_reasons:
                print(f"  - {error['name']}: {error['reason']}")
            print()

        print(f"🔧 WebUI: \033[34m{UI}\033[0m")

        try:
            ipySys(LAUNCHER)
        except KeyboardInterrupt:
            pass

    # Post-execution cleanup
    if zrok_token:
        ipySys('zrok disable &> /dev/null')
        print('/n🔐 Zrok tunnel disabled :3')

    # Display session duration
    try:
        with open(f"{WEBUI}/static/timer.txt") as f:
            timer = float(f.read())
            duration = timedelta(seconds=time.time() - timer)
            print(f"\n⌚️ Session duration: \033[33m{str(duration).split('.')[0]}\033[0m")
    except FileNotFoundError:
        pass