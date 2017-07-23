# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import os
from builtins import DATADIR
from tempfile import mkstemp

from future import standard_library
from pkg_resources import get_default_cache

import autoupgrade
import daemonize
from pyload.utils.fs import makedirs, remove

from pyload.core.__about__ import __namespace__, __package_name__, __version__
from pyload.core.init import Core, _pmap

standard_library.install_aliases()


def _mkdprofile(profile=None, rootdir=None):
    DEFAULT_PROFILE = 'default'
    if not profile:
        profile = DEFAULT_PROFILE
    if rootdir is None:
        dirname = '.' + __namespace__ if os.name != 'nt' else __namespace__
        configdir = os.path.join(DATADIR, dirname)
    else:
        configdir = os.path.expanduser(rootdir)
    profiledir = os.path.realpath(os.path.join(configdir, profile))
    makedirs(profiledir, exist_ok=True)
    return profiledir


def version():
    return __version__


def status(profile=None, configdir=None):
    profiledir = _mkdprofile(profile, configdir)
    if profiledir not in _pmap:
        return None
    inst = _pmap[profiledir]
    return inst.session.get('current', 'profile', 'pid')


# def setup(profile=None, configdir=None):
    # from pyload.setup import SetupAssistant
    # profiledir = _mkdprofile(profile, configdir)
    # configfile = os.path.join(profiledir, 'config.ini')
    # return SetupAssistant(configfile, version()).start()


def quit(profile=None, configdir=None):
    profiledir = _mkdprofile(profile, configdir)
    if profiledir not in _pmap:
        return None
    inst = _pmap[profiledir]
    inst.shutdown()


def start(
        profile=None, configdir=None, tmpdir=None, debug=None, restore=None,
        daemon=False):
    profiledir = _mkdprofile(profile, configdir)

    inst = Core(profiledir, tmpdir, debug, restore)
    inst.start()

    if daemon:
        pidfile = mkstemp(
            suffix='.pid', prefix='daemon-', dir=inst.cachedir)[1]
        d = daemonize.Daemonize("pyLoad", pidfile, inst.join, logger=inst.log)
        d.start()

    return inst  # returns process instance


def restart(*args, **kwargs):
    configdir = kwargs.get('configdir', args[1])
    profile = kwargs.get('profile', args[0])
    quit(profile, configdir)
    return start(*args, **kwargs)


def upgrade():
    if _pmap:
        raise RuntimeError
    autoupgrade.upgrade(__package_name__, dependencies=True, restart=True)


def cleanup():
    if _pmap:
        raise RuntimeError
    packdir = os.path.join(get_default_cache(), __package_name__)
    remove(packdir, ignore_errors=True)


# def test():
    # raise NotImplementedError
