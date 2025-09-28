"""
This is a modified `main.py` script from the `gradio-tunneling` library.
The script was rewritten specifically for sdAIgen (to get the tunneling URL)
"""

from typing import List, Optional, Tuple
from pathlib import Path
import subprocess
import platform
import argparse
import requests
import logging
import secrets
import atexit
import stat
import time
import sys
import os
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinaryManager:
    """Manages downloading and configuration of frpc binary"""
    VERSION = '0.2'
    BASE_URL = "https://cdn-media.huggingface.co/frpc-gradio-{version}/{binary_name}{extension}"

    def __init__(self):
        self.system = platform.system().lower()
        self.machine = self._normalize_architecture(platform.machine().lower())
        self.extension = '.exe' if os.name == 'nt' else ''

        self.binary_name = f"frpc_{self.system}_{self.machine}"
        self.binary_path = Path(__file__).parent / f"{self.binary_name}_v{self.VERSION}"

    @staticmethod
    def _normalize_architecture(arch: str) -> str:
        return 'amd64' if arch == 'x86_64' else arch

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

        logger.info('Downloading frpc binary...')
        response = requests.get(self.download_url)

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
        local_host: str,
        local_port: int,
        share_token: str,
        remote_server: Optional[str] = None
    ):
        self.local_host = local_host
        self.local_port = local_port
        self.share_token = share_token
        self.remote_host, self.remote_port = self._resolve_remote_server(remote_server)

        self.proc: Optional[subprocess.Popen] = None
        self.binary = BinaryManager()
        self.url: Optional[str] = None

    def _resolve_remote_server(self, server: Optional[str]) -> Tuple[str, int]:
        """Determines remote tunnel server address"""
        if server:
            host, port = server.split(':', 1)
            return host, int(port)

        response = requests.get(self.GRADIO_API)
        response.raise_for_status()
        data = response.json()[0]
        return data['host'], int(data['port'])

    def start(self) -> str:
        """Starts tunnel and returns public URL"""
        self.binary.download()
        self._launch_process()
        self.url = self._read_process_output()
        logger.info("Tunnel established at %s", self.url)
        return self.url

    def _launch_process(self):
        """Launches frpc process"""
        command = [
            str(self.binary.binary_path),
            'http',
            '-n', self.share_token,
            '-l', str(self.local_port),
            '-i', self.local_host,
            '--uc',
            '--sd', 'random',
            '--ue',
            '--server_addr', f"{self.remote_host}:{self.remote_port}",
            '--disable_log_color',
        ]

        self.proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        atexit.register(self.stop)

    def _read_process_output(self) -> str:
        """Reads process output to extract tunnel URL"""
        start_time = time.time()
        logs = []

        while True:
            if time.time() - start_time > self.TIMEOUT:
                self._handle_error(logs)

            line = self.proc.stdout.readline().strip()  # type: ignore
            if not line:
                continue

            logs.append(line)
            logger.debug(line)

            if 'start proxy success' in line:
                if match := re.search(r"start proxy success: (.+)", line):
                    return match.group(1)
                self._handle_error(logs)

            elif 'login to server failed' in line:
                self._handle_error(logs)

    def _handle_error(self, logs: List[str]):
        """Handles tunnel errors"""
        self.stop()
        logger.error("Tunnel failure logs:\n%s", '\n'.join(logs))
        raise RuntimeError(self.ERROR_MSG.format(logs='\n'.join(logs)))

    def stop(self):
        """Stops tunnel process"""
        if self.proc and self.proc.poll() != None:
            logger.info('Stopping tunnel...')
            self.proc.terminate()
            self.proc.wait()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Create application tunnel')
    parser.add_argument(
        'port',
        nargs='?',
        type=int,
        default=7860,
        help='Local port to expose (default: 7860)'
    )
    parser.add_argument(
        '--subdomain', '-s',
        type=str,
        help='Custom subdomain for the tunnel'
    )
    args = parser.parse_args()

    try:
        tunnel = Tunnel(
            local_host='127.0.0.1',
            local_port=args.port,
            share_token=args.subdomain or secrets.token_urlsafe(32)
        )
        url = tunnel.start()
        print(f"Tunnel URL: {url}")

        # Keep alive with interrupt handling
        while True:
            time.sleep(3600 * 24 * 3)
    except KeyboardInterrupt:
        logger.info('Interrupt received. Exiting...')
    except Exception as e:
        logger.error('Tunnel creation failed: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    main()