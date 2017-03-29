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
from setuptools.command.install import install
from setuptools.command.sdist import sdist


def _get_long_description(fromline=None, lines=None):
    try:
        import requests
    except ImportError:
        return None
    with io.open('README.md') as fp1:
        readme = ''.join(fp1.readlines()[fromline:lines])
    with io.open('CHANGELOG.md') as fp2:
        desc = '\r\n\r\n\r\n\r\n'.join([readme, fp2.read()])
    req = requests.post(
        url='http://c.docverter.com/convert',
        data={'from': 'markdown', 'to': 'rst'},
        files={'input_files[]': ('DESCRIPTION.md', desc)}
    )
    return req.text if req.ok else None

    
def _get_requires(filename):
    path = os.path.join('requirements', filename)
    with io.open(path) as fp:
        return fp.read().splitlines()

        
def _get_version():
    return io.open('VERSION').read().strip()
    
    
def _setx_path():
    if os.name != 'nt':
        return None
    try:
        packdir = os.path.abspath(os.path.dirname(__file__))
        subprocess.call('SETX path "%PATH%;{0}"'.format(packdir), shell=True)
    except Exception:
        pass


class Configure(Command):
    """
    Configure the package
    """
    description = 'configure the package'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            os.mkdir('locale')
        except OSError:
            pass
        self.run_command('extract_messages')
        self.run_command('init_catalog')
        # self.run_command('get_catalog')
        self.run_command('compile_catalog')


class GetCatalog(Command):
    """
    Download the translation catalog from the remote repository
    """
    description = 'download the translation catalog from the remote repository'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise NotImplementedError


class Install(install):
    """
    Custom ``install`` command
    """
    def run(self):
        install.run(self)
        _setx_path()


class Sdist(sdist):
    """
    Custom ``sdist`` command
    """
    def run(self):
        self.run_command('configure')
        sdist.run(self)


NAME = "pyload.core"
VERSION = _get_version()
STATUS = "2 - Pre-Alpha"
DESC = """Free and Open Source download manager written in Pure Python and
designed to be extremely lightweight, fully customizable and remotely
manageable"""
LONG_DESC = _get_long_description(fromline=2, lines=20) or ""
KEYWORDS = [
    "pyload", "download", "download-manager", "download-station", "downloader",
    "jdownloader", "one-click-hoster", "upload", "upload-manager",
    "upload-station", "uploader"
]
URL = "https://pyload.net"
DOWNLOAD_URL = "https://github.com/pyload/pyload/releases"
LICENSE = "GNU Affero General Public License v3"
AUTHOR = "Walter Purcaro"
AUTHOR_EMAIL = "vuolter@gmail.com"
PLATFORMS = ['any']
PACKAGES = ['pyload', 'pyload/core', 'pyload/plugins']
INCLUDE_PACKAGE_DATA = True
NAMESPACE_PACKAGES = ['pyload']
INSTALL_REQUIRES = _get_requires('install.txt')
SETUP_REQUIRES = _get_requires('setup.txt')
TEST_SUITE = 'nose.collector'
TESTS_REQUIRE = [
    'future', 'nose', 'requests>=1.2.2', 'unittest2',
    'websocket-client>=0.8'
]
EXTRAS_REQUIRE = {
    'colorlog': ['colorlog'],
    'rpc': ['pyload.rpc'],
    'setup': ['pyload.setup'],
    'webui': ['pyload.webui']
}
EXTRAS_REQUIRE['full'] = list(set(chain(*EXTRAS_REQUIRE.values())))
PYTHON_REQUIRES = ">=2.6,!=3.0,!=3.1,!=3.2"
ENTRY_POINTS = {
    'console_scripts': ['pyload = pyLoad:main']
}
CMDCLASS = {
    'configure': Configure,
    'get_catalog': GetCatalog,
    'install': Install,
    'sdist': Sdist
}
MESSAGE_EXTRACTORS = {
    'pyload': [('**.py', 'python', None)]
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
    entry_points=ENTRY_POINTS,
    cmdclass=CMDCLASS,
    message_extractors=MESSAGE_EXTRACTORS,
    test_suite=TEST_SUITE,
    tests_require=TESTS_REQUIRE,
    zip_safe=ZIP_SAFE,
    classifiers=CLASSIFIERS
)

setup(**SETUP_MAP)
