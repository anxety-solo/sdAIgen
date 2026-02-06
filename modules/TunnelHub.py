"""
Modified script for creating tunnels.
Originated from: https://raw.githubusercontent.com/cupang-afk/subprocess-tunnel/refs/heads/master/src/tunnel.py
Author: cupang-afk https://github.com/cupang-afk

This script has been modified specifically for the 'sdAIgen' project and may not be compatible with normal use.
Use the original script of the author cupang-afk.
"""

import subprocess
import logging
import signal
import socket
import shlex
import time
import os
import re
from typing import Callable, List, Optional, Tuple, TypedDict, Union, get_args
from threading import Event, Lock, Thread
from pathlib import Path


StrOrPath = Union[str, Path]
StrOrRegexPattern = Union[str, re.Pattern]
ListHandlersOrBool = Union[List[logging.Handler], bool]


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    COLORS = {
        logging.DEBUG: '\033[36m',        # Cyan
        logging.INFO: '\033[32m',         # Green
        logging.WARNING: '\033[33m',      # Yellow
        logging.ERROR: '\033[31m',        # Red
        logging.CRITICAL: '\033[31;1m',   # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"\n{color}[{record.name}]:{self.RESET} {message}"


class FileFormatter(logging.Formatter):
    """Formatter for file output (strips ANSI codes)"""
    @staticmethod
    def strip_ansi_codes(text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def format(self, record: logging.LogRecord) -> str:
        formatted_message = super().format(record)
        return self.strip_ansi_codes(formatted_message)


class TunnelDict(TypedDict):
    command: str
    pattern: re.Pattern
    name: str
    note: Optional[str]
    callback: Optional[Callable[[str, Optional[str], Optional[str]], None]]


class Tunnel:
    def __init__(
        self,
        port: int,
        check_local_port: bool = True,
        check_command_available: bool = False,
        debug: bool = False,
        timeout: int = 30,
        propagate: bool = False,
        log_handlers: ListHandlersOrBool = None,
        log_dir: StrOrPath = None,
        callback: Callable[[List[Tuple[str, Optional[str], Optional[str]]]], None] = None,
    ):
        """
        Tunnel class for managing subprocess-based tunnels.

        Args:
            port (int): The local port on which the tunnels will be created.
            check_local_port (bool, optional): Flag to check if the local port is available.
            check_command_available (bool, optional): Flag to check if tunnel command is available in PATH.
            debug (bool, optional): Flag to enable debug mode for additional output.
            timeout (int, optional): Maximum time to wait for the tunnels to start.
            propagate (bool, optional): Flag to propagate log messages to the root logger.
            log_handlers (ListHandlersOrBool, optional): List of logging handlers or False to disable.
            log_dir (StrOrPath, optional): Directory to store tunnel log files.
            callback (Callable, optional): Callback when URLs are collected.
        """
        self._is_running = False
        self.urls: List[Tuple[str, Optional[str], Optional[str]]] = []
        self.urls_lock = Lock()
        self.jobs: List[Thread] = []
        self.processes: List[subprocess.Popen] = []
        self.tunnel_list: List[TunnelDict] = []
        self.stop_event = Event()
        self.printed = Event()

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
        self.logger = self._setup_logger(propagate)

    def _setup_logger(self, propagate: bool) -> logging.Logger:
        """Setup logger with colored console and file output"""
        logger = logging.getLogger('TunnelHub')
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        logger.propagate = propagate

        if not propagate:
            logger.handlers.clear()

        # Add console handler
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logger.level)
            console_handler.setFormatter(ColoredFormatter('{message}', style='{'))
            logger.addHandler(console_handler)

        tunnelhub_log = self.log_dir / 'tunnelhub.log'
        file_handler = logging.FileHandler(tunnelhub_log, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter("[%(asctime)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)

        # Add custom handlers
        if isinstance(self.log_handlers, list):
            for handler in self.log_handlers:
                logger.addHandler(handler)

        return logger

    @classmethod
    def with_tunnel_list(
        cls,
        port: int,
        tunnel_list: List[TunnelDict],
        check_local_port: bool = True,
        check_command_available: bool = False,
        debug: bool = False,
        timeout: int = 60,
        propagate: bool = False,
        log_handlers: ListHandlersOrBool = None,
        log_dir: StrOrPath = None,
        callback: Callable[[List[Tuple[str, Optional[str], Optional[str]]]], None] = None,
    ):
        """Create a Tunnel instance with a pre-defined list of tunnels"""
        if not tunnel_list or not all(
            isinstance(i, dict)
            and {'command', 'pattern', 'name'}.issubset(i)
            and isinstance(i['command'], str)
            and isinstance(i['pattern'], get_args(StrOrRegexPattern))
            and isinstance(i['name'], str)
            for i in tunnel_list
        ):
            raise ValueError(
                "tunnel_list must be a list of dictionaries with required key-value pairs:\n"
                "  command: str\n"
                "  pattern: StrOrRegexPattern\n"
                "  name: str\n"
                "optional key-value pairs:\n"
                "  note: str\n"
                "  callback: Callable[[str, str, str], None]"
            )

        instance = cls(
            port,
            check_local_port=check_local_port,
            check_command_available=check_command_available,
            debug=debug,
            timeout=timeout,
            propagate=propagate,
            log_handlers=log_handlers,
            log_dir=log_dir,
            callback=callback,
        )
        for tunnel in tunnel_list:
            instance.add_tunnel(**tunnel)
        return instance

    def _is_command_available(self, command: str) -> bool:
        """Check if command is available in system PATH"""
        cmd_name = command.split()[0]
        return any(
            os.access(os.path.join(path, cmd_name), os.X_OK)
            for path in os.environ.get('PATH', '').split(os.pathsep)
        )

    def add_tunnel(
        self,
        *,
        command: str,
        pattern: StrOrRegexPattern,
        name: str,
        note: str = None,
        callback: Callable[[str, Optional[str], Optional[str]], None] = None,
    ) -> None:
        """Add a tunnel configuration"""
        # Check command availability if enabled
        if self.check_command_available and not self._is_command_available(command):
            self.logger.warning(f"Skipping {name} - {command.split()[0]} not installed")
            return

        # Compile pattern if string
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        self.logger.debug(f"Adding tunnel {command=} {pattern=} {name=} {note=} {callback=}")

        self.tunnel_list.append({
            'command': command,
            'pattern': pattern,
            'name': name,
            'note': note,
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
            self.logger.warning('\033[33m⚠️ Keyboard Interrupt detected, stopping tunnel\033[0m')
            self.stop()

    def stop(self) -> None:
        """Stop all tunnels and cleanup"""
        if not self._is_running:
            raise RuntimeError('Tunnel is not running')

        self.logger.info(f"💣 \033[32mTunnels:\033[0m \033[34m{self._get_tunnel_names()}\033[0m -> \033[31mKilled.\033[0m")
        self.stop_event.set()

        # Terminate processes
        for process in self.processes:
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if self.WINDOWS:
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    process.kill()
                except Exception as e:
                    self.logger.warning(f"Error terminating process: {str(e)}")

        for job in self.jobs:
            job.join()

        self.reset()

    def _get_tunnel_names(self) -> str:
        """Get comma-separated tunnel names"""
        return ', '.join(tunnel['name'] for tunnel in self.tunnel_list)

    def reset(self) -> None:
        """Reset internal state"""
        self.urls.clear()
        self.jobs.clear()
        self.processes.clear()
        self.stop_event.clear()
        self.printed.clear()
        self._is_running = False

    def get_port(self) -> int:
        return self.port

    def __enter__(self):
        if self._is_running:
            raise RuntimeError('Tunnel is already running by another method')
        if not self.tunnel_list:
            raise ValueError('No tunnels added')

        # Start print job
        print_job = Thread(target=self._print, daemon=True)
        print_job.start()
        self.jobs.append(print_job)

        # Start tunnel jobs
        for tunnel in self.tunnel_list:
            cmd = tunnel['command'].format(port=self.port)
            name = tunnel['name']
            tunnel_thread = Thread(target=self._run, args=(cmd, name), daemon=True)
            tunnel_thread.start()
            self.jobs.append(tunnel_thread)

        self._is_running = True
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
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
    def wait_for_condition(
        condition: Callable[[], bool], *, interval: int = 1, timeout: int = None
    ) -> bool:
        """Wait for condition to be true"""
        start_time = time.time()
        checks_count = 0

        if timeout is not None:
            timeout = max(1, timeout)

        while True:
            if condition():
                return True

            checks_count += 1

            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                next_interval = min(interval, (timeout - elapsed) / (checks_count + 1))
            else:
                next_interval = interval

            time.sleep(next_interval)

    def _process_line(self, line: str) -> bool:
        """Process output line to extract URL"""
        for tunnel in self.tunnel_list:
            matches = tunnel['pattern'].search(line)
            if matches:
                link = matches.group().strip()
                link = link if link.startswith('http') else 'http://' + link

                with self.urls_lock:
                    self.urls.append((link, tunnel.get('note'), tunnel['name']))

                # Invoke individual callback
                if tunnel.get('callback'):
                    try:
                        tunnel['callback'](link, tunnel.get('note'), tunnel['name'])
                    except Exception:
                        self.logger.error('An error occurred while invoking URL callback', exc_info=True)

                return True
        return False

    def _run(self, cmd: str, name: str) -> None:
        """Run tunnel process"""
        log_path = self.log_dir / f"tunnel_{name}.log"
        log_path.write_text('')  # Clear previous log

        # Setup child logger
        log = self.logger.getChild(name)
        log.setLevel(logging.DEBUG)
        log.propagate = False
        log.handlers.clear()

        # Add file handler for individual tunnel log
        tunnel_file_handler = logging.FileHandler(log_path, encoding='utf-8')
        tunnel_file_handler.setLevel(logging.DEBUG)
        tunnel_file_handler.setFormatter(FileFormatter("[%(name)s]: %(message)s"))
        log.addHandler(tunnel_file_handler)

        # Add file handler for main tunnelhub.log (to include all tunnel logs)
        main_file_handler = logging.FileHandler(self.log_dir / 'tunnelhub.log', encoding='utf-8')
        main_file_handler.setLevel(logging.DEBUG)
        main_file_handler.setFormatter(FileFormatter("[%(asctime)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        log.addHandler(main_file_handler)

        try:
            if self.check_local_port:
                self.wait_for_condition(
                    lambda: self.is_port_in_use(self.port) or self.stop_event.is_set(),
                    interval=1,
                    timeout=None,
                )

            # Start process
            if not self.WINDOWS:
                cmd = shlex.split(cmd)

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

            # Monitor output
            url_extracted = False
            while not self.stop_event.is_set() and process.poll() is None:
                line = process.stdout.readline()
                if not line:
                    break

                if not url_extracted:
                    url_extracted = self._process_line(line)

                log.debug(line.rstrip())

        except Exception as e:
            log.error(f"Error in tunnel: {str(e)}", exc_info=self.debug)
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

        # Display URLs
        if not self.stop_event.is_set() and self.urls:
            with self.urls_lock:
                width = 100
                tunnel_name_width = max(len(name) for _, _, name in self.urls) if self.urls else 6

                print('\n\033[32m+' + '=' * (width - 2) + '+\033[0m\n')
                for url, note, name in self.urls:
                    print(f"\033[32m 🔗 Tunnel \033[0m{name:<{tunnel_name_width}}  \033[32mURL: \033[0m{url} {note or ''}")
                print('\n\033[32m+' + '=' * (width - 2) + '+\033[0m\n')

                # Invoke global callback
                if self.callback:
                    try:
                        self.callback(self.urls)
                    except Exception:
                        self.logger.error('An error occurred while invoking URLs callback', exc_info=True)

        # Log failed tunnels in debug mode
        if self.debug:
            failed = set(t['name'] for t in self.tunnel_list) - set(name for _, _, name in self.urls)
            if failed:
                self.logger.debug(f"Failed to get URLs for: {', '.join(failed)}")

        self.printed.set()