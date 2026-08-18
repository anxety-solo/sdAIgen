""" Main Project Widgets | by ANXETY """

import ipywidgets as widgets
import requests
import base64
import json

from IPython.display import display, HTML, Javascript
from datetime import datetime

# === SDAIGEN ===
from sdai.constants import SETTINGS_PATH, CSS_DIR_PATH, JS_DIR_PATH, GITHUB_API, GITHUB_BASE, HUGGINGFACE_BASE
from sdai.utils.webui import update_current_webui, find_model_by_partial_name
from sdai.models import XL, MODEL_CATEGORIES, get_category
from sdai.webui_meta import DEFAULT_UI, WEBUIS, meta
from sdai.utils.json import read, save, key_exists
from sdai.factory import WidgetFactory
from sdai.translations import tr


ENV_NAME = read(SETTINGS_PATH, 'ENVIRONMENT.env_name')

CONTAINERS_WIDTH = '1080px'


# ~~ HELPERS ~~

def numbered(data):
    """Prefix each model key with its number"""
    return {f"{i}. {k}": v for i, (k, v) in enumerate(data.items(), 1)}


def options_from(data, prefixes):
    """Build dropdown options from a models dict"""
    return prefixes + list(numbered(data))


def get_widget(key):
    """Get a widget by its settings key"""
    return globals()[f"{key}_widget"]


def create_expandable_button(text, url):
    """Create an anchor button widget"""
    return factory.create_html(f'<a href="{url}" target="_blank" class="button button_api"><span class="icon"><</span><span class="text">{text}</span></a>')


def fetch_github_branches(ui):
    """Fetch branch names from GitHub API with optional filtering"""
    _m = meta(ui)
    repo_path = _m['github_url'].replace(f"{GITHUB_BASE}/", '')
    api_url   = f"{GITHUB_API}/repos/{repo_path}/branches"

    try:
        resp = requests.get(api_url, timeout=15)
        if resp.status_code != 200:
            return ['none']

        branches = [b['name'] for b in resp.json()]
        excluded = _m.get('branch_exclude') or []

        ordered = ['none']
        for preferred in (_m['branch'], 'main', 'master'):
            if preferred in branches:
                ordered.append(preferred)
                branches.remove(preferred)

        ordered += [b for b in branches if not any(e in b.lower() for e in excluded)]
        return ordered

    except requests.RequestException:
        return ['none']


# ~~ WIDGETS (Main Container) ~~

factory = WidgetFactory()
HR = widgets.HTML('<hr>')

# --- MODEL ---
model_header      = factory.create_header(tr('model_header'))
model_widget      = factory.create_dropdown(options_from(XL['model'], ['none']), tr('model_label'), 'Nova-IL')
model_num_widget  = factory.create_text(tr('model_num_label'), '', tr('model_num_hint'))
model_type_widget = factory.create_dropdown(list(MODEL_CATEGORIES), tr('model_type'), 'XL', layout={'width': 'min-content'})

# --- VAE ---
vae_header     = factory.create_header(tr('vae_header'))
vae_widget     = factory.create_dropdown(options_from(XL['vae'], ['none', 'ALL']), 'Vae:', 'sdxl.vae')
vae_num_widget = factory.create_text(tr('vae_num_label'), '', tr('vae_num_hint'))

# --- ADDITIONAL ---
additional_header        = factory.create_header(tr('additional_header'))
update_scope_widget      = factory.create_dropdown(['none', 'UI', 'Extensions', 'ALL'], tr('update_scope_label'), 'ALL', layout={'width': 'auto'})
clone_ui_widget          = factory.create_checkbox(tr('clone_ui_label'), False)
check_nodes_deps_widget  = factory.create_checkbox(tr('check_nodes_deps_label'), True, layout={'display': 'none'})
selected_webui_widget    = factory.create_dropdown(list(WEBUIS), 'WebUI:', DEFAULT_UI, layout={'width': 'auto'})
detailed_download_widget = factory.create_dropdown(['off', 'on'], tr('detailed_download_label'), 'off', layout={'width': 'auto'})
choose_changes_box = factory.create_hbox(
    [
        update_scope_widget,
        clone_ui_widget,
        check_nodes_deps_widget,    # For ComfyUI
        selected_webui_widget,
        detailed_download_widget
    ],
    layout={'justify_content': 'space-between'}
)

controlnet_widget     = factory.create_dropdown(options_from(XL['controlnet'], ['none', 'ALL']), 'ControlNet:', 'none')
controlnet_num_widget = factory.create_text(tr('controlnet_num_label'), '', tr('controlnet_num_hint'))

