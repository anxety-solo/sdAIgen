""" Manager Module (V2) | by ANXETY """

from CivitaiAPI import CivitAiAPI   # CivitAI API
import json_utils as js             # JSON

from urllib.parse import urlparse
from pathlib import Path
import subprocess
import zipfile
import shlex
import re
import os


osENV = os.environ
CD = os.chdir

# Constants (auto-convert env vars to Path)
PATHS = {k: Path(v) for k, v in osENV.items() if k.endswith('_path')}   # k -> key; v -> value

HOME = PATHS['home_path']
SCR_PATH = PATHS['scr_path']
SETTINGS_PATH = PATHS['settings_path']

CAI_TOKEN = js.read(SETTINGS_PATH, 'WIDGETS.civitai_token') or '65b66176dcf284b266579de57fbdc024'
HF_TOKEN = js.read(SETTINGS_PATH, 'WIDGETS.huggingface_token') or ''


# ========================= Logging ========================

def log_message(message, log=False, status='info'):
    """Display colored log messages."""
    if not log:
        return
    colors = {
        'error': '\033[31m[ERROR]:\033[0m',
        'warning': '\033[33m[WARNING]:\033[0m',
        'success': '\033[32m[SUCCESS]:\033[0m',
        'info': '\033[34m[INFO]:\033[0m'
    }
    prefix = colors.get(status.lower(), '')
    print(f">> {prefix} {message}" if prefix else message)

