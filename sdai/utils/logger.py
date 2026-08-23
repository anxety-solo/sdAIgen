""" Logger Module | by ANXETY """

# === SDAIGEN ===
from sdai.constants import COL


class Logger:
    """Colored console logger. Errors always shown; other levels require enabled=True"""
    LEVEL_COLORS = {
        'debug':   'P',    # Purple
        'info':    'B',    # Blue
        'warning': 'Y',    # Yellow
        'error':   'R',    # Red
        'success': 'G',    # Green
    }

    def __init__(self, enabled=True, debug=False):
        self.enabled = enabled
        self.debug_enabled = debug

    def _write(self, message: str, level: str):
        if level == 'debug' and not self.debug_enabled:
            return
        if level != 'error' and not self.enabled:
            return

        color = getattr(COL, self.LEVEL_COLORS.get(level, 'X'))
        print(f">> {color}[{level.upper()}]:{COL.X} {message}")

    def debug(self, msg: str):   self._write(msg, 'debug')
    def info(self, msg: str):    self._write(msg, 'info')
    def warning(self, msg: str): self._write(msg, 'warning')
    def error(self, msg: str):   self._write(msg, 'error')
    def success(self, msg: str): self._write(msg, 'success')
