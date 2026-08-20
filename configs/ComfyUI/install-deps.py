""" ComfyUI Dependencies Installer | by ANXETY """

import subprocess
import importlib
import sys
import re

from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path


# ~~ COLORS ~~

C_CYAN   = '\033[1;34m'    # Checking
C_GREEN  = '\033[1;32m'    # Installing
C_YELLOW = '\033[1;33m'    # Install script
C_RED    = '\033[1;31m'    # Error
C_RESET  = '\033[0m'


# ~~ PACKAGE CHECKS ~~

def get_git_package_name(git_url: str) -> str | None:
    """Extract the package name from a Git URL"""
    clean_url = git_url.split('git+')[-1].rstrip('/')

    if 'github.com' in clean_url:
        match = re.search(r'github\.com/[^/]+/([^/]+)', clean_url)
        if match:
            return match.group(1).replace('.git', '')

    match = re.search(r'/([^/]+?)(\.git)?$', clean_url)
    return match.group(1) if match else None


def is_git_installed(git_url: str) -> bool:
    """Check if a Git package is importable"""
    package = get_git_package_name(git_url)
    if not package:
        return False

    variants = {package, package.lower(), package.replace('-', '_'), package.lower().replace('-', '_')}
    for variant in variants:
        try:
            importlib.import_module(variant)
            return True
        except ImportError:
            continue
    return False


def check_package(package_spec: str) -> bool:
    """Check if a package is installed, with version verification"""
    if 'git+' in package_spec:
        return is_git_installed(package_spec)

    match = re.match(r'^([^=><]+)([<>=!]+)(.+)$', package_spec)
    if not match:
        try:
            distribution(package_spec.strip())
            return True
        except PackageNotFoundError:
            return False

    name, op, version = map(str.strip, match.groups())
    try:
        return compare_versions(distribution(name).version, version, op)
    except (PackageNotFoundError, AttributeError):
        return False


def compare_versions(v1: str, v2: str, operator: str) -> bool:
    """Compare two version strings numerically"""
    v1_parts = list(map(int, re.findall(r'\d+', v1)))
    v2_parts = list(map(int, re.findall(r'\d+', v2)))

    for a, b in zip(v1_parts, v2_parts):
        if a != b:
            break
    else:
        a, b = len(v1_parts), len(v2_parts)

    return {'==': a == b, '>=': a >= b, '<=': a <= b, '>': a > b, '<': a < b}.get(operator, False)


def install_package(package_spec: str):
    """Install a package with pip"""
    print(f"{C_GREEN}Installing >> {C_RESET}{package_spec}")
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-q', package_spec],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ~~ PROCESSING ~~

def get_enabled_subdirectories(base_directory: str | Path) -> list[tuple[Path, Path, Path]]:
    """Find enabled subdirectories with requirements or install scripts"""
    subdirs = []

    for subdir in Path(base_directory).iterdir():
        name = subdir.name
        if not subdir.is_dir() or name.startswith('.') or name.endswith('.disabled') or name == '__pycache__':
            continue

        print(f"{C_CYAN}Checking dependencies >> {C_RESET}{name}")
        requirements  = subdir / 'requirements.txt'
        install_script = subdir / 'install.py'

        if requirements.exists() or install_script.exists():
            subdirs.append((subdir, requirements, install_script))

    print()
    return subdirs


def process_requirements(file_path: Path, installed: set[str]):
    """Install missing packages from a requirements file"""
    if not file_path.exists():
        return

    for line in file_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line in installed:
            continue

        if not check_package(line):
            install_package(line)
            installed.add(line)


def run_install_script(script_path: Path, executed: set[str]):
    """Run a node install script once"""
    if not script_path.exists() or str(script_path) in executed:
        return

    print(f"{C_YELLOW}Running install script >> {C_RESET}{script_path}")
    subprocess.run(
        [sys.executable, str(script_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    executed.add(str(script_path))


# ~~ STATE ~~

def save_state(installed: set[str], scripts: set[str], log_file: str | Path):
    """Save installation state to the log file"""
    content = '\n'.join(installed) + '\n\n# Executed scripts:\n' + '\n'.join(scripts)
    Path(log_file).write_text(content, encoding='utf-8')


def load_previous_state(log_file: str | Path) -> tuple[set[str], set[str]]:
    """Load the previous installation state from the log file"""
    installed, scripts = set(), set()

    if not Path(log_file).exists():
        return installed, scripts

    section = 0
    for line in Path(log_file).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('# Executed scripts:'):
            section = 1
            continue

        (installed if section == 0 else scripts).add(line)

    return installed, scripts


# ~~ MAIN ~~

def main():
    base_dir = 'custom_nodes'
    log_file = 'installed_packages.txt'

    installed, executed = load_previous_state(log_file)

    try:
        for _, requirements, script in get_enabled_subdirectories(base_dir):
            process_requirements(requirements, installed)
            run_install_script(script, executed)

        save_state(installed, executed, log_file)

    except KeyboardInterrupt:
        print(f"\n{C_RED}Interrupted by user{C_RESET}")
    except Exception as exc:
        print(f"\n{C_RED}Error: {exc}{C_RESET}")


if __name__ == '__main__':
    main()
