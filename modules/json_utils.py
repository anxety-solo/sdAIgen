import json
import os

def _get_nested_value(data, keys):
    """
    Gets a value by key from a nested data structure.
    Returns `default` if the key is not found.
    """
    current_level = data
    for part in keys:
        if part in current_level:
            current_level = current_level[part]
        else:
            return None
    return current_level

def _set_nested_value(data, keys, value):
    """
    Sets a value by key into a nested data structure.
    Creates intermediate levels if they do not exist.
    """
    current_level = data
    for part in keys[:-1]:
        if part not in current_level:
            current_level[part] = {}
        current_level = current_level[part]
    current_level[keys[-1]] = value

def read_json(filepath, key, default=None):
    """Reads a value by key from a JSON file, supporting nested structures."""
    if not os.path.exists(filepath):
        return default

    with open(filepath, 'r') as json_file:
        data = json.load(json_file)

    keys = key.split('.')
    result = _get_nested_value(data, keys)
    return result if result is not None else default

def save_json(filepath, key, value):
    """Saves a value by key in a JSON file, supporting nested structures."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}

    keys = key.split('.')
    _set_nested_value(data, keys, value)

    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def update_json(filepath, key, value):
    """Updates a value by key in a JSON file, supporting nested structures, 
    appending if the key already exists."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as json_file:
            data = json.load(json_file)
    else:
        data = {}

    keys = key.split('.')
    current_level = data
    for part in keys[:-1]:
        if part not in current_level:
            current_level[part] = {}
        current_level = current_level[part]

    last_key = keys[-1]
    if last_key in current_level and isinstance(current_level[last_key], dict):
        current_level[last_key].update(value)
    else:
        current_level[last_key] = value

    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def key_or_value_exists(filepath, key=None, value=None):
    """Checks for the existence of a key or value in a JSON file, supporting nested structures."""
    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r') as json_file:
        data = json.load(json_file)

    keys = key.split('.') if key else []
    result = _get_nested_value(data, keys)

    if value is not None:
        return result == value
    else:
        return result is not None

def delete_key(filepath, key):
    """Deletes a key from a JSON file, supporting nested structures."""
    if not os.path.exists(filepath):
        return

    with open(filepath, 'r') as json_file:
        data = json.load(json_file)

    keys = key.split('.')
    current_level = data
    for part in keys[:-1]:
        if part in current_level:
            current_level = current_level[part]
        else:
            return

    last_key = keys[-1]
    if last_key in current_level:
        del current_level[last_key]

    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)