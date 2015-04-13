"""A logging formatter for colored output."""

from __future__ import absolute_import

from colorlog.colorlog import (
    ColoredFormatter, escape_codes, default_log_colors)

from colorlog.logging import (
    basicConfig, root, getLogger, log,
    debug, info, warning, error, exception, critical)

__all__ = ('ColoredFormatter', 'default_log_colors', 'escape_codes',
           'basicConfig', 'root', 'getLogger', 'debug', 'info', 'warning',
           'error', 'exception', 'critical', 'log', 'exception')
