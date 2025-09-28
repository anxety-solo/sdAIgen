"""
Modified script for creating tunnels.
Originated from: https://raw.githubusercontent.com/cupang-afk/subprocess-tunnel/refs/heads/master/src/tunnel.py
Author: cupang-afk https://github.com/cupang-afk

This script has been modified specifically for the 'sdAIgen' project and may not be compatible with normal use.
Use the original script of the author cupang-afk.
"""


from typing import Callable, List, Optional, Tuple, TypedDict, Union
from threading import Event, Lock, Thread
from pathlib import Path
import subprocess
import logging
import socket
import shlex
import time
import re
import os


StrOrPath = Union[str, Path]
StrOrRegexPattern = Union[str, re.Pattern]
ListHandlersOrBool = Union[List[logging.Handler], bool]


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: '\033[36m',        # Cyan
        logging.INFO: '\033[32m',         # Green
        logging.WARNING: '\033[33m',      # Yellow
        logging.ERROR: '\033[31m',        # Red
        logging.CRITICAL: '\033[31;1m',   # Bold Red
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, '\033[0m')
        message = super().format(record)
        return f"\n{color}[{record.name}]:\033[0m {message}"


class FileFormatter(logging.Formatter):
    @staticmethod
    def strip_ansi_codes(text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def format(self, record):
        formatted_message = super().format(record)
        return self.strip_ansi_codes(formatted_message)


class TunnelDict(TypedDict):
    command: str
    pattern: re.Pattern
    name: str
    note: Optional[str]
    callback: Optional[Callable[[str, Optional[str], Optional[str]], None]]


class Tunnel:
    """
    A class for creating and managing tunnels.

    This class allows for the establishment of tunnels to redirect traffic through specified ports.
    It supports local port checking, process and thread management, as well as logging for debugging
    and monitoring tunnel operations.

    Attributes:
        port (int): The port on which the tunnel will be created.
        check_local_port (bool): Flag indicating whether to check the local port before creating the tunnel.
        debug (bool): Flag enabling debug mode, which outputs additional information to the logs.
        timeout (int): The timeout (in seconds) for operations related to the tunnel.
        propagate (bool): Flag indicating whether to propagate logs to the parent logger.
        log_handlers (List[logging.Handler]): List of log handlers for configuring log output.
        log_dir (StrOrPath): Directory for storing logs. If not specified, the current working directory is used.
        callback (Callable[[List[Tuple[str, Optional[str]]]], None]): A callback function that will be invoked with
            a list of URLs after the tunnel is created.

    Instance Attributes:
        _is_running (bool): Indicates whether the tunnel is currently running.
        urls (List[Tuple[str, Optional[str], Optional[str]]]): List of URLs associated with the tunnel,
            including the URL, note, and name of the tunnel.
        urls_lock (Lock): Mutex for safe access to the list of URLs, ensuring thread-safety.
        jobs (List[Thread]): List of threads associated with the tunnel, used for managing tunnel processes.
        processes (List[subprocess.Popen]): List of running subprocesses for managing tunnels.
        tunnel_list (List[TunnelDict]): List of dictionaries containing parameters for each tunnel added.
        stop_event (Event): Event used to signal the stopping of tunnel operations.
        printed (Event): Event indicating whether tunnel information has been printed to the console.
        logger (logging.Logger): Logger for recording information about the tunnel's operation, including
            errors and status updates.

    Exceptions:
        ValueError: Raised if the specified port is invalid or occupied.
        RuntimeError: Raised if the tunnel is already running or if an operation is attempted when the tunnel is not running.
    """

    def __init__(
        self,
        port: int,
        check_local_port: bool = True,
        debug: bool = False,
        timeout: int = 15,
        propagate: bool = False,
        log_handlers: ListHandlersOrBool = None,
        log_dir: StrOrPath = None,
        callback: Callable[[List[Tuple[str, Optional[str]]]], None] = None,
    ):
        """Initialize the Tunnel class with provided parameters"""
        self._is_running = False
        self.urls: List[Tuple[str, Optional[str], Optional[str]]] = []
        self.urls_lock = Lock()
        self.jobs: List[Thread] = []
        self.processes: List[subprocess.Popen] = []
        self.tunnel_list: List[TunnelDict] = []
        self.stop_event: Event = Event()
        self.printed = Event()
        self.port = port
        self.check_local_port = check_local_port
        self.debug = debug
        self.timeout = timeout
        self.log_handlers = log_handlers or []
        self.log_dir = Path(log_dir) if log_dir else Path.home() / 'tunnel_logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.callback = callback

        self.logger = self.setup_logger(propagate)

    def setup_logger(self, propagate: bool) -> logging.Logger:
        """Logger for the tunnel operations"""
        logger = logging.getLogger('TunnelHub')
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        logger.propagate = propagate

        if not propagate:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)

        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logger.level)
            stream_handler.setFormatter(ColoredFormatter('{message}', style='{'))
            logger.addHandler(stream_handler)

        log_file = self.log_dir / 'tunnelhub.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter("[%(asctime)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(file_handler)

        for handler in self.log_handlers:
            logger.addHandler(handler)

        return logger

    def is_command_available(self, command: str) -> bool:
        """Check if the specified command is available in the system PATH"""
        return any(
            os.access(os.path.join(path, command), os.X_OK)
            for path in os.environ['PATH'].split(os.pathsep)
        )

    def add_tunnel(self, *, command: str, pattern: StrOrRegexPattern, name: str,
                 note: str = None, callback: Callable[[str, Optional[str], Optional[str]], None] = None) -> None:
        """Add a new tunnel with the specified command, pattern, name, and optional note and callback"""
        cmd_name = command.split()[0]
        if not self.is_command_available(cmd_name):
            self.logger.warning(f"Skipping {name} - {cmd_name} not installed")
            return

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
        """Start the tunnel and its associated threads"""
        if self._is_running:
            raise RuntimeError('Tunnel is already running')

        self.__enter__()

        try:
            while not self.printed.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.warning('\033[33m⚠️  Keyboard Interrupt detected, stopping tunnel\033[0m')
            self.stop()

    def stop(self) -> None:
        """Stop the tunnel and clean up resources"""
        if not self._is_running:
            raise RuntimeError('Tunnel is not running')

        self.logger.info(f"💣 \033[32mTunnels:\033[0m \033[34m{self.get_tunnel_names()}\033[0m -> \033[31mKilled.\033[0m")
        self.stop_event.set()
        self.terminate_processes()
        self.join_threads()
        self.reset()

    def get_tunnel_names(self) -> str:
        """Get a comma-separated string of tunnel names"""
        return ', '.join(tunnel['name'] for tunnel in self.tunnel_list)

    def terminate_processes(self) -> None:
        """Terminate all running subprocesses associated with the tunnels"""
        for process in self.processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                self.logger.warning(f"Error terminating process: {str(e)}")
        self.processes.clear()

    def join_threads(self) -> None:
        """Wait for all threads associated with the tunnels to finish"""
        for job in self.jobs:
            job.join()

    def __enter__(self):
        """Enter the runtime context for the tunnel"""
        if self._is_running:
            raise RuntimeError('Tunnel is already running by another method')

        if not self.tunnel_list:
            raise ValueError('No tunnels added')

        print_job = Thread(target=self._print)
        print_job.start()
        self.jobs.append(print_job)

        for tunnel in self.tunnel_list:
            self.start_tunnel_thread(tunnel)

        self._is_running = True
        return self

    def start_tunnel_thread(self, tunnel: TunnelDict) -> None:
        """Start a new thread for the specified tunnel"""
        try:
            cmd = tunnel['command'].format(port=self.port)
            name = tunnel.get('name')
            tunnel_thread = Thread(target=self._run, args=(cmd, name))
            tunnel_thread.start()
            self.jobs.append(tunnel_thread)
        except Exception as e:
            self.logger.error(f"Failed to start tunnel {tunnel.get('name')}: {str(e)}")

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Exit the runtime context for the tunnel, stopping it"""
        self.stop()

    def reset(self) -> None:
        """Reset the tunnel state, clearing all stored URLs, jobs, and processes"""
        self.urls.clear()
        self.jobs.clear()
        self.processes.clear()
        self.stop_event.clear()
        self.printed.clear()
        self._is_running = False

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """Check if the specified port is currently in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(('localhost', port)) == 0
        except Exception:
            return False

    @staticmethod
    def wait_for_condition(condition: Callable[[], bool], *, interval: int = 1, timeout: int = 10) -> bool:
        """Wait for a condition to be true, checking at specified intervals"""
        start_time = time.time()
        elapsed_time = 0
        checks_count = 0
        timeout = max(1, timeout) if timeout is not None else None

        while True:
            if condition():
                return True

            checks_count += 1
            elapsed_time = time.time() - start_time

            if timeout is not None and elapsed_time >= timeout:
                return False

            next_interval = min(interval, (timeout - elapsed_time) / (checks_count + 1)) if timeout else interval
            time.sleep(next_interval)

    def _process_line(self, line: str) -> bool:
        """Process a line of output from the tunnel command to check for URLs"""
        for tunnel in self.tunnel_list:
            if self.extract_url(tunnel, line):
                return True
        return False

    def extract_url(self, tunnel: TunnelDict, line: str) -> bool:
        """Extract a URL from a line of output based on the tunnel's regex pattern"""
        regex = tunnel['pattern']
        matches = regex.search(line)

        if matches:
            link = matches.group().strip()
            link = link if link.startswith('http') else 'http://' + link
            note = tunnel.get('note')
            name = tunnel.get('name')
            callback = tunnel.get('callback')

            with self.urls_lock:
                self.urls.append((link, note, name))

            if callback:
                self.invoke_callback(callback, link, note, name)
            return True
        return False

    def invoke_callback(self, callback: Callable, link: str, note: Optional[str], name: Optional[str]) -> None:
        """Invoke the provided callback with the extracted URL and its associated metadata"""
        try:
            callback(link, note, name)
        except Exception:
            self.logger.error('An error occurred while invoking URL callback', exc_info=True)

    def _run(self, cmd: str, name: str) -> None:
        """Run the specified command in a subprocess, monitoring its output"""
        log_path = self.log_dir / f"tunnel_{name}.log"
        log_path.write_text('')  # Clear previous log file

        log = self.logger.getChild(name)        # Create a child logger for this tunnel
        self.setup_file_logging(log, log_path)  # Set up file logging for this tunnel

        try:
            self.wait_for_port_if_needed()
            cmd = shlex.split(cmd)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
            )
            self.processes.append(process)
            self.monitor_process_output(process, log)

        except Exception as e:
            log.error(f"Error in tunnel: {str(e)}", exc_info=self.debug)
        finally:
            for handler in log.handlers:
                handler.close()  # Close any handlers associated with this logger

    def setup_file_logging(self, log: logging.Logger, log_path: Path) -> None:
        """Set up file logging for the specified logger and log file path"""
        if not log.handlers:
            handler = logging.FileHandler(log_path, encoding='utf-8')
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(FileFormatter("[%(name)s]: %(message)s"))
            log.addHandler(handler)

    def wait_for_port_if_needed(self) -> None:
        """Wait for the specified port to be available if the check_local_port flag is set"""
        if self.check_local_port:
            self.wait_for_condition(
                lambda: self.is_port_in_use(self.port) or self.stop_event.is_set(),
                interval=1,
                timeout=None,
            )

    def monitor_process_output(self, process: subprocess.Popen, log: logging.Logger) -> None:
        """Monitor the output of the subprocess and process any lines received"""
        url_extracted = False
        while not self.stop_event.is_set() and process.poll() is None:
            line = process.stdout.readline()
            if not line:
                break
            if not url_extracted:
                url_extracted = self._process_line(line)
            log.debug(line.rstrip())

    def _print(self) -> None:
        """Print the collected tunnel URLs"""
        if self.check_local_port:
            self.wait_for_port_if_needed()

        if not self.wait_for_condition(
            lambda: len(self.urls) == len(self.tunnel_list) or self.stop_event.is_set(),
            interval=1,
            timeout=self.timeout,
        ):
            self.logger.warning('⏳ Timeout while getting tunnel URLs, print available URLs:')

        if not self.stop_event.is_set():
            self.display_urls()

    def display_urls(self) -> None:
        """Display the collected URLs in a formatted manner"""
        with self.urls_lock:
            width = 100
            tunnel_name_width = max(len(name) for _, _, name in self.urls) if self.urls else 6

            # Print the header
            print('\n\033[32m+' + '=' * (width - 2) + '+\033[0m\n')

            # Print each URL
            for url, note, name in self.urls:
                print(f"\033[32m 🔗 Tunnel \033[0m{name:<{tunnel_name_width}}  \033[32mURL: \033[0m{url} {note or ''}")

            # Print the footer
            print('\n\033[32m+' + '=' * (width - 2) + '+\033[0m\n')

            if self.callback:
                self.invoke_callback(self.callback, self.urls)

            self.printed.set()