commit_hash_widget   = factory.create_text(tr('commit_hash_label'), '', tr('commit_hash_hint'))
branch_widget        = factory.create_dropdown(fetch_github_branches(DEFAULT_UI), tr('branch_label'), 'none', layout={'width': '400px', 'margin': '0 0 0 8px'}) # margin-left
checkout_options_box = factory.create_hbox([commit_hash_widget, branch_widget])

civitai_token_widget = factory.create_text(tr('civitai_token_label'), '', tr('civitai_token_hint'), class_names=['cai-token-input'])    # for check API-Key
civitai_button       = create_expandable_button(tr('get_token_btn', service='CivitAI'), 'https://civitai.com/user/account')
civitai_box          = factory.create_hbox([civitai_token_widget, civitai_button])

huggingface_token_widget = factory.create_text(tr('huggingface_token_label'), '', tr('huggingface_token_hint'))
huggingface_button       = create_expandable_button(tr('get_token_btn', service='HuggingFace'), f"{HUGGINGFACE_BASE}/settings/tokens")
huggingface_box          = factory.create_hbox([huggingface_token_widget, huggingface_button])

ngrok_token_widget = factory.create_text(tr('ngrok_token_label'))
ngrok_button       = create_expandable_button(tr('get_token_btn', service='Ngrok'), 'https://dashboard.ngrok.com/get-started/your-authtoken')
ngrok_box          = factory.create_hbox([ngrok_token_widget, ngrok_button])

zrok2_token_widget = factory.create_text(tr('zrok2_token_label'))
zrok2_button       = create_expandable_button(tr('register_token_btn', service='Zrok2'), 'https://colab.research.google.com/drive/1d2sjWDJi_GYBUavrHSuQyHTDuLy36WpU')
zrok2_box          = factory.create_hbox([zrok2_token_widget, zrok2_button])

commandline_arguments_widget = factory.create_text(tr('arguments_label'), meta(DEFAULT_UI)['launch_args'])

accent_colors_options = ['anxety', 'blue', 'green', 'peach', 'pink', 'red', 'yellow']
theme_accent_widget   = factory.create_dropdown(accent_colors_options, tr('theme_accent_label'), 'anxety', layout={'width': 'auto', 'margin': '0 0 0 8px'}) # margin-left
additional_footer_box = factory.create_hbox([commandline_arguments_widget, theme_accent_widget])

# --- CUSTOM DOWNLOAD ---
custom_download_header_popup = factory.create_html(f'''
<div class='header' style='cursor: pointer;' onclick='toggleContainer()'>{tr('cdl_header')}</div>
<div class='info'>{tr('cdl_info')}</div>
<div class='popup'>
    {tr('cdl_separate')}
    {tr('cdl_custom_name')}
    <span class='required'>{tr('cdl_required')}</span> - <span class='extension'>{tr('cdl_extension')}</span>
    <div class='sample'>
        <span class='sample_label'>{tr('cdl_file_example')}</span>
        https://civitai.com/api/download/models/229782<span class='braces'>[</span><span class='file_name'>Detailer</span><span class='extension'>.safetensors</span><span class='braces'>]</span>
        <br>
        <span class='sample_label'>{tr('cdl_ext_example')}</span>
        https://github.com/hako-mikan/sd-webui-regional-prompter<span class='braces'>[</span><span class='file_name'>Regional-Prompter</span><span class='braces'>]</span>
    </div>
</div>
''')

empowerment_widget       = factory.create_checkbox(tr('empowerment_label'), False, class_names=['empowerment'])
empowerment_input_widget = factory.create_textarea('', '', tr('empowerment_hint'), class_names=['empowerment-input', 'hidden'])

model_urls_widget       = factory.create_text('Model:')
vae_urls_widget         = factory.create_text('Vae:')
lora_urls_widget        = factory.create_text('LoRa:')
embedding_urls_widget   = factory.create_text('Embedding:')
extensions_urls_widget  = factory.create_text('Extensions:')
adetailer_urls_widget   = factory.create_text('ADetailer:')
custom_file_urls_widget = factory.create_text(tr('file_urls_label'))

# --- Save Button ---
save_button = factory.create_button(tr('save'), class_names=['button', 'button_save'])


# ~~ Side Container ~~

