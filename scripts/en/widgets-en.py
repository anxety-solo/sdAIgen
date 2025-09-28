# ~ widgets.py | by ANXETY ~

from widget_factory import WidgetFactory        # WIDGETS
from webui_utils import update_current_webui    # WEBUI
import json_utils as js                         # JSON

from IPython.display import display, HTML, Javascript
from google.colab import output
import ipywidgets as widgets
from pathlib import Path
import requests
import time
import json
import os


osENV = os.environ

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

SCRIPTS = SCR_PATH / 'scripts'

CSS = SCR_PATH / 'CSS'
JS = SCR_PATH / 'JS'
widgets_css = CSS / 'main-widgets.css'
widgets_js = JS / 'main-widgets.js'


# ================ WIDGETS (Main Container) ================

def create_expandable_button(text, url):
    return factory.create_html(f'''
    <a href="{url}" target="_blank" class="button button_api">
        <span class="icon"><</span>
        <span class="text">{text}</span>
    </a>
    ''')

def read_model_data(file_path, data_type):
    """Reads model, VAE, or ControlNet data from the specified file."""
    type_map = {
        'model': ('model_list', ['none']),
        'vae': ('vae_list', ['none', 'ALL']),
        'cnet': ('controlnet_list', ['none', 'ALL'])
    }
    key, prefixes = type_map[data_type]
    local_vars = {}

    with open(file_path) as f:
        exec(f.read(), {}, local_vars)

    names = list(local_vars[key].keys())
    return prefixes + names

def fetch_github_branches(repo_url, max_retries=3):
    """Fetch branch names from GitHub API."""
    repo_path = repo_url.replace('https://github.com/', '')
    api_url = f'https://api.github.com/repos/{repo_path}/branches'

    for attempt in range(max_retries):
        try:
            r = requests.get(api_url, timeout=10)
            if r.status_code == 200:
                branches = [b['name'] for b in r.json()]
                ordered = ['none']
                for preferred in ('main', 'master'):
                    if preferred in branches:
                        ordered.append(preferred)
                        branches.remove(preferred)
                return ordered + branches

            if r.status_code == 403 and attempt < max_retries - 1:
                time.sleep(2)
            else:
                break

        except requests.RequestException:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                break

    # Fail-Safe
    return ['none']

REPO_MAP = {
    'A1111':   "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
    'ComfyUI': "https://github.com/comfyanonymous/ComfyUI",
    'Forge':   "https://github.com/lllyasviel/stable-diffusion-webui-forge",
    'Classic': "https://github.com/Haoming02/sd-webui-forge-classic",
    'ReForge': "https://github.com/Panchovix/stable-diffusion-webui-reForge",
    'SD-UX':   "https://github.com/anapnoe/stable-diffusion-webui-ux"
}

WEBUI_PARAMS = {
    'A1111':   "--xformers --no-half-vae",
    'ComfyUI': "--dont-print-server",
    'Forge':   "--xformers --cuda-stream",              # Remove: --disable-xformers --opt-sdp-attention --pin-shared-memory
    'Classic': "--persistent-patches --cuda-stream",    # Remove: --xformers --pin-shared-memory
    'ReForge': "--xformers --cuda-stream",              # Remove: --pin-shared-memory
    'SD-UX':   "--xformers --no-half-vae"
}

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# --- MODEL ---
"""Create model selection widgets."""
model_header = factory.create_header('Model Selection')
model_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'model')
model_widget = factory.create_dropdown(model_options, 'Model:', '2. BluMix [Anime] [V7] + INP')
model_num_widget = factory.create_text('Model Number:', '', 'Enter model numbers for download.')
inpainting_model_widget = factory.create_checkbox('Inpainting Models', False, class_names=['inpaint'], layout={'width': '250px'})
XL_models_widget = factory.create_checkbox('SDXL', False, class_names=['sdxl'])

switch_model_widget = factory.create_hbox([inpainting_model_widget, XL_models_widget])

# --- VAE ---
"""Create VAE selection widgets."""
vae_header = factory.create_header('VAE Selection')
vae_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'vae')
vae_widget = factory.create_dropdown(vae_options, 'Vae:', '3. Blessed2.vae')
vae_num_widget = factory.create_text('Vae Number:', '', 'Enter vae numbers for download.')

