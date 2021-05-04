#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys

from . import __version__
from .core import Core

DESCRIPTION = """
       ____________
   ___/       |    \_____________ _ _______________ _ ___
  /   |    ___/    |    _ __ _  _| |   ___  __ _ __| |   \\
 /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \\
 \        |   ◯|       | .__/\_, |____\___/\__,_\__,_|    /
  \_______\    /_______|_|___|__/________________________/
           \  /
            \/

The free and open-source Download Manager written in pure Python
"""


def _daemon(core_args):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit()
    except OSError as exc:
        sys.stderr.write(f"fork #1 failed: {exc.errno} ({exc.strerror})\n")
        sys.exit(os.EX_OSERR)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print(eventual PID before)
            print(f"Daemon PID {pid}")
            sys.exit()
    except OSError as exc:
        sys.stderr.write(f"fork #2 failed: {exc.errno} ({exc.strerror})\n")
        sys.exit(os.EX_OSERR)

    # Iterate through and close some file descriptors.
    for fd in range(3):
        try:
            os.close(fd)
        except OSError:  #: ERROR as fd wasn't open to begin with (ignored)
            pass

    os.open(os.devnull, os.O_RDWR)  #: standard input (0)
    os.dup2(0, 1)  #: standard output (1)
    os.dup2(0, 2)

    pyload_core = Core(*core_args)
    pyload_core.start()


def _parse_args(cmd_args):
    """
    Parse command line parameters.

    Args:
      cmd_args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()

    parser.add_argument(
        "-d", "--debug", action="store_true", help="enable debug mode", default=None
    )
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="reset default username/password",
        default=None,
    )
    parser.add_argument(
        "--storagedir",
        help="use this location to save downloads",
        default=None,
    )
    parser.add_argument(
        "--userdir",
        help="use this location to store user data files",
        default=Core.DEFAULT_DATADIR,
    )
    parser.add_argument(
        "--tempdir",
        help="use this location to store temporary files",
        default=Core.DEFAULT_TMPDIR,
    )
    parser.add_argument("--dry-run", action="store_true", help="test start-up and exit", default=False)
    parser.add_argument("--daemon", action="store_true", help="run as daemon")

    group.add_argument("--version", action="version", version=f"pyLoad {__version__}")

    return parser.parse_args(cmd_args)


def run(core_args, daemon=False):
    # change name to 'pyLoad'
    # from .lib.rename_process import rename_process
    # rename_process('pyLoad')
    if daemon:
        return _daemon(core_args)

    pyload_core = Core(*core_args)
    try:
        pyload_core.start()
    except KeyboardInterrupt:
        pyload_core.log.info(pyload_core._("Killed from terminal"))
        pyload_core.terminate()
        sys.exit(os.EX_TEMPFAIL)


def main(cmd_args=sys.argv[1:]):
    """
    Entry point for console_scripts.
    """
    args = _parse_args(cmd_args)
    core_args = (args.userdir, args.tempdir, args.storagedir, args.debug, args.reset, args.dry_run)

    run(core_args, args.daemon)


if __name__ == "__main__":
    main()
