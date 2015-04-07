# Copyright 2013 Hardcoded Software (http://www.hardcoded.net)

# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

from __future__ import unicode_literals

from ctypes import windll, Structure, byref, c_uint
from ctypes.wintypes import HWND, UINT, LPCWSTR, BOOL
import os.path as op

from .compat import text_type

shell32 = windll.shell32
SHFileOperationW = shell32.SHFileOperationW

class SHFILEOPSTRUCTW(Structure):
    _fields_ = [
        ("hwnd", HWND),
        ("wFunc", UINT),
        ("pFrom", LPCWSTR),
        ("pTo", LPCWSTR),
        ("fFlags", c_uint),
        ("fAnyOperationsAborted", BOOL),
        ("hNameMappings", c_uint),
        ("lpszProgressTitle", LPCWSTR),
        ]

FO_MOVE = 1
FO_COPY = 2
FO_DELETE = 3
FO_RENAME = 4

FOF_MULTIDESTFILES = 1
FOF_SILENT = 4
FOF_NOCONFIRMATION = 16
FOF_ALLOWUNDO = 64
FOF_NOERRORUI = 1024

def send2trash(path):
    if not isinstance(path, text_type):
        path = text_type(path, 'mbcs')
    if not op.isabs(path):
        path = op.abspath(path)
    fileop = SHFILEOPSTRUCTW()
    fileop.hwnd = 0
    fileop.wFunc = FO_DELETE
    fileop.pFrom = LPCWSTR(path + '\0')
    fileop.pTo = None
    fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT
    fileop.fAnyOperationsAborted = 0
    fileop.hNameMappings = 0
    fileop.lpszProgressTitle = None
    result = SHFileOperationW(byref(fileop))
    if result:
        msg = "Couldn't perform operation. Error code: %d" % result
        raise OSError(msg)

