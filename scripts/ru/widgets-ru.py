# ~ widgets.py | by ANXETY ~

from json_utils import read_json, save_json, update_json  # JSON (main)
from json_utils import key_or_value_exists, delete_key    # JSON (other)
from widget_factory import WidgetFactory                  # WIDGETS
from webui_utils import update_current_webui              # WEBUI

import ipywidgets as widgets
from pathlib import Path
import os

# Constants
HOME = Path.home()
SCR_PATH = Path(HOME / 'ANXETY')
SETTINGS_PATH = SCR_PATH / 'settings.json'
ENV_NAME = read_json(SETTINGS_PATH, 'ENVIRONMENT.env_name')

CSS = SCR_PATH / 'CSS'
JS = SCR_PATH / 'JS'
widgets_css = CSS / 'main-widgets.css'
widgets_js = JS / 'main-widgets.js'

# ====================== WIDGETS =====================
webui_selection = {
    'A1111': "--listen --xformers --enable-insecure-extension-access --disable-console-progressbars --no-half-vae --theme dark",
    'ReForge': "--xformers --cuda-stream --pin-shared-memory --enable-insecure-extension-access --disable-console-progressbars --theme dark",
    'ComfyUI': "--dont-print-server --preview-method auto --use-pytorch-cross-attention",
    'Forge': "--disable-xformers --opt-sdp-attention --cuda-stream --pin-shared-memory --enable-insecure-extension-access --disable-console-progressbars --theme dark"
}

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# --- MODEL ---
"""Create model selection widgets."""
model_header = factory.create_header('Выбор Модели')
model_options = [
    'none', '1.Anime (by XpucT) + INP', '2.BluMix [Anime] [V7] + INP',
    '3.Cetus-Mix [Anime] [V4] + INP', '4.Counterfeit [Anime] [V3] + INP',
    '5.CuteColor [Anime] [V3]', '6.Dark-Sushi-Mix [Anime]',
    '7.Meina-Mix [Anime] [V11] + INP', '8.Mix-Pro [Anime] [V4] + INP'
]
xl_model_options = [
    'none', '1.Nova [Anime] [V7] [XL]'
]
model_widget = factory.create_dropdown(model_options, 'Модель:', '4.Counterfeit [Anime] [V3] + INP')
model_num_widget = factory.create_text('Номер Модели:', '', 'Введите номера моделей для скачивания.')
inpainting_model_widget = factory.create_checkbox('Inpainting Модели', False, class_names=['inpaint'])
XL_models_widget = factory.create_checkbox('SDXL', False, class_names=['sdxl'])

switch_model_widget = factory.create_hbox([inpainting_model_widget, XL_models_widget])

# --- VAE ---
"""Create VAE selection widgets."""
vae_header = factory.create_header('Выбор VAE')
vae_options = [
    'none', '1.Anime.vae',
    '2.Anything.vae', '3.Blessed2.vae',
    '4.ClearVae.vae', '5.WD.vae'
]
xl_vae_options = [
    'none', 'ALL', '1.sdxl.vae'
]
vae_widget = factory.create_dropdown(vae_options, 'Vae:', '3.Blessed2.vae')
vae_num_widget = factory.create_text('Номер Vae:', '', 'Введите номера vae для скачивания.')

# --- ADDITIONAL ---
"""Create additional configuration widgets."""
additional_header = factory.create_header('Дополнительно')
latest_webui_widget = factory.create_checkbox('Обновить WebUI', True)
latest_extensions_widget = factory.create_checkbox('Обновить Расширения', True)
change_webui_widget = factory.create_dropdown(['A1111', 'ReForge', 'ComfyUI', 'Forge'], 'WebUI:', 'A1111', layout={'width': 'auto'})
detailed_download_widget = factory.create_dropdown(['off', 'on'], 'Подробная Загрузка:', 'off', layout={'width': 'auto'})
choose_changes_widget = factory.create_hbox([latest_webui_widget, latest_extensions_widget, change_webui_widget, detailed_download_widget],
                                            layout={'justify_content': 'space-between'})