# --- GDrive Symlinks Panel ---
gdrive_header         = factory.create_header(tr('gd_symlinks_header'))
gdrive_files_widget   = factory.create_checkbox(tr('gd_files_label'), True)
gdrive_outputs_widget = factory.create_checkbox(tr('gd_outputs_label'), False)
gdrive_configs_widget = factory.create_checkbox(tr('gd_configs_label'), False)

gdrive_settings_box = factory.create_vbox(
    [gdrive_header, HR, gdrive_files_widget, gdrive_outputs_widget, gdrive_configs_widget],
    class_names=['container', 'container_gdrive'],
    layout={'display': 'none'},
)

# --- GDrive Toggle Button ---
BTN_STYLE = {'width': '48px', 'height': '48px'}
TOOLTIPS  = (tr('gd_unmount_tooltip'), tr('gd_mount_tooltip'))

gdrive_status         = read(SETTINGS_PATH, 'GDRIVE.mount', False)
gdrive_button         = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'gdrive-btn'])
gdrive_button.tooltip = TOOLTIPS[not gdrive_status] # Invert index
gdrive_button.toggle  = gdrive_status


def _set_gdrive_state(state):
    """Apply GDrive mount state to the toggle button and panel classes"""
    gdrive_button.toggle = state
    if state:
        gdrive_button.add_class('active')
        gdrive_settings_box.add_class('gdrive-visible')
    else:
        gdrive_button.remove_class('active')
        gdrive_settings_box.remove_class('gdrive-visible')


if ENV_NAME != 'Google Colab':
    gdrive_button.layout.display = 'none'   # Hide button if not Colab
else:
    _set_gdrive_state(gdrive_status)

    def handle_toggle(btn):
        _set_gdrive_state(not btn.toggle)
        btn.tooltip = TOOLTIPS[not btn.toggle]

    gdrive_button.on_click(handle_toggle)


# --- Export/Import Widget Settings Buttons ---
export_button = factory.create_button('', layout=BTN_STYLE, class_names=['sideContainer-btn', 'export-btn'])
export_button.tooltip = tr('export_tooltip')

import_button = factory.create_file_upload(accept='.json', layout=BTN_STYLE, class_names=['sideContainer-btn', 'import-btn'])
import_button.tooltip = tr('import_tooltip')

export_output = widgets.Output(layout={'display': 'none'})

# --- PopUp Notification (Alias) ---
# PopUp Notification — hidden output widget, JS renders notifications
notify_output = widgets.Output(layout={'height': '0', 'overflow': 'hidden', 'margin': '0', 'padding': '0'})
display(notify_output)


def show_notification(message, message_type='info', duration=2500):
    """Call JS function showNotification"""
    message_escaped = message.replace('`', '\\`').replace('\n', '\\n')
    js_code = f"showNotification(`{message_escaped}`, '{message_type}', {duration});"

    with notify_output:
        display(Javascript(js_code))


# --- EXPORT SETTINGS ---
def _collect_widget_values():
    """Collect current widget values for export/save"""
    return {
        'widgets': {key: get_widget(key).value for key in SETTINGS_KEYS},
        'gdrive':  {'mount': gdrive_button.toggle, **{key: get_widget(key).value for key in GDRIVE_KEYS}},
    }


def export_settings(button=None):
    """Export widget settings to a JSON file"""
    try:
        settings_data = _collect_widget_values()

        json_str = json.dumps(settings_data, indent=2, ensure_ascii=False)
        b64      = base64.b64encode(json_str.encode()).decode()

        webui    = selected_webui_widget.value
        date     = datetime.now().strftime('%Y%m%d')
        filename = f"widgets_settings-{webui}-{date}.json"

        with export_output:
            export_output.clear_output()
            display(HTML(f'''
                <a download='{filename}'
                   href='data:application/json;base64,{b64}'
                   id='aw-download-link'
                   style='display:none;'></a>
                <script>
                    document.getElementById('aw-download-link').click();
                </script>
            '''))
        show_notification(tr('exported'), 'success')
    except Exception as exc:
        show_notification(tr('export_failed', error=str(exc)), 'error')


# --- APPLY SETTINGS ---
def apply_imported_settings(data):
    """Apply imported widget settings"""
    try:
        success_count = total_count = 0

        if 'widgets' in data:
            for key, value in data['widgets'].items():
                total_count += 1
                if key in SETTINGS_KEYS:
                    try:
                        get_widget(key).value = value
                        success_count += 1
                    except Exception:
                        pass

        if 'gdrive' in data:
            gd_data = data['gdrive']

            _set_gdrive_state(gd_data.get('mount', False))

            for key in GDRIVE_KEYS:
                total_count += 1
                try:
                    get_widget(key).value = gd_data.get(key, False)
                    success_count += 1
                except Exception:
                    pass

        if success_count == total_count:
            show_notification(tr('imported'), 'success')
        else:
            show_notification(tr('import_partial', count=success_count, total=total_count), 'warning')
    except Exception as exc:
        show_notification(tr('import_failed', error=str(exc)), 'error')


