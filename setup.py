#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

from __future__ import absolute_import, division

import os
import subprocess

from itertools import chain
from setuptools import Command, setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.sdist import sdist


def _setx_path():
    if os.name != 'nt':
        return None
    try:
        packdir = os.path.abspath(os.path.dirname(__file__))
        subprocess.call('SETX path "%PATH%;{0}"'.format(packdir), shell=True)
    except Exception:
        pass


class Build(build_py):
    """
    Custom ``build`` command
    """
    def run(self):
        self.run_command('compile_webui')
        # self.run_command('compile_catalog')
        build_py.run(self)


class CompileWebui(Command):
    """
    Compile the web user interface
    """
    description = 'compile the web user interface'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        return subprocess.call("cd pyload/webui/app && npm install @modules", shell=True)


class Develop(develop):
    """
    Custom ``develop`` command
    """
    def run(self):
        self.run_command('compile_webui')
        develop.run(self)


class Install(install):
    """
    Custom ``install`` command
    """
    def run(self):
        self.run_command('compile_webui')
        install.run(self)
        _setx_path()


class Sdist(sdist):
    """
    Custom ``sdist`` command
    """
    def run(self):
        self.run_command('compile_webui')
        # self.run_command('compile_catalog')
        sdist.run(self)


NAME = "pyload-ng"
VERSION = "0.5.0"
STATUS = "3 - Alpha"
DESC = """Free and Open Source download manager written in pure Python and
designed to be extremely lightweight, easily extensible and fully manageable
via web"""
LONG_DESC="README.rst"
KEYWORDS = [
    "pyload", "download", "download-manager", "download-station", "downloader",
    "jdownloader", "one-click-hoster", "upload", "upload-manager",
    "upload-station", "uploader"
]
URL = "https://pyload.net/"
DOWNLOAD_URL = "https://github.com/pyload/pyload/releases"
LICENSE = "AGPLv3"
AUTHOR = "Walter Purcaro"
AUTHOR_EMAIL = "vuolter@gmail.com"
PLATFORMS = ['any']
PACKAGES = ['pyload', 'pyload/config', 'pyload/core', 'pyload/plugins','pyload/rpc', 'pyload/setup', 'pyload/utils', 'pyload/webui']
INCLUDE_PACKAGE_DATA = True
EXCLUDE_PACKAGE_DATA = {
    'pyload': ['docs*', 'tests*']
}
NAMESPACE_PACKAGES = ['pyload']
INSTALL_REQUIRES = [
    'argparse;python_version<"2.7"', 'autoupgrade-ng',
    'configparser;python_version<"3.5"', 'daemonize',
    'enum34;python_version<"3.4"', 'future', 'psutil', 'pycurl',
    'requests>=2.0', 'tld', 'validators'
]
SETUP_REQUIRES = [
    'Babel', 'readme_renderer',
    'sphinx<=1.4;python_version=="2.6" or python_version=="3.3"',
    'sphinx>1.4;python_version=="2.7" or python_version>"3.3"'
]
TEST_SUITE = 'nose.collector'
TESTS_REQUIRE = [
    'future', 'nose', 'requests>=1.2.2', 'unittest2',
    'websocket-client>=0.8'
]
EXTRAS_REQUIRE = {
    # 'unrar': ['rarfile'],
    # TODO: Fix `tesserocr` installation
    'cnl': ['Js2Py', 'pycryptodome'],
    'colorlog': ['colorclass', 'colorlog'],
    'ocr': ['Pillow>=2.0'],
    'rpc': ['mod_pywebsocket', 'thrift'],
    'trash': ['Send2Trash'],
    'webui': ['Beaker>=1.6', 'bottle>=0.10', 'pycryptodome'],
    'extra': [
        'IPy', 'bitmath', 'bjoern;os_name!="nt"',
        'dbus-python;os_name!="nt"', 'goslate', 'setproctitle'
    ]
}
EXTRAS_REQUIRE['full'] = list(chain(*EXTRAS_REQUIRE.values()))
PYTHON_REQUIRES = ">=2.6,!=3.0,!=3.1,!=3.2"
ENTRY_POINTS = {
    'console_scripts': ['pyload = pyLoad:main']
}
CMDCLASS = {
    'build_py': Build,
    'compile_webui': CompileWebui,
    'develop': Develop,
    'install': Install,
    'sdist': Sdist
}
MESSAGE_EXTRACTORS = {
    'pyload': [
        ('**.py', 'python', None),
        ('webui/app/scripts/**.js', 'javascript', None)
    ]
}
ZIP_SAFE = False
CLASSIFIERS = [
    "Development Status :: {0}".format(STATUS),
    "Environment :: Web Environment",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: {0}".format(LICENSE),
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
SETUP_MAP = dict(
    name=NAME,
    version=VERSION,
    status=STATUS,
    description=DESC,
    long_description=LONG_DESC,
    keywords=KEYWORDS,
    url=URL,
    download_url=DOWNLOAD_URL,
    license=LICENSE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    platforms=PLATFORMS,
    packages=PACKAGES,
    include_package_data=INCLUDE_PACKAGE_DATA,
    exclude_package_data=EXCLUDE_PACKAGE_DATA,
    namespace_packages=NAMESPACE_PACKAGES,
    install_requires=INSTALL_REQUIRES,
    setup_requires=SETUP_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=PYTHON_REQUIRES,
    entry_points=ENTRY_POINTS,
    cmdclass=CMDCLASS,
    message_extractors=MESSAGE_EXTRACTORS,
    test_suite=TEST_SUITE,
    tests_require=TESTS_REQUIRE,
    zip_safe=ZIP_SAFE,
    classifiers=CLASSIFIERS
)

setup(**SETUP_MAP)
