""" Manager Module (V2.7) | by ANXETY """

from CivitaiAPI import CivitAiAPI, CIVITAI_DOMAINS   # CivitAI API
import json_utils as js                              # JSON

from typing import Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path
import subprocess
import requests
import zipfile
import shlex
import re
import os


osENV = os.environ
CD = os.chdir

PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}
HOME, SCR_PATH, SETTINGS_PATH = (
    PATHS['home_path'], PATHS['scr_path'], PATHS['settings_path']
)


def _cai_token() -> str:
    return js.read(SETTINGS_PATH, 'WIDGETS.civitai_token') or 'd13740311c9f4ca5b250dfb26cf43a26'    # FAKE

def _hf_token() -> str:
    return js.read(SETTINGS_PATH, 'WIDGETS.huggingface_token') or ''


# ========================= Logging ========================

COLORS = {
    'red':    '\033[31m',
    'green':  '\033[32m',
    'yellow': '\033[33m',
    'blue':   '\033[34m',
    'purple': '\033[35m',
    'cyan':   '\033[36m',
    'reset':  '\033[0m',
}

def _color(text: str, key: str) -> str:
    """Wrap text in ANSI color escape codes"""
    return f"{COLORS[key]}{text}{COLORS['reset']}"


class Logger:
    """Colored console logger"""
    _LEVEL_COLORS = {
        'info':    'blue',
        'warning': 'yellow',
        'error':   'red',
        'success': 'green',
        'debug':   'purple',
    }

    def __init__(self, enabled: bool = False, debug: bool = False):
        self.enabled = enabled
        self.debug_enabled = debug

    def _write(self, message: str, level: str):
        if level == 'debug':
            if not self.debug_enabled:
                return
        elif not self.enabled:
            return
        prefix = _color(f"[{level.upper()}]:", self._LEVEL_COLORS.get(level, 'reset'))
        print(f">> {prefix} {message}")

    def debug(self, msg: str):   self._write(msg, 'debug')
    def info(self, msg: str):    self._write(msg, 'info')
    def warning(self, msg: str): self._write(msg, 'warning')
    def error(self, msg: str):   self._write(msg, 'error')
    def success(self, msg: str): self._write(msg, 'success')


log = Logger()


