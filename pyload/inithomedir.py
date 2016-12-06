# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from os import makedirs, path, chdir
from os.path import join
import sys
from sys import argv, platform

from . import __dev__

import builtins

builtins.owd = path.abspath("") #original working directory
builtins.pypath = path.abspath(path.join(__file__, "..", ".."))

# Before changing the cwd, the abspath of the module must be manifested
if 'pyload' in sys.modules:
    rel_pyload = sys.modules['pyload'].__path__[0]
    abs_pyload = path.abspath(rel_pyload)
    if abs_pyload != rel_pyload:
        sys.modules['pyload'].__path__.insert(0, abs_pyload)

sys.path.append(join(pypath, "pyload", "lib"))

homedir = ""

if platform == 'nt':
    homedir = path.expanduser("~")
    if homedir == "~":
        import ctypes

        CSIDL_APPDATA = 26
        _SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
        _SHGetFolderPath.argtypes = [ctypes.wintypes.HWND,
                                     ctypes.c_int,
                                     ctypes.wintypes.HANDLE,
                                     ctypes.wintypes.DWORD, ctypes.wintypes.LPCWSTR]

        path_buf = ctypes.wintypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        result = _SHGetFolderPath(0, CSIDL_APPDATA, 0, 0, path_buf)
        homedir = path_buf.value
else:
    homedir = path.expanduser("~")

builtins.homedir = homedir

configdir = None
final = False
args = " ".join(argv)
# dirty method to set configdir from commandline arguments
if "--configdir=" in args:
    for arg in argv:
        if arg.startswith("--configdir="):
            configdir = arg.replace('--configdir=', '').strip()

elif "nosetests" in args:
    print("Running in test mode")
    configdir = join(pypath, "tests", "config")

elif path.exists(path.join(pypath, "pyload", "config", "configdir")):
    f = open(path.join(pypath, "pyload", "config", "configdir"), "rb")
    c = f.read().strip()
    f.close()
    configdir = path.join(pypath, c)

# default config dir
if not configdir:
    # suffix when running dev version
    dev = "-dev" if __dev__ else ""
    configname = ".pyload" if platform in ("posix", "linux2", "darwin") else "pyload"
    configdir = path.join(homedir, configname + dev)


def init_dir(other_path=None, no_change=False):
    # switch to pyload home directory, or path at other_path
    global configdir
    global final

    if final: return

    if no_change: final = True

    if other_path is not None:
        configdir = join(pypath, other_path)

    if not path.exists(configdir):
        makedirs(configdir, 0o700)

    builtins.configdir = configdir
    chdir(configdir)

#print("Using %s as working directory." % configdir)
