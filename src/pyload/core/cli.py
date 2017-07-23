# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import argparse
import operator
import os
import sys
from builtins import map

from future import standard_library
from pkg_resources import resource_filename

from pyload.utils.system import set_console_icon, set_console_title

from . import iface
from .__about__ import __credits__, __package__

standard_library.install_aliases()

try:
    import colorclass
except ImportError:
    colorclass = None
    autoblue = autogreen = autored = autowhite = autoyellow = lambda msg: msg
else:
    for tag, reset, _, _ in (_f for _f in colorclass.list_tags() if _f):
        globals()[tag] = lambda msg: colorclass.Color(
            "{{{0}}}{1}{{{2}}}".format(tag, msg, reset))
    if os.name == 'nt':
        colorclass.Windows.enable(auto_colors=True, reset_atexit=True)
    elif colorclass.is_light():
        colorclass.set_light_background()
    else:
        colorclass.set_dark_background()


def _gen_logo():
    text = os.linesep.join(
        '{0}© {3} {1} <{2}>'.format(' ' * 15, *info) for info in __credits__)
    return autowhite("""
      ____________
   _ /       |    \ ___________ _ _______________ _ ___
  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\
 /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\
 \       |   o|      | .__/\_, |____\___/\__,_\__,_|    /
  \______\    /______|_|___|__/________________________/
          \  /
           \/  {0}
""".format(text))


LOGO = _gen_logo()


def parse_args(argv=None):
    prog = autoblue("py") + autoyellow("Load")
    desc = autored(
        "Free and Open Source download manager written in Pure"
        "Python and designed to be extremely lightweight, fully customizable "
        "and remotely manageable")
    epilog = autogreen("*** Visit https://pyload.net for further details ***")

    ap = argparse.ArgumentParser(
        prog=prog, description=desc, epilog=epilog, add_help=False)
    pg = ap.add_argument_group(autogreen("Optional arguments"))
    sp = ap.add_subparsers(
        title=autogreen("Commands"),
        dest='command',
        help=''.join(
            (
                autored("Available sub-commands ("),
                autoyellow("`COMMAND --help`"),
                autored(" for detailed help)")
            )
        )
    )

    sc = (
        ('start', "Start process instance"),
        ('quit', "Terminate process instance"),
        ('restart', "Restart process instance"),
        ('status', "Show process PID"),
        ('version', "Show pyLoad version")
    )
    for prog, desc in sc:
        desc = autored(desc)
        prsr = sp.add_parser(
            prog, description=desc, epilog=epilog, help=desc, add_help=False)
        globals()['sp_' + prog] = prsr

    for prsr in (pg, sp_start, sp_quit, sp_restart, sp_status, sp_version):
        prsr.add_argument(
            '-h', '--help', action='help',
            help=autored("Show this help message and exit"))

    for prsr in (pg, sp_start, sp_quit, sp_restart, sp_status):
        profile_help = ''.join((
            autored("Profile name to use ("),
            autoyellow("`default`"),
            autored(" if missing)"),
        ))
        configdir_help = autored("Change path of config directory")
        prsr.add_argument('-p', '--profile', help=profile_help)
        prsr.add_argument('-c', '--configdir', help=configdir_help)

    for prsr in (pg, sp_start, sp_restart):
        tmpdir_help = autored("Change path of temp files directory")
        debug_help = ''.join((
            autored("Enable debug mode ("),
            autoyellow("`-dd`"),
            autored(" for extended debug)"),
        ))
        restore_help = ''.join((
            autored("Restore default login credentials "),
            autoyellow("`admin|pyload`"),
            autored(")"),
        ))
        daemon_help = autored("Run as daemon")
        prsr.add_argument('-t', '--tmpdir', help=tmpdir_help)
        prsr.add_argument('-d', '--debug', action='count', help=debug_help)
        prsr.add_argument(
            '-r', '--restore', action='store_true', help=restore_help)
        prsr.add_argument(
            '-D', '--daemon', action='store_true', help=daemon_help)

    # NOTE: Workaround to `required subparsers` bug in Python 2
    if not set(map(operator.itemgetter(0), sc)).intersection(argv):
        argv.append('start')

    print(LOGO + os.linesep)
    return ap.parse_args(argv)


def _setup_console():
    icon = resource_filename(__package__, 'icon.ico')
    try:
        set_console_title("pyLoad console")
        set_console_icon(icon)
    except Exception:
        pass


def main(argv=sys.argv[1:]):
    args = parse_args(argv)

    _setup_console()

    # TODO: Handle --help output

    func = getattr(iface, args.command)
    kwgs = vars(args)
    kwgs.pop('command', None)

    res = func(**kwgs)

    if args.command in ('restart', 'start'):
        if not args.daemon:
            res.join()

    elif args.command == 'status':
        print("" if res is None else res)

    elif args.command == 'version':
        print(res)

    # sys.exit()
