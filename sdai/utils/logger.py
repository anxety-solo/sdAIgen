""" Logger Module | by ANXETY """

from sdai.constants import COL


class Logger:
    """Colored console logger. Errors always shown; other levels require enabled=True"""
    _LEVEL_COLORS = {
        'debug':   'P',    # Purple
        'info':    'B',    # Blue
        'warning': 'Y',    # Yellow
        'error':   'R',    # Red
        'success': 'G',    # Green
    }

    def __init__(self, enabled: bool = True, debug: bool = False):
        self.enabled = enabled
        self.debug_enabled = debug

    def _write(self, message: str, level: str):
        if level == 'debug' and not self.debug_enabled:
            return
        if level != 'error' and not self.enabled:
            return

        color = getattr(COL, self._LEVEL_COLORS.get(level, 'X'))
        print(f">> {color}[{level.upper()}]:{COL.X} {message}")

    def debug(self, msg):   self._write(msg, 'debug')
    def info(self, msg):    self._write(msg, 'info')
    def warning(self, msg): self._write(msg, 'warning')
    def error(self, msg):   self._write(msg, 'error')
    def success(self, msg): self._write(msg, 'success')