# --- ADDITIONAL ---
"""Create additional configuration widgets."""
additional_header = factory.create_header('Additionally')
check_custom_nodes_deps_widget = factory.create_checkbox('Check Custom-Nodes Dependencies', True)
change_webui_widget = factory.create_dropdown(list(WEBUI_PARAMS.keys()), 'WebUI:', 'A1111', layout={'width': 'auto'})
detailed_download_widget = factory.create_dropdown(['off', 'on'], 'Detailed Download:', 'off', layout={'width': 'auto'})
choose_changes_box = factory.create_hbox(
    [
        check_custom_nodes_deps_widget,   # For ComfyUI
        change_webui_widget,
        detailed_download_widget
    ],
    layout={'justify_content': 'space-between'}
)

controlnet_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'cnet')
controlnet_widget = factory.create_dropdown(controlnet_options, 'ControlNet:', 'none')
controlnet_num_widget = factory.create_text('ControlNet Number:', '', 'Enter ControlNet numbers for download.')

commit_hash_widget = factory.create_text('Commit Hash:', '', 'Switching between branches or commits.')
branches_options = fetch_github_branches(REPO_MAP['A1111'])
branch_widget = factory.create_dropdown(branches_options, 'Branch:', 'none', layout={'width': '400px', 'margin': '0 0 0 8px'})    # margin-left
checkout_options_box = factory.create_hbox([commit_hash_widget, branch_widget])

civitai_token_widget = factory.create_text('CivitAI Token:', '', 'Enter your CivitAi API token.')
civitai_button = create_expandable_button('Get CivitAI Token', 'https://civitai.com/user/account')
civitai_box = factory.create_hbox([civitai_token_widget, civitai_button])

huggingface_token_widget = factory.create_text('HuggingFace Token:')
huggingface_button = create_expandable_button('Get HuggingFace Token', 'https://huggingface.co/settings/tokens')
huggingface_box = factory.create_hbox([huggingface_token_widget, huggingface_button])

ngrok_token_widget = factory.create_text('Ngrok Token:')
ngrok_button = create_expandable_button('Get Ngrok Token', 'https://dashboard.ngrok.com/get-started/your-authtoken')
ngrok_box = factory.create_hbox([ngrok_token_widget, ngrok_button])

zrok_token_widget = factory.create_text('Zrok Token:')
zrok_button = create_expandable_button('Register Zrok Token', 'https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU')
zrok_box = factory.create_hbox([zrok_token_widget, zrok_button])

commandline_arguments_widget = factory.create_text('Arguments:', WEBUI_PARAMS['A1111'])

accent_colors_options = ['anxety', 'blue', 'green', 'peach', 'pink', 'red', 'yellow']
theme_accent_widget = factory.create_dropdown(accent_colors_options, 'Theme Accent:', 'anxety',
                                              layout={'width': 'auto', 'margin': '0 0 0 8px'})    # margin-left

additional_footer_box = factory.create_hbox([commandline_arguments_widget, theme_accent_widget])

additional_widget_list = [
    additional_header,
    choose_changes_box,
    HR,
    controlnet_widget, controlnet_num_widget,
    # commit_hash_widget,
    checkout_options_box,
    civitai_box, huggingface_box, zrok_box, ngrok_box,
    HR,
    # commandline_arguments_widget
    additional_footer_box
]

# --- CUSTOM DOWNLOAD ---
"""Create Custom-Download Selection widgets."""
custom_download_header_popup = factory.create_html('''
<div class="header" style="cursor: pointer;" onclick="toggleContainer()">Custom Download</div>
<div class="info">INFO</div>
<div class="popup">
    Separate multiple URLs with a comma/space.
    For a <span class="file_name">custom name</span> file/extension, specify it with <span class="braces">[ ]</span> after the URL without spaces.
    <span style="color: #ff9999">For files, be sure to specify</span> - <span class="extension">Filename Extension.</span>
    <div class="sample">
        <span class="sample_label">Example for File:</span>
        https://civitai.com/api/download/models/229782<span class="braces">[</span><span class="file_name">Detailer</span><span class="extension">.safetensors</span><span class="braces">]</span>
        <br>
        <span class="sample_label">Example for Extension:</span>
        https://github.com/hako-mikan/sd-webui-regional-prompter<span class="braces">[</span><span class="file_name">Regional-Prompter</span><span class="braces">]</span>
    </div>
</div>
''')

