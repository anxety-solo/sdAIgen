""" Download Results Widget | by ANXETY """

import os
import re

import ipywidgets as widgets

from collections.abc import Callable
from pathlib import Path

# === SDAIGEN ===
from sdai.constants import SETTINGS_PATH, CSS_DIR_PATH
from sdai.factory import WidgetFactory
from sdai.utils.json import read, load_settings


# ~~ CONSTANTS ~~

UI_NAME         = read(SETTINGS_PATH, 'WEBUI.current')
CONTAINER_WIDTH = '1200px'
HEADER_DL       = 'DOWNLOAD RESULTS'
VERSION         = 'v1.5'
WIDGET_CSS      = CSS_DIR_PATH / 'download-result.css'


# ~~ LOADING SETTINGS ~~

settings = load_settings(SETTINGS_PATH)
locals().update(settings)


# ~~ INIT ~~

factory = WidgetFactory()
HR = factory.create_html('<hr>')


# ~~ FILE UTILS ~~

def get_files(directory: str | Path, extensions: str | tuple[str, ...], excluded_dirs: list[str] = None, filter_func: Callable[[str], bool] = None) -> list[str]:
    """Return files matching extensions, with optional exclusion and filtering"""
    directory = Path(directory)
    if not directory.is_dir():
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


def get_folders(directory: str | Path, exclude_hidden=True) -> list[str]:
    """List folders, flattening 'GDrive' into its subfolders"""
    directory = Path(directory)
    if not directory.is_dir():
        return []

    folders = []
    for folder in directory.iterdir():
        if not folder.is_dir() or (exclude_hidden and folder.name.startswith('__')):
            continue
        if folder.name == 'GDrive':
            folders.extend(
                f.name for f in folder.iterdir() if f.is_dir()
            )
        else:
            folders.append(folder.name)

    return folders


def controlnet_filter(filename: str) -> bool:
    """Match ControlNet filenames with the standard naming pattern"""
    return bool(re.match(r'^[^_]*_[^_]*_[^_]*_(.*)_fp16\.safetensors', filename))


# ~~ SECTIONS ~~

def create_section(title: str, items: list[str], is_grid=False) -> widgets.Widget:
    """Create a section with a title and its items"""
    item_widgets = [
        factory.create_html(f'<div class="output-item">{item}</div>') for item in items
    ]

    box     = factory.create_hbox if is_grid else factory.create_vbox
    content = box(item_widgets, class_names=['_horizontal'] if is_grid else None)
    header  = factory.create_html(f'<div class="section-title">{title} ➤</div>')

    return factory.create_vbox([header, content], class_names=['output-section'])


def create_sections() -> list[widgets.Widget]:
    """Create all sections, skipping empty ones"""
    ext_type = 'Nodes' if UI_NAME == 'ComfyUI' else 'Extensions'

    sections = [
        # (Title, Items)
        ('Models',      get_files(model_dir, ('.safetensors', '.ckpt'))),
        ('VAEs',        get_files(vae_dir, ('.safetensors', '.vae'))),
        ('Embeddings',  get_files(embed_dir, ('.safetensors', '.pt'), excluded_dirs=['SD', 'XL'])),
        ('LoRAs',       get_files(lora_dir, '.safetensors')),
        (ext_type,      get_folders(extension_dir)),
        ('ADetailers',  get_files(adetailer_dir, ('.safetensors', '.pt'))),
        ('Clips',       get_files(clip_dir, '.safetensors')),
        ('Unets',       get_files(unet_dir, ('.safetensors', '.gguf'))),
        ('Visions',     get_files(vision_dir, '.safetensors')),
        ('Encoders',    get_files(encoder_dir, '.safetensors')),
        ('Diffusions',  get_files(diffusion_dir, '.safetensors')),
        ('ControlNets', get_files(control_dir, '.safetensors', filter_func=controlnet_filter)),
    ]

    return [
        create_section(title, items, is_grid=(title == ext_type))
        for title, items in sections
        if items
    ]


# ~~ DISPLAY ~~

factory.load_css(WIDGET_CSS)

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
