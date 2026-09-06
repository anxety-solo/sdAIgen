""" Download Manager: aria2/gdown/curl & Git Clone | by ANXETY """

import subprocess
import requests
import zipfile
import shlex
import re

from collections.abc import Callable
from urllib.parse import urlparse
from pathlib import Path
from typing import Any

# === SDAIGEN ===
from sdai.api.civitai import CIVITAI_DOMAINS, CivitaiAPI
from sdai.constants import SETTINGS_PATH, COL
from sdai.utils.logger import Logger
from sdai.utils.json import read


logger = Logger(enabled=False)


ARIA2_FLAGS = (
    '--allow-overwrite=true'
    ' --auto-file-renaming=false'
    ' --console-log-level=error'
    ' --stderr=true'
    ' --max-tries=10'
    ' --retry-wait=5'
    ' --check-certificate=false'
    ' -c -x16 -s16 -k1M -j5'
)


def _cai_token() -> str:
    """CivitAI API token from settings"""
    token = (read(SETTINGS_PATH, 'WIDGETS.civitai_token') or '').strip()
    return token or 'd13740311c9f4ca5b250dfb26cf43a26'  # FAKE


def _hf_token() -> str:
    """HuggingFace API token from settings"""
    return (read(SETTINGS_PATH, 'WIDGETS.huggingface_token') or '').strip()


def handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: catch and log exceptions, return None on failure"""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            logger.error(str(exc))
            return None
    return wrapper


# ~~ URL UTILITIES ~~

def _is_civitai(url: str) -> bool:
    """Return True if the URL belongs to a CivitAI domain"""
    host = urlparse(url).netloc.lower()
    return any(host == dom or host.endswith(f".{dom}") for dom in CIVITAI_DOMAINS)


def _is_signed_storage(url: str) -> bool:
    """Return True for Backblaze/CDN signed URLs that must NOT receive token params"""
    host = urlparse(url).netloc.lower()
    return host.startswith('b2.') or 'Authorization=' in url


def _normalize_url(url: str) -> str:
    """Normalize HuggingFace and GitHub blob URLs to direct download URLs"""
    if 'huggingface.co' in url:
        return url.replace('/blob/', '/resolve/').split('?')[0]
    if 'github.com' in url:
        return url.replace('/blob/', '/raw/')
    return url


def _with_extension(filename: str | None, url: str) -> str | None:
    """Append the URL's extension to a filename that lacks one"""
    if filename and not Path(filename).suffix:
        ext = Path(urlparse(url).path).suffix
        filename = (filename + ext) if ext else None
    return filename


def _get_filename_from_url(url: str, is_git=False) -> str | None:
    """Derive a local filename from a URL"""
    if any(domain in url for domain in [*CIVITAI_DOMAINS, 'drive.google.com']):
        return None

    name = Path(urlparse(url).path).name or None
    return name if is_git else _with_extension(name, url)


def _parse_line_parts(parts: list[str], url: str, is_git=False) -> tuple[Path | None, str | None]:
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

    filename = filename or Path(urlparse(url).path).name or None
    if not is_git and 'drive.google.com' not in url:
        filename = _with_extension(filename, url)

    return save_path, filename


def _resolve_civitai_url(url: str) -> tuple[str | None, str | None]:
    """Resolve a CivitAI model/version page URL to a direct download URL via API"""
    data = CivitaiAPI(_cai_token()).validate_download(url)
    return (data.download_url, data.file_name) if data else (None, None)


def _resolve_civitai_redirect(url: str) -> str:
    """Preflight GET to follow CivitAI to Backblaze signed redirect"""
    headers = {
        'User-Agent':    'CivitaiLink:Automatic1111',
        'Authorization': f"Bearer {_cai_token()}",
    }
    try:
        resp  = requests.get(url, headers=headers, allow_redirects=True, stream=True, timeout=30)
        final = resp.url
        resp.close()
        if final and final != url:
            logger.debug(f"Redirect resolved: {final}")
            return final
    except Exception as exc:
        logger.warning(f"Preflight redirect failed: {exc}")

    return url


# ~~ DOWNLOAD ~~

