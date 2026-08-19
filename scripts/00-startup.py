""" Auto Recovery IPython | by ANXETY """

import importlib
import sys
import os

from pathlib import Path


# ~~ RUNTIME PATHS ~~

HOME_PATH     = Path.home()
PROJECT_PATH  = HOME_PATH / 'SDAIGEN'
SETTINGS_PATH = PROJECT_PATH / 'settings.json'
VENV_PATH     = HOME_PATH / 'venv'

SCRIPTS_PATH = PROJECT_PATH / 'scripts'


if SETTINGS_PATH.exists():
    os.environ.update({
        'home_path':     str(HOME_PATH),
        'project_path':  str(PROJECT_PATH),
        'settings_path': str(SETTINGS_PATH),
        'venv_path':     str(VENV_PATH),
    })

    if str(PROJECT_PATH) not in sys.path:
        sys.path.insert(0, str(PROJECT_PATH))

    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', '')
        try:
            if path and PROJECT_PATH in Path(path).resolve().parents:
                del sys.modules[name]
        except (ValueError, RuntimeError):
            pass

    importlib.invalidate_caches()
