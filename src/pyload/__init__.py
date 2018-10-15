# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import builtins
# import codecs
import os
import pkg_resources
import semver
import tempfile
# import sys

try:
    dist_name = "pyload"
    pkgdir = pkg_resources.resource_filename(dist_name, "")
    __version__ = pkg_resources.get_distribution(dist_name).version
    
except pkg_resources.DistributionNotFound:
    pkgdir = os.path.realpath(os.path.join(__file__, "..", "..", ".."))
    
    ver_path = os.path.join(pkgdir, 'VERSION.md')
    with open(ver_path) as f:
        __version__ = f.read().strip()
        
finally:
    __version_info__ = semver.parse_version_info(__version__)
    del pkg_resources
    del semver

# remove from builtins and keep them just here?
builtins.PKGDIR = pkgdir
builtins.HOMEDIR = os.path.expanduser('~')
builtins.DATADIR = os.getenv('APPDATA') if os.name == 'nt' else builtins.HOMEDIR
builtins.TMPDIR = tempfile.gettempdir()

# TODO: remove
builtins._ = lambda x: x
builtins.REQUESTS = None
builtins.ADDONMANAGER = None


locale.setlocale(locale.LC_ALL, '')


# codecs.register(lambda enc: codecs.lookup('utf-8') if enc == 'cp65001' else None)
# sys.stdout = codecs.getwriter(sys.console_encoding(sys.stdout.encoding))(sys.stdout, errors="replace")  

del pkgdir
del locale
del os
del tempfile
