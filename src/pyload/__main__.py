#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import atexit
import os
import sys
import time
from functools import partial

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


def _daemon(core_args, pid_file=""):
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

    if pid_file:
        write_pid_file(pid_file)
        atexit.register(partial(delete_pid_file, pid_file))

    pyload_core = Core(*core_args)
    pyload_core.start()


def write_pid_file(pid_file):
    delete_pid_file(pid_file)
    pid = os.getpid()
    os.makedirs(os.path.dirname(pid_file), exist_ok=True)
    with open(pid_file, "w") as fp:
        fp.write(str(pid))


def delete_pid_file(pid_file):
    if os.path.isfile(pid_file):
        os.remove(pid_file)


def read_pid_file(pid_file):
    """ return pid as int or 0"""
    if os.path.isfile(pid_file):
        with open(pid_file, "r") as fp:
            pid = fp.read().strip()

        if pid:
            pid = int(pid)
            return pid

    else:
        return 0


def is_already_running(pid_file):
    pid = read_pid_file(pid_file)
    if not pid:
        return 0

    if os.name == "nt":
        ret = 0
        import ctypes
        import ctypes.wintypes

        TH32CS_SNAPPROCESS = 2
        INVALID_HANDLE_VALUE = -1

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [('dwSize', ctypes.wintypes.DWORD),
                        ('cntUsage', ctypes.wintypes.DWORD),
                        ('th32ProcessID', ctypes.wintypes.DWORD),
                        ('th32DefaultHeapID', ctypes.wintypes.LPVOID),
                        ('th32ModuleID', ctypes.wintypes.DWORD),
                        ('cntThreads', ctypes.wintypes.DWORD),
                        ('th32ParentProcessID', ctypes.wintypes.DWORD),
                        ('pcPriClassBase', ctypes.wintypes.LONG),
                        ('dwFlags', ctypes.wintypes.DWORD),
                        ('szExeFile', ctypes.c_char * 260)]

        kernel32 = ctypes.windll.kernel32

        process_info = PROCESSENTRY32()
        process_info.dwSize = ctypes.sizeof(PROCESSENTRY32)
        hProcessSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hProcessSnapshot != INVALID_HANDLE_VALUE:
            found = False
            status = kernel32.Process32First(hProcessSnapshot , ctypes.pointer(process_info))
            while status:
                if process_info.th32ProcessID == pid:
                    found = True
                    break
                status = kernel32.Process32Next(hProcessSnapshot, ctypes.pointer(process_info))

            kernel32.CloseHandle(hProcessSnapshot)
            if found and process_info.szExeFile.decode().lower() in ("python.exe", "pythonw.exe"):
                ret = pid

        else:
            sys.stderr.write("Unhandled error in CreateToolhelp32Snapshot: {}\n".format(kernel32.GetLastError()))

        return ret

    else:
        try:
            os.kill(pid, 0)  # 0 - default signal (does nothing)
        except Exception:
            return 0

        return pid


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
    parser.add_argument(
        "--pidfile",
        help="set the full path to the pidfile",
        default=os.path.join(Core.DEFAULT_TMPDIR, "pyload.pid"),
    )
    parser.add_argument("--dry-run", action="store_true", help="test start-up and exit", default=False)
    parser.add_argument("--daemon", action="store_true", help="run as daemon")
    parser.add_argument("--quit", action="store_true", help="quit running pyLoad instance", default=False)
    parser.add_argument("--status", action="store_true", help="display pid if running or 0", default=False)
    group.add_argument("--version", action="version", version=f"pyLoad {__version__}")

    return parser.parse_args(cmd_args)


def run(core_args, daemon=False, pid_file=""):
    # change name to 'pyLoad'
    # from .lib.rename_process import rename_process
    # rename_process('pyLoad')

    if pid_file:
        pid = is_already_running(pid_file)
        if pid:
            sys.stderr.write(f"pyLoad already running with pid {pid}\n")
            if os.name == "nt":
                sys.exit(70)
            else:
                sys.exit(os.EX_SOFTWARE)

    if daemon:
        if os.name == "nt":
            sys.stderr.write("Daemon is not supported under windows\n")
            sys.exit(70)  #: EX_SOFTWARE
        else:
            return _daemon(core_args, pid_file=pid_file)

    else:
        if pid_file:
            write_pid_file(pid_file)
            atexit.register(partial(delete_pid_file, pid_file))

    pyload_core = Core(*core_args)
    try:
        pyload_core.start()
    except KeyboardInterrupt:
        pyload_core.log.info(pyload_core._("Killed from terminal"))
        pyload_core.terminate()
        if os.name == "nt":
            sys.exit(75)
        else:
            sys.exit(os.EX_TEMPFAIL)


def quit_instance(pid_file):
    if not pid_file:
        sys.stderr.write("Cannot quit without pidfile.\n")
        return

    if os.name == "nt":
        sys.stderr.write("Not supported on windows.\n")
        return

    pid = is_already_running(pid_file)
    if not pid:
        sys.stderr.write("No pyLoad running.\n")
        return

    try:
        os.kill(pid, 3)  #: SIGQUIT

        t = time.time()
        sys.stdout.write("waiting for pyLoad to quit\n")

        while os.path.exists(pid_file) and t + 10 > time.time():
            time.sleep(0.25)

        if not os.path.exists(pid_file):
            sys.stdout.write("pyLoad successfully stopped\n")

        else:
            os.kill(pid, 9)  #: SIGKILL
            sys.stderr.write("pyLoad did not respond\n")
            sys.stderr.write(f"Kill signal was send to process with id {pid}\n")

    except Exception as exc:
        sys.stderr.write("Error quitting pyLoad\n")


def main(cmd_args=sys.argv[1:]):
    """
    Entry point for console_scripts.
    """
    args = _parse_args(cmd_args)
    core_args = (args.userdir, args.tempdir, args.storagedir, args.debug, args.reset, args.dry_run)

    if args.quit:
        quit_instance(args.pidfile)
    else:
        run(core_args, args.daemon, args.pidfile)


if __name__ == "__main__":
    main()
