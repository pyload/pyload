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


def _extract_text(path, fromline=None, toline=None):
    text = None
    with io.open(path) as fp:
        if fromline or toline:
            text = ''.join(fp.readlines()[fromline:toline])
        else:
            text = fp.read()
    return text.strip()


def _gen_long_description(fromline=None, toline=None):
    import requests

    readme = _extract_text('README.md', fromline, toline)
    history = _extract_text('CHANGELOG.md')
    desc = '\r\n\r\n'.join([readme, history])
    req = requests.post(
        url='http://c.docverter.com/convert',
        data={'from': 'markdown', 'to': 'rst'},
        files={'input_files[]': ('DESCRIPTION.md', desc)}
    )
    req.raise_for_status()
    return req.text


def _get_long_description(fromline=None, toline=None):
    try:
        return _extract_text('README.rst')
    except IOError:
        return _gen_long_description(fromline, toline)


def _get_requires(filename):
    path = os.path.join('requirements', filename)
    return _extract_text(path).splitlines()


def _get_version():
    return _extract_text('VERSION')


def _setx_ntpath():
    if os.name != 'nt':
        return None
    packdir = os.path.abspath(os.path.dirname(__file__))
    subprocess.call('SETX path "%PATH%;{0}"'.format(packdir), shell=True)


class BuildLocale(Command):
    """
    Build the locales
    """
    description = 'build the locales'
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
        # self.run_command('download_catalog')
        self.run_command('compile_catalog')


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
        self.run_command('make_readme')
        self.run_command('build_locale')


class DownloadCatalog(Command):
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


class MakeReadme(Command):
    """
    Create a valid README.rst file
    """
    description = 'create a valid README.rst file'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with io.open('README.rst', mode='w') as fp:
            fp.write(_gen_long_description(fromline=1, toline=36))


class Install(install):
    """
    Custom ``install`` command
    """
    def run(self):
        install.run(self)
        _setx_ntpath()


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
LONG_DESC = _get_long_description(fromline=1, toline=36)
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
TESTS_REQUIRE = _get_requires('test.txt')
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
    'build_locale': BuildLocale,
    'download_catalog': DownloadCatalog,
    'install': Install,
    'make_readme': MakeReadme,
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
