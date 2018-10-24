#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: vuolter

import os
import sys
import argparse

from .core import Core


def daemon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #1 failed: {} ({})\n".format(e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print(eventual PID before)
            print("Daemon PID {}".format(pid))
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #2 failed: {} ({})\n".format(e.errno, e.strerror))
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

    pyload_core = Core()
    pyload_core.start()
    
    
def parse_args(args):
    """Parse command line parameters

    Args:
      args ([str]): command line parameters as list of strings

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="pyLoad Download Manager")
    parser.add_argument(
        '--version',
        action='version',
        version='snakel {ver}'.format(ver=__version__))
    parser.add_argument(
        dest="n",
        help="n-th Fibonacci number",
        type=int,
        metavar="INT")
    parser.add_argument(
        '-v',
        '--verbose',
        dest="loglevel",
        help="set loglevel to INFO",
        action='store_const',
        const=logging.INFO)
    parser.add_argument(
        '-vv',
        '--very-verbose',
        dest="loglevel",
        help="set loglevel to DEBUG",
        action='store_const',
        const=logging.DEBUG)
    return parser.parse_args(args)

    
def run(args=sys.argv[1:]):
    """
    Entry point for console_scripts
    """
    # change name to 'pyLoad'
    # from .lib.rename_process import renameProcess
    # renameProcess('pyLoad')
    args = parse_args(args)
    
    # TODO: use parsed args
    if args.daemon:
        daemon()
    else:
        pyload_core = Core()
        try:
            pyload_core.start()
        except KeyboardInterrupt:
            pyload_core.log.info(self._("Killed from terminal"))
            pyload_core.shutdown()
            os._exit(1)
            
            
if __name__ == "__main__":
    run()
