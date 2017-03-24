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

import io
import os
import subprocess

from itertools import chain

from setuptools import Command, setup
from setuptools.command.sdist import sdist


NAME = "pyload.utils"
VERSION = "0.5.0"
STATUS = "1 - Planning"
DESC = """pyLoad Utils module"""
LONG_DESC='\n\n'.join(
    [io.open("README.md").read(), io.open("HISTORY.md").read()])
KEYWORDS = ["pyload"]
URL = "https://pyload.net"
DOWNLOAD_URL = "https://github.com/pyload/utils/releases"
LICENSE = "AGPLv3"
AUTHOR = "Walter Purcaro"
AUTHOR_EMAIL = "vuolter@gmail.com"
PLATFORMS = ['any']
PACKAGES = ['pyload', 'pyload/utils']
INCLUDE_PACKAGE_DATA = True
NAMESPACE_PACKAGES = ['pyload']
INSTALL_REQUIRES = [
    'IPy', 'Send2Trash', 'colorclass', 'filetype', 'goslate', 'psutil',
    'setproctitle', 'tld', 'validators'
]
SETUP_REQUIRES = ['readme_renderer', 'recommonmark']
# TEST_SUITE = ''
# TESTS_REQUIRE = []
EXTRAS_REQUIRE = {
    'dbus;os_name!="nt"': ['dbus-python'],
    'bitmath': ['bitmath']
}
EXTRAS_REQUIRE['full'] = list(set(chain(*EXTRAS_REQUIRE.values())))
PYTHON_REQUIRES = ">=2.6,!=3.0,!=3.1,!=3.2"
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
    "Programming Language :: Python :: 3.7",
    "Topic :: Communications",
    "Topic :: Communications :: File Sharing",
    "Topic :: Internet",
    "Topic :: Internet :: File Transfer Protocol (FTP)",
    "Topic :: Internet :: WWW/HTTP"
]
SETUP_MAP = dict(
    name=NAME,
    version=VERSION,
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
    namespace_packages=NAMESPACE_PACKAGES,
    install_requires=INSTALL_REQUIRES,
    setup_requires=SETUP_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=PYTHON_REQUIRES,
    # test_suite=TEST_SUITE,
    # tests_require=TESTS_REQUIRE,
    zip_safe=ZIP_SAFE,
    classifiers=CLASSIFIERS
)

setup(**SETUP_MAP)
