# ~ download-result.py | by ANXETY ~

from widget_factory import WidgetFactory    # WIDGETS
import json_utils as js                     # JSON

import ipywidgets as widgets
from pathlib import Path
import json
import re
import os


osENV = os.environ

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

UI = js.read(SETTINGS_PATH, 'WEBUI.current')

CSS = SCR_PATH / 'CSS'
widgets_css = CSS / 'download-result.css'

EXCLUDED_EXTENSIONS = {'.txt', '.yaml', '.log', '.json'}
CONTAINER_WIDTH = '1200px'
HEADER_DL = 'DOWNLOAD RESULTS'
VERSION = 'v1.1'


# =================== loading settings V5 ==================

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


# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')


# ====================== File Utilities ====================

def get_files(directory, extensions, excluded_dirs=None, filter_func=None):
    """Generic function to get files with optional filtering."""
    if not os.path.isdir(directory):
        return []

    # Convert single extension string to tuple
    if isinstance(extensions, str):
        extensions = (extensions,)

    excluded_dirs = excluded_dirs or []
    files = []

    for root, dirs, filenames in os.walk(directory, followlinks=True):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for filename in filenames:
            if (filename.endswith(extensions)) and not filename.endswith(tuple(EXCLUDED_EXTENSIONS)):
                if filter_func is None or filter_func(filename):
                    files.append(filename)
    return files

def get_folders(directory, exclude_hidden=True):
    """List folders in a directory, excluding hidden folders.
       If 'GDrive' is found, include its subfolders instead."""
    if not os.path.isdir(directory):
        return []
    folders = []
    for folder in os.listdir(directory):
        path = os.path.join(directory, folder)
        if not os.path.isdir(path) or (exclude_hidden and folder.startswith('__')):
            continue
        if folder == 'GDrive':
            folders.extend(
                f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))
            )
        else:
            folders.append(folder)
    return folders

def controlnet_filter(filename):
    """Filter function for ControlNet files."""
    match = re.match(r'^[^_]*_[^_]*_[^_]*_(.*)_fp16\.safetensors', filename)
    return match.group(1) if match else filename


# ==================== Widget Generators ===================

def create_section(title, items, is_grid=False):
    """Create a standardized section widget."""
    header = factory.create_html(f'<div class="section-title">{title} ➤</div>')
    items_widgets = [
        factory.create_html(f'<div class="output-item">{item}</div>') for item in items
    ]

    container = factory.create_hbox if is_grid else factory.create_vbox
    content = container(items_widgets).add_class('_horizontal' if is_grid else '')

    return factory.create_vbox([header, content], class_names=['output-section'])

def create_all_sections():
    """Create all content sections."""
    ext_type = 'Nodes' if UI == 'ComfyUI' else 'Extensions'
    SECTIONS = [
        # TITLE | GET LIST(content_dir) | file.formats | excluded_dirs=[List] (files); is_grid=bool (folders)
        ## Mains
        ('Models', get_files(model_dir, ('.safetensors', '.ckpt'))),
        ('VAEs', get_files(vae_dir, '.safetensors', '.vae')),
        ('Embeddings', get_files(embed_dir, ('.safetensors', '.pt'), excluded_dirs=['SD', 'XL'])),
        ('LoRAs', get_files(lora_dir, '.safetensors')),
        (ext_type, get_folders(extension_dir), True),
        ('ADetailers', get_files(adetailer_dir, ('.safetensors', '.pt'))),
        ## Others
        ('Clips', get_files(clip_dir, '.safetensors')),
        ('Unets', get_files(unet_dir, '.safetensors', '.gguf')),
        ('Visions', get_files(vision_dir, '.safetensors')),
        ('Encoders', get_files(encoder_dir, '.safetensors')),
        ('Diffusions', get_files(diffusion_dir, '.safetensors')),
        ('ControlNets', get_files(control_dir, '.safetensors', filter_func=controlnet_filter)),
    ]

    return {create_section(*section): section[1] for section in SECTIONS}


# =================== DISPLAY / SETTINGS ===================

factory.load_css(widgets_css)   # load CSS (widgets)

header = factory.create_html(
    f'<div><span class="header-main-title">{HEADER_DL}</span>'
    f'<span style="color: grey; opacity: 0.25;"> | {VERSION}</span></div>'
)

widget_section = create_all_sections()
output_widgets = [widget for widget, items in widget_section.items() if items]
result_output_container = factory.create_hbox(
    output_widgets,
    class_names=['sectionsContainer'],
    layout={'width': '100%'}
)

main_container = factory.create_vbox(
    [header, HR, result_output_container, HR],
    class_names=['mainResult-container'],
    layout={'min_width': CONTAINER_WIDTH, 'max_width': CONTAINER_WIDTH}
)

factory.display(main_container)