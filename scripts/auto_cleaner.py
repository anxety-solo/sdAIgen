""" Auto Cleaner Widget | by ANXETY """

import psutil
import os

import ipywidgets as widgets

from IPython.display import HTML, display
from pathlib import Path

# === SDAIGEN ===
from sdai.constants import SETTINGS_PATH, CSS_DIR_PATH, GD_BASE, GD_FILES, GD_OUTPUTS
from sdai.factory import WidgetFactory
from sdai.utils.json import read, load_settings
from sdai.translations import tr


# ~~ CONSTANTS ~~

WIDGET_CSS = CSS_DIR_PATH / 'auto-cleaner.css'
CONTAINER_WIDTH = '1080px'

GB = 1024 ** 3

TRASH_EXTENSIONS = {'.txt', '.aria2', '.ipynb_checkpoints', '.mp4'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif'}


# ~~ LOADING SETTINGS ~~

settings = load_settings(SETTINGS_PATH)
locals().update(settings)

UI_NAME      = read(SETTINGS_PATH, 'WEBUI.current')
ENV_NAME     = read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
mount_gdrive = read(SETTINGS_PATH, 'GDRIVE.mount', False)

show_gdrive_toggle = ENV_NAME == 'Colab' and mount_gdrive and os.path.exists(GD_BASE)


# ~~ DIRECTORY MAPPING ~~

def gdrive_path(name: str, gd_folder: str, ui: str) -> str:
    """Return the GDrive path for a directory"""
    return str(GD_OUTPUTS / ui) if name == 'Output Images' else str(GD_FILES / gd_folder)


def build_directories(ui: str) -> dict[str, dict[bool, str]]:
    """Build directory mapping: name -> {False: local, True: gdrive}"""
    # gdrive_map: display_name | (gd_folder, local_dir)
    gdrive_map = {
        # Display Name | GD folder | Local dir
        'Models':            ('Checkpoints',  model_dir),
        'VAE':               ('VAE',          vae_dir),
        'LoRA':              ('Lora',         lora_dir),
        'ControlNet Models': ('ControlNet',   control_dir),
        'CLIP Models':       ('Clip',         clip_dir),
        'UNET Models':       ('Unet',         unet_dir),
        'Vision Models':     ('Vision',       vision_dir),
        'Encoder Models':    ('Encoder',      encoder_dir),
        'Diffusion Models':  ('Diffusion',    diffusion_dir),
        'Output Images':     ('Output',       output_dir),
    }

    return {
        name: {
            False: local,
            True:  gdrive_path(name, gd, ui) if show_gdrive_toggle else local,
        }
        for name, (gd, local) in gdrive_map.items()
    }


DIRECTORIES = build_directories(UI_NAME)


# ~~ CORE LOGIC ~~

def should_delete_file(filename: str, directory_type: str) -> tuple[bool, bool]:
    """Return (should_delete, should_count) flags for a file"""
    if filename.endswith(tuple(TRASH_EXTENSIONS)):
        return False, False

    is_image = filename.endswith(tuple(IMAGE_EXTENSIONS))

    if directory_type == 'Output Images':
        return True, True
    if is_image:
        return True, False

    has_dot = '.' in filename
    return has_dot, has_dot


def clean_directory(directory: str | Path, directory_type: str, on_error=None) -> int:
    """Clean directory and return the number of deleted files"""
    deleted_count = 0

    for root, _, files in os.walk(directory):
        for file in files:
            should_delete, should_count = should_delete_file(file, directory_type)
            if not should_delete:
                continue

            file_path = str(Path(root) / file)
            try:
                os.remove(file_path)
                deleted_count += should_count
            except Exception as exc:
                message = tr('cleaner_delete_error', file_path=file_path, exc=exc)
                if on_error:
                    on_error(message)
                else:
                    print(message)

    return deleted_count


def get_disk_usage() -> dict[str, float]:
    """Get disk usage statistics in GB"""
    usage = psutil.disk_usage(os.getcwd())
    return {
        'total': usage.total / GB,
        'used':  usage.used / GB,
        'free':  usage.free / GB,
    }


def storage_html(stats: dict[str, float] = None) -> str:
    """Return the storage info HTML block"""
    stats = stats or get_disk_usage()
    return tr(
        'cleaner_storage',
        total=stats['total'],
        used=stats['used'],
        free=stats['free']
    )


def update_storage_display():
    """Update the storage info widget"""
    storage_info.value = storage_html()


# ~~ EVENT HANDLERS ~~

def on_execute_click(_: widgets.Button):
    """Handle execute button click"""
    is_gdrive_mode = gdrive_mode_widget.value if show_gdrive_toggle else False

    errors = []
    results = {}
    for option in selection_widget.value:
        if option not in DIRECTORIES:
            continue
        try:
            results[option] = clean_directory(
                DIRECTORIES[option][is_gdrive_mode],
                option,
                on_error=errors.append,
            )
        except Exception as exc:
            errors.append(str(exc))

    try:
        messages = [
            f'<p class="output-message">{tr("cleaner_deleted", count=count, dir_name=dir_name)}</p>'
            for dir_name, count in results.items()
        ]
        messages += [f'<p class="output-message" style="color: #fc3468">{msg}</p>' for msg in errors]

        with output_widget:
            output_widget.clear_output()
            for message in messages:
                display(HTML(message))
    except Exception as exc:
        output_widget.outputs = [{
            'output_type': 'stream',
            'name': 'stderr',
            'text': str(exc),
        }]

    try:
        update_storage_display()
    except Exception:
        pass


def on_hide_click(_: widgets.Button):
    """Handle hide button click"""
    factory.close(main_container, class_names=['hide'], delay=0.5)


def on_gdrive_mode_change(change: dict):
    """Handle GDrive mode checkbox change"""
    suffix = ' (GD)' if change['new'] else ''
    execute_button.description = f"{tr('cleaner_execute_btn')}{suffix}"


# ~~ UI CONSTRUCTION ~~

factory = WidgetFactory()
HR = factory.create_html('<hr>')

factory.load_css(WIDGET_CSS)

instruction_label = factory.create_html(f'<span class="instruction">{tr("cleaner_instruction")}</span>')

selection_widget = factory.create_select_multiple(
    list(DIRECTORIES.keys()),
    '',
    [],
    class_names=['selection-panel']
)

output_widget = widgets.Output().add_class('output-panel')

execute_button = factory.create_button(
    tr('cleaner_execute_btn'),
    class_names=['cleaner_button', 'button_execute']
)

hide_button = factory.create_button(
    tr('cleaner_hide_btn'),
    class_names=['cleaner_button', 'button_hide']
)

gdrive_mode_widget = factory.create_checkbox(
    'GDrive',
    False,
    class_names=['gdrive-mode']
)
if not show_gdrive_toggle:
    gdrive_mode_widget.layout.display = 'none'

storage_info = factory.create_html(storage_html())

# Attach event handlers
execute_button.on_click(on_execute_click)
hide_button.on_click(on_hide_click)
gdrive_mode_widget.observe(on_gdrive_mode_change, names='value')

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
