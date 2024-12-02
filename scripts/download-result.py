# ~ download-result.py | by ANXETY ~

from json_utils import read_json, save_json, update_json    # JSON (main)
from widget_factory import WidgetFactory                    # WIDGETS

import ipywidgets as widgets
from pathlib import Path
import json
import time
import re
import os

# Constants
HOME = Path.home()
SCR_PATH = Path(HOME / 'ANXETY')
SETTINGS_PATH = SCR_PATH / 'settings.json'

UI = read_json(SETTINGS_PATH, 'WEBUI.current')

CSS = SCR_PATH / 'CSS'
widgets_css = CSS / 'download-result.css'

def load_settings(path):
    """Load settings from a JSON file."""
    if os.path.exists(path):
        try:
            _webui = read_json(path, 'WEBUI')

            settings = {**_webui}
            return settings
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}")
    return {}

settings = load_settings(SETTINGS_PATH)

# Create local variables for each key in the settings
for key, value in settings.items():
    locals()[key] = value

# ====================== WIDGETS =====================
HR = widgets.HTML('<hr class="divider-line">')
HEADER_DL = 'DOWNLOAD RESULTS'
VERSION = 'v0.51'

factory = WidgetFactory()

# Load CSS
factory.load_css(widgets_css)

# Define extensions to filter out
EXCLUDED_EXTENSIONS = {'.txt', '.yaml', '.log'}

## Functions
def output_container_generator(header, items, is_grid=False):
    header_widget = factory.create_html(f'<div class="header-output-title">{header} ➤</div>')
    content_widgets = [factory.create_html(f'<div class="output-item">{item}</div>') for item in items]

    container_method = factory.create_hbox if is_grid else factory.create_vbox    # hbox -> grid
    content_container = container_method(content_widgets).add_class("output-items" if is_grid else "")

    return factory.create_vbox([header_widget, content_container]).add_class("output-section")

def get_files_list(directory, extensions):
    if not os.path.isdir(directory):
        return []  # Return empty list if directory does not exist
    return [file for file in os.listdir(directory) if file.endswith(extensions) and not file.endswith(tuple(EXCLUDED_EXTENSIONS))]

def get_folders_list(directory):
    if not os.path.isdir(directory):
        return []  # Return empty list if directory does not exist
    return [
        folder for folder in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, folder)) and not folder.startswith('__')
    ]

def get_controlnets_list(directory, filter_pattern):
    if not os.path.isdir(directory):
        return []  # Return empty list if directory does not exist
    filter_name = re.compile(filter_pattern)
    return [
        filter_name.match(file).group(1) if filter_name.match(file) else file
        for file in os.listdir(directory)
        if not file.endswith(tuple(EXCLUDED_EXTENSIONS)) and '.' in file
    ]

## Widgets
header_widget = factory.create_html(f'''
<div><span class="header-main-title">{HEADER_DL}</span> <span style="color: grey; opacity: 0.25;">| {VERSION}</span></div>
''')

# Models
models_list = get_files_list(model_dir, ('.safetensors', '.ckpt'))
models_widget = output_container_generator('Models', models_list)
# Vaes
vaes_list = get_files_list(vae_dir, ('.safetensors',))
vaes_widget = output_container_generator('VAEs', vaes_list)
# Embeddings
embeddings_list = get_files_list(embed_dir, ('.safetensors', '.pt'))
embeddings_widget = output_container_generator('Embeddings', embeddings_list)
# LoRAs
loras_list = get_files_list(lora_dir, ('.safetensors',))
loras_widget = output_container_generator('LoRAs', loras_list)
# Extensions
extensions_list = get_folders_list(extension_dir)
extension_type = 'Nodes' if UI == 'ComfyUI' else 'Extensions'
extensions_widget = output_container_generator(extension_type, extensions_list, is_grid=True)
# ControlNet
controlnets_list = get_controlnets_list(control_dir, r'^[^_]*_[^_]*_[^_]*_(.*)_fp16\.safetensors')
controlnets_widget = output_container_generator('ControlNets', controlnets_list)

## Sorting and Output
widgets_dict = {
    models_widget: models_list,
    vaes_widget: vaes_list,
    embeddings_widget: embeddings_list,
    loras_widget: loras_list,
    extensions_widget: extensions_list,
    controlnets_widget: controlnets_list
}

outputs_widgets_list = [widget for widget, widget_list in widgets_dict.items() if widget_list]
result_output_widget = factory.create_hbox(outputs_widgets_list).add_class("result-output-container")

container_widget = factory.create_vbox([header_widget, HR, result_output_widget, HR],
                                       layout={'width': '1080px'}).add_class("result-container")
factory.display(container_widget)