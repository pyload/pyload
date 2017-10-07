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


class LoggerFactory(object):

    def __new__(cls, core, debug, name=__package__):
        config = core.config

        # Init logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG if debug else logging.INFO)

        # Set console handler
        if core.config.get('log', 'console'):
            cls._setup_console(logger, config)

        # Set syslog handler
        if core.config.get('log', 'syslog'):
            cls._setup_syslog(logger, config)

        # Set file handler
        if core.config.get('log', 'filelog'):
            cls._setup_filelog(logger, config)

        return logger

    @staticmethod
    def _setup_console(logger, config):
        if config.get(
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
        logger.addHandler(consolehdlr)

    @staticmethod
    def _setup_syslog(logger, config):
        # try to mimic to normal syslog messages
        fmt = '%(asctime)s %(name)s: %(message)s'
        datefmt = '%b %e %H:%M:%S'
        syslogform = logging.Formatter(fmt, datefmt)
        syslogaddr = None

        syslog = config.get('log', 'syslog')
        if syslog == 'remote':
            syslog_host = config.get('log', 'syslog_host')
            syslog_port = config.get('log', 'syslog_port')
            syslogaddr = (syslog_host, syslog_port)
        else:
            syslog_folder = config.get('log', 'syslog_folder')
            if syslogaddr:
                syslogaddr = syslog_folder
            elif sys.platform == 'darwin':
                syslogaddr = '/var/run/syslog'
            elif os.name != 'nt':
                syslogaddr = '/dev/log'

        sysloghdlr = logging.handlers.SysLogHandler(syslogaddr)
        sysloghdlr.setFormatter(syslogform)
        logger.addHandler(sysloghdlr)

    @staticmethod
    def _setup_filelog(logger, config):
        fmt = '%(asctime)s  %(levelname)-8s  %(message)s'
        datefmt = '%Y-%m-%d %H:%M:%S'
        fileform = logging.Formatter(fmt, datefmt)

        filelog_folder = config.get('log', 'filelog_folder')
        makedirs(filelog_folder, exist_ok=True)

        filelog_name = config.get('log', 'filelog_name')
        filelog = os.path.join(filelog_folder, filelog_name)

        if config.get('log', 'rotate'):
            filelog_size = config.get('log', 'filelog_size') << 10
            max_logfiles = config.get('log', 'max_logfiles')
            filehdlr = logging.handlers.RotatingFileHandler(
                filelog, maxBytes=filelog_size, backupCount=max_logfiles,
                encoding=locale.getpreferredencoding(do_setlocale=False))
        else:
            filehdlr = logging.FileHandler(
                filelog, encoding=locale.getpreferredencoding(
                    do_setlocale=False))

        filehdlr.setFormatter(fileform)
        logger.addHandler(filehdlr)
