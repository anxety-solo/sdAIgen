# ~ widgets.py | by ANXETY ~

from widget_factory import WidgetFactory    # WIDGETS
from webui_utils import *                   # WEBUI / MODELs-DATA
import json_utils as js                     # JSON

from IPython.display import display, HTML, Javascript
from google.colab import output
from datetime import datetime
import ipywidgets as widgets
from pathlib import Path
import requests
import base64
import time
import json
import os


osENV = os.environ

# Auto-convert *_path env vars to Path
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, SCR_PATH, SETTINGS_PATH = (
    PATHS['home_path'], PATHS['scr_path'], PATHS['settings_path']
)

ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
SCRIPTS = PATHS['scripts_path']

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
    """Reads model, VAE, or ControlNet data from the specified file with auto-numbering"""
    type_map = {
        'model': ('model_list', ['none']),
        'vae': ('vae_list', ['none', 'ALL']),
        'cnet': ('controlnet_list', ['none', 'ALL'])
    }
    key, prefixes = type_map[data_type]
    local_vars = {}

    with open(file_path) as f:
        exec(f.read(), {}, local_vars)

    # Auto-numbering: add "n. " prefix to each model name
    original_dict = local_vars[key]
    numbered_names = [f"{i}. {name}" for i, name in enumerate(original_dict.keys(), start=1)]

    return prefixes + numbered_names

def fetch_github_branches(repo_url, webui=None):
    """Fetch branch names from GitHub API with optional filtering"""
    repo_path = repo_url.replace('https://github.com/', '')
    api_url = f'https://api.github.com/repos/{repo_path}/branches'

    try:
        r = requests.get(api_url, timeout=10)
        if r.status_code != 200:
            return ['none']

        branches = [b['name'] for b in r.json()]

        # --- ORDER MAIN / MASTER ---
        ordered = ['none']
        for preferred in ('main', 'master'):
            if preferred in branches:
                ordered.append(preferred)
                branches.remove(preferred)
        branches = ordered + branches

        # --- FILTERING LOGIC ---
        if webui == 'Classic':
            branches = [b for b in branches if 'neo' not in b.lower()]
        elif webui == 'Neo':
            branches = [b for b in branches if 'classic' not in b.lower()]

        return branches

    except requests.RequestException:
        return ['none']

REPO_MAP = {
    'A1111':   "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
    'ComfyUI': "https://github.com/comfyanonymous/ComfyUI",
    'Forge':   "https://github.com/lllyasviel/stable-diffusion-webui-forge",
    'Classic': "https://github.com/Haoming02/sd-webui-forge-classic",
    'Neo':     "https://github.com/Haoming02/sd-webui-forge-classic",
    'ReForge': "https://github.com/Panchovix/stable-diffusion-webui-reForge",
    'SD-UX':   "https://github.com/anapnoe/stable-diffusion-webui-ux"
}

WEBUI_PARAMS = {
    'A1111':   "--xformers",
    'ComfyUI': "--dont-print-server",
    'Forge':   "--xformers --cuda-stream",                       # Remove: --disable-xformers --opt-sdp-attention --pin-shared-memory
    'Classic': "--xformers --cuda-stream --persistent-patches",  # Remove: --pin-shared-memory
    'Neo':     "--xformers --cuda-stream --skip-version-check",
    'ReForge': "--xformers",                                     # Remove: --pin-shared-memory --cuda-stream
    'SD-UX':   "--xformers"
}

# Initialize the WidgetFactory
factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# --- MODEL ---
"""Create model selection widgets"""
model_header = factory.create_header('Выбор Модели')
model_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'model')
model_widget = factory.create_dropdown(model_options, 'Модель:', '2. BluMix [Anime] [V7] + INP')
model_num_widget = factory.create_text('Номер Модели:', '', 'Введите номера моделей для скачивания.')
inpainting_model_widget = factory.create_checkbox('Inpainting Модели', False, class_names=['inpaint'], layout={'width': '250px'})
XL_models_widget = factory.create_checkbox('SDXL', False, class_names=['sdxl'])

