"""The ColoredFormatter class."""

from __future__ import absolute_import

import logging
import collections
import sys

from colorlog.escape_codes import escape_codes, parse_colors

__all__ = ('escape_codes', 'default_log_colors', 'ColoredFormatter')

# The default colors to use for the debug levels
default_log_colors = {
    'DEBUG': 'white',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

# The default format to use for each style
default_formats = {
    '%': '%(log_color)s%(levelname)s:%(name)s:%(message)s',
    '{': '{log_color}{levelname}:{name}:{message}',
    '$': '${log_color}${levelname}:${name}:${message}'
}


class ColoredRecord(object):
    """
    Wraps a LogRecord and attempts to parse missing keys as escape codes.

    When the record is formatted, the logging library uses ``record.__dict__``
    directly - so this class replaced the dict with a ``defaultdict`` that
    checks if a missing key is an escape code.
    """

    class __dict(collections.defaultdict):
        def __missing__(self, name):
            try:
                return parse_colors(name)
            except Exception:
                raise KeyError("{} is not a valid record attribute "
                               "or color sequence".format(name))

    def __init__(self, record):
        # Replace the internal dict with one that can handle missing keys
        self.__dict__ = self.__dict()
        self.__dict__.update(record.__dict__)

        # Keep a refrence to the original refrence so ``__getattr__`` can
        # access functions that are not in ``__dict__``
        self.__record = record

    def __getattr__(self, name):
        return getattr(self.__record, name)


class ColoredFormatter(logging.Formatter):
    """
    A formatter that allows colors to be placed in the format string.

    Intended to help in creating more readable logging output.
    """

    def __init__(self, fmt=None, datefmt=None,
                 log_colors=None, reset=True, style='%',
                 secondary_log_colors=None):
        """
        Set the format and colors the ColoredFormatter will use.

        The ``fmt``, ``datefmt`` and ``style`` args are passed on to the
        ``logging.Formatter`` constructor.

        The ``secondary_log_colors`` argument can be used to create additional
        ``log_color`` attributes. Each key in the dictionary will set
        ``log_color_{key}``, using the value to select from a different
        ``log_colors`` set.

        :Parameters:
        - fmt (str): The format string to use
        - datefmt (str): A format string for the date
        - log_colors (dict):
            A mapping of log level names to color names
        - reset (bool):
            Implictly append a color reset to all records unless False
        - style ('%' or '{' or '$'):
            The format style to use. (*No meaning prior to Python 3.2.*)
        - secondary_log_colors (dict):
            Map secondary ``log_color`` attributes. (*New in version 2.6.*)
        """
        if fmt is None:
            if sys.version_info > (3, 2):
                fmt = default_formats[style]
            else:
                fmt = default_formats['%']

        if sys.version_info > (3, 2):
            super(ColoredFormatter, self).__init__(fmt, datefmt, style)
        elif sys.version_info > (2, 7):
            super(ColoredFormatter, self).__init__(fmt, datefmt)
        else:
            logging.Formatter.__init__(self, fmt, datefmt)

        self.log_colors = (
            log_colors if log_colors is not None else default_log_colors)
        self.secondary_log_colors = secondary_log_colors
        self.reset = reset

    def color(self, log_colors, name):
        """Return escape codes from a ``log_colors`` dict."""
        return parse_colors(log_colors.get(name, ""))

    def format(self, record):
        """Format a message from a record object."""
        record = ColoredRecord(record)
        record.log_color = self.color(self.log_colors, record.levelname)

        # Set secondary log colors
        if self.secondary_log_colors:
            for name, log_colors in self.secondary_log_colors.items():
                color = self.color(log_colors, record.levelname)
                setattr(record, name + '_log_color', color)

        # Format the message
        if sys.version_info > (2, 7):
            message = super(ColoredFormatter, self).format(record)
        else:
            message = logging.Formatter.format(self, record)

        # Add a reset code to the end of the message
        # (if it wasn't explicitly added in format str)
        if self.reset and not message.endswith(escape_codes['reset']):
            message += escape_codes['reset']

        return message