empowerment_widget = factory.create_checkbox('Empowerment', False, class_names=['empowerment'])
empowerment_output_widget = factory.create_textarea(
'', '', """Use special tags. Portable analog of "File (txt)"
Tags: model (ckpt), vae, lora, embed (emb), extension (ext), adetailer (ad), control (cnet), upscale (ups), clip, unet, vision (vis), encoder (enc), diffusion (diff), config (cfg)
Short tags: start with '$' without a space -> $ckpt
------ Example ------

# Lora
https://civitai.com/api/download/models/229782

$ext
https://github.com/hako-mikan/sd-webui-cd-tuner[CD-Tuner]
""")

Model_url_widget = factory.create_text('Model:')
Vae_url_widget = factory.create_text('Vae:')
LoRA_url_widget = factory.create_text('LoRa:')
Embedding_url_widget = factory.create_text('Embedding:')
Extensions_url_widget = factory.create_text('Extensions:')
ADetailer_url_widget = factory.create_text('ADetailer:')
custom_file_urls_widget = factory.create_text('File (txt):')

# --- Save Button ---
"""Create button widgets."""
save_button = factory.create_button('Save', class_names=['button', 'button_save'])


# ===================== Side Container =====================
# --- GDrive Toggle Button ---
"""Create Google Drive toggle button for Colab only."""
BTN_STYLE = {'width': '48px', 'height': '48px'}
TOOLTIPS = ("Unmount Google Drive storage", "Mount Google Drive storage")

GD_status = js.read(SETTINGS_PATH, 'mountGDrive', False)
GDrive_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'gdrive-btn'])
GDrive_button.tooltip = TOOLTIPS[not GD_status]    # Invert index
GDrive_button.toggle = GD_status

if ENV_NAME != 'Google Colab':
    GDrive_button.layout.display = 'none'  # Hide button if not Colab
else:
    if GD_status:
        GDrive_button.add_class('active')

    def handle_toggle(btn):
        """Toggle Google Drive button state"""
        btn.toggle = not btn.toggle
        btn.tooltip = TOOLTIPS[not btn.toggle]
        btn.toggle and btn.add_class('active') or btn.remove_class('active')

    GDrive_button.on_click(handle_toggle)

# === Export/Import Widget Settings Buttons ===
"""Create buttons to export/import widget settings to JSON for Colab only."""
export_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'export-btn'])
export_button.tooltip = "Export settings to JSON"

import_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'import-btn'])
import_button.tooltip = "Import settings from JSON"

if ENV_NAME != 'Google Colab':
    # Hide buttons if not Colab
    export_button.layout.display = 'none'
    import_button.layout.display = 'none'

# EXPORT
def export_settings(button=None, filter_empty=False):
    try:
        widgets_data = {}
        for key in SETTINGS_KEYS:
            value = globals()[f"{key}_widget"].value
            if not filter_empty or (value not in [None, '', False]):
                widgets_data[key] = value

        settings_data = {
            'widgets': widgets_data,
            # 'mountGDrive': GDrive_button.toggle
        }

        display(Javascript(f'downloadJson({json.dumps(settings_data)});'))
        show_notification("Settings exported successfully!", "success")
    except Exception as e:
        show_notification(f"Export failed: {str(e)}", "error")

# IMPORT
def import_settings(button=None):
    display(Javascript('openFilePicker();'))

# APPLY SETTINGS
def apply_imported_settings(data):
    try:
        success_count = 0
        total_count = 0

        if 'widgets' in data:
            for key, value in data['widgets'].items():
                total_count += 1
                if key in SETTINGS_KEYS and f"{key}_widget" in globals():
                    try:
                        globals()[f"{key}_widget"].value = value
                        success_count += 1
                    except:
                        pass

        if 'mountGDrive' in data:
            GDrive_button.toggle = data['mountGDrive']
            if GDrive_button.toggle:
                GDrive_button.add_class('active')
            else:
                GDrive_button.remove_class('active')

        if success_count == total_count:
            show_notification("Settings imported successfully!", "success")
        else:
            show_notification(f"Imported {success_count}/{total_count} settings", "warning")

    except Exception as e:
        show_notification(f"Import failed: {str(e)}", "error")
        pass

