"""
Modified script for creating tunnels.

Originated from: https://github.com/gutris1/segsmaker/blob/main/script/SM/cupang.py
Author: gutris1 https://github.com/gutris1
"""

import logging
import re
import shlex
import socket
import time
import subprocess
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable, List, Optional, Tuple, TypedDict, Union, get_args


StrOrPath = Union[str, Path]
StrOrRegexPattern = Union[str, re.Pattern]
ListHandlersOrBool = Union[List[logging.Handler], bool]


class CustomLogFormat(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        names = record.name.split(".") if record.name else []
        if len(names) > 1:
            _, *names = names
            record.msg = f"[{' '.join(names)}] {record.msg}"
        return super().format(record)


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
        timeout: int = 30,
        propagate: bool = False,
        log_handlers: ListHandlersOrBool = None,
        log_dir: StrOrPath = Path.home(),
        callback: Callable[[List[Tuple[str, Optional[str]]]], None] = None,
    ):
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
        self.log_dir = log_dir or Path.cwd()
        self.callback = callback

        self.logger = self.setup_logger(propagate)

    def setup_logger(self, propagate: bool) -> logging.Logger:
        logger = logging.getLogger("Tunnel")
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        if not propagate:
            logger.propagate = False
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setLevel(logger.level)
                handler.setFormatter(CustomLogFormat("{message}", style="{"))
                logger.addHandler(handler)
        for handler in self.log_handlers:
            logger.addHandler(handler)
        return logger

    def add_tunnel(self, *, command: str, pattern: StrOrRegexPattern, name: str, note: str = None, callback: Callable[[str, Optional[str], Optional[str]], None] = None) -> None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        self.logger.debug(f"Adding tunnel {command=} {pattern=} {name=} {note=} {callback=}")
        self.tunnel_list.append({
            "command": command,
            "pattern": pattern,
            "name": name,
            "note": note,
            "callback": callback,
        })

    def start(self) -> None:
        if self._is_running:
            raise RuntimeError("Tunnel is already running")

        self.__enter__()

        try:
            while not self.printed.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.warning("Keyboard Interrupt detected, stopping tunnel")
            self.stop()

    def stop(self) -> None:
        if not self._is_running:
            raise RuntimeError("Tunnel is not running")

        self.logger.info(f"\n\033[32m💣 Tunnels:\033[0m \033[34m{self.get_tunnel_names()}\033[0m \033[31mKilled.\033[0m")
        self.stop_event.set()
        self.terminate_processes()
        self.join_threads()
        self.reset()

    def get_tunnel_names(self) -> str:
        return ', '.join(tunnel["name"] for tunnel in self.tunnel_list)

    def terminate_processes(self) -> None:
        for process in self.processes:
            while process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    self.handle_process_timeout(process)

    def handle_process_timeout(self, process: subprocess.Popen) -> None:
        process.kill()

    def join_threads(self) -> None:
        for job in self.jobs:
            job.join()

    def __enter__(self):
        if self._is_running:
            raise RuntimeError("Tunnel is already running by another method")

        if not self.tunnel_list:
            raise ValueError("No tunnels added")

        print_job = Thread(target=self._print)
        print_job.start()
        self.jobs.append(print_job)

        for tunnel in self.tunnel_list:
            self.start_tunnel_thread(tunnel)

        self._is_running = True
        return self

    def start_tunnel_thread(self, tunnel: TunnelDict) -> None:
        cmd = tunnel["command"]
        name = tunnel.get("name")
        tunnel_thread = Thread(target=self._run, args=(cmd.format(port=self.port),), kwargs={"name": name})
        tunnel_thread.start()
        self.jobs.append(tunnel_thread)

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop()

    def reset(self) -> None:
        self.urls.clear()
        self.jobs.clear()
        self.processes.clear()
        self.stop_event.clear()
        self.printed.clear()
        self._is_running = False

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """Check if the specified port is in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(("localhost", port)) == 0
        except Exception:
            return False

    @staticmethod
    def wait_for_condition(condition: Callable[[], bool], *, interval: int = 1, timeout: int = 10) -> bool:
        """Wait for the condition to be true until the specified timeout."""
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
        """Process a line of output to extract tunnel information."""
        for tunnel in self.tunnel_list:
            if self.extract_url(tunnel, line):
                return True
        return False

    def extract_url(self, tunnel: TunnelDict, line: str) -> bool:
        """Extract the URL from the line and invoke the callback if applicable."""
        regex = tunnel["pattern"]
        matches = regex.search(line)

        if matches:
            link = matches.group().strip()
            link = link if link.startswith("http") else "http://" + link
            note = tunnel.get("note")
            name = tunnel.get("name")
            callback = tunnel.get("callback")

            with self.urls_lock:
                self.urls.append((link, note, name))

            if callback:
                self.invoke_callback(callback, link, note, name)
            return True
        return False

    def invoke_callback(self, callback: Callable, link: str, note: Optional[str], name: Optional[str]) -> None:
        """Invoke the callback and handle any exceptions."""
        try:
            callback(link, note, name)
        except Exception:
            self.logger.error("An error occurred while invoking URL callback", exc_info=True)

    def _run(self, cmd: str, name: str) -> None:
        """Run the tunnel process and monitor its output."""
        log_path = Path(self.log_dir, f"tunnel_{name}.log")
        log_path.write_text("")  # Clear the log

        log = self.logger.getChild(name)
        self.setup_file_logging(log, log_path)

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

        except Exception:
            log.error(f"An error occurred while running the command: {cmd}", exc_info=True)
        finally:
            for handler in log.handlers:
                handler.close()

    def setup_file_logging(self, log: logging.Logger, log_path: Path) -> None:
        """Set up file logging for the specified logger."""
        if not log.handlers:
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            log.addHandler(handler)

    def wait_for_port_if_needed(self) -> None:
        """Wait for the port to be available if required."""
        if self.check_local_port:
            self.wait_for_condition(
                lambda: self.is_port_in_use(self.port) or self.stop_event.is_set(),
                interval=1,
                timeout=None,
            )

    def monitor_process_output(self, process: subprocess.Popen, log: logging.Logger) -> None:
        """Monitor the output of the tunnel process."""
        url_extracted = False
        while not self.stop_event.is_set() and process.poll() is None:
            line = process.stdout.readline()
            if not line:
                break
            if not url_extracted:
                url_extracted = self._process_line(line)
            log.debug(line.rstrip())

    def _print(self) -> None:
        """Print the tunnel URLs."""
        if self.check_local_port:
            self.wait_for_port_if_needed()

        if not self.wait_for_condition(
            lambda: len(self.urls) == len(self.tunnel_list) or self.stop_event.is_set(),
            interval=1,
            timeout=self.timeout,
        ):
            self.logger.warning("Timeout while getting tunnel URLs, print available URLs")

        if not self.stop_event.is_set():
            self.display_urls()

    def display_urls(self) -> None:
        """Display the collected URLs."""
        with self.urls_lock:
            print()  # space
            for url, note, name in self.urls:
                print(f"\033[32m 🔗 Tunnel \033[0m{name} \033[32mURL: \033[0m{url} {note if note else ''}")
            print()  # space

            if self.callback:
                self.invoke_callback(self.callback, self.urls)

            self.printed.set()

    def set_log_handlers(self, log_handlers: ListHandlersOrBool) -> None:
        """Set logging handlers for the tunnel logger."""
        if log_handlers is False:
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)
        elif isinstance(log_handlers, list):
            for handler in log_handlers:
                self.logger.addHandler(handler)