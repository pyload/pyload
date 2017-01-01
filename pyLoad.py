#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: vuolter
#     ____________
#    /       |    \
#    |    ___/    |
#    \___/  ______/
#        |   o|
#        \    /
#         \  /
#          \/

from __future__ import print_function
from __future__ import unicode_literals

import argparse
# import multiprocessing
import operator
import sys

import colorama
# colorama.init(autoreset=True)  #@NOTE: Doesn't work on Windows...

import pyload

from pyload.utils import format
from pyload.utils.sys import set_console_icon, set_console_title


__all__ = ['logo', 'main', 'parse_args']


def logo():
    from colorama import Fore, Back, Style

    ws = lambda x: " " * x
    info = pyload.info()
    logo = (
        "{}{}{}{}{}".format(Fore.BLUE, ws(1), '________', Fore.YELLOW, "____"),
        "{}{}{}{}{}{}{}".format(Fore.BLUE, '/', ws(7), '|', Fore.YELLOW, ws(4), "\\"),
        "{}{}{}{}{}{}{}{}{}{}{}{}".format(Fore.BLUE, '|', ws(4), '___/', ws(4), Fore.YELLOW, "|", ws(7), Fore.BLUE, "__py", Fore.YELLOW, "Load__"),
        "{}{}{}{}{}".format(Fore.BLUE,'\___/', ws(2), Fore.YELLOW, "______/"),
        "{}{}{}{}{}{}{}{}{}v{}{}".format(Fore.YELLOW, ws(4), '|', ws(3), 'o|', ws(12), Style.BRIGHT, Back.BLUE, Fore.WHITE, info.version, Style.RESET_ALL),
        "{}{}{}{}{}".format(Fore.YELLOW, ws(4), "\\", ws(4), "/"),
        "{}{}{}{}{}{}{}{}".format(Fore.YELLOW, ws(5), "\\", ws(2), "/", ws(5), Fore.BLUE, "© 2009-2016 The pyLoad Team"),
        "{}{}{}{}{}{}{}".format(Fore.YELLOW, ws(6), "\\/", ws(13), Fore.GREEN, info.url, Style.RESET_ALL),
    )
    return '\n'.join(ws(17) + i for i in logo)


def parse_args(argv=None):
    #@NOTE: Workaround to `required subparsers` issue in Python 2
    if not argv:
        argv = sys.argv[1:]
    if not set(map(operator.itemgetter(0), sc)) & set(argv):
        argv.append('start')

    color  = lambda c, msg: getattr(colorama.Fore, c) + msg + colorama.Style.RESET_ALL
    blue   = lambda msg: color('BLUE'  , msg)
    green  = lambda msg: color('GREEN' , msg)
    red    = lambda msg: color('RED'   , msg)
    yellow = lambda msg: color('YELLOW', msg)

    prog   = blue("py") + yellow("Load")
    desc   = red(pyload.info().description)
    epilog = green("*** Please refer to the included `README.md` for further info ***")

    ap = argparse.ArgumentParser(prog=prog,
                                 description=desc,
                                 epilog=epilog,
                                 add_help=False)
    pg = ap.add_argument_group(green("Optional arguments"))
    sp = ap.add_subparsers(title=green("Commands"),
                           dest='command',
                           help=red("Available sub-commands (") +
                                yellow("`COMMAND --help`") +
                                red(" for detailed help)"))

    sc = (('start'  , "Start process instance"),
          ('stop'   , "Terminate process instance"),
          ('restart', "Restart process instance"),
          ('setup'  , "Setup package"),
          ('update' , "Update package"),
          ('status' , "Show process PID"),
          ('version', "Show package version"),
          ('info'   , "Show package info"))

    for prog, desc in sc:
        desc = red(desc)
        p = sp.add_parser(prog, description=desc, epilog=epilog, help=desc, add_help=False)
        globals()['sp_' + prog] = p

    for p in pg, sp_start, sp_stop, sp_restart, sp_status, sp_update, sp_setup, sp_version:
        p.add_argument('-h', '--help',
                       action='help',
                       help=red("Show this help message and exit"))

    for p in pg, sp_start, sp_stop, sp_restart, sp_status:
        profile_help = red("Config profile to use (") + yellow("`default`") + \
                       red(" if missing)")
        p.add_argument('-p', '--profile', help=profile_help)

    for p in pg, sp_start, sp_restart:
        configdir_help = red("Change path of config directory")
        refresh_help   = red("Remove compiled files and tmp config (") + \
                         yellow("`-rr`") + red(" to restore admin access ") + \
                         yellow("`admin|pyload`") + red(")")
        remote_help    = red("Enable remote api interface at entered ") + \
                         yellow("`IP address:Port number`") + \
                         red(" (use defaults if missing)")
        webui_help     = red("Enable webui interface at entered ") + \
                         yellow("`IP address:Port number`") + \
                         red(" (use defaults if missing)")
        debug_help     = red("Enable debug mode (") + yellow("`-dd`") + \
                         red(" for extended debug)")
        webdebug_help  = red("Enable webserver debugging")
        daemon_help    = red("Run as daemon")

        p.add_argument('-c', '--configdir', help=configdir_help)
        p.add_argument('-r', '--refresh', '--restore', action='count', help=refresh_help)
        p.add_argument('-a', '--remote', help=remote_help)
        p.add_argument('-u', '--webui', help=webui_help)
        p.add_argument('-d', '--debug', action='count', help=debug_help)
        p.add_argument('-w', '--webdebug', action='count', help=webdebug_help)
        p.add_argument('-D', '--daemon', action='store_true', help=daemon_help)

    force_help = red("Force package installation")
    sp_update.add_argument('-f', '--force', action='store_true', help=force_help)

    print(logo() + '\n')
    return ap.parse_args(argv)


def _set_console():
    try:
        set_console_title("pyLoad console")
        set_console_icon(os.path.join(ROOTDIR, 'media', 'favicon.ico'))
    except Exception:
        pass


def _open_browser(p):
    webserver = p.servermanager.get('webui')
    if not webserver or not webserver.active:
        return
    import webbrowser
    url = '{}:{}'.format(webserver.host, webserver.port)
    webbrowser.open_new_tab(url)


def main():
    _set_console()

    args = parse_args()
    func = getattr(pyload, args.command)
    kwgs = vars(args)
    kwgs.pop('command', None)

    res = func(**kwgs)

    if args.command in ('restart', 'start'):
        _open_browser(p)

    elif args.command in ('status', 'version'):
        print(' '.join(format.iter(res)))

    elif args.command == 'info':
        print('\n'.join(format.map(res)))

    sys.exit()


if __name__ == "__main__":
    # multiprocessing.freeze_support()
    main()
