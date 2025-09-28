# ~ auto-cleaner.py | by ANXETY ~

from widget_factory import WidgetFactory    # WIDGETS
import json_utils as js                     # JSON

from IPython.display import display, HTML
import ipywidgets as widgets
from pathlib import Path
import psutil
import json
import os


osENV = os.environ

# Auto-convert *_path env vars to Path
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, SCR_PATH, SETTINGS_PATH = (
    PATHS['home_path'], PATHS['scr_path'], PATHS['settings_path']
)

CSS = SCR_PATH / 'CSS'
cleaner_css = CSS / 'auto-cleaner.css'
CONTAINER_WIDTH = '1080px'


# =================== loading settings V5 ==================

def load_settings(path):
    """Load settings from a JSON file"""
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


# ================== AutoCleaner function ==================

def _update_memory_info():
    disk_space = psutil.disk_usage(os.getcwd())
    total = disk_space.total / (1024 ** 3)
    used = disk_space.used / (1024 ** 3)
    free = disk_space.free / (1024 ** 3)
    storage_info.value = f'''
    <div class="storage_info">Total storage: {total:.2f} GB <span style="color: #555">|</span> Used: {used:.2f} GB <span style="color: #555">|</span> Free: {free:.2f} GB</div>
    '''

def clean_directory(directory, directory_type):
    trash_extensions = {'.txt', '.aria2', '.ipynb_checkpoints', '.mp4'}
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    deleted_files = 0

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if directory_type != 'Output Images' and file.endswith(tuple(image_extensions)):
                os.remove(file_path)
                continue
            if not file.endswith(tuple(trash_extensions)) and '.' in file:
                deleted_files += 1
            os.remove(file_path)

    return deleted_files

def generate_messages(deleted_files_dict):
    return [f"Deleted {value} {key}" for key, value in deleted_files_dict.items()]

def execute_button_press(_):
    deleted_files_dict = {
        option: clean_directory(directories[option], option)
        for option in selection_widget.value
        if option in directories
    }

    output_widget.clear_output()
    with output_widget:
        for message in generate_messages(deleted_files_dict):
            display(HTML(f'<p class="output-message">{message}</p>'))
    _update_memory_info()

def hide_button_press(_):
    factory.close(mainContainer, class_names=['hide'], delay=0.5)


# =================== AutoCleaner Widgets ==================

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# Load Css
factory.load_css(cleaner_css)

directories = {
    'Output Images': output_dir,
    'Models': model_dir,
    'VAE': vae_dir,
    'LoRA': lora_dir,
    'ControlNet Models': control_dir,
    'CLIP Models': clip_dir,
    'UNET Models': unet_dir,
    'Vision Models': vision_dir,
    'Encoder Models': encoder_dir,
    'Diffusion Models': diffusion_dir
}

# UI Components
disk_space = psutil.disk_usage(os.getcwd())
total, used, free = (x / (1024 ** 3) for x in (disk_space.total, disk_space.used, disk_space.free))

instruction_label = factory.create_html('''
<span class="instruction">Use <span style="color: #B2B2B2;">ctrl</span> or <span style="color: #B2B2B2;">shift</span> for multiple selections.</span>
''')

selection_widget = factory.create_select_multiple(
    list(directories.keys()),
    '',
    [],
    class_names=['selection-panel']
)
output_widget = widgets.Output().add_class('output-panel')

execute_button = factory.create_button('Execute Cleaning', class_names=['cleaner_button', 'button_execute'])
hide_button = factory.create_button('Hide Widget', class_names=['cleaner_button', 'button_hide'])
execute_button.on_click(execute_button_press)
hide_button.on_click(hide_button_press)

storage_info = factory.create_html(f'''
<div class="storage_info">Total storage: {total:.2f} GB <span style="color: #555">|</span> Used: {used:.2f} GB <span style="color: #555">|</span> Free: {free:.2f} GB</div>
''')

# Containers
buttons_box = factory.create_hbox(
    [execute_button, hide_button],
    class_names=['lower_buttons_box']
)

lower_information_panel_box = factory.create_hbox(
    [buttons_box, storage_info],
    class_names=['lower_information-panel'],
    layout={'justify_content': 'space-between'}
)

selection_output_panel_box = factory.create_hbox(
    [selection_widget, output_widget],
    class_names=['selection_output-layout'],
    layout={'width': '100%'}
)

mainContainer = factory.create_vbox(
    [instruction_label, HR, selection_output_panel_box, HR, lower_information_panel_box],
    class_names=['mainCleaner-container'],
    layout={'min_width': CONTAINER_WIDTH, 'max_width': CONTAINER_WIDTH}
)

factory.display(mainContainer)