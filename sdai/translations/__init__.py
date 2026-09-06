""" i18n: Language Loader & tr() Resolver | by ANXETY """

import json

from pathlib import Path
from typing import Any

# === SDAIGEN ===
from sdai.constants import SETTINGS_PATH
from sdai.utils.json import read


LANG = read(SETTINGS_PATH, 'ENVIRONMENT.lang', 'en')

_DIR      = Path(__file__).parent
_lang_src = _DIR / f"{LANG}.json"
if not _lang_src.exists():
    print(f"⚠️ Language '{LANG}' not found, falling back to 'en'")
    _lang_src = _DIR / 'en.json'

_data     = json.loads(_lang_src.read_text(encoding='utf-8'))
_fallback = json.loads((_DIR / 'en.json').read_text(encoding='utf-8'))


def tr(key: str, **kwargs: Any) -> str:
    text = _data.get(key, _fallback.get(key, key))
    return text.format(**kwargs) if kwargs else text
