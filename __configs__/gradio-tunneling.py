from typing import List, Optional, Tuple, Dict
from pathlib import Path

import subprocess
import threading
import platform
import argparse
import requests
import logging
import secrets
import signal
import select
import atexit
import queue
import stat
import time
import sys
import re
import os


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global registry of active tunnels
ACTIVE_TUNNELS: Dict[str, 'Tunnel'] = {}
TUNNELS_LOCK = threading.Lock()


class BinaryManager:
    """Manages downloading and configuration of frpc binary"""
    VERSION = "0.2"
    BASE_URL = "https://cdn-media.huggingface.co/frpc-gradio-{version}/{binary_name}{extension}"

    def __init__(self):
        self.system = platform.system().lower()
        self.machine = self._normalize_architecture(platform.machine().lower())
        self.extension = ".exe" if os.name == "nt" else ""

        self.binary_name = f"frpc_{self.system}_{self.machine}"
        self.binary_path = Path(__file__).parent / f"{self.binary_name}_v{self.VERSION}"

    @staticmethod
    def _normalize_architecture(arch: str) -> str:
        return "amd64" if arch == "x86_64" else arch

    @property
    def download_url(self) -> str:
        return self.BASE_URL.format(
            version=self.VERSION,
            binary_name=self.binary_name,
            extension=self.extension
        )

    def download(self):
        """Downloads and configures binary if needed"""
        if self.binary_path.exists():
            return

        logger.info("Downloading frpc binary...")
        response = requests.get(self.download_url, timeout=30)

        if response.status_code == 403:
            raise OSError(f"Unsupported platform: {platform.uname()}")

        response.raise_for_status()

        self.binary_path.write_bytes(response.content)
        self.binary_path.chmod(self.binary_path.stat().st_mode | stat.S_IEXEC)


class Tunnel:
    """Manages application tunnel lifecycle"""
    TIMEOUT = 30
    ERROR_MSG = "Failed to create share URL. Logs:\n{logs}"
    GRADIO_API = "https://api.gradio.app/v2/tunnel-request"

    def __init__(
        self,
        tunnel_id: str,
        local_host: str,
        local_port: int,
        share_token: str,
        remote_server: Optional[str] = None
    ):
        self.tunnel_id = tunnel_id
        self.local_host = local_host
        self.local_port = local_port
        self.share_token = share_token
        self.remote_host, self.remote_port = self._resolve_remote_server(remote_server)

        self.proc: Optional[subprocess.Popen] = None
        self.binary = BinaryManager()
        self.url: Optional[str] = None
        self.log_queue = queue.Queue()
        self.log_thread: Optional[threading.Thread] = None
        self.alive = threading.Event()
        self.alive.set()

        # Register the tunnel
        with TUNNELS_LOCK:
            ACTIVE_TUNNELS[self.tunnel_id] = self

    def _resolve_remote_server(self, server: Optional[str]) -> Tuple[str, int]:
        """Determines remote tunnel server address"""
        if server:
            host, port = server.split(":", 1)
            return host, int(port)

        response = requests.get(self.GRADIO_API, timeout=10)
        response.raise_for_status()
        data = response.json()[0]
        return data["host"], int(data["port"])

    def start(self) -> str:
        """Starts tunnel and returns public URL"""
        self.binary.download()
        self._launch_process()
        self.url = self._wait_for_tunnel_ready()
        logger.info("Tunnel %s established at %s", self.tunnel_id, self.url)
        return self.url

    def _launch_process(self):
        """Launches frpc process"""
        command = [
            str(self.binary.binary_path),
            "http",
            "-n", self.share_token,
            "-l", str(self.local_port),
            "-i", self.local_host,
            "--uc",
            "--sd", "random",
            "--ue",
            "--server_addr", f"{self.remote_host}:{self.remote_port}",
            "--disable_log_color",
        ]

        self.proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,  # Line-buffered
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Start a thread to read the logs
        self.log_thread = threading.Thread(
            target=self._read_logs,
            daemon=True,
            name=f"LogReader-{self.tunnel_id}"
        )
        self.log_thread.start()

        atexit.register(self.stop)

    def _wait_for_tunnel_ready(self) -> str:
        """Waits for tunnel to become ready and returns URL"""
        start_time = time.time()
        logs = []

        while self.alive.is_set():
            # Startup timeout
            if time.time() - start_time > self.TIMEOUT:
                self._handle_error(logs, "Tunnel startup timeout")

            try:
                # Collect timeout logs
                line = self.log_queue.get(timeout=1)
                logs.append(line)
                logger.debug("[%s] %s", self.tunnel_id, line)

                # Check for a successful launch
                if "start proxy success" in line:
                    if match := re.search(r"start proxy success: (.+)", line):
                        return match.group(1)
                    self._handle_error(logs, "Failed to parse tunnel URL")

                elif "login to server failed" in line:
                    self._handle_error(logs, "Login to server failed")

            except queue.Empty:
                # Check the status of the process
                if self.proc and self.proc.poll() is not None:
                    self._handle_error(logs, f"Process exited with code {self.proc.returncode}")

        self._handle_error(logs, "Tunnel stopped unexpectedly")

    def _read_logs(self):
        """Continuously reads logs from process output"""
        while self.alive.is_set() and self.proc and self.proc.stdout:
            # Use select for non-blocking reading
            if select.select([self.proc.stdout], [], [], 0.5)[0]:
                line = self.proc.stdout.readline().strip()
                if line:
                    self.log_queue.put(line)

            # Check that the process is complete
            if self.proc.poll() is not None:
                logger.warning("[%s] Process terminated", self.tunnel_id)
                self.alive.clear()
                break

    def _handle_error(self, logs: List[str], message: str):
        """Handles tunnel errors"""
        logger.error("Tunnel %s failed: %s", self.tunnel_id, message)
        self.stop()
        full_logs = "\n".join(logs)
        logger.error("Failure logs:\n%s", full_logs)
        raise RuntimeError(f"{self.ERROR_MSG}\n{message}\nLogs:\n{full_logs}")

    def stop(self):
        """Stops tunnel process and cleans up"""
        if not self.alive.is_set():
            return

        self.alive.clear()
        logger.info("Stopping tunnel %s...", self.tunnel_id)

        if self.proc:
            # Smooth completion of the process
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            finally:
                self.proc = None

        # Clear the log queue
        while not self.log_queue.empty():
            self.log_queue.get_nowait()

        # Delete from the registry
        with TUNNELS_LOCK:
            if self.tunnel_id in ACTIVE_TUNNELS:
                del ACTIVE_TUNNELS[self.tunnel_id]

        # Unregister atexit
        atexit.unregister(self.stop)
        logger.info("Tunnel %s stopped", self.tunnel_id)

    def is_alive(self) -> bool:
        """Checks if tunnel is still running"""
        return self.alive.is_set() and self.proc and self.proc.poll() is None


