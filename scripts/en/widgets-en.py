# ~ widgets.py | by ANXETY ~

from widget_factory import WidgetFactory        # WIDGETS
from webui_utils import update_current_webui, SHARED_MODEL_BASE # WEBUI # Import SHARED_MODEL_BASE
import json_utils as js                         # JSON

import ipywidgets as widgets
from pathlib import Path
import os

# Platform-aware widget configuration
PLATFORM = os.environ.get('DETECTED_PLATFORM', 'local')

# --- START OF MODIFICATION ---
def get_platform_paths():
    """
    Get platform-specific paths.
    Model-related paths (models, vae, lora, embeddings, controlnet) will now
    consistently refer to subdirectories within SHARED_MODEL_BASE.
    Only UI-specific directories (like extensions, outputs) will be under the UI's base.
    """
    # Base path for the current studio instance
    if PLATFORM == 'lightning':
        base = Path('/teamspace/studios/this_studio')
    elif PLATFORM == 'colab':
        base = Path('/content')
    elif PLATFORM == 'kaggle':
        base = Path('/kaggle/working')
    else:
        base = Path.cwd()

    return {
        # Model-related directories should reference SHARED_MODEL_BASE
        'models': SHARED_MODEL_BASE / 'Stable-diffusion',
        'vae': SHARED_MODEL_BASE / 'vae',
        'lora': SHARED_MODEL_BASE / 'Lora',
        'embeddings': SHARED_MODEL_BASE / 'embeddings',
        'controlnet': SHARED_MODEL_BASE / 'ControlNet',
        'adetailer': SHARED_MODEL_BASE / 'adetailer', 
        'clip': SHARED_MODEL_BASE / 'text_encoder', 
        'unet': SHARED_MODEL_BASE / 'unet', 
        'vision': SHARED_MODEL_BASE / 'clip_vision', 
        'encoder': SHARED_MODEL_BASE / 'text_encoder', 
        'diffusion': SHARED_MODEL_BASE / 'diffusion_models', 
        'upscale': SHARED_MODEL_BASE / 'ESRGAN', 

        # UI-specific directories (these are typically within the WebUI's own folder)
        # Note: 'base' here means the root of the studio, not the specific UI's folder.
        # The actual UI folder path (WEBUI) is determined later by settings.
        # We ensure these paths are created, assuming they are general top-level dirs.
        'outputs': base / 'outputs', 
        'extensions_root': base / 'extensions', # This is where generic extensions might be cloned if not UI-specific
        'config_root': base / 'config', # Generic config root
        
        # Temporary/Cache directories (often global or in /tmp)
        'temp': Path('/tmp/sdaigen') if PLATFORM == 'lightning' else base / 'temp',
        'cache': base / '.cache'
    }

# Get paths (not creating them here yet)
PATHS = get_platform_paths()

# Constants
HOME = Path.home()
SCR_PATH = Path(HOME / 'ANXETY')
SETTINGS_PATH = SCR_PATH / 'settings.json'
ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

SCRIPTS = SCR_PATH / 'scripts'

CSS = SCR_PATH / 'CSS'
JS = SCR_PATH / 'JS'
widgets_css = CSS / 'main-widgets.css'
widgets_js = JS / 'main-widgets.js'

## --- Ensure all necessary directories exist (only for paths that are directly managed/created here) ---
# This loop now explicitly creates only the paths returned by get_platform_paths().
# It's crucial that SHARED_MODEL_BASE and its subdirectories are also explicitly created.
# These paths are what determine your top-level folder structure.
for path_key, path_obj in PATHS.items():
    if path_obj: # Ensure path_obj is not empty/None
        # These are all top-level directories or critical shared directories.
        # We assume they should exist in the root if not part of system /tmp.
        if path_key not in ['temp', 'cache']: # Exclude system temp/cache as they might be handled elsewhere
            path_obj.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path_obj}")

# Explicitly ensure SHARED_MODEL_BASE itself and its known main subdirectories exist
SHARED_MODEL_BASE.mkdir(parents=True, exist_ok=True)
print(f"Ensured SHARED_MODEL_BASE exists: {SHARED_MODEL_BASE}")