# === NOTIFICATION for Export/Import ===
"""Create widget-popup displaying status of Export/Import settings."""
notification_popup = factory.create_html('', class_names=['notification-popup', 'hidden'])

def show_notification(message, message_type='info'):
    icon_map = {
        'success':  '✅',
        'error':    '❌',
        'info':     '💡',
        'warning':  '⚠️'
    }
    icon = icon_map.get(message_type, 'info')

    notification_popup.value = f'''
    <div class="notification {message_type}">
        <span class="notification-icon">{icon}</span>
        <span class="notification-text">{message}</span>
    </div>
    '''

    # Trigger re-show | Anxety-Tip: JS Script removes class only from DOM but not from widgets?!
    notification_popup.remove_class('visible')
    notification_popup.remove_class('hidden')
    notification_popup.add_class('visible')

    # Auto-hide PopUp After 2.5s
    display(Javascript("hideNotification(delay = 2500);"))

# REGISTER CALLBACK
"""
Registers the Python function 'apply_imported_settings' under the name 'importSettingsFromJS'
so it can be called from JavaScript via google.colab.kernel.invokeFunction(...)
"""
output.register_callback('importSettingsFromJS', apply_imported_settings)
output.register_callback('showNotificationFromJS', show_notification)

export_button.on_click(export_settings)
import_button.on_click(import_settings)


# =================== DISPLAY / SETTINGS ===================

factory.load_css(widgets_css)   # load CSS (widgets)
factory.load_js(widgets_js)     # load JS (widgets)

# Display sections
model_widgets = [model_header, model_widget, model_num_widget, switch_model_widget]
vae_widgets = [vae_header, vae_widget, vae_num_widget]
additional_widgets = additional_widget_list
custom_download_widgets = [
    custom_download_header_popup,
    empowerment_widget,
    empowerment_output_widget,
    Model_url_widget,
    Vae_url_widget,
    LoRA_url_widget,
    Embedding_url_widget,
    Extensions_url_widget,
    ADetailer_url_widget,
    custom_file_urls_widget
]

# Create Boxes
model_box = factory.create_vbox(model_widgets, class_names=['container'])
vae_box = factory.create_vbox(vae_widgets, class_names=['container'])
additional_box = factory.create_vbox(additional_widgets, class_names=['container'])
custom_download_box = factory.create_vbox(custom_download_widgets, class_names=['container', 'container_cdl'])

# Create Containers
CONTAINERS_WIDTH = '1080px'
model_vae_box = factory.create_hbox(
    [model_box, vae_box],
    class_names=['widgetContainer', 'model-vae'],
    # layout={'width': '100%'}
)

widgetContainer = factory.create_vbox(
    [model_vae_box, additional_box, custom_download_box, save_button],
    class_names=['widgetContainer'],
    layout={'min_width': CONTAINERS_WIDTH, 'max_width': CONTAINERS_WIDTH}
)
sideContainer = factory.create_vbox(
    [GDrive_button, export_button, import_button, notification_popup],
    class_names=['sideContainer']
)
mainContainer = factory.create_hbox(
    [widgetContainer, sideContainer],
    class_names=['mainContainer'],
    layout={'align_items': 'flex-start'}
)

factory.display(mainContainer)


# ==================== CALLBACK FUNCTION ===================

# Initialize visibility | hidden
# check_custom_nodes_deps_widget.layout.display = 'none'
check_custom_nodes_deps_widget.add_class('_disable')
empowerment_output_widget.add_class('empowerment-output')
empowerment_output_widget.add_class('hidden')

# Callback functions for XL options
def update_XL_options(change, widget):
    is_xl = change['new']
    defaults = {
        True: ('3. Nova-IL [Anime] [V11] [XL]', '1. sdxl.vae', 'none'),     # XL models
        False: ('2. BluMix [Anime] [V7] + INP', '3. Blessed2.vae', 'none')  # SD 1.5 models
    }

    data_file = '_xl-models-data.py' if is_xl else '_models-data.py'
    model_widget.options = read_model_data(f"{SCRIPTS}/{data_file}", 'model')
    vae_widget.options = read_model_data(f"{SCRIPTS}/{data_file}", 'vae')
    controlnet_widget.options = read_model_data(f"{SCRIPTS}/{data_file}", 'cnet')

    # Set default values from the dictionary
    model_widget.value, vae_widget.value, controlnet_widget.value = defaults[is_xl]

    # Disable/enable inpainting checkbox based on SDXL state
    if is_xl:
        inpainting_model_widget.add_class('_disable')
        inpainting_model_widget.value = False
    else:
        inpainting_model_widget.remove_class('_disable')

