""" WebUI Utilities Module | by ANXETY """

import shutil
import re

from pathlib import Path

from sdai.constants import HOME_PATH, SETTINGS_PATH
from sdai.utils.json import read, save, update
from sdai.webui_meta import meta, build_paths


# ~~ WEBUI HANDLERS ~~

def update_current_webui(current_ui: str):
    """Update the current WebUI value and save settings"""
    current_stored = read(SETTINGS_PATH, 'WEBUI.current')
    latest_ui = read(SETTINGS_PATH, 'WEBUI.latest', None)

    if latest_ui is None or current_stored != current_ui:
        save(SETTINGS_PATH, 'WEBUI.latest', current_stored)
        save(SETTINGS_PATH, 'WEBUI.current', current_ui)

    _m = meta(current_ui)
    save(SETTINGS_PATH, 'WEBUI.python_version', _m['python'])
    save(SETTINGS_PATH, 'WEBUI.webui_path', str(HOME_PATH / current_ui))
    update(SETTINGS_PATH, 'WEBUI', {k: str(v) for k, v in build_paths(current_ui).items()})
    _update_webui_symlink(current_ui)


def _update_webui_symlink(ui: str):
    """Create/Update webui_root symlink in home_work_path"""
    try:
        home_work = Path(read(SETTINGS_PATH, 'ENVIRONMENT.home_work_path') or '')
        if not home_work.exists():
            return

        webui_root   = HOME_PATH / ui
        symlink_path = home_work / 'webui_root'

        _remove_path(symlink_path)
        symlink_path.symlink_to(webui_root, target_is_directory=True)
    except Exception:
        pass


def _remove_path(path: Path):
    """Remove file, directory or symlink"""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def handle_setup_timer(webui_path: str, timer_webui: float) -> float:
    """Manage timer persistence for WebUI instances"""
    timer_file = Path(webui_path) / 'static' / 'timer.txt'
    timer_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with timer_file.open('r', encoding='utf-8') as f:
            timer_webui = float(f.read())
    except FileNotFoundError:
        pass

    with timer_file.open('w', encoding='utf-8') as f:
        f.write(str(timer_webui))

    return timer_webui


# ~~ WIDGETS HANDLERS ~~

def find_model_by_partial_name(partial_name, model_dict):
    """
    Find model in dictionary by partial name (case-insensitive)
    Returns the full key name if found, None otherwise.
    """
    if not partial_name or partial_name.lower() in {'none', 'all'}:
        return partial_name

    def normalize(name: str) -> str:
        return re.sub(r'^\d+\.\s*', '', name).lower()

    target = normalize(partial_name)
    return next((key for key in model_dict if target in normalize(key)), None)
