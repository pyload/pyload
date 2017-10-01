# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import locale
import logging
import logging.handlers
import os
import sys

from pyload.__about__ import __package__
from pyload.utils.check import ismodule
from pyload.utils.convert import to_str
from pyload.utils.fs import makedirs

try:
    import colorlog
except ImportError:
    colorlog = None


class Logger(object):

    DEFAULT_SEPARATOR = ' | '

    def __init__(self, core, debug=None, verbose=None, name=__package__):
        self.pyload = core

        if debug is None:
            debug = core.config.get('log', 'debug')

        if verbose is None:
            self.verbose = core.config.get('log', 'verbose')
        else:
            self.verbose = bool(verbose)

        # Init logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        # Set console handler
        if core.config.get('log', 'console'):
            self._init_console()

        # Set syslog handler
        if core.config.get('log', 'syslog'):
            self._init_syslog()

        # Set file handler
        if core.config.get('log', 'filelog'):
            self._init_filelog()

    def level(self):
        return self.logger.getEffectiveLevel()

    def log(self, level, msg, *msgs, **kwgs):
        label = kwgs.pop('label')
        sep = kwgs.pop('separator', self.DEFAULT_SEPARATOR)

        if self.verbose:
            msgs.insert(msg)
            body = sep.join(map(to_str, msgs))
        else:
            body = to_str(msg)

        header = to_str(label) if label else ''
        message = '[{0}] {1}'.format(header, body)

        log = getattr(self.logger, level)
        log(message, **kwgs)

    def debug(self, msg, *msgs, **kwgs):
        self.log('debug', msg, *msgs, **kwgs)

    def info(self, msg, *msgs, **kwgs):
        self.log('info', msg, *msgs, **kwgs)

    def warning(self, msg, *msgs, **kwgs):
        self.log('warning', msg, *msgs, **kwgs)

    def error(self, msg, *msgs, **kwgs):
        self.log('error', msg, *msgs, **kwgs)

    def critical(self, msg, *msgs, **kwgs):
        self.log('critical', msg, *msgs, **kwgs)

    def exception(self, msg, *msgs, **kwgs):
        self.log('exception', msg, *msgs, **kwgs)

    def _init_console(self):
        if self.pyload.config.get(
                'log', 'colorlog') and ismodule('colorlog'):
            fmt = '%(label)s %(levelname)-8s %(reset)s %(log_color)s%(asctime)s  %(message)s'
            datefmt = '%Y-%m-%d  %H:%M:%S'
            primary_colors = {
                'DEBUG': 'bold,cyan',
                'WARNING': 'bold,yellow',
                'ERROR': 'bold,red',
                'CRITICAL': 'bold,purple',
            }
            secondary_colors = {
                'label': {
                    'DEBUG': 'bold,white,bg_cyan',
                    'INFO': 'bold,white,bg_green',
                    'WARNING': 'bold,white,bg_yellow',
                    'ERROR': 'bold,white,bg_red',
                    'CRITICAL': 'bold,white,bg_purple',
                }
            }
            consoleform = colorlog.ColoredFormatter(
                fmt, datefmt, primary_colors,
                secondary_log_colors=secondary_colors)
        else:
            fmt = '%(asctime)s  %(levelname)-8s  %(message)s'
            datefmt = '%Y-%m-%d %H:%M:%S'
            consoleform = logging.Formatter(fmt, datefmt)

        consolehdlr = logging.StreamHandler(sys.stdout)
        consolehdlr.setFormatter(consoleform)
        self.logger.addHandler(consolehdlr)

    def _init_syslog(self):
        # try to mimic to normal syslog messages
        fmt = '%(asctime)s %(name)s: %(message)s'
        datefmt = '%b %e %H:%M:%S'
        syslogform = logging.Formatter(fmt, datefmt)
        syslogaddr = None

        syslog = self.pyload.config.get('log', 'syslog')
        if syslog == 'remote':
            syslog_host = self.pyload.config.get('log', 'syslog_host')
            syslog_port = self.pyload.config.get('log', 'syslog_port')
            syslogaddr = (syslog_host, syslog_port)
        else:
            syslog_folder = self.pyload.config.get('log', 'syslog_folder')
            if syslogaddr:
                syslogaddr = syslog_folder
            elif sys.platform == 'darwin':
                syslogaddr = '/var/run/syslog'
            elif os.name != 'nt':
                syslogaddr = '/dev/log'

        sysloghdlr = logging.handlers.SysLogHandler(syslogaddr)
        sysloghdlr.setFormatter(syslogform)
        self.logger.addHandler(sysloghdlr)

    def _init_filelog(self):
        fmt = '%(asctime)s  %(levelname)-8s  %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'
        fileform = logging.Formatter(fmt, datefmt)

        filelog_folder = self.pyload.config.get('log', 'filelog_folder')
        makedirs(filelog_folder, exist_ok=True)

        filelog_name = self.pyload.config.get('log', 'filelog_name')
        filelog = os.path.join(filelog_folder, filelog_name)

        if self.pyload.config.get('log', 'rotate'):
            filelog_size = self.pyload.config.get('log', 'filelog_size') << 10
            max_logfiles = self.pyload.config.get('log', 'max_logfiles')
            filehdlr = logging.handlers.RotatingFileHandler(
                filelog, maxBytes=filelog_size, backupCount=max_logfiles,
                encoding=locale.getpreferredencoding(do_setlocale=False))
        else:
            filehdlr = logging.FileHandler(
                filelog, encoding=locale.getpreferredencoding(
                    do_setlocale=False))

        filehdlr.setFormatter(fileform)
        self.logger.addHandler(filehdlr)
