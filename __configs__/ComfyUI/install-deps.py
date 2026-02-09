""" install-deps.py | by ANXETY """

from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path
import subprocess
import importlib
import sys
import re
import os

def get_enabled_subdirectories(base_directory):
    """Find active directories with dependencies"""
    base_path = Path(base_directory)
    subdirs = []

    for subdir in base_path.iterdir():
        if subdir.is_dir() and not subdir.name.endswith('.disabled') and not subdir.name.startswith('.') and subdir.name != '__pycache__':
            print(f"\033[1;34mChecking dependencies >> \033[0m{subdir.name}")
            req_file = subdir / 'requirements.txt'
            inst_script = subdir / 'install.py'

            if req_file.exists() or inst_script.exists():
                subdirs.append((subdir, req_file, inst_script))

    print()
    return subdirs

def get_git_package_name(git_url):
    """Extract package name from Git URL"""
    clean_url = git_url.split('git+')[-1].rstrip('/')

    # Attempt to extract name from GitHub URL
    if 'github.com' in clean_url:
        match = re.search(r'github\.com/[^/]+/([^/]+)', clean_url)
        if match:
            return match.group(1).replace('.git', '')

    # General case for .git repositories
    match = re.search(r'/([^/]+?)(\.git)?$', clean_url)
    return match.group(1) if match else None

def is_git_installed(git_url):
    """Check if Git package is installed by attempting import"""
    pkg_name = get_git_package_name(git_url)
    if not pkg_name:
        return False

    variants = {
        pkg_name,
        pkg_name.lower(),
        pkg_name.replace('-', '_'),
        pkg_name.lower().replace('-', '_')
    }

    for variant in variants:
        try:
            importlib.import_module(variant)
            return True
        except ImportError:
            continue
    return False

def check_package(package_spec):
    """Check package installation with version verification"""
    try:
        if 'git+' in package_spec:
            return is_git_installed(package_spec)

        match = re.match(r'^([^=><]+)([<>=!]+)(.+)$', package_spec)
        if not match:
            dist = distribution(package_spec.strip())
            return True

        name, op, version = map(str.strip, match.groups())
        installed = distribution(name).version
        return compare_versions(installed, version, op)

    except (PackageNotFoundError, AttributeError):
        return False

def compare_versions(v1, v2, operator):
    """Universal version comparison"""
    v1_parts = list(map(int, re.findall(r'\d+', v1)))
    v2_parts = list(map(int, re.findall(r'\d+', v2)))

    for a, b in zip(v1_parts, v2_parts):
        if a != b:
            break
    else:
        a, b = len(v1_parts), len(v2_parts)

    if operator == '==': return a == b
    if operator == '>=': return a >= b
    if operator == '<=': return a <= b
    if operator == '>': return a > b
    if operator == '<': return a < b
    return False

def install_package(package_spec):
    """Install a package"""
    print(f"\033[1;32mInstalling >> \033[0m{package_spec}")
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-q', package_spec],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def process_requirements(file_path, installed):
    """Process requirements file"""
    if not file_path.exists():
        return

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line in installed:
                continue

            if not check_package(line):
                install_package(line)
                installed.add(line)

def run_install_script(script_path, executed):
    """Execute installation script"""
    if script_path.exists() and str(script_path) not in executed:
        print(f"\033[1;33mRunning install script >> \033[0m{script_path}")
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        executed.add(str(script_path))

def save_state(installed, scripts, log_file):
    """Save installation state to log file"""
    with open(log_file, 'w') as f:
        f.write('\n'.join(installed))
        f.write('\n\n# Executed scripts:\n')
        f.write('\n'.join(scripts))

def load_previous_state(log_file):
    """Load previous installation state from log"""
    installed = set()
    scripts = set()

    if Path(log_file).exists():
        with open(log_file) as f:
            section = 0
            for line in f:
                line = line.strip()
                if not line: continue

                if line.startswith('# Executed scripts:'):
                    section = 1
                    continue

                if section == 0:
                    installed.add(line)
                else:
                    scripts.add(line)

    return installed, scripts

def main():
    base_dir = 'custom_nodes'
    log_file = 'installed_packages.txt'

    installed, executed = load_previous_state(log_file)
    directories = get_enabled_subdirectories(base_dir)

    try:
        for _, req, script in directories:
            process_requirements(req, installed)
            run_install_script(script, executed)

        save_state(installed, executed, log_file)

    except KeyboardInterrupt:
        print('\n\033[1;31mInterrupted by user\033[0m')
    except Exception as e:
        print(f"\n\033[1;31mError: {e}\033[0m")

if __name__ == '__main__':
    main()