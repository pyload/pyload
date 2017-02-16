# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import absolute_import, unicode_literals
from __future__ import print_function
from __future__ import division

from builtins import dict
from future import standard_library
standard_library.install_aliases()
import os
import shlex
from builtins import map
from platform import platform
from sys import *

import psutil

import ctypes
from pyload.utils.lib.subprocess import PIPE, Popen

try:
    import dbus
except ImportError:
    pass
try:
    from setproctitle import setproctitle
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


def exec_cmd(command, *args, **kwargs):
    cmd = shlex.split(command)
    cmd.extend(x.encode('uft-8') for x in args)
    xargs = {'bufsize': -1,
             'stdout': PIPE,
             'stderr': PIPE}
    xargs.update(kwargs)
    return Popen(cmd, **xargs)


def call_cmd(command, *args, **kwargs):
    ignore_except = kwargs.pop('ignore_errors', False)
    try:
        p = exec_cmd(command, *args, **kwargs)

    except Exception as e:
        if not ignore_except:
            raise
        else:
            returncode = 1
            stdoutdata = ""
            stderrdata = e.message().strip()
    else:
        returncode = p.returncode
        stdoutdata, stderrdata = map(str.strip, p.communicate())

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
    return dict(platform=platform(),
                version=version,
                path=os.path.abspath(''),
                encoding=getdefaultencoding(),
                fs_encoding=getfilesystemencoding())


def get_process_id(name):
    procs = psutil.process_iter()
    zombie = psutil.STATUS_ZOMBIE
    return [p.pid() for p in procs if p.name() == name and
            p.is_running() and
            p.status() != zombie]


def get_process_name(pid):
    procs = psutil.process_iter()
    zombie = psutil.STATUS_ZOMBIE
    return [p.name() for p in procs if p.pid() == pid and
            p.is_running() and
            p.status() != zombie]


def kill_process(pid, wait=None):
    try:
        p = psutil.Process(pid)
        p.terminate()
        p.wait(wait)
    except (psutil.TimeoutExpired, psutil.ZombieProcess):
        p.kill()


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

    p = psutil.Process(pid)
    p.nice(value)


def set_console_icon(filepath):
    if os.name != 'nt':
        return

    if not os.path.isfile(filepath):
        return

    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x00000010
    LR_DEFAULTSIZE = 0x00000040

    file = os.path.abspath(filepath)
    flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
    hicon = ctypes.windll.kernel32.LoadImageW(
        None, file, IMAGE_ICON, 0, 0, flags)

    ctypes.windll.kernel32.SetConsoleIcon(hicon)


def set_console_title(value):
    title = value.encode('utf-8')
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleA(title)
    else:
        stdout.write("\x1b]2;{}\x07".format(title))


def set_process_group(value):
    gid = grp.getgrnam(value)[2]
    os.setgid(gid)


def set_process_title(value):
    setproctitle('pyLoad-{}'.format(value))


def set_process_user(value):
    uid = pwd.getpwnam(value).pw_uid
    os.setuid(uid)


def shutdown():
    if os.name == 'nt':
        call_cmd('rundll32.exe user.exe,ExitWindows')

    elif platform() == "darwin":
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