# Also ensure specific model subdirectories within SHARED_MODEL_BASE are created here,
# as widgets script might be the first to trigger their need.
(SHARED_MODEL_BASE / 'Stable-diffusion').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'vae').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'Lora').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'embeddings').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'ControlNet').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'adetailer').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'text_encoder').mkdir(parents=True, exist_ok=True) # For clip/encoder
(SHARED_MODEL_BASE / 'unet').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'clip_vision').mkdir(parents=True, exist_ok=True) # For vision
(SHARED_MODEL_BASE / 'diffusion_models').mkdir(parents=True, exist_ok=True)
(SHARED_MODEL_BASE / 'ESRGAN').mkdir(parents=True, exist_ok=True)

# Update the settings.json with the definitive paths from this script
# (These would have been read from settings.json in downloading.py)
# This ensures consistency for other scripts relying on settings.json
js.save(SETTINGS_PATH, 'WEBUI.model_dir', str(SHARED_MODEL_BASE / 'Stable-diffusion'))
js.save(SETTINGS_PATH, 'WEBUI.vae_dir', str(SHARED_MODEL_BASE / 'vae'))
js.save(SETTINGS_PATH, 'WEBUI.lora_dir', str(SHARED_MODEL_BASE / 'Lora'))
js.save(SETTINGS_PATH, 'WEBUI.embed_dir', str(SHARED_MODEL_BASE / 'embeddings'))
js.save(SETTINGS_PATH, 'WEBUI.control_dir', str(SHARED_MODEL_BASE / 'ControlNet'))
js.save(SETTINGS_PATH, 'WEBUI.adetailer_dir', str(SHARED_MODEL_BASE / 'adetailer'))
js.save(SETTINGS_PATH, 'WEBUI.clip_dir', str(SHARED_MODEL_BASE / 'text_encoder'))
js.save(SETTINGS_PATH, 'WEBUI.unet_dir', str(SHARED_MODEL_BASE / 'unet'))
js.save(SETTINGS_PATH, 'WEBUI.vision_dir', str(SHARED_MODEL_BASE / 'clip_vision'))
js.save(SETTINGS_PATH, 'WEBUI.encoder_dir', str(SHARED_MODEL_BASE / 'text_encoder'))
js.save(SETTINGS_PATH, 'WEBUI.diffusion_dir', str(SHARED_MODEL_BASE / 'diffusion_models'))
js.save(SETTINGS_PATH, 'WEBUI.upscale_dir', str(SHARED_MODEL_BASE / 'ESRGAN'))
js.save(SETTINGS_PATH, 'WEBUI.output_dir', str(PATHS['outputs'])) # Use the base/outputs path
js.save(SETTINGS_PATH, 'WEBUI.extension_dir', str(PATHS['extensions_root'])) # Use the base/extensions path
js.save(SETTINGS_PATH, 'WEBUI.config_dir', str(PATHS['config_root'])) # Use the base/config path


# Re-load settings to ensure `model_dir`, `vae_dir` etc. are updated for the rest of this script's execution
# This is crucial for the widgets to reflect the correct paths if they need to.
settings = js.read(SETTINGS_PATH)
locals().update(settings) # Re-populate locals with updated settings
# --- END OF MODIFICATION ---


## ======================= WIDGETS =======================

def create_expandable_button(text, url):
    return factory.create_html(f'''
    <a href="{url}" target="_blank" class="button button_api">
        <span class="icon"><</span>
        <span class="text">{text}</span>
    </a>
    ''')

# Modified read_model_data to be more generic for data files
def read_model_data(file_path, data_key_in_file, prefixes=['none']):
    """Reads data from the specified file based on a key within that file."""
    local_vars = {}
    with open(file_path) as f:
        exec(f.read(), {}, local_vars)
    
    # Safely get the nested dictionary if data_key_in_file is like 'lora_data.sd15_loras'
    data_dict = local_vars
    for key_part in data_key_in_file.split('.'):
        data_dict = data_dict.get(key_part, {})
        if not isinstance(data_dict, dict): # Handle cases where a key part might not lead to a dict
            data_dict = {}
            break

    names = list(data_dict.keys())
    return prefixes + names


