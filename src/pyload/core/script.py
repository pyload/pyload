#!/usr/bin/env python
# -*- coding: utf-8 -*-
# AUTHOR: vuolter

import argparse
import os
import sys

from pyload import DATADIR, TMPDIR

from . import Core
from .. import __version__


def _daemon(core_args):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as exc:
        sys.stderr.write(f"fork #1 failed: {exc.errno} ({exc.strerror})\n")
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print(eventual PID before)
            print(f"Daemon PID {pid}")
            sys.exit(0)
    except OSError as exc:
        sys.stderr.write(f"fork #2 failed: {exc.errno} ({exc.strerror})\n")
        sys.exit(1)

    # Iterate through and close some file descriptors.
    for fd in range(0, 3):
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
        description="Free and open-source Download Manager written in pure Python"
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--version", action="version", version=f"pyLoad {__version__}"
    )

    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug mode", default=None
    )
    parser.add_argument(
        "--userdir", help="Run with custom user folder", default=DATADIR
    )
    parser.add_argument(
        "--cachedir", help="Run with custom cache folder", default=TMPDIR
    )
    parser.add_argument("--daemon", action="store_true", help="Daemonmize after start")
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore default admin user",
        default=None,
    )

    return parser.parse_args(cmd_args)


def run(core_args, daemon=False):
    # change name to 'pyLoad'
    # from .lib.rename_process import renameProcess
    # renameProcess('pyLoad')
    if daemon:
        return _daemon(core_args)

    pyload_core = Core(*core_args)
    try:
        pyload_core.start()
    except KeyboardInterrupt:
        pyload_core.log.info(pyload_core._("Killed from terminal"))
        pyload_core.terminate()
        os._exit(1)


def main(cmd_args=sys.argv[1:]):
    """
    Entry point for console_scripts.
    """
    args = _parse_args(cmd_args)
    core_args = (args.userdir, args.cachedir, args.debug, args.restore)

    run(core_args, args.daemon)


if __name__ == "__main__":
    main()
