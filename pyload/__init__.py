# -*- coding: utf-8 -*-
#@author: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import int
import builtins
import codecs
import os
import tempfile

import daemonize
import psutil
from future import standard_library

from pyload.core import Core
from pyload.utils import convert, path, sys

standard_library.install_aliases()


__all__ = ['info', 'restart', 'setup', 'start', 'status', 'stop',
           'update', 'version']


builtins.PACKDIR = PACKDIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."))
builtins.COREDIR = COREDIR = os.path.join(PACKDIR, 'pyload')
builtins.USERDIR = USERDIR = os.getenv(
    'APPDATA') if os.name == 'nt' else os.path.expanduser('~')
builtins.REQUEST = None  # TODO: Remove
builtins.ADDONMANAGER = None  # TODO: Remove

# Before changing the cwd, the abspath of the module must be manifested
if 'pyload' in sys.modules:
    sys.modules['pyload'].__path__ = [os.path.abspath(
        p) for p in sys.modules['pyload'].__path__]


# sys.path.append(os.path.join(PACKDIR, 'venv'))
sys.path.append(PACKDIR)
sys.path.append(USERDIR)

# import codecs
# codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)
writer = codecs.getwriter(sys.console_encoding(sys.stdout.encoding))
sys.stdout = writer(sys.stdout, errors="replace")


def info():
    from pyload.utils.struct import Info

    file = os.path.join(os.path.dirname(__file__), "..", "README.md")
    with path.open(file) as f:
        long_description = f.read()

    return Info(
        name=Core.__title__,
        version=Core.__version__,
        status=Core.__status__,
        description=Core.__description__,
        long_description=long_description,
        url="https://pyload.net/",
        download_url="https://github.com/pyload/pyload/releases",
        license=Core.__license__,
        author="pyLoad Team",
        author_email="info@pyload.net",
        maintainer=Core.__authors__[0][0],
        maintainer_email=Core.__authors__[0][1],
        platforms=['Any']
    )


def _list_pids():
    pids = set()
    tmpdir = tempfile.gettempdir()
    info = info()
    for filename in os.listdir(tmpdir):
        if not filename.endswith('.pid'):
            continue
        if not filename.startswith(info.name + '-'):
            continue
        file = os.path.join(tmpdir, filename)
        try:
            with path.open(file, 'rb') as f:
                pid = int(f.read().strip())
        except Exception:
            continue
        else:
            pids.add(pid)
    return sorted(pids)


def status(profile=None):  # NOTE: If not profile, then catch all pyLoad pids
    # NOTE: Include zombie pids
    return [pid for pid in _list_pids() if psutil.pid_exists(pid)]


def version():
    return convert.ver_to_tuple(info().version)


def setup():
    # TODO: Move setup into the pyload package, then call it from setup.py
    from pyload.setup import main
    main()


def update(dependencies=True, reinstall=False, prerelease=False):
    try:
        from pyload.utils.lib import autoupgrade
    except ImportError:
        return
    au = autoupgrade.AutoUpgrade(info().name, verbose=True)
    if reinstall:
        au.upgrade(True, dependencies, prerelease)
    else:
        au.smartupgrade(False, dependencies, prerelease)


def stop(profile=None, wait=300):
    for pid in status(profile):
        try:
            sys.kill_process(pid, wait)
        except Exception:
            continue


def start(profile=None, configdir=None, refresh=0, remote=None, webui=None,
          debug=0, webdebug=0, daemon=False):
    #: Use virtualenv
    # from .. import setup
    # setup.run_venv()

    p = Core(profile, configdir, refresh, debug, webdebug)
    p.start(webui, remote)

    if daemon:
        name = info().name
        app = "{}-{}".format(name, profile or 'default')
        pid = tempfile.mkstemp(
            suffix='.pid', prefix='daemon-{}-'.format(name))[1]
        d = daemonize.Daemonize(app, pid, p.join)
        d.start()

    return p  #: returns process instance


def restart(profile=None, configdir=None, refresh=0, remote=None, webui=None,
            debug=0, webdebug=0, daemon=False):
    stop(profile or 'default')
    return start(profile, configdir, refresh, remote,
                 webui, debug, webdebug, daemon)


# TODO: Implement test suite
def test():
    raise NotImplementedError
