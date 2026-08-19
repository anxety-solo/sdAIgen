""" Translations Module (i18n) | by ANXETY """

import json

from pathlib import Path

# === SDAIGEN ===
from sdai.constants import SETTINGS_PATH
from sdai.utils.json import read


LANG = read(SETTINGS_PATH, 'ENVIRONMENT.lang')

_DIR      = Path(__file__).parent
_data     = json.loads((_DIR / f"{LANG}.json").read_text(encoding='utf-8'))
_fallback = json.loads((_DIR / 'en.json').read_text(encoding='utf-8'))


def tr(key: str, **kwargs) -> str:
    text = _data.get(key, _fallback.get(key, key))
    return text.format(**kwargs) if kwargs else text
