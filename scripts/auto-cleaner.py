# ~ auto-cleaner.py | by ANXETY ~

from widget_factory import WidgetFactory    # WIDGETS
import json_utils as js                     # JSON

from IPython.display import display, HTML, clear_output
import ipywidgets as widgets
from pathlib import Path
import psutil
import json
import time
import os
import shutil # Added for comprehensive deletion

# Constants
HOME = Path.home()
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

CSS = SCR_PATH / 'CSS'
cleaner_css = CSS / 'auto-cleaner.css'


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

## ================= AutoCleaner function ================

def _update_memory_info():
    """Updates and displays current disk space information."""
    disk_space = psutil.disk_usage(os.getcwd())
    total = disk_space.total / (1024 ** 3)
    used = disk_space.used / (1024 ** 3)
    free = disk_space.free / (1024 ** 3)

    storage_info.value = f'''
    <div class="storage_info">Total storage: {total:.2f} GB <span style="color: #555">|</span> Used: {used:.2f} GB <span style="color: #555">|</span> Free: {free:.2f} GB</div>
    '''

def clean_directory(directory, directory_type):
    """Cleans a specific directory by removing certain file types."""
    trash_extensions = {'.txt', '.aria2', '.ipynb_checkpoints'}
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    deleted_files = 0

    if not Path(directory).is_dir():
        print(f"ℹ️ Directory '{directory}' does not exist. Skipping.")
        return 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file

            # Skip protected files like .gitkeep or similar
            if file_path.name == '.gitkeep':
                continue

            if directory_type == 'Models' and file.endswith(tuple(image_extensions)):
                try:
                    file_path.unlink()
                    deleted_files += 1
                except Exception as e:
                    print(f"❌ Error deleting image {file_path}: {e}")
                continue

            if file.endswith(tuple(trash_extensions)) or ('.' in file and not file.endswith(('.safetensors', '.ckpt', '.pt', '.zip', '.json', '.yaml', '.csv', '.ini'))):
                try:
                    file_path.unlink()
                    deleted_files += 1
                except Exception as e:
                    print(f"❌ Error deleting trash file {file_path}: {e}")

    return deleted_files

# --- START OF MODIFICATION ---
# No longer using a global status variable or interactive confirmation
def clean_all_except_notebook_and_main():
    """Deletes all files and folders in the current working directory except the notebook and main.py."""
    output.clear_output()
    with output:
        print("!!! Initiating COMPREHENSIVE DELETION !!!")
        print("This will remove almost everything in your studio instance.")
        print("This action is irreversible and requires a runtime restart for a clean state.")
        print("\n--- Proceeding with deletion in 5 seconds... (Ctrl+C to abort) ---")
        time.sleep(5) # Give user a moment to react and Ctrl+C if needed

        HOME_PATH = Path.home() # Use Path.home() to target the studio root

        # Get the current notebook's filename reliably within the execution environment
        notebook_filename = None
        for fname in os.listdir(HOME_PATH):
            if fname.endswith('.ipynb') and 'LightningAnxiety' in fname: # Heuristic for your notebook name
                notebook_filename = fname
                break
        
        notebook_path = HOME_PATH / notebook_filename if notebook_filename else None
        main_py_path = HOME_PATH / "main.py"

        EXCLUDE_LIST = []
        if notebook_path and notebook_path.exists():
            EXCLUDE_LIST.append(notebook_path.resolve()) # Resolve to absolute path for consistent comparison
            print(f"ℹ️ Protecting notebook: {notebook_path.name}")
        if main_py_path.exists():
            EXCLUDE_LIST.append(main_py_path.resolve()) # Resolve to absolute path
            print(f"ℹ️ Protecting main.py: {main_py_path.name}")
        
        deleted_count = 0
        skipped_count = 0

        # Iterate through contents of HOME_PATH and delete
        print(f"\n--- Starting Comprehensive Deletion in {HOME_PATH} ---")
        for item in HOME_PATH.iterdir():
            # Convert item to absolute path for consistent comparison with EXCLUDE_LIST
            abs_item = item.resolve()
            if abs_item in EXCLUDE_LIST:
                skipped_count += 1
                continue # Skip protected items

            print(f"🗑️ Deleting: {item.name}...")
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink() # Delete file
                print(f"✅ Deleted: {item.name}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting {item.name}: {e}")
        
        print("\n--- Global Cleanup Process Complete ---")
        print(f"Summary: {deleted_count} items deleted, {skipped_count} items skipped (protected).")
        print("Please restart your runtime and run the notebook from the first cell for a fresh start.")
    _update_memory_info()