def handle_errors(func):
    """Decorator: catch and log exceptions, return None on failure"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error(str(e))
            return None
    return wrapper


# ===================== Core Utilities =====================

def _is_civitai(url: str) -> bool:
    """Return True if the URL belongs to a CivitAI domain"""
    host = urlparse(url).netloc.lower()
    return any(host == dom or host.endswith(f".{dom}") for dom in CIVITAI_DOMAINS)

def _is_signed_storage(url: str) -> bool:
    """Return True for Backblaze/CDN signed URLs that must NOT receive token params"""
    host = urlparse(url).netloc.lower()
    return host.startswith('b2.') or 'Authorization=' in url

def _get_filename_from_url(url: str, is_git: bool = False) -> Optional[str]:
    """Derive a local filename from a URL"""
    if any(domain in url for domain in [*CIVITAI_DOMAINS, 'drive.google.com']):
        return None
    name = Path(urlparse(url).path).name or None
    if not is_git and name and not Path(name).suffix:
        ext = Path(urlparse(url).path).suffix
        name = (name + ext) if ext else None
    return name

def _parse_line_parts(parts: list, url: str, is_git: bool = False) -> Tuple[Optional[Path], Optional[str]]:
    """Extract (save_path, filename) from a tokenised download/clone line"""
    save_path, filename = None, None

    if len(parts) >= 3:
        save_path = Path(parts[1]).expanduser()
        filename  = parts[2]
    elif len(parts) == 2:
        arg = parts[1]
        if '/' in arg or arg.startswith('~'):
            save_path = Path(arg).expanduser()
        else:
            filename = arg

    if not filename:
        url_name = Path(urlparse(url).path).name
        if url_name:
            filename = url_name

    if not is_git and 'drive.google.com' not in url:
        if filename and not Path(filename).suffix:
            ext = Path(urlparse(url).path).suffix
            filename = (filename + ext) if ext else None

    return save_path, filename

def _normalize_url(url: str) -> str:
    """Normalize HuggingFace and GitHub blob URLs to direct download URLs"""
    if 'huggingface.co' in url:
        return url.replace('/blob/', '/resolve/').split('?')[0]
    if 'github.com' in url:
        return url.replace('/blob/', '/raw/')
    return url

def _resolve_civitai_url(url: str) -> Tuple[Optional[str], Optional[object]]:
    """Resolve a CivitAI model/version page URL to a direct download URL via API"""
    api = CivitAiAPI(_cai_token())
    model_data = api.validate_download(url)
    if not model_data:
        return None
    return model_data.download_url

def _resolve_civitai_redirect(url: str) -> str:
    """Preflight GET to follow CivitAI to Backblaze signed redirect"""
    headers = {
        'User-Agent':    'CivitaiLink:Automatic1111',
        'Authorization': f"Bearer {_cai_token()}",
    }
    try:
        resp = requests.get(url, headers=headers, allow_redirects=True, stream=True, timeout=30)
        final = resp.url
        resp.close()
        if final and final != url:
            log.debug(f"Redirect resolved: {final}")
            return final
    except Exception as e:
        log.warning(f"Preflight redirect failed: {e}")
    return url


# ======================== Download ========================

@handle_errors
def m_download(line=None, verbose=False, debug=False, unzip=False):
    """Download files (comma-separated or from .txt file)"""
    log.enabled = verbose
    log.debug_enabled = debug

    if not line:
        return log.error('Missing URL argument, nothing to download')

    links = [lnk.strip() for lnk in line.split(',') if lnk.strip()]
    if not links:
        return log.info('No links provided, downloading nothing')

    for link in links:
        path = Path(link).expanduser()
        if link.endswith('.txt') and path.is_file():
            for subline in path.read_text().splitlines():
                _process_download(subline.strip(), unzip)
        else:
            _process_download(link, unzip)

@handle_errors
def _process_download(line: str, unzip: bool):
    """Process a single download line: URL with optional save path and filename"""
    if not line:
        return

    parts   = line.split()
    raw_url = parts[0].replace('\\', '')

    # Resolve/Normalize Download URL
    if _is_civitai(raw_url) and '/api/download/models/' not in raw_url:
        url = _resolve_civitai_url(raw_url)
    else:
        url = _normalize_url(raw_url)

    if not url:
        return

    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        log.warning(f"Invalid URL: {url}")
        return

    save_path, filename = _parse_line_parts(parts, url)
    prev_dir = Path.cwd()

    try:
        if save_path:
            save_path.mkdir(parents=True, exist_ok=True)
            CD(save_path)
        success = _download_file(url, filename)
        if success and unzip and filename and filename.lower().endswith('.zip'):
            _unzip_file(filename)
    finally:
        CD(prev_dir)

def _download_file(url: str, filename: Optional[str]) -> bool:
    """Dispatch download method by domain"""
    if any(domain in url for domain in [*CIVITAI_DOMAINS, 'huggingface.co', 'github.com']):
        return _aria2_download(url, filename)
    if 'drive.google.com' in url:
        return _gdrive_download(url, filename)
    # Download using curl
    cmd = f'curl -#JL "{url}"' + (f' -o "{filename}"' if filename else '')
    return _run_command(cmd)

def _aria2_download(url: str, filename: Optional[str]) -> bool:
    """Download via aria2c with domain-appropriate auth headers and token injection"""
    ua = 'CivitaiLink:Automatic1111' if _is_civitai(url) else 'Mozilla/5.0'

    aria2_args = (
        'aria2c'
        ' --allow-overwrite=true'
        ' --auto-file-renaming=false'
        ' --console-log-level=error'
        ' --stderr=true'
        ' --max-tries=10'
        ' --retry-wait=5'
        ' --check-certificate=false'
        ' -c -x16 -s16 -k1M -j5'
        f' --header="User-Agent: {ua}"'
    )

    # CivitAI Auth & Resolve Redirect
    if _is_civitai(url) and not _is_signed_storage(url):
        url = _resolve_civitai_redirect(url)

        token = _cai_token()
        if token and len(token) == 32 and '/api/download/models/' in url:
            aria2_args += f' --header="Authorization: Bearer {token}"'

    # HuggingFace Auth
    if 'huggingface.co' in url:
        hf_tok = _hf_token()
        if hf_tok:
            aria2_args += f' --header="Authorization: Bearer {hf_tok}"'

    if not filename:
        filename = _get_filename_from_url(url)

    cmd = f'{aria2_args} "{url}"'
    if filename:
        cmd += f' -o "{filename}"'

    return _aria2_monitor(cmd)

def _gdrive_download(url: str, filename: Optional[str]) -> bool:
    """Download from Google Drive using gdown"""
    cmd = f"gdown --fuzzy {url}"
    if filename:
        cmd += f' -O "{filename}"'
    if 'drive/folders' in url:
        cmd += ' --folder'
    return _run_command(cmd)

def _unzip_file(file: str):
    """Extract a ZIP archive into a subdirectory and remove the archive"""
    path = Path(file)
    with zipfile.ZipFile(path, 'r') as zf:
        zf.extractall(path.parent / path.stem)
    path.unlink()
    log.success(f"Unpacked {file} to '{path.parent / path.stem}'")

# aria2c progress monitor

ARIA_PROGRESS_RE = re.compile(
    r"\[#([0-9a-f]+)\s+"
    r"([\d.]+\w+)/([\d.]+\w+)\((\d+)%\)\s+"
    r"CN:(\d+)\s+"
    r"DL:([\d.]+\w+)\s+"
    r"ETA:([\w\d]+)\]"
)

def _aria2_monitor(cmd: str) -> bool:
    """Run aria2c command and print live progress bar, return True on success"""
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Extract filename from -o arg for success message
    parts    = shlex.split(cmd)
    filename = parts[parts.index('-o') + 1] if '-o' in parts else None

    errors, last_stats = [], None

    try:
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break

            if 'errorCode' in line or 'Exception' in line or ('|' in line and 'ERR' in line):
                errors.append(line.replace('ERR', _color('ERR', 'red')))

            match = ARIA_PROGRESS_RE.search(line)
            if not match or not log.enabled:
                continue

            gid, done, total, pct, conns, speed, eta = match.groups()
            pct        = int(pct)
            last_stats = (total, speed)

            bar_width = 30
            filled    = bar_width * pct // 100
            bar       = '■' * filled + ' ' * (bar_width - filled)
            out = (
                f"{_color('[', 'purple')}{_color(f'#{gid}', 'green')}{_color(']', 'purple')} "
                f"[{bar}] {pct}% "
                f"{_color(done, 'cyan')}/{_color(total, 'cyan')} "
                f"{_color(speed + '/s', 'green')} "
                f"{_color('CN:', 'blue')}{conns} "
                f"{_color('ETA:', 'yellow')}{eta}"
            )
            print(f"\r{' ' * 180}\r{out}", end='', flush=True)

        process.wait()
        success = process.returncode == 0 and not errors

        if log.enabled:
            print(f"\r{' ' * 180}\r", end='', flush=True)
            for err in errors:
                print(err)
            if success and last_stats:
                total, speed = last_stats
                file_part  = _color(filename, 'blue') + ' ' if filename else ''
                stats_part = _color(f"({total} @ {speed}/s)", 'cyan')
                print(f"{_color('✔ Done', 'green')} | {file_part}{stats_part}")
            elif success:
                print(f"{_color('✔ Download Complete', 'green')}")
            elif not errors:
                log.error(f"Download failed (exit code {process.returncode})")

        return success

    except KeyboardInterrupt:
        print()
        log.info('Download interrupted')
        return False

def _run_command(cmd: str) -> bool:
    """Execute a shell command string, return True on success"""
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if log.enabled:
        for line in process.stderr:
            print(line, end='')
    process.wait()
    return process.returncode == 0


# ======================== Git Clone =======================

@handle_errors
def m_clone(input_source=None, recursive=True, depth=1, verbose=False, debug=False):
    """Clone one or more GitHub repositories (comma-separated or from .txt file)"""
    log.enabled = verbose
    log.debug_enabled = debug

    if not input_source:
        return log.error('Missing repository source')

    sources = [src.strip() for src in input_source.split(',') if src.strip()]
    if not sources:
        return log.info('No valid repositories to clone')

    for source in sources:
        path = Path(source).expanduser()
        if source.endswith('.txt') and path.is_file():
            for line in path.read_text().splitlines():
                _process_clone(line.strip(), recursive, depth)
        else:
            _process_clone(source, recursive, depth)

@handle_errors
def _process_clone(line: str, recursive: bool, depth: int):
    """Process a single clone line: URL with optional save path and repo name"""
    if not line:
        return

    parts = shlex.split(line)
    url   = parts[0].replace('\\', '')

    if urlparse(url).netloc not in ('github.com', 'www.github.com'):
        return log.warning(f"Not a GitHub URL: {url}")

    save_path, repo_name = _parse_line_parts(parts, url, is_git=True)
    prev_dir = Path.cwd()

    try:
        if save_path:
            save_path.mkdir(parents=True, exist_ok=True)
            CD(save_path)

        cmd_parts = ['git', 'clone']
        if depth > 0:
            cmd_parts += ['--depth', str(depth)]
        if recursive:
            cmd_parts.append('--recursive')
        cmd_parts.append(url)
        if repo_name:
            cmd_parts.append(repo_name)

        _run_git(' '.join(cmd_parts))
    finally:
        CD(prev_dir)

def _run_git(cmd: str):
    """Run a git command string and log clone progress and errors"""
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for output in iter(process.stdout.readline, ''):
        output = output.strip()
        if not output:
            continue
        if 'Cloning into' in output:
            repo = re.search(r"'(.+?)'", output)
            if repo:
                log.info(f"Cloning: {_color(repo.group(1), 'green')}")
        if 'fatal' in output.lower():
            log.error(output)
    process.wait()