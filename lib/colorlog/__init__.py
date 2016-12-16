"""A logging formatter for colored output"""

from __future__ import absolute_import

__all__ = ['ColoredFormatter', 'default_log_colors', 'escape_codes']

from colorlog.colorlog import (
    ColoredFormatter, default_log_colors, escape_codes)
