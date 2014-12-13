# -*- coding: utf-8 -*-

from __future__ import with_statement

import __builtin__

import os
import platform
import sys

from codecs import getwriter

from pyload.utils import get_console_encoding


__all__ = ["__status_code__", "__status__", "__version_info__", "__version__", "__author_name__", "__author_mail__", "__license__"]

__version_info__ = (0, 4, 10)
__version__      = '.'.join(map(str, __version_info__))

__status_code__ = 4
__status__      = {1: "Planning",
                   2: "Pre-Alpha",
                   3: "Alpha",
                   4: "Beta",
                   5: "Production/Stable",
                   6: "Mature",
                   7: "Inactive"}[__status_code__]  #: PyPI Development Status Classifiers

__license__ = "GNU Affero General Public License v3"

__authors__ = [("Marius"        , "mkaay@mkaay.de"        ),
               ("RaNaN"         , "Mast3rRaNaN@hotmail.de"),
               ("Stefano"       , "l.stickell@yahoo.it"   ),
               ("Walter Purcaro", "vuolter@gmail.com"     ),
               ("himbrr"        , "himbrr@himbrr.ws"      ),
               ("sebnapi"       , ""                      ),
               ("spoob"         , "spoob@gmx.de"          ),
               ("zoidberg10"    , "zoidberg@mujmail.cz"   )]


################################# InitHomeDir #################################

__builtin__.owd       = os.path.abspath("")  #: original working directory
__builtin__.homedir   = os.path.expanduser("~")
__builtin__.rootdir   = os.path.abspath(os.path.join(__file__, ".."))
__builtin__.configdir = ""
__builtin__.pypath    = os.path.abspath(os.path.join(rootdir, ".."))


if "64" in platform.machine():
    sys.path.append(os.path.join(pypath, "lib64"))
sys.path.append(os.path.join(pypath, "lib"))

sys.stdout = getwriter(get_console_encoding(sys.stdout.encoding))(sys.stdout, errors="replace")

if homedir == "~" and os.name == "nt":
    import ctypes

    CSIDL_APPDATA = 26

    _SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
    _SHGetFolderPath.argtypes = [ctypes.wintypes.HWND,
                                 ctypes.c_int,
                                 ctypes.wintypes.HANDLE,
                                 ctypes.wintypes.DWORD,
                                 ctypes.wintypes.LPCWSTR]

    path_buf = ctypes.wintypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)

    _SHGetFolderPath(0, CSIDL_APPDATA, 0, 0, path_buf)

    __builtin__.homedir = path_buf.value

try:
    p = os.path.join(rootdir, "config", "configdir")

    with open(p, "rb") as f:
        configdir = f.read().strip()

except IOError:
    if os.name == "posix":
        configdir = os.path.join(homedir, ".pyload")
    else:
        configdir = os.path.join(homedir, "pyload")

try:
    if not os.path.exists(configdir):
        os.makedirs(configdir, 0700)

    os.chdir(configdir)

except IOError, e:
    print >> sys.stderr, "configdir init failed: %d (%s)" % (e.errno, e.strerror)
    sys.exit(1)

else:
    __builtin__.configdir  = configdir
