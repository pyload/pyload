#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

from __future__ import absolute_import, unicode_literals

import argparse
import operator
import os
import sys
from builtins import map

from future import standard_library
standard_library.install_aliases()

import pyload.core
from pyload.utils import convert, format
from pyload.utils.sys import set_console_icon, set_console_title

# from multiprocessing import freeze_support


try:
    from pyload.utils.layer.mycolorclass import (autoblue, autogreen, autored,
                                                 autowhite, autoyellow)
except ImportError:
    autoblue = autogreen = autored = autowhite = autoyellow = lambda msg: msg


__all__ = ['logo', 'main', 'parse_args']


PACKDIR = os.path.abspath(os.path.dirname(__file__))


def _gen_logo():
    text = """
      ____________
   _ /       |    \ ___________ _ _______________ _ ___
  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \
 /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \
 \       |   o|      | .__/\_, |____\___/\__,_\__,_|    /
  \______\    /______|_|___|__/________________________/
          \  /
           \/  © 2009-2017 pyLoad Team <{}>
""".format(pyload.core.info().url)
    return autowhite(text)

logo = _gen_logo()


def parse_args(argv=None):
    prog = autoblue("py") + autoyellow("Load")
    desc = autored(pyload.core.info().description)
    epilog = autogreen(
        "*** Please refer to the included `README.md` for further details ***")

    ap = argparse.ArgumentParser(prog=prog,
                                 description=desc,
                                 epilog=epilog,
                                 add_help=False)
    pg = ap.add_argument_group(autogreen("Optional arguments"))
    sp = ap.add_subparsers(title=autogreen("Commands"),
                           dest='command',
                           help=autored("Available sub-commands (") +
                                autoyellow("`COMMAND --help`") +
                                autored(" for detailed help)"))

    sc = (('start', "Start process instance"),
          ('quit', "Terminate process instance"),
          ('restart', "Restart process instance"),
          ('setup', "Setup package"),
          ('status', "Show process PID"),
          ('version', "Show package version"),
          ('info', "Show package info"))

    for prog, desc in sc:
        desc = autored(desc)
        p = sp.add_parser(prog, description=desc,
                          epilog=epilog, help=desc, add_help=False)
        globals()['sp_' + prog] = p

    for p in pg, sp_start, sp_stop, sp_restart, sp_status, sp_setup, sp_version:
        p.add_argument('-h', '--help',
                       action='help',
                       help=autored("Show this help message and exit"))

    for p in pg, sp_start, sp_stop, sp_restart, sp_status, sp_setup:
        profile_help = autored("Config profile to use (") + autoyellow("`default`") + \
            autored(" if missing)")
        configdir_help = autored("Change path of config directory")
        p.add_argument('-p', '--profile', help=profile_help)
        p.add_argument('-c', '--configdir', help=configdir_help)

    for p in pg, sp_start, sp_restart:
        debug_help = autored("Enable debug mode (") + autoyellow("`-dd`") + \
            autored(" for extended debug)")
        # webdebug_help = autored("Enable webserver debugging")
        refresh_help = autored("Remove compiled files and temp folder (") + \
            autoyellow("`-rr`") + autored(" to restore default login credentials ") + \
            autoyellow("`admin|pyload`") + autored(")")
        webui_help = autored("Enable webui interface at entered ") + \
            autoyellow("`IP address:Port number`") + \
            autored(" (use defaults if missing)")
        remote_help = autored("Enable remote api interface at entered ") + \
            autoyellow("`IP address:Port number`") + \
            autored(" (use defaults if missing)")
        daemon_help = autored("Run as daemon")
        p.add_argument('-d', '--debug', action='count', help=debug_help)
        # p.add_argument('-w', '--webdebug', action='count', help=webdebug_help)
        p.add_argument('-r', '--refresh', '--restore',
                       action='count', help=refresh_help)
        p.add_argument('-u', '--webui', help=webui_help)
        p.add_argument('-a', '--rpc', help=remote_help)
        p.add_argument('-D', '--daemon', action='store_true', help=daemon_help)

    wait_help = autored("Timeout for graceful exit (in seconds)")
    sp_stop.add_argument('--wait', help=wait_help)

    # NOTE: Workaround to `required subparsers` issue in Python 2
    if not set(map(operator.itemgetter(0), sc)).intersection(argv):
        argv.append('start')

    print(logo + '\n')
    return ap.parse_args(argv)


def _set_console():
    try:
        set_console_title("pyLoad console")
        set_console_icon(os.path.join(PACKDIR, 'media', 'favicon.ico'))
    except Exception:
        pass


# TODO: Recheck...
# def _open_browser(p):
    # webserver = p.svm.get('webui')
    # if not webserver or not webserver.active:
        # return None
    # import webbrowser
    # url = "{0}:{1}".format(webserver.host, webserver.port)
    # webbrowser.open_new_tab(url)


def main():
    _set_console()

    exc = None

    args = parse_args(sys.argv[1:])

    # TODO: Handle --help output

    func = getattr(pyload.core, args.command)
    kwgs = vars(args)
    kwgs.pop('command', None)

    res = func(**kwgs)

    if args.command in ('restart', 'start'):
        if not args.daemon:
            # _open_browser(p)
            try:
                res.join()
            except Exception as e:
                exc = e

    elif args.command == 'status':
        print(res if res is not None else "")

    elif args.command == 'version':
        print(convert.from_version(res))

    elif args.command == 'info':
        print('\n'.join(format.items(res)))

    sys.exit(exc)


if __name__ == '__main__':
    # freeze_support()
    main()