webui_selection = {
    'A1111':   "--xformers --no-half-vae",
    'ComfyUI': "--use-sage-attention --dont-print-server",
    'Forge':   "--disable-xformers --opt-sdp-attention --cuda-stream --pin-shared-memory",
    'Classic': "--persistent-patches --cuda-stream --pin-shared-memory",    # Remove: --xformers
    'ReForge': "--xformers --cuda-stream --pin-shared-memory",
    'SD-UX':   "--xformers --no-half-vae"
}

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# --- MODEL ---
"""Create model selection widgets."""
model_header = factory.create_header('Model Selection')
model_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'model_list') # Updated key here
model_widget = factory.create_dropdown(model_options, 'Model:', '4. Counterfeit [Anime] [V3] + INP')
model_num_widget = factory.create_text('Model Number:', '', 'Enter model numbers for download.')
inpainting_model_widget = factory.create_checkbox('Inpainting Models', False, class_names=['inpaint'], layout={'width': '25%'})
XL_models_widget = factory.create_checkbox('SDXL', False, class_names=['sdxl'])

switch_model_widget = factory.create_hbox([inpainting_model_widget, XL_models_widget])

# --- VAE ---
"""Create VAE selection widgets."""
vae_header = factory.create_header('VAE Selection')
vae_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'vae_list') # Updated key here
vae_widget = factory.create_dropdown(vae_options, 'Vae:', '3. Blessed2.vae')
vae_num_widget = factory.create_text('Vae Number:', '', 'Enter vae numbers for download.')

# --- LORA (NEW SECTION) ---
"""Create LoRA selection widgets."""
lora_header = factory.create_header('LoRA Selection')
# Initial load of LoRA options (defaults to SD 1.5 LoRAs)
lora_options = read_model_data(f"{SCRIPTS}/_loras-data.py", 'lora_data.sd15_loras')
lora_widget = factory.create_dropdown(lora_options, 'LoRA:', 'none')
lora_num_widget = factory.create_text('LoRA Number:', '', 'Enter LoRA numbers for download.')


# --- ADDITIONAL ---
"""Create additional configuration widgets."""
additional_header = factory.create_header('Additionally')
latest_webui_widget = factory.create_checkbox('Update WebUI', True)
latest_extensions_widget = factory.create_checkbox('Update Extensions', True)
check_custom_nodes_deps_widget = factory.create_checkbox('Check Custom-Nodes Dependencies', True)
change_webui_widget = factory.create_dropdown(list(webui_selection.keys()), 'WebUI:', 'A1111', layout={'width': 'auto'})
detailed_download_widget = factory.create_dropdown(['off', 'on'], 'Detailed Download:', 'off', layout={'width': 'auto'})
choose_changes_widget = factory.create_hbox(
    [
        latest_webui_widget,
        latest_extensions_widget,
        check_custom_nodes_deps_widget,   # Only ComfyUI
        change_webui_widget,
        detailed_download_widget
    ],
    layout={'justify_content': 'space-between'}
)

controlnet_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'controlnet_list') # Updated key here
controlnet_widget = factory.create_dropdown(controlnet_options, 'ControlNet:', 'none')
controlnet_num_widget = factory.create_text('ControlNet Number:', '', 'Enter ControlNet numbers for download.')
commit_hash_widget = factory.create_text('Commit Hash:', '', 'Switching between branches or commits.')

# HARDCODED TOKENS START HERE
civitai_token_widget = factory.create_text('CivitAI Token:', 'ff14ef326fa02885e8202e4d44fc9a13', 'Enter your CivitAi API token.')
civitai_button = create_expandable_button('Get CivitAI Token', 'https://civitai.com/user/account')
civitai_widget = factory.create_hbox([civitai_token_widget, civitai_button])

huggingface_token_widget = factory.create_text('HuggingFace Token:', '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')
huggingface_button = create_expandable_button('Get HuggingFace Token', 'https://huggingface.co/settings/tokens')
huggingface_widget = factory.create_hbox([huggingface_token_widget, huggingface_button])

ngrok_token_widget = factory.create_text('Ngrok Token:', '2tjxIXifSaGR3dMhkvhk6sZqbGo_6ZfBZLZHMbtAjfRmfoDW5')
ngrok_button = create_expandable_button('Get Ngrok Token', 'https://dashboard.ngrok.com/get-started/your-authtoken')
ngrok_widget = factory.create_hbox([ngrok_token_widget, ngrok_button])

