"""
Modified script for creating tunnels.

Original author: gutris1
Author's GitHub: https://github.com/gutris1
"""

import logging
import os
import re
import shlex
import signal
import socket
import time
import subprocess
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Callable, List, Optional, Tuple, TypedDict, Union


StrOrPath = Union[str, Path]
StrOrRegexPattern = Union[str, re.Pattern]


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
    callback: Optional[
        Callable[[str, Optional[str], Optional[str]], None]
    ]  # (url, note, name) -> None


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
        _is_running (bool): Indicates whether the tunnel is running.
        urls (List[Tuple[str, Optional[str], Optional[str]]]): List of URLs associated with the tunnel.
        urls_lock (Lock): Mutex for safe access to the list of URLs.
        jobs (List[Thread]): List of threads associated with the tunnel.
        processes (List[subprocess.Popen]): List of running processes for managing tunnels.
        tunnel_list (List[TunnelDict]): List of dictionaries containing tunnel parameters.
        stop_event (Event): Event for stopping the tunnel operation.
        printed (Event): Event indicating whether tunnel information has been printed.
        logger (logging.Logger): Logger for recording information about the tunnel's operation.

    Exceptions:
        ValueError: Raised if the specified port is invalid or occupied.
    """
    def __init__(
        self,
        port: int,
        check_local_port: bool = True,
        debug: bool = False,
        timeout: int = 30,    # default - 60 sec
        propagate: bool = False,
        log_handlers: List[logging.Handler] = None,
        log_dir: StrOrPath = Path.home(),    # default - None
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
        self.log_handlers = log_handlers
        self.log_dir = log_dir or os.getcwd()
        self.callback = callback

        self.logger = logging.getLogger("Tunnel")
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        if not propagate:
            self.logger.propagate = False
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setLevel(self.logger.level)
                handler.setFormatter(CustomLogFormat("{message}", style="{"))
                self.logger.addHandler(handler)
        if self.log_handlers:
            for i in self.log_handlers:
                self.logger.addHandler(i)

        self.WINDOWS = os.name == "nt"

    def add_tunnel(
        self,
        *,
        command: str,
        pattern: StrOrRegexPattern,
        name: str,
        note: str = None,
        callback: Callable[[str, Optional[str], Optional[str]], None] = None,
    ) -> None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        log = self.logger
        log.debug(f"Adding tunnel {command=} {pattern=} {name=} {note=} {callback=}")
        self.tunnel_list.append(
            dict(
                command=command,
                pattern=pattern,
                name=name,
                note=note,
                callback=callback,
            )
        )

    def start(self) -> None:
        if self._is_running:
            raise RuntimeError("Tunnel is already running")

        log = self.logger
        self.__enter__()

        try:
            while not self.printed.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            log.warning("Keyboard Interrupt detected, stopping tunnel")
            self.stop()

    def stop(self) -> None:
        if not self._is_running:
            raise RuntimeError("Tunnel is not running")

        log = self.logger
        self.stop_event.set()
        tunnel_names = ', '.join(tunnel["name"] for tunnel in self.tunnel_list)
        log.info(f"\n\033[32m💣 Tunnels:\033[0m \033[34m{tunnel_names}\033[0m \033[31mKilled.\033[0m")

        for process in self.processes:
            while process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    if self.WINDOWS:
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                        process.send_signal(signal.CTRL_C_EVENT)
                    process.kill()

        for job in self.jobs:
            job.join()

        self.reset()

    def __enter__(self):
        if self._is_running:
            raise RuntimeError("Tunnel is already running by another method")

        if not self.tunnel_list:
            raise ValueError("No tunnels added")

        log = self.logger
        self.tunnel_names = []

        print_job = Thread(target=self._print)
        print_job.start()
        self.jobs.append(print_job)

        for tunnel in self.tunnel_list:
            cmd = tunnel["command"]
            name = tunnel.get("name")
            self.tunnel_names.append(name)
            tunnel_thread = Thread(
                target=self._run,
                args=(cmd.format(port=self.port),),
                kwargs={"name": name},
            )
            tunnel_thread.start()
            self.jobs.append(tunnel_thread)

        self._is_running = True
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stop()

    def reset(self) -> None:
        self.urls = []
        self.jobs = []
        self.processes = []
        self.stop_event.clear()
        self.printed.clear()
        self._is_running = False

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        """
        Check if the specified port is in use.

        Args:
            port (int): The port to check.

        Returns:
            bool: `True` if the port is in use, `False` otherwise.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(("localhost", port)) == 0
        except Exception:
            return False

    @staticmethod
    def wait_for_condition(
        condition: Callable[[], bool], *, interval: int = 1, timeout: int = 10
    ) -> bool:
        """
        Wait for the condition to be true until the specified timeout.

        Mostly for internal use but can be used for anything else.

        Args:
            condition (Callable[[], bool]): The condition to check.
            interval (int, optional): The interval (in seconds) between condition checks.
            timeout (int, optional): Maximum time to wait for the condition. `None` for no timeout.

        Returns:
            bool: `True` if the condition is met, `False` if timeout is reached.
        """
        start_time = time.time()

        # Initialize variables to track elapsed time and number of checks
        elapsed_time = 0
        checks_count = 0

        # Prevent zero or negative timeout
        if timeout is not None:
            timeout = max(1, timeout)

        while True:
            if condition():
                return True

            checks_count += 1

            if timeout is not None:
                elapsed_time = time.time() - start_time
                remaining_time = timeout - elapsed_time

                # If remaining time is non-positive, return False (timeout occurred)
                if remaining_time <= 0:
                    return False

                # Adjust the interval to respect the remaining time
                # and distribute it evenly among the remaining checks
                next_interval = min(interval, remaining_time / (checks_count + 1))
            else:
                next_interval = interval

            time.sleep(next_interval)

    def _process_line(self, line: str) -> bool:
        """
        Process a line of output to extract tunnel information.

        Args:
            line (str): A line of output from the tunnel process.

        Returns:
            bool: True if a URL is extracted, False otherwise.
        """
        for tunnel in self.tunnel_list:
            note = tunnel.get("note")
            name = tunnel.get("name")
            callback = tunnel.get("callback")
            regex = tunnel["pattern"]
            matches = regex.search(line)

            if matches:
                link = matches.group().strip()
                link = link if link.startswith("http") else "http://" + link
                with self.urls_lock:
                    self.urls.append((link, note, name))
                if callback:
                    try:
                        callback(link, note, name)
                    except Exception:
                        self.logger.error(
                            "An error occurred while invoking URL callback",
                            exc_info=True,
                        )
                return True
        return False

    def _run(self, cmd: str, name: str) -> None:
        """
        Run the tunnel process and monitor its output.

        Args:
            cmd (str): The command to execute for the tunnel.
            name (str): Name of the tunnel.
        """
        log_path = Path(self.log_dir, f"tunnel_{name}.log")
        log_path.write_text("")  # Clear the log

        log = self.logger.getChild(name)
        if not log.handlers:
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            log.addHandler(handler)

        try:
            if self.check_local_port:
                self.wait_for_condition(
                    lambda: self.is_port_in_use(self.port) or self.stop_event.is_set(),
                    interval=1,
                    timeout=None,
                )
            if not self.WINDOWS:
                cmd = shlex.split(cmd)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if self.WINDOWS
                else 0,
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

        except Exception:
            log.error(
                f"An error occurred while running the command: {cmd}", exc_info=True
            )
        finally:
            for handler in log.handlers:
                handler.close()

    def _print(self) -> None:
        """
        Print the tunnel URLs.
        """
        log = self.logger
        D = ', '.join(tunnel["name"] for tunnel in self.tunnel_list)

        if self.check_local_port:
            self.wait_for_condition(
                lambda: self.is_port_in_use(self.port) or self.stop_event.is_set(),
                interval=1,
                timeout=None,
            )
            if not self.stop_event.is_set():
                pass

        if not self.wait_for_condition(
            lambda: len(self.urls) == len(self.tunnel_list) or self.stop_event.is_set(),
            interval=1,
            timeout=self.timeout,
        ):
            log.warning("Timeout while getting tunnel URLs, print available URLs")

        if not self.stop_event.is_set():
            with self.urls_lock:
                print()   # space
                for url, note, name in self.urls:
                    print(f"\033[32m 🔗 Tunnel \033[0m{name} \033[32mURL: \033[0m{url} {note if note else ''}")
                print()   # space

                if self.callback:
                    try:
                        self.callback(self.urls)
                    except Exception:
                        log.error(
                            "An error occurred while invoking URLs callback",
                            exc_info=True,
                        )
            self.printed.set()