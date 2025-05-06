# File Descriptions in the Repository

## Directory -> `__configs__`
> UI customization files, styles, and configuration scripts.
- **[install-deps.py](../__configs__/ComfyUI/install-deps.py)**: Automatic dependency installer for ComfyUI user nodes.
- **[gradio-tunneling.py](../__configs__/ComfyUI/gradio-tunneling.py)**: Modified tunnel creation script (replaces default ComfyUI version).

## Directory -> `CSS`
> Stylesheets for UI-Widgets components.
- **[download-result.css](../CSS/download-result.css)**: Download results widget styles.
- **[auto-cleaner.css](../CSS/auto-cleaner.css)**: Auto-cleaner widget styles.
- **[main-widgets.css](../CSS/main-widgets.css)**: Core widget styles.

## Directory -> `JS`
> JavaScript functionality (Widgets).
- **[main-widgets.js](../JS/main-widgets.js)**: Core widget interaction logic.

## Directory -> `modules`
> Modules for backend functionality.
- **[CivitaiAPI.py](../modules/CivitaiAPI.py)**: Civitai API interaction handler.
- **[webui_utils.py](../modules/webui_utils.py)**: WebUI utilities (timers, path management).
- **[json_utils.py](../modules/json_utils.py)**: JSON data processing tools.
- **[TunnelHub.py](../modules/TunnelHub.py)**: Tunnel management system.
- **[widget_factory.py](../modules/widget_factory.py)**: IPyWidgets factory generator.
- **[Manager.py](../modules/Manager.py)**: Downloader/Cloner (git) (`m_download`, `m_clone`).
- **[__season.py](../modules/__season.py)**: Aesthetic startup message display (used by setup.py).

## Directory -> `scripts`
> Core application scripts.
- **[_models-data.py](../scripts/_models-data.py)**: SD-1.5 model metadata (URLs/names).
- **[_xl-models-data.py](../scripts/_xl-models-data.py)**: XL model metadata (URLs/names).
- **[launch.py](../scripts/launch.py)**: WebUI main launcher.
- **[auto-cleaner.py](../scripts/auto-cleaner.py)**: Automated file cleanup system.
- **[download-result.py](../scripts/download-result.py)**: Download results widget.
- **[setup.py](../scripts/setup.py)**: Initial setup and file provisioning.

### Subdirectory -> `scripts/en/ru`
> Localization scripts.
- **[downloading-{lang}.py](../scripts/en/downloading-en.py)**: Localized data downloader (`en`/`ru`).
- **[widgets-{lang}.py](../scripts/en/widgets-en.py)**: Localized widget generator (`en`/`ru`).

### Subdirectory -> `scripts/UIs`
> WebUI management.
- **[WebUI Manager](../scripts/UIs/)**: Handles WebUI repo installation, config deployment, and extension/node setup.