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


def _get_long_description():
    try:
        import requests
    except ImportError:
        return None
    with io.open('README.md') as fp1:
        fp1.readline()  #: Avoid first line, because not CommonMark-compliant
        with io.open('HISTORY.md') as fp2:
            body = '\r\n\r\n'.join([fp1.read(), fp2.read()])
    req = requests.post(
        url='http://c.docverter.com/convert',
        data={'from': 'markdown', 'to': 'rst'},
        files={'input_files[]': ('DESCRIPTION.md', body)}
    )
    return req.text if req.ok else None
    
    
NAME = "pyload.utils2"
VERSION = io.open('VERSION').readline()
STATUS = "1 - Planning"
DESC = """pyLoad Utils module"""
LONG_DESC=_get_long_description() or ""
KEYWORDS = ["pyload"]
URL = "https://pyload.net"
DOWNLOAD_URL = "https://github.com/pyload/utils/releases"
LICENSE = "GNU Affero General Public License v3"
AUTHOR = "Walter Purcaro"
AUTHOR_EMAIL = "vuolter@gmail.com"
PLATFORMS = ['any']
PACKAGES = ['pyload', 'pyload/utils']
INCLUDE_PACKAGE_DATA = True
NAMESPACE_PACKAGES = ['pyload']
INSTALL_REQUIRES = io.open(
    os.path.join('requirements', 'install.txt')).read().splitlines()
SETUP_REQUIRES = io.open(
    os.path.join('requirements', 'setup.txt')).read().splitlines()
# TEST_SUITE = ''
# TESTS_REQUIRE = []
EXTRAS_REQUIRE = {
    'bitmath': ['bitmath'],
    'dbus;os_name!="nt"': ['dbus-python'],
    'magic;os_name!="nt"': ['python-magic']
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
    "Programming Language :: Python :: Implementation :: PyPy",
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
