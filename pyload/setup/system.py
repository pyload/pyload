# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
import os
import sys

from pyload.utils.lib.collections import OrderedDict

# gettext decorator, translated only when needed
_ = lambda x: x

# platform usually do not change at runtime
info = None


def get_system_info():
    """
    Returns system information as dict.
    """
    global info

    if info is None:
        import platform

        info = OrderedDict((
            (_("Platform"), platform.platform()),
            (_("Version"), sys.version),
            (_("Path"), os.path.abspath("")),
            (_("Encoding"), sys.getdefaultencoding()),
            (_("FS-Encoding"), sys.getfilesystemencoding())
        ))

    return info