controlnet_options = [
    'none', 'ALL', '1.Openpose', '2.Canny', '3.Depth',
    '4.Lineart', '5.ip2p', '6.Shuffle', '7.Inpaint',
    '8.MLSD', '9.Normalbae', '10.Scribble', '11.Seg',
    '12.Softedge', '13.Tile'
]
xl_controlnet_options = [
    'none', 'ALL', '1.Kohya Controllite XL Blur',
    '2.Kohya Controllite XL Canny', '3.Kohya Controllite XL Depth',
    '4.Kohya Controllite XL Openpose Anime', '5.Kohya Controllite XL Scribble Anime',
    '6.T2I Adapter XL Canny',
    '7.T2I Adapter XL Openpose',
    '8.T2I Adapter XL Sketch',
    '9.T2I Adapter Diffusers XL Canny',
    '10.T2I Adapter Diffusers XL Depth Midas',
    '11.T2I Adapter Diffusers XL Depth Zoe',
    '12.T2I Adapter Diffusers XL Lineart',
    '13.T2I Adapter Diffusers XL Openpose',
    '14.T2I Adapter Diffusers XL Sketch',
]
controlnet_widget = factory.create_dropdown(controlnet_options, 'ControlNet:', 'none')
controlnet_num_widget = factory.create_text('Номер ControlNet:', '', 'Введите номера моделей ControlNet для скачивания.')
commit_hash_widget = factory.create_text('Commit Hash:')
civitai_token_widget = factory.create_text('Токен CivitAI:', '', 'Введите свой API-токен CivitAi.')
huggingface_token_widget = factory.create_text('Токен HuggingFace:')

zrok_token_widget = factory.create_text('Токен Zrok:')
zrok_button = factory.create_html('<a href="https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU" target="_blank">Зарегать Zrok Токен</a>', class_names=["button", "button_ngrok"])
zrok_widget = factory.create_hbox([zrok_token_widget, zrok_button])

commandline_arguments_widget = factory.create_text('Аргументы:', webui_selection['A1111'])

additional_widget_list = [
    additional_header, choose_changes_widget, HR, controlnet_widget, controlnet_num_widget,
    civitai_token_widget, huggingface_token_widget, zrok_widget, HR, commandline_arguments_widget
]

# --- CUSTOM DOWNLOAD ---
"""Create Custom-Download Selection widgets."""
custom_download_header_popup = factory.create_html('''
<div class="header" style="cursor: pointer;" onclick="toggleContainer()">Кастомная Загрузка</div>
<div class="info" id="info_dl">INFO</div>
<div class="popup">
    Разделите несколько URL-адресов запятой/пробелом. Для <span class="file_name">пользовательского имени</span> файла/расширения укажите его через <span class="braces">[]</span> после URL без пробелов.
    <span class="required">Для файлов обязательно укажите</span> - <span class="extension">Расширение Файла.</span>
    <div class="sample">
        <span class="sample_label">Пример для Файла:</span>
        https://civitai.com/api/download/models/229782<span class="braces">[</span><span class="file_name">Detailer</span><span class="extension">.safetensors</span><span class="braces">]</span>
        <br>
        <span class="sample_label">Пример для Расширения:</span>
        https://github.com/hako-mikan/sd-webui-regional-prompter<span class="braces">[</span><span class="file_name">Regional-Prompter</span><span class="braces">]</span>
    </div>
</div>
''')

Model_url_widget = factory.create_text('Model:')
Vae_url_widget = factory.create_text('Vae:')
LoRA_url_widget = factory.create_text('LoRa:')
Embedding_url_widget = factory.create_text('Embedding:')
Extensions_url_widget = factory.create_text('Extensions:')
custom_file_urls_widget = factory.create_text('Файл (txt):')

# --- Save Button ---
"""Create button widgets."""
save_button = factory.create_button('Сохранить', class_names=["button", "button_save"])

