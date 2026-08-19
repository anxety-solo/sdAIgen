""" Download Results Widget | by ANXETY """

import os
import re

# === SDAIGEN ===
from sdai.constants import CSS_DIR_PATH, SETTINGS_PATH
from sdai.factory import WidgetFactory
from sdai.utils.json import read


# ~~ CONSTANTS ~~

UI_NAME         = read(SETTINGS_PATH, 'WEBUI.current')
CONTAINER_WIDTH = '1200px'
HEADER_DL       = 'DOWNLOAD RESULTS'
VERSION         = 'v1.5'


# ~~ SETTINGS ~~

def load_settings(path):
    """Load settings from a JSON file"""
    return {
        **read(path, 'ENVIRONMENT'),
        **read(path, 'WIDGETS'),
        **read(path, 'WEBUI'),
    }


settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ~~ INIT ~~

factory = WidgetFactory()
HR = factory.create_html('<hr>')


# ~~ FILE UTILS ~~

def get_files(directory, extensions, excluded_dirs=None, filter_func=None):
    """Return files matching extensions, with optional exclusion and filtering"""
    if not os.path.isdir(directory):
        return []
    if isinstance(extensions, str):
        extensions = (extensions,)

    excluded = excluded_dirs or []
    files = []
    for _, dirs, filenames in os.walk(directory, followlinks=True):
        dirs[:] = [d for d in dirs if d not in excluded]
        for filename in filenames:
            if filename.endswith(extensions) and (filter_func is None or filter_func(filename)):
                files.append(filename)

    return files


def get_folders(directory, exclude_hidden=True):
    """List folders, flattening 'GDrive' into its subfolders"""
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
    """Extract the model name from a ControlNet filename"""
    match = re.match(r'^[^_]*_[^_]*_[^_]*_(.*)_fp16\.safetensors', filename)
    return match.group(1) if match else filename


# ~~ SECTIONS ~~

def create_section(title, items, is_grid=False):
    """Create a section with a title and its items"""
    item_widgets = [
        factory.create_html(f'<div class="output-item">{item}</div>') for item in items
    ]

    box     = factory.create_hbox if is_grid else factory.create_vbox
    content = box(item_widgets, class_names=['_horizontal'] if is_grid else None)
    header  = factory.create_html(f'<div class="section-title">{title} ➤</div>')

    return factory.create_vbox([header, content], class_names=['output-section'])


def create_sections():
    """Create all sections, skipping empty ones"""
    ext_type = 'Nodes' if UI_NAME == 'ComfyUI' else 'Extensions'

    sections = [
        # (Title, Items, is_grid)
        ('Models',      get_files(model_dir, ('.safetensors', '.ckpt'))),
        ('VAEs',        get_files(vae_dir, ('.safetensors', '.vae'))),
        ('Embeddings',  get_files(embed_dir, ('.safetensors', '.pt'), excluded_dirs=['SD', 'XL'])),
        ('LoRAs',       get_files(lora_dir, '.safetensors')),
        (ext_type,      get_folders(extension_dir), True),
        ('ADetailers',  get_files(adetailer_dir, ('.safetensors', '.pt'))),
        ('Clips',       get_files(clip_dir, '.safetensors')),
        ('Unets',       get_files(unet_dir, ('.safetensors', '.gguf'))),
        ('Visions',     get_files(vision_dir, '.safetensors')),
        ('Encoders',    get_files(encoder_dir, '.safetensors')),
        ('Diffusions',  get_files(diffusion_dir, '.safetensors')),
        ('ControlNets', get_files(control_dir, '.safetensors', filter_func=controlnet_filter)),
    ]

    return [create_section(*section) for section in sections if section[1]]


# ~~ DISPLAY ~~

factory.load_css(CSS_DIR_PATH / 'download-result.css')

header = factory.create_html(
    f'''
    <div class="header-wrap">
        <span class="header-main-title">{HEADER_DL}</span>
        <span class="header-ui">{UI_NAME}</span>
        <span class="header-version">| {VERSION}</span>
    </div>
    '''
)

output_widgets   = create_sections()
output_container = factory.create_hbox(
    output_widgets,
    class_names=['sectionsContainer'],
    layout={'width': '100%'}
)

main_container = factory.create_vbox(
    [header, HR, output_container, HR],
    class_names=['mainResult-container'],
    layout={'min_width': CONTAINER_WIDTH, 'max_width': CONTAINER_WIDTH}
)

factory.display(main_container)
