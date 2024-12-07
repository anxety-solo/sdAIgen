import json
import os

def _get_nested_value(data, keys):
    """Gets a value by key from a nested data structure."""
    current_level = data
    for part in keys:
        current_level = current_level.get(part)
        if current_level is None:
            return None
    return current_level

def _set_nested_value(data, keys, value):
    """Sets a value by key into a nested data structure."""
    current_level = data
    for part in keys[:-1]:
        current_level = current_level.setdefault(part, {})
    current_level[keys[-1]] = value

def _read_json(filepath):
    """Reads JSON data from a file."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as json_file:
        return json.load(json_file)

def _write_json(filepath, data):
    """Writes JSON data to a file."""
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)

# =======================
## Main Functions

def read_json(filepath, key, default=None):
    """Reads a value by key from a JSON file, supporting nested structures."""
    data = _read_json(filepath)
    keys = key.split('.')
    return _get_nested_value(data, keys) or default

def save_json(filepath, key, value):
    """Saves a value by key in a JSON file, supporting nested structures."""
    data = _read_json(filepath)
    keys = key.split('.')
    _set_nested_value(data, keys, value)
    _write_json(filepath, data)

def update_json(filepath, key, value):
    """Updates a value by key in a JSON file, supporting nested structures."""
    data = _read_json(filepath)
    keys = key.split('.')
    current_level = data
    for part in keys[:-1]:
        current_level = current_level.setdefault(part, {})
    last_key = keys[-1]
    
    if isinstance(current_level.get(last_key), dict) and isinstance(value, dict):
        current_level[last_key].update(value)
    else:
        current_level[last_key] = value

    _write_json(filepath, data)

def key_or_value_exists(filepath, key=None, value=None):
    """Checks for the existence of a key or value in a JSON file, supporting nested structures."""
    data = _read_json(filepath)
    keys = key.split('.') if key else []
    result = _get_nested_value(data, keys)

    return (result == value) if value is not None else (result is not None)

def delete_key(filepath, key):
    """Deletes a key from a JSON file, supporting nested structures."""
    data = _read_json(filepath)
    keys = key.split('.')
    current_level = data

    for part in keys[:-1]:
        current_level = current_level.get(part)
        if current_level is None:
            return

    last_key = keys[-1]
    current_level.pop(last_key, None)

    _write_json(filepath, data)