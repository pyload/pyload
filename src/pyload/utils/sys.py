# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import os
import shlex
import sys as _sys
from builtins import dict, map
from sys import *

import psutil
from future import standard_library
standard_library.install_aliases()

from pyload.utils import convert

from .layer.legacy.subprocess_ import PIPE, Popen


try:
    import dbus
except ImportError:
    pass
try:
    import setproctitle
except ImportError:
    pass
try:
    import grp
except ImportError:
    pass
try:
    import pwd
except ImportError:
    pass


# TODO: Recheck...
def exec_cmd(command, *args, **kwargs):
    cmd = shlex.split(command)
    cmd.extend(convert.to_bytes(x, x) for x in args)
    xargs = {'bufsize': -1,
             'stdout': PIPE,
             'stderr': PIPE}
    xargs.update(kwargs)
    return Popen(cmd, **xargs)


# TODO: Recheck...
def call_cmd(command, *args, **kwargs):
    ignore_errors = kwargs.pop('ignore_errors', False)
    try:
        proc = exec_cmd(command, *args, **kwargs)

    except Exception as exc:
        if not ignore_errors:
            raise
        else:
            returncode = 1
            stdoutdata = ""
            stderrdata = exc.message.strip()
    else:
        returncode = proc.returncode
        stdoutdata, stderrdata = map(str.strip, proc.communicate())

    finally:
        return returncode, stdoutdata, stderrdata


def console_encoding(enc):
    if os.name != 'nt':
        return 'utf-8'
    return "cp850" if enc == "cp65001" else enc  #: aka UTF-8 under Windows


def get_info():
    """
    Returns system information as dict.
    """
    return dict(platform=_sys.platform,
                version=_sys.version,
                path=os.path.abspath(''),
                encoding=_sys.getdefaultencoding(),
                fs_encoding=_sys.getfilesystemencoding())


def get_process_id(name):
    procs = psutil.process_iter()
    zombie = psutil.STATUS_ZOMBIE
    return [proc.pid() for proc in procs if proc.name() == name and
            proc.is_running() and
            proc.status() != zombie]


def get_process_name(pid):
    procs = psutil.process_iter()
    zombie = psutil.STATUS_ZOMBIE
    return [proc.name() for proc in procs if proc.pid() == pid and
            proc.is_running() and
            proc.status() != zombie]


def kill_process(pid, wait=None):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(wait)
    except (psutil.TimeoutExpired, psutil.ZombieProcess):
        proc.kill()


def renice(value, pid=None):
    """
    Unix notation process nicener.
    """
    if os.name == 'nt':
        MIN_NICENESS = -20
        MAX_NICENESS = 19

        normval = min(MAX_NICENESS, value) if value else max(
            MIN_NICENESS, value)
        priocls = [psutil.IDLE_PRIORITY_CLASS,
                   psutil.BELOW_NORMAL_PRIORITY_CLASS,
                   psutil.NORMAL_PRIORITY_CLASS,
                   psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                   psutil.HIGH_PRIORITY_CLASS,
                   psutil.REALTIME_PRIORITY_CLASS]
        prioval = (normval - MAX_NICENESS) * \
            (len(priocls) - 1) // (MIN_NICENESS - MAX_NICENESS)
        value = priocls[prioval]

    proc = psutil.Process(pid)
    proc.nice(value)


def ionice(ioclass=None, value=None, pid=None):
    """
    Unix notation process I/O nicener.
    """
    if os.name == 'nt':
        ioclass = {0: 2, 1: 2, 2: 2, 3: 0}[ioclass]
    proc = psutil.Process(pid)
    proc.ionice(ioclass, value)


def set_console_icon(iconpath):
    if os.name != 'nt':
        raise NotImplementedError
    if not os.path.isfile(iconpath):
        raise TypeError

    import ctypes

    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x00000010
    LR_DEFAULTSIZE = 0x00000040

    fpath = os.path.abspath(iconpath)
    flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
    hicon = ctypes.windll.kernel32.LoadImageW(
        None, fpath, IMAGE_ICON, 0, 0, flags)

    ctypes.windll.kernel32.SetConsoleIcon(hicon)


def set_console_title(value):
    title = convert.to_bytes(value, value)
    if os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleA(title)
    else:
        stdout.write("\x1b]2;{0}\x07".format(title))


def set_process_group(value):
    gid = grp.getgrnam(value)[2]
    os.setgid(gid)


def set_process_name(value):
    setproctitle.setproctitle(value)


def set_process_user(value):
    uid = pwd.getpwnam(value).pw_uid
    os.setuid(uid)


def shutdown():
    if os.name == 'nt':
        call_cmd('rundll32.exe user.exe,ExitWindows')

    elif _sys.platform == "darwin":
        call_cmd('osascript -e tell app "System Events" to shut down')

    else:
        #: See `http://stackoverflow.com/questions/23013274/shutting-down-computer-linux-using-python`
        try:
            sys_bus = dbus.SystemBus()
            ck_srv = sys_bus.get_object('org.freedesktop.ConsoleKit',
                                        '/org/freedesktop/ConsoleKit/Manager')
            ck_iface = dbus.Interface(
                ck_srv, 'org.freedesktop.ConsoleKit.Manager')
            stop_method = ck_iface.get_dbus_method("Stop")
            stop_method()
        except NameError:
            call_cmd('stop -h now')  # NOTE: Root privileges needed


# Cleanup
del _sys, PIPE, Popen, convert, dict, map, os, psutil, shlex
try:
    del dbus
except NameError:
    pass
try:
    del setproctitle
except NameError:
    pass
try:
    del grp
except NameError:
    pass
try:
    del pwd
except NameError:
    pass
