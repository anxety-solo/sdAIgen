# File Descriptions in the Repository

## Directory -> `_configs_`
- Customization files, styles and other files for the UI

## Directory -> `CSS`

- **download-result.css**: Styles for the download results widget.
- **auto-cleaner.css**: Styles for the auto-cleaner widget.
- **main-widgets.css**: Main styles for widgets.

## Directory -> `JS`

- **main-widgets.js**: Main JavaScript file for widget functionality.

## Directory -> `modules`

- **CivitaiAPI.py**: Module for interacting with the Civitai API.
- **webui_utils.py**: Utilities for working with the WebUI - setting the timer and folder paths.
- **json_utils.py**: Utilities for handling JSON data.
- **TunnelHub.py**: Module for managing tunnels.
- **widget_factory.py**: Factory for creating ipywidgets.
- **Manager.py**: Adding quick functions for downloading and cloning git repositories: `m_download` & `m_clone`.

## Directory -> `scripts`

- **_models-data.py**: Model data - url, name
- **_xl-models-data.py**: Model data [XL] - url, name
- **launch.py**: Main script to launch the WebUI.
- **auto-cleaner.py**: Script for automatically cleaning up unnecessary files.
- **download-result.py**: Script for processing download results.

#### Subdirectory -> `en/ru`

- **setup-{lang}.py**: Downloading files for work.
- **downloading-{lang}.py**: The main script for downloading data.
- **widgets-{lang}.py**: Script for creating and displaying main widgets.
  
#### Subdirectory -> `UIs`

- Downloading the UI repo and its customizations.