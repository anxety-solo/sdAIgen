""" JSON Utilities Module | by ANXETY """

import logging
import json

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any


# ~~ LOGGER CONFIGURATION ~~

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class ColoredFormatter(logging.Formatter):
    colors = {
        logging.WARNING: '\033[33m',
        logging.ERROR:   '\033[31m',
        'RESET':         '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.colors.get(record.levelno, '')
        return f"{color}{super().format(record)}{self.colors['RESET']}"


handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.addHandler(handler)
logger.propagate = False


# ~~ ARGUMENT VALIDATION DECORATOR ~~

def validate_args(min_args: int, max_args: int) -> Callable[..., Any]:
    """Validate argument count for variadic functions"""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            arg_count = len(args) + len(kwargs)
            if not (min_args <= arg_count <= max_args):
                expected = f"exactly {min_args}" if min_args == max_args else f"{min_args}-{max_args}"
                logger.error(
                    f"Invalid argument count for {func.__name__}.\n"
                    f"Expected {expected}, got {arg_count}"
                )
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ~~ CORE FUNCTIONALITY ~~

def parse_key(key: str) -> list[str]:
    """Parse dot-separated key with `..` escape support"""
    if not isinstance(key, str):
        logger.error('Key must be a string')
        return []

    temp_char = '\uE000'
    return [p.replace(temp_char, '.') for p in key.replace('..', temp_char).split('.')]


def _get_nested_value(data: dict[str, Any], keys: list[str]) -> Any:
    """Get value by path through nested dictionaries"""
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _set_nested_value(data: dict[str, Any], keys: list[str], value: Any):
    """Set value at path, creating missing intermediate dicts"""
    current = data
    for key in keys[:-1]:
        if not isinstance(current.get(key), dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def _update_nested(data: dict[str, Any], keys: list[str], value: Any):
    """Update existing path, merging dicts and preserving siblings"""
    current = data
    for part in keys[:-1]:
        current = current.setdefault(part, {})

    last_key = keys[-1]
    if last_key in current:
        if isinstance(current[last_key], dict) and isinstance(value, dict):
            current[last_key].update(value)
        else:
            current[last_key] = value
    else:
        logger.warning(f"Key '{'.'.join(keys)}' not found. Update failed.")


def _delete_nested(data: dict[str, Any], keys: list[str], _: Any = None):
    """Delete key at path if it exists"""
    current = data
    for part in keys[:-1]:
        current = current.get(part)
        if not isinstance(current, dict):
            return
    if keys[-1] in current:
        del current[keys[-1]]


def _load(filepath: str | Path, key: str) -> tuple[dict[str, Any], list[str]]:
    """Load file data and parsed key segments"""
    return _read_json(filepath), parse_key(key)


def _read_json(filepath: str | Path) -> dict[str, Any]:
    """Read JSON file, returning {} on error or missing file"""
    try:
        filepath = Path(filepath)
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    return json.loads(content)
    except Exception as exc:
        logger.error(f"Read error ({filepath}): {str(exc)}")

    return {}


def _write_json(filepath: str | Path, data: dict[str, Any]):
    """Write JSON file, creating parent directories"""
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as exc:
        logger.error(f"Write error ({filepath}): {str(exc)}")


def _mutate(filepath: str | Path, key: str, value: Any, action: Callable[..., Any]):
    """Load JSON, apply action at parsed path, then write back"""
    data, keys = _load(filepath, key)
    if not keys:
        return

    action(data, keys, value)
    _write_json(filepath, data)


# ~~ MAIN FUNCTIONS ~~

@validate_args(1, 3)
def read(filepath: str | Path, key: str = None, default: Any = None) -> Any:
    """Read value from JSON file by optional dot-separated key path"""
    data = _read_json(filepath)
    if key is None:
        return data

    keys = parse_key(key)
    if not keys:
        return default

    result = _get_nested_value(data, keys)
    return result if result is not None else default


@validate_args(3, 3)
def save(filepath: str | Path, key: str, value: Any):
    """Save value, creating full path in JSON file"""
    _mutate(filepath, key, value, _set_nested_value)


@validate_args(3, 3)
def update(filepath: str | Path, key: str, value: Any):
    """Update existing path, preserving surrounding data"""
    _mutate(filepath, key, value, _update_nested)


@validate_args(2, 2)
def delete_key(filepath: str | Path, key: str):
    """Delete key from JSON file"""
    _mutate(filepath, key, None, _delete_nested)


@validate_args(2, 3)
def key_exists(filepath: str | Path, key: str, value: Any = None) -> bool:
    """Check key existence, optionally verifying value match"""
    result = read(filepath, key)
    return result == value if value is not None else result is not None


# ~~ SETTINGS LOADING ~~

def load_settings(path: str | Path) -> dict:
    """Load settings from a JSON file"""
    return {
        **(read(path, 'ENVIRONMENT') or {}),
        **(read(path, 'WIDGETS') or {}),
        **(read(path, 'WEBUI') or {})
    }
