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

CSS_PATH = SCR_PATH / 'CSS' / 'auto-cleaner.css'
CONTAINER_WIDTH = '1080px'

# File handling rules
TRASH_EXTENSIONS = {'.txt', '.aria2', '.ipynb_checkpoints', '.mp4'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}

# Google Drive base path
GD_BASE = '/content/drive/MyDrive/sdAIgen'


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


# ======================= Core Logic =======================

def should_delete_file(filename, directory_type):
    """
    Determine if file should be deleted and counted.
    Returns: (should_delete: bool, should_count: bool)
    """
    # Skip trash files
    if any(filename.endswith(ext) for ext in TRASH_EXTENSIONS):
        return False, False

    is_image = any(filename.endswith(ext) for ext in IMAGE_EXTENSIONS)

    # Output Images: delete and count everything (except trash)
    if directory_type == 'Output Images':
        return True, True

    # Other directories: delete images but DON'T count them
    if is_image:
        return True, False

    return ('.' in filename), ('.' in filename)  # Delete and count regular files


def clean_directory(directory, directory_type):
    """Clean directory and return count of deleted files"""
    deleted_count = 0

    for root, _, files in os.walk(directory):
        for file in files:
            should_delete, should_count = should_delete_file(file, directory_type)

            if should_delete:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    if should_count:
                        deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    return deleted_count


def get_disk_usage():
    """Get disk usage statistics in GB"""
    disk = psutil.disk_usage(os.getcwd())
    return {
        'total': disk.total / (1024 ** 3),
        'used': disk.used / (1024 ** 3),
        'free': disk.free / (1024 ** 3)
    }


def update_storage_display():
    """Update storage information widget"""
    stats = get_disk_usage()
    storage_info.value = f'''
    <div class="storage_info">Total storage: {stats['total']:.2f} GB <span style="color: #555">|</span> Used: {stats['used']:.2f} GB <span style="color: #555">|</span> Free: {stats['free']:.2f} GB</div>
    '''


# ===================== Event Handlers =====================

def on_execute_click(_):
    """Handle execute button click"""
    is_gdrive_mode = gdrive_mode_widget.value if show_gdrive_toggle else False

    results = {
        option: clean_directory(DIRECTORIES[option][is_gdrive_mode], option)
        for option in selection_widget.value
        if option in DIRECTORIES
    }

    output_widget.clear_output()
    with output_widget:
        for dir_name, count in results.items():
            display(HTML(f'<p class="output-message">Deleted {count} {dir_name}</p>'))

    update_storage_display()


def on_hide_click(_):
    """Handle hide button click"""
    factory.close(main_container, class_names=['hide'], delay=0.5)


def on_gdrive_mode_change(change):
    """Handle GDrive mode checkbox change"""
    is_gdrive = change['new']
    button_suffix = ' (GD)' if is_gdrive else ''
    execute_button.description = f"Execute Cleaning{button_suffix}"


# ===================== UI Construction ====================

# Initialize the WidgetFactory
factory = WidgetFactory()
factory.load_css(CSS_PATH)
HR = widgets.HTML('<hr>')

# Check GDrive toggle
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
mount_gdrive = js.read(SETTINGS_PATH, 'mountGDrive', False)
show_gdrive_toggle = (ENV_NAME == 'Google Colab' and mount_gdrive and os.path.exists(GD_BASE))

# Directory mapping - returns tuple (local_path, gdrive_path)
def get_directory_paths():
    """Build directory mapping with local and GDrive paths"""
    gdrive_map = {
        # Display Names | Name Dirs in GD | path to dir
        'Models': ('Checkpoints', model_dir),
        'VAE': ('VAE', vae_dir),
        'LoRA': ('Lora', lora_dir),
        'ControlNet Models': ('ControlNet', control_dir),
        'CLIP Models': ('Clip', clip_dir),
        'UNET Models': ('Unet', unet_dir),
        'Vision Models': ('Vision', vision_dir),
        'Encoder Models': ('Encoder', encoder_dir),
        'Diffusion Models': ('Diffusion', diffusion_dir),
        'Output Images': ('Output', output_dir),
    }

    return {
        name: {
            False: local,
            True: os.path.join(GD_BASE, gd) if show_gdrive_toggle else local
        }
        for name, (gd, local) in gdrive_map.items()
    }

DIRECTORIES = get_directory_paths()

# Create widgets
instruction_label = factory.create_html(
    '<span class="instruction">Use <span style="color: #B2B2B2;">ctrl</span> or '
    '<span style="color: #B2B2B2;">shift</span> for multiple selections.</span>'
)

selection_widget = factory.create_select_multiple(
    list(DIRECTORIES.keys()),
    '',
    [],
    class_names=['selection-panel']
)

output_widget = widgets.Output().add_class('output-panel')

execute_button = factory.create_button(
    'Execute Cleaning',
    class_names=['cleaner_button', 'button_execute']
)

hide_button = factory.create_button(
    'Hide Widget',
    class_names=['cleaner_button', 'button_hide']
)

# GDrive mode checkbox (only shown in Colab when GDrive is mounted)
gdrive_mode_widget = factory.create_checkbox(
    'GDrive',
    False,
    class_names=['gdrive-mode']
)
if not show_gdrive_toggle:
    gdrive_mode_widget.layout.display = 'none'

stats = get_disk_usage()
storage_info = factory.create_html(
    f'<div class="storage_info">Total storage: {stats["total"]:.2f} GB '
    f'<span style="color: #555">|</span> Used: {stats["used"]:.2f} GB '
    f'<span style="color: #555">|</span> Free: {stats["free"]:.2f} GB</div>'
)

# Attach event handlers
execute_button.on_click(on_execute_click)
hide_button.on_click(on_hide_click)
gdrive_mode_widget.observe(on_gdrive_mode_change, names='value')

# Build layout
buttons_box = factory.create_hbox(
    [execute_button, hide_button, gdrive_mode_widget],
    class_names=['lower_buttons_box']
)

info_panel = factory.create_hbox(
    [buttons_box, storage_info],
    class_names=['lower_information-panel'],
    layout={'justify_content': 'space-between'}
)

selection_output_box = factory.create_hbox(
    [selection_widget, output_widget],
    class_names=['selection_output-layout'],
    layout={'width': '100%'}
)

main_container = factory.create_vbox(
    [instruction_label, HR, selection_output_box, HR, info_panel],
    class_names=['mainCleaner-container'],
    layout={'min_width': CONTAINER_WIDTH, 'max_width': CONTAINER_WIDTH}
)

factory.display(main_container)