# --- OBSERVE (CALLBACK) ---
def handle_file_upload(change):
    """Handle JSON file upload and apply settings"""
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
    except Exception as exc:
        show_notification(tr('import_failed', error=str(exc)), 'error')
    finally:
        # Reset for re-uploading
        import_button._counter = 0
        import_button.value.clear()


import_button.observe(handle_file_upload, names='value')
export_button.on_click(export_settings)


# ~~ DISPLAY / SETTINGS ~~

factory.load_css(CSS_DIR_PATH / 'main-widgets.css') # load CSS (widgets)
factory.load_js(JS_DIR_PATH / 'main-widgets.js')    # load JS (widgets)

# Display Sections
model_widgets = [model_header, model_widget, model_num_widget, model_type_widget]
vae_widgets   = [vae_header, vae_widget, vae_num_widget]
additional_widgets = [
    additional_header,
    choose_changes_box,
    HR,
    controlnet_widget, controlnet_num_widget,
    checkout_options_box,
    civitai_box, huggingface_box, zrok2_box, ngrok_box,
    HR,
    additional_footer_box
]
custom_download_widgets = [
    custom_download_header_popup,
    empowerment_widget, empowerment_input_widget,
    model_urls_widget,
    vae_urls_widget,
    lora_urls_widget,
    embedding_urls_widget,
    extensions_urls_widget,
    adetailer_urls_widget,
    custom_file_urls_widget
]

# Create Boxes
model_box           = factory.create_vbox(model_widgets, class_names=['container'])
vae_box             = factory.create_vbox(vae_widgets, class_names=['container'])
additional_box      = factory.create_vbox(additional_widgets, class_names=['container'])
custom_download_box = factory.create_vbox(custom_download_widgets, class_names=['container', 'container_cdl'])

# Create Containers
model_vae_box = factory.create_hbox(
    [model_box, vae_box],
    class_names=['widgetContainer', 'model-vae-wrapper'],
)

widgetContainer = factory.create_vbox(
    [model_vae_box, additional_box, custom_download_box, save_button],
    class_names=['widgetContainer'],
    layout={'min_width': CONTAINERS_WIDTH, 'max_width': CONTAINERS_WIDTH}
)
_buttons_col = factory.create_vbox(
    [gdrive_button, export_button, import_button, export_output],
    class_names=['sideContainer-buttons']
)
_side_inner = factory.create_hbox(
    [_buttons_col, gdrive_settings_box],
    class_names=['sideContainer-inner'],
    layout={'align_items': 'flex-start'}
)
sideContainer = factory.create_vbox(
    [_side_inner],
    class_names=['sideContainer'],
)
mainContainer = factory.create_hbox(
    [widgetContainer, sideContainer],
    class_names=['mainContainer'],
    layout={'align_items': 'flex-start'}
)

factory.display(mainContainer)


# --- Post Run Scripts ---
display(Javascript('setTimeout(checkCivitaiKey, 2500)'))


# ~~ CALLBACK FUNCTION ~~

def update_model_type(change, widget):
    """Switch Model/Vae/ControlNet options"""
    model_type = change['new']
    data       = get_category(model_type)

    model_dict = numbered(data.get('model', {}))
    vae_dict   = numbered(data.get('vae', {}))
    cnet_dict  = numbered(data.get('controlnet', {}))

    model_widget.options      = ['none'] + list(model_dict)
    vae_widget.options        = ['none', 'ALL'] + list(vae_dict)
    controlnet_widget.options = ['none', 'ALL'] + list(cnet_dict)

    # Defaults set
    defaults = {
        'SD':    ('BluMix', 'Blessed2.vae', 'none'),
        'XL':    ('Nova-IL', 'sdxl.vae', 'none'),
        'ANIMA': ('MiaoMiao', 'ALL', 'none'),
    }
    d_model, d_vae, d_cnet = defaults[model_type]

    # Apply values
    def pick(partial, dictionary, fallback):
        return find_model_by_partial_name(partial, dictionary) or fallback

    model_widget.value      = pick(d_model, model_dict, model_widget.options[-1])
    vae_widget.value        = pick(d_vae,   vae_dict,   vae_widget.options[-1])
    controlnet_widget.value = pick(d_cnet,  cnet_dict,  d_cnet)


