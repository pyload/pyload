#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: vuolter

from __future__ import unicode_literals

import os
from builtins import PACKDIR

from past.builtins import execfile

import pyload

__all__ = ['info', 'main', 'run_venv', 'setup']


def info():
    from pyload.utils.struct import Info

    info = pyload.info()

    keywords = [
        "pyload", "download", "download-manager", "download-station", "downloader",
        "jdownloader", "one-click-hoster", "upload", "upload-manager",
        "upload-station", "uploader"
    ]
    install_requires = [
        "argparse", "daemonize", "future", "psutil", "pycurl", "requests >= 2.0",
        "tld", "validators"
    ]

    extras_require = {
        # 'Archive decompression': ['rarfile'],
        # TODO: Fix `tesserocr` installation
        'Captcha recognition': ["Pillow >= 2.0"],
        'Click\'n\'Load support': ['Js2Py', 'pycryptodomex'],
        'Colored log': ['colorama', 'colorlog'],
        'JavaScript evaluation': ['Js2Py'],
        'Lightweight webserver:sys_platform!="win32"': ['bjoern'],
        'pyLoad auto-update': ['pip'],
        'Remote API support': ['mod_pywebsocket', 'thrift'],
        'SSL connection': ['pyOpenSSL'],
        'Text translation': ['goslate'],
        'Trash support': ['Send2Trash'],
        'Web User Interface': ['Beaker >= 1.6', 'bottle >= 0.10.0', 'pycryptodomex'],
        'Additional features': ['beautifulsoup4', 'bitmath', 'IPy', 'setproctitle'],
        'Additional features:sys_platform!="win32"': ['dbus-python']
    }
    # if os.name != 'nt':
    # extras_require['Lightweight webserver'] = ['bjoern']
    # extras_require['Additional features'].append('dbus-python')

    entry_points = {
        'console_scripts': ['{} = {}:main'.format(info.title.lower(), info.title)]
    }
    tests_require = ['nose', 'requests >= 1.2.2', 'unittest2', 'websocket-client >= 0.8.0']
    classifiers = [
        "Development Status :: {}".format(info.status),
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: {}".format(info.license),
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications",
        "Topic :: Communications :: File Sharing",
        "Topic :: Internet",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: Internet :: WWW/HTTP"
    ]

    return Info(
        keywords=keywords,
        packages=[info.title.lower()],
        include_package_data=True,
        install_requires=install_requires,
        extras_require=extras_require,
        entry_points=entry_points,
        test_suite='nose.collector',
        tests_require=tests_require,
        zip_safe=False,  # TODO: Recheck...
        classifiers=classifiers
    )


def _create_venv(env_dir):
    import virtualenv
    virtualenv.create_environment(env_dir,
                                  site_packages=False,
                                  clear=False,
                                  symlink=False)


def _activate_venv(env_dir):
    activate_script = os.path.join(env_dir, 'bin', 'activate_this.py')
    execfile(activate_script, dict(__file__=activate_script))


def run_venv():
    venv = os.path.join(PACKDIR, "venv")
    _create_venv(venv)
    _activate_venv(venv)


def _set_win_env():
    if os.name != 'nt':
        return
    try:
        os.system('SETX path "%PATH%;{}"'.format(PACKDIR))
    except Exception:
        pass


def _pre_setup():
    info = pyload.info()
    setupinfo = {
        'name': info.title,
        'version': info.version,
        'url': info.url
    }
    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup
        setupinfo.update(requires=["setuptools", "virtualenv"])
    else:
        setupinfo.update(setup_requires=['setuptools'],
                         install_requires=["setuptools", "virtualenv"])
    setup(**setupinfo)


def setup():
    import setuptools
    setupinfo = info()
    setupinfo.update(pyload.info())
    setuptools.setup(**setupinfo)
    _set_win_env()


def main():
    _pre_setup()
    # run_venv()
    setup()


if __name__ == "__main__":
    main()