# Callback functions for updating widgets
def update_change_webui(change, widget):
    webui = change['new']
    commandline_arguments_widget.value = WEBUI_PARAMS.get(webui, '')

    if webui in REPO_MAP:
        repo_url = REPO_MAP[webui]
        new_branches = fetch_github_branches(repo_url)
        branch_widget.options = new_branches

    is_comfy = webui == 'ComfyUI'

    # Disable/enable check custom_nodes checkbox based on UI state
    if is_comfy:
        check_custom_nodes_deps_widget.remove_class('_disable')
        check_custom_nodes_deps_widget.value = True
    else:
        check_custom_nodes_deps_widget.add_class('_disable')

    # check_custom_nodes_deps_widget.layout.display = '' if is_comfy else 'none'
    theme_accent_widget.layout.display = 'none' if is_comfy else ''
    Extensions_url_widget.description = 'Custom Nodes:' if is_comfy else 'Extensions:'

# Callback functions for Empowerment
def update_empowerment(change, widget):
    selected_emp = change['new']

    customDL_widgets = [
        Model_url_widget,
        Vae_url_widget,
        LoRA_url_widget,
        Embedding_url_widget,
        Extensions_url_widget,
        ADetailer_url_widget
    ]
    for widget in customDL_widgets:    # For switching animation
        widget.add_class('empowerment-text-field')

    # idk why, but that's the way it's supposed to be >_<'
    if selected_emp:
        for wg in customDL_widgets:
            wg.add_class('hidden')
        empowerment_output_widget.remove_class('hidden')
    else:
        for wg in customDL_widgets:
            wg.remove_class('hidden')
        empowerment_output_widget.add_class('hidden')

# Connecting widgets
factory.connect_widgets([(change_webui_widget, 'value')], update_change_webui)
factory.connect_widgets([(XL_models_widget, 'value')], update_XL_options)
factory.connect_widgets([(empowerment_widget, 'value')], update_empowerment)


# ================ Load / Save - Settings V4 ===============

SETTINGS_KEYS = [
      'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
      # Additional
      'check_custom_nodes_deps', 'change_webui', 'detailed_download',
      'controlnet', 'controlnet_num', 'commit_hash', 'branch',
      'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
      # CustomDL
      'empowerment', 'empowerment_output',
      'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
      'custom_file_urls'
]

def save_settings():
    """Save widget values to settings."""
    widgets_values = {key: globals()[f"{key}_widget"].value for key in SETTINGS_KEYS}
    js.save(SETTINGS_PATH, 'WIDGETS', widgets_values)
    js.save(SETTINGS_PATH, 'mountGDrive', True if GDrive_button.toggle else False)  # Save Status GDrive-btn

    update_current_webui(change_webui_widget.value)  # Update Selected WebUI in settings.json

def load_settings():
    """Load widget values from settings."""
    if js.key_exists(SETTINGS_PATH, 'WIDGETS'):
        widget_data = js.read(SETTINGS_PATH, 'WIDGETS')
        for key in SETTINGS_KEYS:
            if key in widget_data:
                globals()[f"{key}_widget"].value = widget_data.get(key, '')

    # Load Status GDrive-btn
    GD_status = js.read(SETTINGS_PATH, 'mountGDrive', False)
    GDrive_button.toggle = (GD_status == True)
    if GDrive_button.toggle:
        GDrive_button.add_class('active')
    else:
        GDrive_button.remove_class('active')

def save_data(button):
    """Handle save button click."""
    save_settings()
    all_widgets = [
        model_box, vae_box, additional_box, custom_download_box, save_button,   # mainContainer
        GDrive_button, export_button, import_button, notification_popup         # sideContainer
    ]
    factory.close(all_widgets, class_names=['hide'], delay=0.8)

load_settings()
save_button.on_click(save_data)