def _expand_sources(sources: list[str], callback: Callable[..., Any], *args: Any):
    """Call callback for each source line, expanding local .txt files line-by-line"""
    for source in sources:
        path  = Path(source).expanduser()
        lines = (path.read_text(encoding='utf-8').splitlines() if source.endswith('.txt') and path.is_file() else [source])

        for line in lines:
            callback(line.strip(), *args)


@handle_errors
def download(line: str = None, verbose=False, debug=False, unzip=False):
    """Download files (comma-separated or from .txt file)"""
    logger.enabled, logger.debug_enabled = verbose, debug

    if not line:
        return logger.error('Missing URL argument, nothing to download')

    links = [link.strip() for link in line.split(',') if link.strip()]
    if not links:
        return logger.info('No links provided, downloading nothing')

    _expand_sources(links, _process_download, unzip)


@handle_errors
def _process_download(line: str, unzip: bool):
    """Process a single download line: URL with optional save path and filename"""
    if not line:
        return

    parts   = line.split()
    raw_url = parts[0].replace('\\', '')

    civitai_filename = None
    is_model_page = 'modelVersionId=' in raw_url or any(f"{d}/models/" in raw_url for d in CIVITAI_DOMAINS)
    if is_model_page and '/api/download/models/' not in raw_url:
        url, civitai_filename = _resolve_civitai_url(raw_url)
    else:
        url = _normalize_url(raw_url)

    if not url:
        return

    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        logger.warning(f"Invalid URL: {url}")
        return

    save_path, filename = _parse_line_parts(parts, url)
    if not filename and civitai_filename:
        filename = civitai_filename

    if save_path:
        save_path.mkdir(parents=True, exist_ok=True)

    success = _download_file(url, filename, save_path)
    if success and unzip and filename and filename.lower().endswith('.zip'):
        _unzip_file(save_path / filename if save_path else filename)


def _download_file(url: str, filename: str | None, save_path: Path = None) -> bool:
    """Dispatch download method by domain"""
    if any(domain in url for domain in [*CIVITAI_DOMAINS, 'huggingface.co', 'github.com']):
        return _aria2_download(url, filename, save_path)
    if 'drive.google.com' in url:
        return _gdrive_download(url, filename, save_path)
    # Download using curl
    cmd = f'curl -#JL "{url}"'
    if filename:
        cmd += f' -o "{save_path / filename if save_path else filename}"'
    return _run_command(cmd)


def _aria2_download(url: str, filename: str | None, save_path: Path = None) -> bool:
    """Download via aria2c with domain-appropriate auth headers and token injection"""
    ua = 'CivitaiLink:Automatic1111' if _is_civitai(url) else 'Mozilla/5.0'

    aria2_args = f'aria2c {ARIA2_FLAGS} --header="User-Agent: {ua}"'

    # CivitAI Auth & Resolve Redirect
    if _is_civitai(url) and not _is_signed_storage(url):
        url   = _resolve_civitai_redirect(url)
        token = _cai_token()
        if token and len(token) == 32 and '/api/download/models/' in url:
            aria2_args += f' --header="Authorization: Bearer {token}"'

    # HuggingFace Auth
    if 'huggingface.co' in url:
        token = _hf_token()
        if token:
            aria2_args += f' --header="Authorization: Bearer {token}"'

    if not filename:
        filename = _get_filename_from_url(url)

    cmd = f'{aria2_args} "{url}"'

    if filename:
        if save_path:
            cmd += f' -d "{save_path}" -o "{filename}"'
        else:
            cmd += f' -o "{filename}"'

    return _aria2_monitor(cmd)


def _gdrive_download(url: str, filename: str | None, save_path: Path = None) -> bool:
    """Download from Google Drive using gdown"""
    cmd = f"gdown --fuzzy {url}"
    if filename:
        target = save_path / filename if save_path else filename
        cmd += f' -O "{target}"'
    if 'drive/folders' in url:
        cmd += ' --folder'

    return _run_command(cmd)


def _unzip_file(file: str):
    """Extract a ZIP archive into a subdirectory and remove the archive"""
    path = Path(file)
    with zipfile.ZipFile(path, 'r') as zf:
        zf.extractall(path.parent / path.stem)
    path.unlink()
    logger.success(f"Unpacked {file} to '{path.parent / path.stem}'")


