""" JSON Utilities Module | by ANXETY """

from typing import Any, Dict, List, Union
from functools import wraps
from pathlib import Path
import logging
import json
import os


# ================== Logger Configuration ==================

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class CustomFormatter(logging.Formatter):
    """Custom log formatter with color support for warnings/errors"""
    colors = {
        logging.WARNING: '\033[33m',
        logging.ERROR: '\033[31m',
        'ENDC': '\033[0m'
    }

    def format(self, record):
        color = self.colors.get(record.levelno, '')
        message = super().format(record)
        return f"{color}{message}{self.colors['ENDC']}"

handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)
logger.propagate = False


# ============= Argument Validation Decorator ==============

def validate_args(min_args: int, max_args: int):
    """Decorator to validate number of arguments in variadic functions

    Args:
        min_args: Minimum required arguments (inclusive)
        max_args: Maximum allowed arguments (inclusive)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args):
            arg_count = len(args)
            if not (min_args <= arg_count <= max_args):
                if min_args == max_args:
                    logger.error(
                        f"Invalid argument count for {func.__name__}. "
                        f"Expected exactly {min_args}, got {arg_count}"
                    )
                else:
                    logger.error(
                        f"Invalid argument count for {func.__name__}. "
                        f"Expected {min_args}-{max_args}, got {arg_count}"
                    )
                return None
            return func(*args)
        return wrapper
    return decorator


# =================== Core Functionality ===================

def parse_key(key: str) -> List[str]:
    """
    Parse dot-separated key with escape support for double dots

    Args:
        key: Input key string (e.g., 'parent..child.prop')

    Returns:
        List of parsed key segments (e.g., ['parent.child', 'prop'])
    """
    if not isinstance(key, str):
        logger.error('Key must be a string')
        return []

    temp_char = '\uE000'
    parts = key.replace('..', temp_char).split('.')
    return [p.replace(temp_char, '.') for p in parts]

def _get_nested_value(data: Dict[str, Any], keys: List[str]) -> Any:
    """
    Get value using explicit path through nested dictionaries

    Args:
        data: Root dictionary
        keys: List of keys forming exact path

    Returns:
        Value at specified path or None if path breaks
    """
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current

def _set_nested_value(data: Dict[str, Any], keys: List[str], value: Any):
    """
    Update existing nested structure without overwriting sibling keys

    Args:
        data: Root dictionary to modify
        keys: Path to target location
        value: New value to set at target
    """
    current = data
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value

def _read_json(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely read JSON file, returning empty dict on error/missing file

    Args:
        filepath: Path to JSON file (str or Path object)
    """
    try:
        if not os.path.exists(filepath):
            return {}

        with open(filepath, 'r') as f:
            content = f.read()
            return json.loads(content) if content.strip() else {}
    except Exception as e:
        logger.error(f"Read error ({filepath}): {str(e)}")
        return {}

def _write_json(filepath: Union[str, Path], data: Dict[str, Any]):
    """
    Write JSON file with directory creation and error handling

    Args:
        filepath: Destination path (str or Path object)
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Write error ({filepath}): {str(e)}")


# ===================== Main Functions =====================

@validate_args(1, 3)
def read(*args) -> Any:
    """
    Read value from JSON file using explicit path

    Args:
        filepath (str): Path to JSON file
        key (str, optional): Dot-separated key path
        default (any, optional): Default if key not found

    Returns:
        Value at key path, entire data, or default
    """
    filepath, key, default = args[0], None, None
    if len(args) > 1: key = args[1]
    if len(args) > 2: default = args[2]

    data = _read_json(filepath)
    if key is None:
        return data

    keys = parse_key(key)
    if not keys:
        return default

    result = _get_nested_value(data, keys)
    return result if result is not None else default

@validate_args(3, 3)
def save(*args):
    """
    Save value creating full path

    Args:
        filepath (str): JSON file path
        key (str): Dot-separated target path
        value (any): Value to store
    """
    filepath, key, value = args[0], args[1], args[2]

    data = _read_json(filepath)
    keys = parse_key(key)
    if not keys:
        return

    _set_nested_value(data, keys, value)
    _write_json(filepath, data)

@validate_args(3, 3)
def update(*args):
    """
    Update existing path preserving surrounding data

    Args:
        filepath (str): JSON file path
        key (str): Dot-separated target path
        value (any): New value to set
    """
    filepath, key, value = args[0], args[1], args[2]

    data = _read_json(filepath)
    keys = parse_key(key)
    if not keys:
        return

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

    _write_json(filepath, data)

@validate_args(2, 2)
def delete_key(*args):
    """
    Remove specified key from JSON data

    Args:
        filepath (str): JSON file path
        key (str): Dot-separated path to delete
    """
    filepath, key = args[0], args[1]

    data = _read_json(filepath)
    keys = parse_key(key)
    if not keys:
        return

    current = data
    for part in keys[:-1]:
        current = current.get(part)
        if not isinstance(current, dict):
            return

    last_key = keys[-1]
    if last_key in current:
        del current[last_key]
        _write_json(filepath, data)

@validate_args(2, 3)
def key_exists(*args) -> bool:
    """
    Check if key path exists with optional value check

    Args:
        filepath (str): JSON file path
        key (str): Dot-separated path to check
        value (any, optional): Verify exact value match

    Returns:
        True if path exists (and value matches if provided)
    """
    filepath, key = args[0], args[1]
    value = args[2] if len(args) > 2 else None

    data = _read_json(filepath)
    keys = parse_key(key)
    if not keys:
        return False

    result = _get_nested_value(data, keys)

    if value is not None:
        return result == value
    return result is not None