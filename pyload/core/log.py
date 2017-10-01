# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import locale
import logging
import logging.handlers
import os
import sys

from pyload.utils.check import ismodule
from pyload.utils.fs import makedirs

from pyload.__about__ import __package__

try:
    import colorlog
except ImportError:
    colorlog = None


class Logger(object):

    def __init__(self, core, debug=None, verbose=None, name=__package__):
        self.pyload = core

        if debug is None:
            self.debug = core.config.get('log', 'debug')
        else:
            self.debug = bool(debug)

        if verbose is None:
            self.verbose = core.config.get('log', 'verbose')
        else:
            self.verbose = bool(verbose)

        # Init logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)

        # Set console handler
        self._init_console()

        # Set syslog handler
        if core.config.get('log', 'syslog'):
            self._init_syslogger()

        # Set file handler
        if core.config.get('log', 'logfile'):
            self._init_filelogger()

    # TODO: Unicode encoding
    def _pack_msg(self, msg, messages, label=None, separator=' | '):
        if self.verbose:
            messages.insert(msg)
            text = separator.join(messages)
        else:
            text = msg
        return '{0} {1}'.format(label or '', text)

    def echo(self, level, msg, messages, **options):
        log = getattr(self.logger, level)
        log(self._pack_msg(*args, **options))

    def debug(self, msg, *messages, **options):
        self.logger.debug(self._pack_msg(msg, messages, **options))

    def info(self, msg, *messages, **options):
        self.logger.info(self._pack_msg(msg, messages, **options))

    def warning(self, msg, *messages, **options):
        self.logger.warning(self._pack_msg(msg, messages, **options))

    def error(self, msg, *messages, **options):
        self.logger.error(self._pack_msg(msg, messages, **options))

    def critical(self, msg, *messages, **options):
        self.logger.critical(self._pack_msg(msg, messages, **options))

    def _init_console(self):
        if self.pyload.config.get(
                'log', 'color_console') and ismodule('colorlog'):
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

    def _init_syslogger(self):
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

    def _init_filelogger(self):
        fmt = '%(asctime)s  %(levelname)-8s  %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'
        fileform = logging.Formatter(fmt, datefmt)

        logfile_folder = self.pyload.config.get('log', 'logfile_folder')
        makedirs(logfile_folder, exist_ok=True)

        logfile_name = self.pyload.config.get('log', 'logfile_name')
        logfile = os.path.join(logfile_folder, logfile_name)

        if self.pyload.config.get('log', 'rotate'):
            logfile_size = self.pyload.config.get('log', 'logfile_size') << 10
            max_logfiles = self.pyload.config.get('log', 'max_logfiles')
            filehdlr = logging.handlers.RotatingFileHandler(
                logfile, maxBytes=logfile_size, backupCount=max_logfiles,
                encoding=locale.getpreferredencoding(do_setlocale=False))
        else:
            filehdlr = logging.FileHandler(
                logfile, encoding=locale.getpreferredencoding(
                    do_setlocale=False))

        filehdlr.setFormatter(fileform)
        self.logger.addHandler(filehdlr)