def update_clone_ui(change, widget):
    """Disable the Update dropdown when clone mode is enabled"""
    if change['new']:
        update_scope_widget.add_class('_disabled')
    else:
        update_scope_widget.remove_class('_disabled')


def update_selected_webui(change, widget):
    """Update widgets when the WebUI selection changes"""
    webui = change['new']
    _m = meta(webui)
    commandline_arguments_widget.value = _m['launch_args']
    branch_widget.options = fetch_github_branches(webui)

    is_comfy = webui == 'ComfyUI'

    update_scope_widget.options            = ['none', 'UI'] if is_comfy else ['none', 'UI', 'Extensions', 'ALL']
    update_scope_widget.value              = 'UI' if is_comfy else 'ALL'
    check_nodes_deps_widget.layout.display = '' if is_comfy else 'none'
    theme_accent_widget.layout.display     = 'none' if is_comfy else ''
    extensions_urls_widget.description     = 'Custom Nodes:' if is_comfy else 'Extensions:'


def update_empowerment(change, widget):
    """Toggle between empowerment textarea and URL fields"""
    selected_emp = change['new']

    custom_DL_widgets = [
        model_urls_widget,
        vae_urls_widget,
        lora_urls_widget,
        embedding_urls_widget,
        extensions_urls_widget,
        adetailer_urls_widget
    ]
    for widget in custom_DL_widgets:    # For switching animation
        widget.add_class('empowerment-text-field')

    if selected_emp:
        for wg in custom_DL_widgets:
            wg.add_class('hidden')
        empowerment_input_widget.remove_class('hidden')
    else:
        for wg in custom_DL_widgets:
            wg.remove_class('hidden')
        empowerment_input_widget.add_class('hidden')


# Connecting widgets
factory.connect_widgets([(model_type_widget,     'value')], update_model_type)
factory.connect_widgets([(clone_ui_widget,       'value')], update_clone_ui)
factory.connect_widgets([(selected_webui_widget, 'value')], update_selected_webui)
factory.connect_widgets([(empowerment_widget,    'value')], update_empowerment)


# ~~ Load / Save - Settings ~~

SETTINGS_KEYS = [
      'model_type', 'model', 'model_num', 'vae', 'vae_num',
      # Additional
      'update_scope', 'clone_ui', 'selected_webui', 'check_nodes_deps', 'detailed_download',
      'controlnet', 'controlnet_num', 'commit_hash', 'branch',
      'civitai_token', 'huggingface_token', 'zrok2_token', 'ngrok_token', 'commandline_arguments', 'theme_accent',
      # CustomDL
      'empowerment', 'empowerment_input',
      'model_urls', 'vae_urls', 'lora_urls', 'embedding_urls', 'extensions_urls', 'adetailer_urls',
      'custom_file_urls'
]

GDRIVE_KEYS = ['gdrive_files', 'gdrive_outputs', 'gdrive_configs']


def save_settings():
    """Save widget values to settings"""
    settings_data = _collect_widget_values()
    save(SETTINGS_PATH, 'WIDGETS', settings_data['widgets'])
    save(SETTINGS_PATH, 'GDRIVE',  settings_data['gdrive'])

    update_current_webui(selected_webui_widget.value)   # Update Selected WebUI in settings.json


def load_settings():
    """Load widget values from settings"""
    if key_exists(SETTINGS_PATH, 'WIDGETS'):
        widgets_data = read(SETTINGS_PATH, 'WIDGETS')
        for key in SETTINGS_KEYS:
            if key in widgets_data:
                get_widget(key).value = widgets_data.get(key, '')

    # Load gdrive settings
    if key_exists(SETTINGS_PATH, 'GDRIVE'):
        gdrive_data = read(SETTINGS_PATH, 'GDRIVE')
        _set_gdrive_state(gdrive_data.get('mount', False))

        for key in GDRIVE_KEYS:
            if key in gdrive_data:
                get_widget(key).value = gdrive_data[key]


def save_data(button):
    """Handle save button click"""
    save_settings()
    all_widgets = [
        model_box, vae_box, additional_box, custom_download_box, save_button,               # mainContainer
        gdrive_button, export_button, import_button, export_output, gdrive_settings_box     # sideContainer
    ]
    factory.close(all_widgets, class_names=['hide'], delay=0.8)


load_settings()
save_button.on_click(save_data)