def stop_all_tunnels():
    """Gracefully stops all active tunnels"""
    logger.info("Stopping all active tunnels...")
    with TUNNELS_LOCK:
        tunnels = list(ACTIVE_TUNNELS.values())

    for tunnel in tunnels:
        try:
            tunnel.stop()
        except Exception as e:
            logger.error("Error stopping tunnel %s: %s", tunnel.tunnel_id, e)


def generate_tunnel_id(port: int) -> str:
    """Generates unique tunnel ID based on port"""
    return f"tunnel_{port}_{int(time.time())}"


def monitor_tunnels():
    """Monitors active tunnels and restarts if needed"""
    while True:
        with TUNNELS_LOCK:
            tunnels = list(ACTIVE_TUNNELS.values())

        all_alive = True
        for tunnel in tunnels:
            if not tunnel.is_alive():
                logger.warning("Tunnel %s is down, restarting...", tunnel.tunnel_id)
                try:
                    tunnel.start()
                    logger.info("Tunnel %s restarted successfully", tunnel.tunnel_id)
                except Exception as e:
                    logger.error("Failed to restart tunnel %s: %s", tunnel.tunnel_id, e)
                    all_alive = False

        # If all tunnels are working, wait longer
        sleep_time = 10 if all_alive else 2
        time.sleep(sleep_time)


def main():
    """CLI entry point with multi-tunnel support"""
    def sigint_handler(signum, frame):
        logger.info("Interrupt received. Stopping tunnels...")
        stop_all_tunnels()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description="Create application tunnels")
    parser.add_argument(
        "ports",
        nargs="+",
        type=int,
        default=[7860],
        help="Local ports to expose (default: 7860)"
    )
    parser.add_argument(
        "--subdomains", "-s",
        nargs="+",
        type=str,
        help="Custom subdomains for tunnels (one per port)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    args = parser.parse_args()

    logger.setLevel(args.log_level)

    # Register the global stop handler
    atexit.register(stop_all_tunnels)

    if args.subdomains and len(args.subdomains) != len(args.ports):
        logger.error("Number of subdomains must match number of ports")
        sys.exit(1)

    tunnels = {}

    try:
        # Start the tunnels
        for i, port in enumerate(args.ports):
            tunnel_id = generate_tunnel_id(port)
            subdomain = args.subdomains[i] if args.subdomains else secrets.token_urlsafe(16)

            tunnel = Tunnel(
                tunnel_id=tunnel_id,
                local_host="127.0.0.1",
                local_port=port,
                share_token=subdomain
            )

            url = tunnel.start()
            tunnels[port] = url
            print(f"Port {port}: {url}")

        # Run monitoring in a separate thread
        monitor_thread = threading.Thread(
            target=monitor_tunnels,
            daemon=True,
            name="TunnelMonitor"
        )
        monitor_thread.start()

        print("\nActive tunnels:")
        for port, url in tunnels.items():
            print(f"  - Port {port}: {url}")
        print("\nPress Ctrl+C to exit...")

        while True:
            time.sleep(3600)

    except Exception as e:
        logger.exception("Tunnel creation failed")
        sys.exit(1)
    finally:
        stop_all_tunnels()


if __name__ == "__main__":
    main()