switch_model_widget = factory.create_hbox([inpainting_model_widget, XL_models_widget])

# --- VAE ---
"""Create VAE selection widgets"""
vae_header = factory.create_header('Выбор VAE')
vae_options = read_model_data(f"{SCRIPTS}/_models-data.py", 'vae')
vae_widget = factory.create_dropdown(vae_options, 'Vae:', '3. Blessed2.vae')
vae_num_widget = factory.create_text('Номер Vae:', '', 'Введите номера vae для скачивания.')

# --- ADDITIONAL ---
"""Create additional configuration widgets"""
additional_header = factory.create_header('Дополнительно')
latest_webui_widget = factory.create_checkbox('Обновить WebUI', True)
latest_extensions_widget = factory.create_checkbox('Обновить Расширения', True)
check_custom_nodes_deps_widget = factory.create_checkbox('Чекать зависимости Custom-Nodes', True)
change_webui_widget = factory.create_dropdown(list(WEBUI_PARAMS.keys()), 'WebUI:', 'A1111', layout={'width': 'auto'})
detailed_download_widget = factory.create_dropdown(['off', 'on'], 'Подробная Загрузка:', 'off', layout={'width': 'auto'})
choose_changes_box = factory.create_hbox(
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
controlnet_num_widget = factory.create_text('Номер ControlNet:', '', 'Введите номера моделей ControlNet для скачивания.')

commit_hash_widget = factory.create_text('Commit Hash:', '', 'Переключение между ветвями или коммитами.')
branches_options = fetch_github_branches(REPO_MAP['A1111'])
branch_widget = factory.create_dropdown(branches_options, 'Branch:', 'none', layout={'width': '400px', 'margin': '0 0 0 8px'})    # margin-left
checkout_options_box = factory.create_hbox([commit_hash_widget, branch_widget])

civitai_token_widget = factory.create_text('CivitAI Token:', '', 'Введите свой API-токен CivitAi.')
civitai_button = create_expandable_button('Получить CivitAI Токен', 'https://civitai.com/user/account')
civitai_box = factory.create_hbox([civitai_token_widget, civitai_button])

huggingface_token_widget = factory.create_text('HuggingFace Token:')
huggingface_button = create_expandable_button('Получить HuggingFace Токен', 'https://huggingface.co/settings/tokens')
huggingface_box = factory.create_hbox([huggingface_token_widget, huggingface_button])

ngrok_token_widget = factory.create_text('Ngrok Token:')
ngrok_button = create_expandable_button('Получить Ngrok Токен', 'https://dashboard.ngrok.com/get-started/your-authtoken')
ngrok_box = factory.create_hbox([ngrok_token_widget, ngrok_button])

zrok_token_widget = factory.create_text('Zrok Token:')
zrok_button = create_expandable_button('Зарегать Zrok Токен', 'https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU')
zrok_box = factory.create_hbox([zrok_token_widget, zrok_button])

commandline_arguments_widget = factory.create_text('Аргументы:', WEBUI_PARAMS['A1111'])

accent_colors_options = ['anxety', 'blue', 'green', 'peach', 'pink', 'red', 'yellow']
theme_accent_widget = factory.create_dropdown(accent_colors_options, 'Акцент Темы:', 'anxety',
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
    # commandline_arguments_widget,
    additional_footer_box
]

# --- CUSTOM DOWNLOAD ---
"""Create Custom-Download Selection widgets"""
custom_download_header_popup = factory.create_html('''
<div class="header" style="cursor: pointer;" onclick="toggleContainer()">Кастомная Загрузка</div>
<div class="info">INFO</div>
<div class="popup">
    Разделяйте несколько URL запятой/пробелом.
    Для <span class="file_name">пользовательского имени</span> файла/расширения укажите его через <span class="braces">[ ]</span> после URL без пробелов.
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

empowerment_widget = factory.create_checkbox('Расширение возможностей', False, class_names=['empowerment'])
empowerment_output_widget = factory.create_textarea(
'', '', """Используйте специальные теги. Портативный аналог "Файл (txt)"
Теги: model (ckpt), vae, lora, embed (emb), extension (ext), adetailer (ad), control (cnet), upscale (ups), clip, unet, vision (vis), encoder (enc), diffusion (diff), config (cfg)
Короткие-теги: начинаются с '$' без пробела -> $ckpt
------ Например ------

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
custom_file_urls_widget = factory.create_text('Файл (txt):')

# --- Save Button ---
"""Create button widgets"""
save_button = factory.create_button('Сохранить', class_names=['button', 'button_save'])


# ===================== Side Container =====================

# --- GDrive Toggle Button ---
"""Create Google Drive toggle button for Colab only"""
BTN_STYLE = {'width': '48px', 'height': '48px'}
TOOLTIPS = ('Отключить Гугл Диск', 'Подключить Гугл Диск')

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

# --- Export/Import Widget Settings Buttons ---
"""Create buttons to export/import widget settings to JSON"""
export_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'export-btn'])
export_button.tooltip = 'Экспорт настроек в JSON'

import_button = factory.create_file_upload(accept='.json', layout=BTN_STYLE, class_names=['sideContainer-btn', 'import-btn'])
import_button.tooltip = 'Импорт настроек из JSON'

export_output = widgets.Output(layout={'display': 'none'})
# export_output.add_class('export-output-widget')

# --- PopUp Notification (Alias) ---
_out_notify = widgets.Output()
display(_out_notify)

def show_notification(message, message_type='info', duration=2500):
    """Call the already defined JS function showNotification"""
    message_escaped = message.replace("`", "\\`").replace("\n", "\\n")
    js_code = f"showNotification(`{message_escaped}`, '{message_type}', {duration});"
    with _out_notify:
        display(Javascript(js_code))

# EXPORT
def export_settings(filter_empty=False):
    try:
        widgets_data = {}
        for key in SETTINGS_KEYS:
            value = globals()[f"{key}_widget"].value
            # if not filter_empty or (value not in [None, '', False]):
            #     widgets_data[key] = value
            widgets_data[key] = value

        settings_data = {
            'widgets': widgets_data,
            'mountGDrive': GDrive_button.toggle
        }

        json_str = json.dumps(settings_data, indent=2, ensure_ascii=False)
        b64 = base64.b64encode(json_str.encode()).decode()

        webui = change_webui_widget.value
        date = datetime.now().strftime("%Y%m%d")
        filename = f'widget_settings-{webui}-{date}.json'

        with export_output:
            export_output.clear_output()
            display(HTML(f'''
                <a download="{filename}"
                   href="data:application/json;base64,{b64}"
                   id="download-link"
                   style="display:none;"></a>
                <script>
                    document.getElementById('download-link').click();
                </script>
            '''))
        show_notification('Настройки успешно экспортированы!', 'success')
    except Exception as e:
        show_notification(f"Ошибка экспорта: {str(e)}", 'error')

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
            show_notification('Настройки успешно импортированы!', 'success')
        else:
            show_notification(f"Импортировано {success_count}/{total_count} настроек", 'warning')
    except Exception as e:
        show_notification(f"Ошибка импорта: {str(e)}", 'error')

# OBSERVE (CALLBACK)
def handle_file_upload(change):
    if not change.get('new'):
        return
    try:
        uploaded_data = change['new']

        # Get content, support dict (Colab) and tuple/list (Kaggle)
        file_data = list(uploaded_data.values())[0] if isinstance(uploaded_data, dict) else uploaded_data[0]
        content = file_data['content']

        # Decode if necessary
        json_str = bytes(content).decode('utf-8') if isinstance(content, (bytes, memoryview)) else content

        data = json.loads(json_str)
        apply_imported_settings(data)
    except Exception as e:
        show_notification(f"Ошибка импорта: {e}", 'error')
    finally:
        # Reset for re-uploading
        import_button._counter = 0
        import_button.value.clear()

import_button.observe(handle_file_upload, names='value')
export_button.on_click(export_settings)


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
    [GDrive_button, export_button, import_button, export_output],
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
check_custom_nodes_deps_widget.layout.display = 'none'
empowerment_output_widget.add_class('empowerment-output')
empowerment_output_widget.add_class('hidden')

# Callback functions for XL options
def update_XL_options(change, widget):
    is_xl = change['new']
    data_file = '_xl-models-data.py' if is_xl else '_models-data.py'
    data_path = f"{SCRIPTS}/{data_file}"

    # Load options
    def load_opts(kind):
        return read_model_data(data_path, kind)

    model_widget.options = load_opts('model')
    vae_widget.options = load_opts('vae')
    controlnet_widget.options = load_opts('cnet')

    # Defaults set
    defaults = {
        True:  ('Nova-IL', 'sdxl.vae', 'none'),
        False: ('BluMix',  'Blessed2.vae', 'none')
    }
    p_model, p_vae, p_cnet = defaults[is_xl]

    # Load full dictionaries
    scope = {}
    with open(data_path) as f:
        exec(f.read(), {}, scope)

    def indexed(d):
        return {f"{i}. {k}": v for i, (k, v) in enumerate(d.items(), 1)}

    model_dict = indexed(scope['model_list'])
    vae_dict   = indexed(scope['vae_list'])
    cnet_dict  = indexed(scope['controlnet_list'])

    # Apply values with fallback
    def pick(partial, dictionary, fallback):
        return find_model_by_partial_name(partial, dictionary) or fallback

    model_widget.value = pick(p_model, model_dict, model_widget.options[1])
    vae_widget.value   = pick(p_vae, vae_dict, vae_widget.options[1])
    controlnet_widget.value = pick(p_cnet, cnet_dict, p_cnet)

    # Inpainting toggle
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
        new_branches = fetch_github_branches(repo_url, webui)
        branch_widget.options = new_branches

    is_comfy = webui == 'ComfyUI'

    latest_extensions_widget.layout.display = 'none' if is_comfy else ''
    latest_extensions_widget.value = not is_comfy
    check_custom_nodes_deps_widget.layout.display = '' if is_comfy else 'none'
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
      'latest_webui', 'latest_extensions', 'check_custom_nodes_deps', 'change_webui', 'detailed_download',
      'controlnet', 'controlnet_num', 'commit_hash', 'branch',
      'civitai_token', 'huggingface_token', 'zrok_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
      # CustomDL
      'empowerment', 'empowerment_output',
      'Model_url', 'Vae_url', 'LoRA_url', 'Embedding_url', 'Extensions_url', 'ADetailer_url',
      'custom_file_urls'
]

def save_settings():
    """Save widget values to settings"""
    widgets_values = {key: globals()[f"{key}_widget"].value for key in SETTINGS_KEYS}
    js.save(SETTINGS_PATH, 'WIDGETS', widgets_values)
    js.save(SETTINGS_PATH, 'mountGDrive', True if GDrive_button.toggle else False)  # Save Status GDrive-btn

    update_current_webui(change_webui_widget.value)  # Update Selected WebUI in settings.json

def load_settings():
    """Load widget values from settings"""
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
    """Handle save button click"""
    save_settings()
    all_widgets = [
        model_box, vae_box, additional_box, custom_download_box, save_button,   # mainContainer
        GDrive_button, export_button, import_button, export_output              # sideContainer
    ]
    factory.close(all_widgets, class_names=['hide'], delay=0.8)

load_settings()
save_button.on_click(save_data)