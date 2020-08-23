# -*- coding: utf-8 -*-

import os
import shlex
import sys
from subprocess import PIPE, Popen

# import psutil
from . import convert
from .check import is_iterable
from .convert import to_str

try:
    import dbus
except ImportError:
    dbus = None
try:
    import grp
except ImportError:
    grp = None
try:
    import pwd
except ImportError:
    pwd = None


# TODO: Recheck...
def exec_cmd(command, *args, **kwargs):
    cmd = shlex.split(command)
    cmd.extend(map(convert.to_bytes, args))
    xargs = {"bufsize": -1, "stdout": PIPE, "stderr": PIPE}
    xargs.update(kwargs)
    return Popen(cmd, **xargs)


# TODO: Recheck...
def call_cmd(command, *args, **kwargs):
    ignore_errors = kwargs.pop("ignore_errors", False)
    try:
        sp = exec_cmd(command, *args, **kwargs)

    except Exception as exc:
        if not ignore_errors:
            raise
        returncode = 1
        stdoutdata = ""
        stderrdata = to_str(exc).strip()
    else:
        returncode = sp.returncode
        stdoutdata, stderrdata = map(str.strip, sp.communicate())

    return returncode, stdoutdata, stderrdata


# def console_encoding(enc):
#     if os.name != "nt":
#         return "utf-8"
#     return "cp850" if enc == "cp65001" else enc  # aka UTF-8 under Windows


# def _get_psutil_process(pid, ctime):
#     if pid is None:
#         pid = os.getpid()
#     if ctime is None:
#         return psutil.Process(pid)
#     try:
#         psps = (psp for psp in psutil.process_iter() if psp.pid() == pid and psp.create_time() == ctime)
#         return psps[0]
#     except IndexError:
#         raise psutil.NoSuchProcess(pid)


# def is_running_process(pid=None):
#     ctime = None
#     if is_iterable(pid):
#         pid, ctime = pid

#     psp = _get_psutil_process(pid, ctime)
#     return psp.is_running() and psp.create_time() == ctime


# def is_zombie_process(pid=None):
#     ctime = None
#     if is_iterable(pid):
#         pid, ctime = pid

#     try:
#     psp = _get_psutil_process(pid, ctime)
#         flag = psp.status() is psutil.STATUS_ZOMBIE
#     except psutil.ZombieProcess:
#         flag = True
#     return flag


# def kill_process(pid=None, timeout=None):
#     ctime = None
#     if is_iterable(pid):
#         pid, ctime = pid

#     try:
#         psp = _get_psutil_process(pid, ctime)
#         psp.terminate()
#         psp.wait(timeout)
#     except (psutil.TimeoutExpired, psutil.ZombieProcess):
#         psp.kill()


# def renice(pid=None, niceness=None):
#     """Unix notation process nicener."""
#     ctime = None
#     value = None

#     if os.name == "nt":
#     MIN_NICENESS = -20
#     MAX_NICENESS = 19

#     normval = (
#         min(MAX_NICENESS, niceness) if niceness else max(MIN_NICENESS, niceness)
#     )
#     priocls = [
#         psutil.IDLE_PRIORITY_CLASS,
#         psutil.BELOW_NORMAL_PRIORITY_CLASS,
#         psutil.NORMAL_PRIORITY_CLASS,
#         psutil.ABOVE_NORMAL_PRIORITY_CLASS,
#         psutil.HIGH_PRIORITY_CLASS,
#         psutil.REALTIME_PRIORITY_CLASS,
#     ]
#     prioval = (
#         (normval - MAX_NICENESS)
#         * (len(priocls) - 1)
#         // (MIN_NICENESS - MAX_NICENESS)
#     )
#     value = priocls[prioval]

#     if is_iterable(pid):
#         pid, ctime = pid

#     psp = _get_psutil_process(pid, ctime)
#     psp.nice(value)


# def ionice(pid=None, ioclass=None, niceness=None):
#     """Unix notation process I/O nicener."""
#     if os.name == "nt":
#         ioclass = {0: 2, 1: 2, 2: 2, 3: 0}[ioclass]

#     ctime = None
#     if is_iterable(pid):
#         pid, ctime = pid

#     psp = _get_psutil_process(pid, ctime)
#     psp.ionice(ioclass, niceness)


# def set_console_icon(iconpath):
#     if os.name != "nt":
#         raise NotImplementedError
#     if not os.path.isfile(iconpath):
#         raise TypeError

#     import ctypes

#     IMAGE_ICON = 1
#     LR_LOADFROMFILE = 0x00000010
#     LR_DEFAULTSIZE = 0x00000040

#     flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
#     hicon = ctypes.windll.kernel32.LoadImageW(None, iconpath, IMAGE_ICON, 0, 0, flags)

#     ctypes.windll.kernel32.SetConsoleIcon(hicon)


# def set_console_title(value):
#     title = convert.to_bytes(value)
#     if os.name == "nt":
#         import ctypes

#         ctypes.windll.kernel32.SetConsoleTitleA(title)
#     else:
#         sys.stdout.write(f"\x1b]2;{title}\x07")


# def set_process_group(value):
#     gid = grp.getgrnam(value)[2]
#     os.setgid(gid)


# def set_process_user(value):
#     uid = pwd.getpwnam(value).pw_uid
#     os.setuid(uid)


# def shutdown_os():
#     if os.name == "nt":
#         call_cmd("rundll32.exe user.exe,ExitWindows")

#     elif sys.platform == "darwin":
#         call_cmd('osascript -e tell app "System Events" to shut down')

#     else:
#         # See `http://stackoverflow.com/questions/23013274/
#         #      shutting-down-computer-linux-using-python`
#         try:
#             sys_bus = dbus.SystemBus()
#             ck_srv = sys_bus.get_object(
#                 "org.freedesktop.ConsoleKit", "/org/freedesktop/ConsoleKit/Manager"
#             )
#             ck_iface = dbus.Interface(ck_srv, "org.freedesktop.ConsoleKit.Manager")
#             stop_method = ck_iface.get_dbus_method("Stop")
#             stop_method()
#         except AttributeError:
#             call_cmd("shutdown -h now")  # NOTE: Root privileges needed