# Moved Zrok widget definition before additional_widget_list
zrok_token_widget = factory.create_text('Zrok Token:')
zrok_button = create_expandable_button('Register Zrok Token', 'https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU')
zrok_widget = factory.create_hbox([zrok_token_widget, zrok_button])
# HARDCODED TOKENS END HERE

commandline_arguments_widget = factory.create_text('Arguments:', webui_selection['A1111'])

accent_colors_options = ['anxety', 'blue', 'green', 'peach', 'pink', 'red', 'yellow']
theme_accent_widget = factory.create_dropdown(accent_colors_options, 'Theme Accent:', 'anxety',
                                              layout={'width': 'auto', 'margin': '0 0 0 8px'})    # margin-left

additional_footer = factory.create_hbox([commandline_arguments_widget, theme_accent_widget])

additional_widget_list = [
    additional_header,
    choose_changes_widget,
    HR,
    controlnet_widget, controlnet_num_widget,
    commit_hash_widget,
    # Removed redundant LoRA widgets from here, they are now in their own box (lora_box)
    HR,
    civitai_widget, huggingface_widget, zrok_widget, ngrok_widget,
    HR,
    # commandline_arguments_widget,
    additional_footer
]

# --- CUSTOM DOWNLOAD ---
"""Create Custom-Download Selection widgets."""
custom_download_header_popup = factory.create_html('''
<div class="header" style="cursor: pointer;" onclick="toggleContainer()">Custom Download</div>
<div class="info" id="info_dl">INFO</div>
<div class="popup">
    Separate multiple URLs with a comma/space.
    For a <span class="file_name">custom name</span> file/extension, specify it with <span class="braces">[]</span> after the URL without spaces.
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


## ============ MODULE | GDrive Toggle Button ============
"""Create Google Drive toggle button for Colab only."""
from pathlib import Path

TOOLTIPS = ("Unmount Google Drive storage", "Mount Google Drive storage")
BTN_STYLE = {'width': '48px', 'height': '48px'}

GD_status = js.read(SETTINGS_PATH, 'mountGDrive') or False
GDrive_button = factory.create_button('', layout=BTN_STYLE, class_names=['gdrive-btn'])

# Init
GDrive_button.tooltip = TOOLTIPS[0] if GD_status else TOOLTIPS[1]

if ENV_NAME == 'Google Colab':
    GDrive_button.toggle = GD_status
    if GDrive_button.toggle:
        GDrive_button.add_class('active')

    def handle_toggle(btn):
        """Toggle Google Drive button state"""
        btn.toggle = not btn.toggle
        btn.tooltip = TOOLTIPS[0] if btn.toggle else TOOLTIPS[1]
        btn.add_class('active') if btn.toggle else btn.remove_class('active')

    GDrive_button.on_click(handle_toggle)
else:
    GDrive_button.layout.display = 'none'   # Hide GD-btn if ENV is not Colab


## ================== DISPLAY / SETTINGS =================

factory.load_css(widgets_css)   # load CSS (widgets)
factory.load_js(widgets_js)     # load JS (widgets)

# Display sections
model_widgets = [model_header, model_widget, model_num_widget, switch_model_widget]
vae_widgets = [vae_header, vae_widget, vae_num_widget]
lora_widgets = [lora_header, lora_widget, lora_num_widget] # Group LoRA widgets
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
# model_box = factory.create_vbox(model_widgets, class_names=['container'])
model_content = factory.create_vbox(model_widgets, class_names=['container'])   # With GD-btn :#
model_box = factory.create_hbox([model_content, GDrive_button], layout={'width': '1150px'})   # fix layout width...

vae_box = factory.create_vbox(vae_widgets, class_names=['container'])
lora_box = factory.create_vbox(lora_widgets, class_names=['container']) # New LoRA Box
additional_box = factory.create_vbox(additional_widgets, class_names=['container'])
custom_download_box = factory.create_vbox(custom_download_widgets, class_names=['container', 'container_cdl'])

# Added lora_box to the main display list
WIDGET_LIST = factory.create_vbox([model_box, vae_box, lora_box, additional_box, custom_download_box, save_button],
                                  class_names=['mainContainer'])
factory.display(WIDGET_LIST)

## ================== CALLBACK FUNCTION ==================

# Initialize visibility | hidden
check_custom_nodes_deps_widget.layout.display = 'none'
empowerment_output_widget.add_class('empowerment-output')
empowerment_output_widget.add_class('hidden')

# Callback functions for XL options
def update_XL_options(change, widget):
    selected = change['new']

    default_model_values = {
        True: ('4. WAI-illustrious [Anime] [V14] [XL]', 'none', 'none'),           # XL models
        False: ('4. Counterfeit [Anime] [V3] + INP', '3. Blessed2.vae', 'none')    # SD 1.5 models
    }

    # Get data - MODELs | VAEs | CNETs
    # Update main model, VAE, ControlNet options based on SDXL checkbox
    model_data_file = f"{SCRIPTS}/_xl-models-data.py" if selected else f"{SCRIPTS}/_models-data.py"
    model_widget.options = read_model_data(model_data_file, 'model_list')
    vae_widget.options = read_model_data(model_data_file, 'vae_list')
    controlnet_widget.options = read_model_data(model_data_file, 'controlnet_list')

    # Update LoRA options based on SDXL checkbox
    lora_data_key = 'lora_data.sdxl_loras' if selected else 'lora_data.sd15_loras'
    lora_widget.options = read_model_data(f"{SCRIPTS}/_loras-data.py", lora_data_key)


    # Set default values from the dictionary
    model_widget.value, vae_widget.value, controlnet_widget.value = default_model_values[selected]
    # LoRA default value
    lora_widget.value = 'none' # Reset LoRA selection on model type change


# Callback functions for updating widgets
def update_change_webui(change, widget):
    selected_webui = change['new']
    commandline_arguments = webui_selection.get(selected_webui, '')
    commandline_arguments_widget.value = commandline_arguments

    if selected_webui == 'ComfyUI':
        latest_extensions_widget.layout.display = 'none'
        latest_extensions_widget.value = False
        check_custom_nodes_deps_widget.layout.display = ''
        theme_accent_widget.layout.display = 'none'
        theme_accent_widget.value = 'anxety'
        Extensions_url_widget.description = 'Custom Nodes:'
    else:
        latest_extensions_widget.layout.display = ''
        latest_extensions_widget.value = True
        check_custom_nodes_deps_widget.layout.display = 'none'
        theme_accent_widget.layout.display = ''
        theme_accent_widget.value = 'anxety'
        Extensions_url_widget.description = 'Extensions:'

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

## ============== Load / Save - Settings V4 ==============

SETTINGS_KEYS = [
      'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
      'latest_webui', 'latest_extensions', 'check_custom_nodes_deps', 'change_webui', 'detailed_download',
      'controlnet', 'controlnet_num', 'commit_hash',
      'lora', 'lora_num', # Added lora and lora_num to SETTINGS_KEYS
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

    # Save Status GDrive-btn
    js.save(SETTINGS_PATH, 'mountGDrive', True if GDrive_button.toggle else False)

    update_current_webui(change_webui_widget.value)  # Update Selected WebUI in setting.json

def load_settings():
    """Load widget values from settings."""
    if js.key_exists(SETTINGS_PATH, 'WIDGETS'):
        widget_data = js.read(SETTINGS_PATH, 'WIDGETS')
        for key in SETTINGS_KEYS:
            if key in widget_data:
                globals()[f"{key}_widget"].value = widget_data.get(key, '')

    # Load Status GDrive-btn
    GD_status = js.read(SETTINGS_PATH, 'mountGDrive') or False
    GDrive_button.toggle = (GD_status == True)
    if GDrive_button.toggle:
        GDrive_button.add_class('active')
    else:
        GDrive_button.remove_class('active')

def save_data(button):
    """Handle save button click."""
    save_settings()
    # factory.close(list(WIDGET_LIST.children), class_names=['hide'], delay=0.8)
    all_widgets = [model_content, vae_box, lora_box, additional_box, custom_download_box, save_button, GDrive_button] # Added lora_box
    factory.close(all_widgets, class_names=['hide'], delay=0.8)

load_settings()
save_button.on_click(save_data)