# ~~ ARIA PROGRESS MONITOR ~~

ARIA_PROGRESS_RE = re.compile(
    r'\[#([0-9a-f]+)\s+'
    r'([\d.]+\w+)/([\d.]+\w+)\((\d+)%\)\s+'
    r'CN:(\d+)\s+'
    r'DL:([\d.]+\w+)\s+'
    r'ETA:([\w\d]+)\]'
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
                errors.append(line.replace('ERR', f"{COL.R}ERR{COL.X}"))

            match = ARIA_PROGRESS_RE.search(line)
            if not match or not logger.enabled:
                continue

            gid, done, total, pct, conns, speed, eta = match.groups()
            pct = int(pct)
            last_stats = (total, speed)

            bar_width = 30
            filled = bar_width * pct // 100
            bar = '■' * filled + ' ' * (bar_width - filled)

            out = (
                f"{COL.P}[{COL.G}#{gid}{COL.P}]{COL.X} "
                f"[{bar}] {pct}% "
                f"{COL.C}{done}{COL.X}/{COL.C}{total}{COL.X} "
                f"{COL.G}{speed}/s{COL.X} "
                f"{COL.B}CN:{COL.X}{conns} "
                f"{COL.Y}ETA:{COL.X}{eta}"
            )
            print(f"\r{' ' * 180}\r{out}", end='', flush=True)

        process.wait()
        success = process.returncode == 0 and not errors

        if logger.enabled:
            print(f"\r{' ' * 180}\r", end='', flush=True)
            for err in errors:
                print(err)

            if success and last_stats:
                total, speed = last_stats
                file_part  = f"{COL.B}{filename}{COL.X} " if filename else ''
                stats_part = f"{COL.C}({total} @ {speed}/s){COL.X}"
                print(f"{COL.G}✔ Done{COL.X} | {file_part}{stats_part}")
            elif success:
                file_part = f" — {COL.B}{filename}{COL.X}" if filename else ''
                print(f"{COL.G}✔ Download Complete{COL.X}{file_part}")
            elif not errors:
                logger.error(f"Download failed (exit code {process.returncode})")

        return success

    except KeyboardInterrupt:
        print()
        logger.info('Download interrupted')
        return False


def _run_command(cmd: str) -> bool:
    """Execute a shell command string, return True on success"""
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if logger.enabled:
        for line in process.stderr:
            print(line, end='')
    process.wait()
    return process.returncode == 0


# ~~ GIT CLONE ~~

@handle_errors
def clone(input_source: str = None, recursive=True, depth=1, verbose=False, debug=False, branch: str = None):
    """Clone one or more GitHub repositories (comma-separated or from .txt file)"""
    logger.enabled, logger.debug_enabled = verbose, debug

    if not input_source:
        return logger.error('Missing repository source')

    sources = [src.strip() for src in input_source.split(',') if src.strip()]
    if not sources:
        return logger.info('No valid repositories to clone')

    _expand_sources(sources, _process_clone, recursive, depth, branch)


@handle_errors
def _process_clone(line: str, recursive: bool, depth: int, branch: str = None):
    """Process a single clone line: URL with optional save path and repo name"""
    if not line:
        return

    parts = shlex.split(line)
    url   = parts[0].replace('\\', '')

    if urlparse(url).netloc not in ('github.com', 'www.github.com'):
        return logger.warning(f"Not a GitHub URL: {url}")

    save_path, repo_name = _parse_line_parts(parts, url, is_git=True)

    if save_path:
        save_path.mkdir(parents=True, exist_ok=True)
        if not repo_name:
            repo_name = Path(urlparse(url).path).name.removesuffix('.git') or None

    cmd_parts = ['git', 'clone']
    if depth > 0:
        cmd_parts += ['--depth', str(depth)]
    if branch:
        cmd_parts += ['--branch', branch]
    if recursive:
        cmd_parts.append('--recursive')

    cmd_parts.append(url)

    if repo_name:
        cmd_parts.append(str(save_path / repo_name) if save_path else repo_name)

    _run_git(' '.join(cmd_parts))


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
                logger.info(f"Cloning: {COL.G}{repo.group(1)}{COL.X}")
        if 'fatal' in output.lower():
            logger.error(output)
    process.wait()
