# ~ widgets.py | by ANXETY ~

from widget_factory import WidgetFactory        # WIDGETS
from webui_utils import update_current_webui    # WEBUI
import json_utils as js                         # JSON

import ipywidgets as widgets
from pathlib import Path
import os


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


## ======================= WIDGETS =======================

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

webui_selection = {
    'A1111':   "--xformers --no-half-vae",
    'ComfyUI': "--dont-print-server --preview-method auto --use-pytorch-cross-attention",
    'Forge':   "--disable-xformers --opt-sdp-attention --cuda-stream --pin-shared-memory",
    'Classic': "--xformers --cuda-stream --pin-shared-memory",
    'ReForge': "--xformers --cuda-stream --pin-shared-memory",
    'SD-UX':   "--xformers --no-half-vae"
}

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# --- MODEL ---
"""Create model selection widgets."""
model_header = factory.create_header('Model Selection')
model_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'model')
model_widget = factory.create_dropdown(model_options, 'Model:', '4. Counterfeit [Anime] [V3] + INP')
model_num_widget = factory.create_text('Model Number:', '', 'Enter model numbers for download.')
inpainting_model_widget = factory.create_checkbox('Inpainting Models', False, class_names=['inpaint'], layout={'width': '25%'})
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

controlnet_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'cnet')
controlnet_widget = factory.create_dropdown(controlnet_options, 'ControlNet:', 'none')
controlnet_num_widget = factory.create_text('ControlNet Number:', '', 'Enter ControlNet numbers for download.')
commit_hash_widget = factory.create_text('Commit Hash:', '', 'Switching between branches or commits.')
civitai_token_widget = factory.create_text('CivitAI Token:', '', 'Enter your CivitAi API token.')
huggingface_token_widget = factory.create_text('HuggingFace Token:')

ngrok_token_widget = factory.create_text('Ngrok Token:')
ngrok_button = factory.create_html('<a href="https://dashboard.ngrok.com/get-started/your-authtoken" target="_blank">Get Ngrok Token</a>', class_names=['button', 'button_zrok'])
ngrok_widget = factory.create_hbox([ngrok_token_widget, ngrok_button])

zrok_token_widget = factory.create_text('Zrok Token:')
zrok_button = factory.create_html('<a href="https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU" target="_blank">Register Zrok Token</a>', class_names=['button', 'button_zrok'])
zrok_widget = factory.create_hbox([zrok_token_widget, zrok_button])

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
    civitai_token_widget, huggingface_token_widget, zrok_widget, ngrok_widget,
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
Tags: model (ckpt), vae, lora, embed (emb), extension (ext), adetailer (ad), control (cnet), upscale (ups), clip, unet, vision, encoder (enc), diffusion (diff), config (cfg)
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
additional_box = factory.create_vbox(additional_widgets, class_names=['container'])
custom_download_box = factory.create_vbox(custom_download_widgets, class_names=['container', 'container_cdl'])

WIDGET_LIST = factory.create_vbox([model_box, vae_box, additional_box, custom_download_box, save_button],
                                  class_names=['mainContainer'])
factory.display(WIDGET_LIST)

## ================== CALLBACK FUNCTION ==================

# Initialize visibility | hidden
check_custom_nodes_deps_widget.layout.display = 'none'
empowerment_output_widget.layout.display = 'none'

# Callback functions for XL options
def update_XL_options(change, widget):
    selected = change['new']

    default_model_values = {
        True: ('4. WAI-illustrious [Anime] [V14] [XL]', 'none', 'none'),           # XL models
        False: ('4. Counterfeit [Anime] [V3] + INP', '3. Blessed2.vae', 'none')    # SD 1.5 models
    }

    # Get data - MODELs | VAEs | CNETs
    data_file = '_xl-models-data.py' if selected else '_models-data.py'
    model_widget.options = read_model_data(f"{SCRIPTS}/{data_file}", 'model')
    vae_widget.options = read_model_data(f"{SCRIPTS}/{data_file}", 'vae')
    controlnet_widget.options = read_model_data(f"{SCRIPTS}/{data_file}", 'cnet')

    # Set default values from the dictionary
    model_widget.value, vae_widget.value, controlnet_widget.value = default_model_values[selected]

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

    # idk why, but that's the way it's supposed to be >_<'
    if selected_emp:
        for wg in customDL_widgets:
            wg.layout.display = 'none'
        empowerment_output_widget.layout.display = ''
    else:
        for wg in customDL_widgets:
            wg.layout.display = ''
        empowerment_output_widget.layout.display = 'none'

# Connecting widgets
factory.connect_widgets([(change_webui_widget, 'value')], update_change_webui)
factory.connect_widgets([(XL_models_widget, 'value')], update_XL_options)
factory.connect_widgets([(empowerment_widget, 'value')], update_empowerment)

## ============== Load / Save - Settings V4 ==============

SETTINGS_KEYS = [
      'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
      'latest_webui', 'latest_extensions', 'check_custom_nodes_deps', 'change_webui', 'detailed_download',
      'controlnet', 'controlnet_num', 'commit_hash',
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
    all_widgets = [model_content, vae_box, additional_box, custom_download_box, save_button, GDrive_button]
    factory.close(all_widgets, class_names=['hide'], delay=0.8)

load_settings()
save_button.on_click(save_data)