# --- END OF MODIFICATION ---

def generate_messages(deleted_files_dict):
    """Generates informative messages about deleted files."""
    messages = []

    for key, value in deleted_files_dict.items():
        object_word = key
        messages.append(f"Deleted {value} {object_word}")
    return messages

def execute_button_press(button):
    """Handles logic when the 'Execute Cleaning' button is pressed."""
    selected_cleaners = auto_cleaner_widget.value
    deleted_files_dict = {}

    output.clear_output() # Clear previous output each time

    if 'Delete All Except Notebook & Main.py' in selected_cleaners:
        clean_all_except_notebook_and_main() # Call the new global cleanup function
    else:
        for option in selected_cleaners:
            if option in directories:
                with output: # Direct output to the output widget
                    print(f"🗑️ Cleaning {option}...")
                deleted_count = clean_directory(directories[option], option)
                deleted_files_dict[option] = deleted_count
                with output: # Direct output to the output widget
                    for message in generate_messages({option: deleted_count}):
                        message_widget = HTML(f'<p class="output_message animated_message">{message}</p>')
                        display(message_widget)

    _update_memory_info()

def hide_button_press(button):
    """Handles logic when the 'Hide Widget' button is pressed."""
    factory.close(container, class_names=['hide'], delay=0.5)

## ================= AutoCleaner Widgets =================

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# Load Css
factory.load_css(cleaner_css)

# --- START OF MODIFICATION ---
# Get WebUI path from settings.json for the 'Delete All' option's protected folders list
# This assumes settings.json has been populated by setup.py
try:
    settings_data = js.read(SETTINGS_PATH, 'WEBUI', {})
    current_webui_path = Path(settings_data.get('webui_path', str(HOME / 'webui')))
except Exception:
    current_webui_path = HOME / 'webui' # Fallback
# --- END OF MODIFICATION ---

directories = {
    'Images': output_dir,
    'Models': model_dir,
    'Vae': vae_dir,
    'LoRa': lora_dir,
    'ControlNet Models': control_dir
    # Add other categories if needed, using the paths established by webui_utils.py
    # e.g., 'Embeddings': embed_dir,
    # 'Extensions': extension_dir, # Extensions usually in WEBUI folder, be careful with this
}

# --- START OF MODIFICATION ---
clean_options = list(directories.keys())
# Add the new 'Delete All Except Notebook & Main.py' option
clean_options.append('Delete All Except Notebook & Main.py') 
# --- END OF MODIFICATION ---

instruction_label = factory.create_html('''
<span class="instruction">Use <span style="color: #B2B2B2;">ctrl</span> or <span style="color: #B2B2B2;">shift</span> for multiple selections.</span>
''')
auto_cleaner_widget = factory.create_select_multiple(clean_options, '', [], layout={'width': 'auto'}, class_names=['custom_select_multiple'])
output = widgets.Output().add_class('output_panel')
# ---
execute_button = factory.create_button('Execute Cleaning', class_names=['button_execute', 'cleaner_button'])
hide_button = factory.create_button('Hide Widget', class_names=['button_hide', 'cleaner_button'])

# Button Click
execute_button.on_click(execute_button_press)
hide_button.on_click(hide_button_press)
# ---
storage_info = factory.create_html(f'''
<div class="storage_info">Total storage: {psutil.disk_usage(os.getcwd()).total / (1024 ** 3):.2f} GB <span style="color: #555">|</span> Used: {psutil.disk_usage(os.getcwd()).used / (1024 ** 3):.2f} GB <span style="color: #555">|</span> Free: {psutil.disk_usage(os.getcwd()).free / (1024 ** 3):.2f} GB</div>
''')
# ---
buttons = factory.create_hbox([execute_button, hide_button])
lower_information_panel = factory.create_hbox([buttons, storage_info], class_names=['lower_information_panel'])

# Create a horizontal layout for the selection and output areas
hbox_layout = factory.create_hbox([auto_cleaner_widget, output], class_names=['selection_output_layout'])

container = factory.create_vbox([instruction_label, HR, hbox_layout, HR, lower_information_panel],
                                layout={'width': '1080px'}, class_names=['cleaner_container'])

factory.display(container)
