from json_utils import read_json, save_json, update_json
from pathlib import Path
import os

# Constants
HOME = Path.home()
SETTINGS_PATH = HOME / 'ANXETY' / 'settings.json'
SCR_PATH = HOME / 'ANXETY'

WEBUI_PATHS = {
    'A1111': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs'),
    'ReForge': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs'),
    'ComfyUI': ('checkpoints', 'vae', 'loras', 'embeddings', 'custom_nodes', 'upscale_models', 'output'),
    'Forge': ('Stable-diffusion', 'VAE', 'Lora', 'embeddings', 'extensions', 'ESRGAN', 'outputs')
}

def update_current_webui(current_value):
    """Update the current WebUI value and save it."""
    current_stored_value = read_json(SETTINGS_PATH, 'WEBUI.current')
    latest_value = read_json(SETTINGS_PATH, 'WEBUI.latest', None)

    if latest_value is None or current_stored_value != current_value:
        save_json(SETTINGS_PATH, 'WEBUI.latest', current_stored_value)
        save_json(SETTINGS_PATH, 'WEBUI.current', current_value)

    save_json(SETTINGS_PATH, 'WEBUI.webui_path', str(HOME / current_value))
    _set_webui_paths(current_value)

def _set_webui_paths(ui):
    """Set web UI paths based on the selected UI."""
    if ui not in WEBUI_PATHS:
        return

    webui = HOME / ui
    models = webui / 'models'
    checkpoint, vae, lora, embed, extension, upscale, webui_output = WEBUI_PATHS[ui]

    model_dir = models / checkpoint
    vae_dir = models / vae
    lora_dir = models / lora
    embed_dir = models / embed if ui == 'ComfyUI' else webui / embed
    extension_dir = webui / extension
    upscale_dir = models / upscale
    control_dir = models / ('controlnet' if ui == 'ComfyUI' else 'ControlNet')
    adetailer_dir = models / 'adetailer'

    paths = {
        'model_dir': str(model_dir),
        'vae_dir': str(vae_dir),
        'lora_dir': str(lora_dir),
        'embed_dir': str(embed_dir),
        'extension_dir': str(extension_dir),
        'control_dir': str(control_dir),
        'upscale_dir': str(upscale_dir),
        'adetailer_dir': str(adetailer_dir),
        'output_dir': str(webui_output)
    }
    
    update_json(SETTINGS_PATH, 'WEBUI', paths)

def handle_setup_timer(webui_path, timer_webui):
    """Handle the setup timer by reading from and writing to a timer file."""
    timer_file_path = Path(webui_path) / 'static' / 'timer.txt'
    timer_file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with timer_file_path.open('r') as file:
            timer_webui = float(file.read())
    except FileNotFoundError:
        pass

    with timer_file_path.open('w') as file:
        file.write(str(timer_webui))

    return timer_webui