# ================ DISPLAY / SETTINGS ================

factory.load_css(widgets_css)   # load CSS (widgets)
factory.load_js(widgets_js)     # load JS (widgets)

# Display sections
model_widgets = [model_header, model_widget, model_num_widget, switch_model_widget]
vae_widgets = [vae_header, vae_widget, vae_num_widget]
additional_widgets = additional_widget_list
custom_download_widgets = [
    custom_download_header_popup,
    Model_url_widget,
    Vae_url_widget,
    LoRA_url_widget,
    Embedding_url_widget,
    Extensions_url_widget,
    custom_file_urls_widget
]
button_widgets = [save_button]

# Create Boxes
model_box = factory.create_vbox(model_widgets, class_names=["container"])
vae_box = factory.create_vbox(vae_widgets, class_names=["container"])
additional_box = factory.create_vbox(additional_widgets, class_names=["container"])
custom_download_box = factory.create_vbox(custom_download_widgets, class_names=["container", "container_cdl"])
button_box = factory.create_hbox(button_widgets)

WIDGET_LIST = factory.create_vbox([model_box, vae_box, additional_box, custom_download_box, button_box],
                                  layouts=[{'width': '1080px'}])
factory.display(WIDGET_LIST)

# ================ CALLBACK FUNCTION ================
# Callback functions for updating widgets
def update_change_webui(change, widget):
    selected_webui = change['new']
    commandline_arguments = webui_selection.get(selected_webui, "")
    commandline_arguments_widget.value = commandline_arguments
    
    if selected_webui == 'ComfyUI':
        Extensions_url_widget.description = 'Custom Nodes:'
    else:
        Extensions_url_widget.description = 'Extensions:'

def update_XL_options(change, widget):
    selected = change['new']

    if selected:    # SD XL options
        model_widget.options = xl_model_options
        model_widget.value = '1.Nova [Anime] [V7] [XL]'
        vae_widget.options = xl_vae_options
        vae_widget.value = '1.sdxl.vae'
        controlnet_widget.options = xl_controlnet_options
        controlnet_widget.value = 'none'
    else:     # SD 1.5 options
        model_widget.options = model_options
        model_widget.value = '4.Counterfeit [Anime] [V3] + INP'
        vae_widget.options = vae_options
        vae_widget.value = '3.Blessed2.vae'
        controlnet_widget.options = controlnet_options
        controlnet_widget.value = 'none'

# Connecting widgets
factory.connect_widgets([(change_webui_widget, 'value')], [update_change_webui])
factory.connect_widgets([(XL_models_widget, 'value')], [update_XL_options])

## ============ Load / Save - Settings V3 ============

SETTINGS_KEYS = [
      'XL_models', 'model', 'model_num', 'inpainting_model', 'vae', 'vae_num',
      'latest_webui', 'latest_extensions', 'change_webui', 'detailed_download',
      'controlnet', 'controlnet_num', 'commit_hash',
      'civitai_token', 'huggingface_token', 'zrok_token', 'commandline_arguments',
      'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'custom_file_urls'
]

def save_settings():
    """Save widget values to settings."""
    widgets_values = {key: globals()[f"{key}_widget"].value for key in SETTINGS_KEYS}
    save_json(SETTINGS_PATH, "WIDGETS", widgets_values)

    update_current_webui(change_webui_widget.value)  # Upadte Selected WebUI in setting.json

def load_settings():
    """Load widget values from settings."""
    if key_or_value_exists(SETTINGS_PATH, 'WIDGETS'):
        widget_data = read_json(SETTINGS_PATH, 'WIDGETS')
        for key in SETTINGS_KEYS:
            if key in widget_data:
                globals()[f"{key}_widget"].value = widget_data.get(key, "")

def save_data(button):
    """Handle save button click."""
    save_settings()
    factory.close(list(WIDGET_LIST.children), class_names=['hide'], delay=0.5)

load_settings()
save_button.on_click(save_data)