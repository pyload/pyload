# -*- coding: utf-8 -*-
import pkg_resources
import semver

try:
    dist_name = "pyload-ng"
    __version__ = pkg_resources.get_distribution(dist_name).version
except pkg_resources.DistributionNotFound:
    __version__ = "unknown"
finally:
    __version_info__ = semver.parse_version_info(
        "0.0.0" if __version__ == "unknown" else __version__
    )
    del pkg_resources
    del semver

import builtins
import sys
import os
from sys import argv, platform

builtins._ = lambda x: x  # TODO: os.remove

builtins.pyreq = None  # TODO: os.remove
builtins.addonManager = None  # TODO: os.remove

builtins.owd = os.path.abspath("")  # original working directory
builtins.pypath = pypath = os.path.abspath(os.path.join(__file__, "..", ".."))

sys.path.append(os.path.join(pypath, "pyload", "lib"))

homedir = ""

if platform == "nt":
    homedir = os.path.expanduser("~")
    if homedir == "~":
        import ctypes

        CSIDL_APPDATA = 26
        _SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
        _SHGetFolderPath.argtypes = [
            ctypes.wintypes.HWND,
            ctypes.c_int,
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.LPCWSTR,
        ]

        path_buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        result = _SHGetFolderPath(0, CSIDL_APPDATA, 0, 0, path_buf)
        homedir = path_buf.value
else:
    homedir = os.path.expanduser("~")

builtins.homedir = homedir

args = " ".join(argv[1:])

# dirty method to set configdir from commandline arguments
if "--configdir=" in args:
    pos = args.find("--configdir=")
    end = args.find("-", pos + 12)

    if end == -1:
        configdir = args[pos + 12 :].strip()
    else:
        configdir = args[pos + 12 : end].strip()
elif os.path.exists(os.path.join(pypath, "pyload", "config", "configdir")):
    with open(os.path.join(pypath, "pyload", "config", "configdir"), "rb") as f:
        c = f.read().strip()
    configdir = os.path.join(pypath, c)
else:
    if platform in ("posix", "linux2"):
        configdir = os.path.join(homedir, ".pyload")
    else:
        configdir = os.path.join(homedir, "pyload")

if not os.path.exists(configdir):
    os.makedirs(configdir, 0o700)

builtins.configdir = configdir
os.chdir(configdir)

# print("Using {} as working directory.".format(configdir))