# Error handling decorator
def handle_errors(func):
    """Catch and log exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_message(str(e), True, 'error')
            return None
    return wrapper


# ===================== Core Utilities =====================

def _get_file_name(url, is_git=False):
    """Get the file name based on the URL."""
    if any(domain in url for domain in ['civitai.com', 'drive.google.com']):
        return None

    filename = Path(urlparse(url).path).name or None

    if not is_git and filename and not Path(filename).suffix:
        suffix = Path(urlparse(url).path).suffix
        if suffix:
            filename += suffix
        else:
            filename = None

    return filename

def handle_path_and_filename(parts, url, is_git=False):
    """Extract path and filename from parts."""
    path, filename = None, None

    if len(parts) >= 3:
        path = Path(parts[1]).expanduser()
        filename = parts[2]
    elif len(parts) == 2:
        arg = parts[1]
        if '/' in arg or arg.startswith('~'):
            path = Path(arg).expanduser()
        else:
            filename = arg

    if not filename:
        url_path = urlparse(url).path
        if url_path:
            url_filename = Path(url_path).name
            if url_filename:
                filename = url_filename

    if not is_git and 'drive.google.com' not in url:
        if filename and not Path(filename).suffix:
            url_ext = Path(urlparse(url).path).suffix
            if url_ext:
                filename += url_ext
            else:
                filename = None

    return path, filename

@handle_errors
def strip_url(url):
    """Normalize special URLs (civitai, huggingface, github)."""
    if 'civitai.com/models/' in url:
        api = CivitAiAPI(CAI_TOKEN)
        data = api.validate_download(url)
        return data.download_url if data else None

    if 'huggingface.co' in url:
        url = url.replace('/blob/', '/resolve/').split('?')[0]

    if 'github.com' in url:
        url = url.replace('/blob/', '/raw/')

    return url

def is_github_url(url):
    """Check if the URL is a valid GitHub URL"""
    return urlparse(url).netloc in ('github.com', 'www.github.com')


# ======================== Download ========================

@handle_errors
def m_download(line=None, log=False, unzip=False):
    """Download files from a comma-separated list of URLs or file paths."""
    if not line:
        return log_message("Missing URL argument, nothing to download", log, 'error')

    links = [link.strip() for link in line.split(',') if link.strip()]

    if not links:
        log_message('Missing URL, downloading nothing', log, 'info')
        return

    for link in links:
        if link.endswith('.txt') and Path(link).expanduser().is_file():
            with open(Path(link).expanduser(), 'r') as file:
                for subline in file:
                    _process_download(subline.strip(), log, unzip)
        else:
            _process_download(link, log, unzip)

@handle_errors
def _process_download(line, log, unzip):
    """Process an individual download line."""
    parts = line.split()
    url = parts[0].replace('\\', '')
    url = strip_url(url)

    if not url:
        return

    # Validate URL format
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            log_message(f'Invalid URL format: {url}', log, 'warning')
            return
    except Exception as e:
        log_message(f'URL validation failed for {url}: {str(e)}', log, 'warning')
        return


    path, filename = handle_path_and_filename(parts, url)
    current_dir = Path.cwd()

    try:
        if path:
            path.mkdir(parents=True, exist_ok=True)
            CD(path)

        _download_file(url, filename, log)

        if unzip and filename and filename.lower().endswith('.zip'):
            _unzip_file(filename, log)
    finally:
        CD(current_dir)

def _download_file(url, filename, log):
    """Dispatch download method by domain."""
    if any(domain in url for domain in ['civitai.com', 'huggingface.co', 'github.com']):
        _aria2_download(url, filename, log)
    elif 'drive.google.com' in url:
        _gdrive_download(url, filename, log)
    else:
        """Download using curl."""
        cmd = f"curl -#JL '{url}'"
        if filename:
            cmd += f" -o '{filename}'"
        _run_command(cmd, log)

def _aria2_download(url, filename, log):
    """Download using aria2c."""
    user_agent = 'CivitaiLink:Automatic1111' if 'civitai.com' in url else 'Mozilla/5.0'
    aria2_args = f'aria2c --header="User-Agent: {user_agent}" --allow-overwrite=true --console-log-level=error --stderr=true -c -x16 -s16 -k1M -j5'

    if HF_TOKEN and 'huggingface.co' in url:
        aria2_args += f' --header="Authorization: Bearer {HF_TOKEN}"'

    if not filename:
        filename = _get_file_name(url)

    cmd = f"{aria2_args} '{url}'"
    if filename:
        cmd += f" -o '{filename}'"

    _aria2_monitor(cmd, log)

def _gdrive_download(url, filename, log):
    cmd = f"gdown --fuzzy {url}"
    if filename:
        cmd += f" -O '{filename}'"
    if 'drive/folders' in url:
        cmd += " --folder"
    _run_command(cmd, log)

def _unzip_file(file, log):
    """Extract the ZIP file to a directory named after archive."""
    path = Path(file)
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(path.parent / path.stem)
    path.unlink()
    log_message(f"Unpacked {file} to {path.parent / path.stem}", log)

def _aria2_monitor(command, log):
    """Monitor aria2c download progress."""
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result, error_codes, error_messages = '', [], []
    br = False

    try:
        while True:
            line = process.stderr.readline()
            if line == '' and process.poll() is not None:
                break

            result += line
            for raw_line in line.splitlines():
                _handle_aria_errors(raw_line, error_codes, error_messages)
                if re.match(r'\[#\w{6}\s.*\]', raw_line):
                    formatted = _format_aria_line(raw_line)
                    if log:
                        print(f"\r{' ' * 180}\r{formatted}", end='', flush=True)
                        br = True

        if log:
            if error_codes or error_messages:
                print()
            for err in error_codes + error_messages:
                print(err)

            if br:
                print()

            if '======+====+===========' in result:
                for line in result.splitlines():
                    if '|' in line and 'OK' in line:
                        print(re.sub(r'(OK)', '\033[32m\\1\033[0m', line))

        process.wait()
    except KeyboardInterrupt:
        print()
        log_message("Download interrupted", log)

def _format_aria_line(line):
    """Format a line of output with ANSI color codes."""
    line = re.sub(r'\[', '\033[35m【\033[0m', line)
    line = re.sub(r'\]', '\033[35m】\033[0m', line)
    line = re.sub(r'(#)(\w+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(\(\d+%\))', r'\033[36m\1\033[0m', line)
    line = re.sub(r'(CN:)(\d+)', r'\1\033[34m\2\033[0m', line)
    line = re.sub(r'(DL:)([^\s]+)', r'\1\033[32m\2\033[0m', line)
    line = re.sub(r'(ETA:)([^\s]+)', r'\1\033[33m\2\033[0m', line)
    return line

def _handle_aria_errors(line, error_codes, error_messages):
    """Check and collect error messages from the output."""
    if 'errorCode' in line or 'Exception' in line:
        error_codes.append(line)
    if '|' in line and 'ERR' in line:
        error_messages.append(re.sub(r'(ERR)', '\033[31m\\1\033[0m', line))

def _run_command(command, log):
    """Execute a shell command."""
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if log:
        for line in process.stderr:
            print(line, end='')
    process.wait()


# ======================== Git Clone =======================

@handle_errors
def m_clone(input_source=None, recursive=True, depth=1, log=False):
    """Main function to clone repositories"""
    if not input_source:
        return log_message("Missing repository source", log, 'error')

    sources = [link.strip() for link in input_source.split(',') if link.strip()]

    if not sources:
        log_message('No valid repositories to clone', log, 'info')
        return

    for source in sources:
        if source.endswith('.txt') and Path(source).expanduser().is_file():
            with open(Path(source).expanduser()) as file:
                for line in file:
                    _process_clone(line.strip(), recursive, depth, log)
        else:
            _process_clone(source, recursive, depth, log)

@handle_errors
def _process_clone(line, recursive, depth, log):
    parts = shlex.split(line)
    if not parts:
        return log_message("Empty clone entry", log, 'error')

    url = parts[0].replace('\\', '')
    if not is_github_url(url):
        return log_message(f"Not a GitHub URL: {url}", log, 'warning')

    path, name = handle_path_and_filename(parts, url, is_git=True)
    current_dir = Path.cwd()

    try:
        if path:
            path.mkdir(parents=True, exist_ok=True)
            CD(path)

        cmd = _build_git_cmd(url, name, recursive, depth)
        _run_git(cmd, log)
    finally:
        CD(current_dir)

def _build_git_cmd(url, name, recursive, depth):
    cmd = ['git', 'clone']
    if depth > 0:
        cmd += ['--depth', str(depth)]
    if recursive:
        cmd.append('--recursive')
    cmd.append(url)
    if name:
        cmd.append(name)
    return ' '.join(cmd)

def _run_git(command, log):
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    while True:
        output = process.stdout.readline()
        if not output and process.poll() is not None:
            break
        output = output.strip()
        if not output:
            continue

        # Parse cloning progress
        if 'Cloning into' in output:
            repo = re.search(r"'(.+?)'", output)
            if repo:
                log_message(f"Cloning: \033[32m{repo.group(1)}\033[0m -> {command}", log)

        # Handle error messages
        if 'fatal' in output.lower():
            log_message(output, log, 'error')