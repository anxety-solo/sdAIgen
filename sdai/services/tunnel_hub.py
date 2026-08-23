"""
Tunnel management for creating subprocess-based tunnels.
Originated from: https://raw.githubusercontent.com/cupang-afk/subprocess-tunnel/refs/heads/master/src/tunnel.py
Author: cupang-afk https://github.com/cupang-afk

Modified specifically for the 'sdAIgen' project; may not be compatible with normal use. | by ANXETY
"""

import subprocess
import logging
import shutil
import socket
import signal
import shlex
import time
import os
import re

from threading import Event, Lock, Thread
from types import TracebackType
from typing import Callable
from pathlib import Path

# === SDAIGEN ===
from sdai.constants import COL


StrOrPath          = str | Path
StrOrRegexPattern  = str | re.Pattern
ListHandlersOrBool = list[logging.Handler] | bool

FILE_FORMAT   = "[%(asctime)s] [%(name)s]: %(message)s"
TUNNEL_FORMAT = "[%(name)s]: %(message)s"
DATE_FORMAT   = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    COLORS = {
        logging.DEBUG:    '\033[36m',   # Cyan
        logging.INFO:     '\033[32m',   # Green
        logging.WARNING:  '\033[33m',   # Yellow
        logging.ERROR:    '\033[31m',   # Red
        logging.CRITICAL: '\033[31;1m', # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        return f"\n{color}[{record.name}]:{self.RESET} {super().format(record)}"


class FileFormatter(logging.Formatter):
    """Formatter for file output (strips ANSI codes)"""
    ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def format(self, record: logging.LogRecord) -> str:
        return self.ANSI_RE.sub('', super().format(record))


class Tunnel:
    """Manage subprocess-based tunnels and collect their public URLs"""

    def __init__(
        self,
        port: int,
        check_local_port=True,
        check_command_available=False,
        debug=False,
        timeout=30,
        propagate=False,
        log_handlers: ListHandlersOrBool = None,
        log_dir: StrOrPath = None,
        callback: Callable[[list[tuple[str, str | None, str | None]]], None] = None,
    ):
        """
        Args:
            port: Local port on which the tunnels will be created.
            check_local_port: Wait for the local port to be available before starting.
            check_command_available: Skip tunnels whose command is not installed.
            debug: Enable debug mode for additional output.
            timeout: Maximum time to wait for the tunnels to start.
            propagate: Propagate log messages to the root logger.
            log_handlers: Extra logging handlers, or False to disable.
            log_dir: Directory to store tunnel log files.
            callback: Invoked with the collected URLs.
        """
        self.port = port
        self.check_local_port = check_local_port
        self.check_command_available = check_command_available
        self.debug = debug
        self.timeout = timeout
        self.log_handlers = log_handlers or []
        self.log_dir = Path(log_dir) if log_dir else Path.home() / 'tunnel_logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.callback = callback

        self.WINDOWS = os.name == 'nt'
        self.logger  = self._setup_logger(propagate)

        self.urls:        list[tuple[str, str | None, str | None]] = []
        self.urls_lock    = Lock()
        self.jobs:        list[Thread] = []
        self.processes:   list[subprocess.Popen] = []
        self.tunnel_list: list[dict] = []
        self.stop_event   = Event()
        self.printed      = Event()
        self._is_running  = False

    def _setup_logger(self, propagate: bool) -> logging.Logger:
        """Setup logger with colored console and file output"""
        logger = logging.getLogger('TunnelHub')
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        logger.propagate = propagate

        if not propagate:
            logger.handlers.clear()

        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console = logging.StreamHandler()
            console.setLevel(logger.level)
            console.setFormatter(ColoredFormatter('{message}', style='{'))
            logger.addHandler(console)

        file_handler = logging.FileHandler(self.log_dir / 'tunnelhub.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter(FILE_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(file_handler)

        if isinstance(self.log_handlers, list):
            for handler in self.log_handlers:
                logger.addHandler(handler)

        return logger

    def is_command_available(self, command: str) -> bool:
        """Check if command is available in system PATH"""
        return shutil.which(command.split()[0]) is not None

    def add_tunnel(
        self,
        *,
        command: str,
        pattern: StrOrRegexPattern,
        name: str,
        note: str = None,
        callback: Callable[[str, str | None, str | None], None] = None,
    ) -> None:
        """Add a tunnel configuration"""
        if self.check_command_available and not self.is_command_available(command):
            self.logger.warning(f"Skipping {name} - {command.split()[0]} not installed")
            return

        self.tunnel_list.append({
            'command':  command,
            'pattern':  pattern if isinstance(pattern, re.Pattern) else re.compile(pattern),
            'name':     name,
            'note':     note,
            'callback': callback,
        })

    def start(self) -> None:
        """Start the tunnel and wait for URLs"""
        if self._is_running:
            raise RuntimeError('Tunnel is already running')

        self.__enter__()
        try:
            while not self.printed.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.warning(f"{COL.Y}⚠️ Keyboard Interrupt detected, stopping tunnel{COL.X}")
            self.stop()

    def stop(self) -> None:
        """Stop all tunnels and cleanup"""
        if not self._is_running:
            raise RuntimeError('Tunnel is not running')

        self.logger.info(f"💣 {COL.G}Tunnels:{COL.X} {COL.B}{self._get_tunnel_names()}{COL.X} -> {COL.R}Killed.{COL.X}")
        self.stop_event.set()

        for process in self.processes:
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if self.WINDOWS:
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    process.kill()
                except Exception as exc:
                    self.logger.warning(f"Error terminating process: {exc}")

        for job in self.jobs:
            job.join()

        self.reset()

    def _get_tunnel_names(self) -> str:
        """Return comma-separated tunnel names"""
        return ', '.join(tunnel['name'] for tunnel in self.tunnel_list)

    def reset(self) -> None:
        """Reset internal state"""
        self.urls.clear()
        self.jobs.clear()
        self.processes.clear()
        self.stop_event.clear()
        self.printed.clear()
        self._is_running = False

    def __enter__(self) -> "Tunnel":
        if self._is_running:
            raise RuntimeError('Tunnel is already running by another method')
        if not self.tunnel_list:
            raise ValueError('No tunnels added')

        print_job = Thread(target=self._print, daemon=True)
        print_job.start()
        self.jobs.append(print_job)

        for tunnel in self.tunnel_list:
            cmd    = tunnel['command'].format(port=self.port)
            thread = Thread(target=self._run, args=(cmd, tunnel['name']), daemon=True)
            thread.start()
            self.jobs.append(thread)

        self._is_running = True
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, exc_tb: TracebackType | None):
        self.stop()

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """Check if port is in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(('localhost', port)) == 0
        except Exception:
            return False

    @staticmethod
    def wait_for_condition(condition: Callable[[], bool], *, interval=1, timeout: int = None) -> bool:
        """Wait for condition to be true, returning False on timeout"""
        start  = time.time()
        checks = 0

        if timeout is not None:
            timeout = max(1, timeout)

        while True:
            if condition():
                return True

            checks += 1
            if timeout is None:
                time.sleep(interval)
                continue

            elapsed = time.time() - start
            if elapsed >= timeout:
                return False
            time.sleep(min(interval, (timeout - elapsed) / (checks + 1)))

    def _process_line(self, line: str) -> bool:
        """Extract a tunnel URL from an output line"""
        for tunnel in self.tunnel_list:
            matches = tunnel['pattern'].search(line)
            if matches:
                link = matches.group().strip()
                link = link if link.startswith('http') else 'http://' + link

                with self.urls_lock:
                    self.urls.append((link, tunnel.get('note'), tunnel['name']))

                if tunnel.get('callback'):
                    try:
                        tunnel['callback'](link, tunnel.get('note'), tunnel['name'])
                    except Exception:
                        self.logger.error('An error occurred while invoking URL callback', exc_info=True)
                return True
        return False

    def _run(self, cmd: str, name: str) -> None:
        """Run a tunnel process and monitor its output"""
        log_path = self.log_dir / f"tunnel_{name}.log"
        log_path.write_text('', encoding='utf-8')  # Clear previous log

        log = self.logger.getChild(name)
        log.setLevel(logging.DEBUG)
        log.propagate = False
        log.handlers.clear()

        # Per-tunnel log + main tunnelhub.log
        for path, fmt in ((log_path, TUNNEL_FORMAT), (self.log_dir / 'tunnelhub.log', FILE_FORMAT)):
            handler = logging.FileHandler(path, encoding='utf-8')
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(FileFormatter(fmt, datefmt=DATE_FORMAT))
            log.addHandler(handler)

        try:
            if self.check_local_port:
                self.wait_for_condition(
                    lambda: self.is_port_in_use(self.port) or self.stop_event.is_set(),
                    interval=1,
                    timeout=None,
                )

            cmd = shlex.split(cmd) if not self.WINDOWS else cmd

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if self.WINDOWS else 0,
            )
            self.processes.append(process)

            url_extracted = False
            while not self.stop_event.is_set() and process.poll() is None:
                line = process.stdout.readline()
                if not line:
                    break
                if not url_extracted:
                    url_extracted = self._process_line(line)
                log.debug(line.rstrip())

        except Exception as exc:
            log.error(f"Error in tunnel: {exc}", exc_info=self.debug)
        finally:
            for handler in log.handlers:
                handler.close()

    def _print(self) -> None:
        """Print collected tunnel URLs"""
        if self.check_local_port:
            self.wait_for_condition(
                lambda: self.is_port_in_use(self.port) or self.stop_event.is_set(),
                interval=1,
                timeout=None,
            )

        # Wait for URLs
        if not self.wait_for_condition(
            lambda: len(self.urls) == len(self.tunnel_list) or self.stop_event.is_set(),
            interval=1,
            timeout=self.timeout,
        ):
            self.logger.warning('⏳ Timeout while getting tunnel URLs, print available URLs:')

        if not self.stop_event.is_set() and self.urls:
            with self.urls_lock:
                width = 100
                name_width = max(len(name) for _, _, name in self.urls)

                print(f"\n{COL.G}+{'=' * (width - 2)}+{COL.X}\n")
                for url, note, name in self.urls:
                    print(f"{COL.G} 🔗 Tunnel {COL.X}{name:<{name_width}}  {COL.G}URL: {COL.X}{url} {note or ''}")
                print(f"\n{COL.G}+{'=' * (width - 2)}+{COL.X}\n")

                if self.callback:
                    try:
                        self.callback(self.urls)
                    except Exception:
                        self.logger.error('An error occurred while invoking URLs callback', exc_info=True)

        if self.debug:
            failed = set(t['name'] for t in self.tunnel_list) - set(name for _, _, name in self.urls)
            if failed:
                self.logger.debug(f"Failed to get URLs for: {', '.join(failed)}")

        self.printed.set()
