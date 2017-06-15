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
import re
import shutil

from itertools import chain

from setuptools import Command, find_packages, setup
from setuptools.command.bdist_egg import bdist_egg
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist

# import subprocess


_NAMESPACE = 'pyload'
_PACKAGE = 'pyload.core'
_PACKAGE_NAME = 'pyload.core'
_PACKAGE_PATH = 'src/pyload/core'
_CREDITS = (('Walter Purcaro', 'vuolter@gmail.com', '2015-2017'),
            ('pyLoad Team', 'info@pyload.net', '2009-2015'))


def _read_text(file):
    with io.open(file, encoding='utf-8') as fp:
        text = fp.read().strip()
    try:
        text = str(text)
    except UnicodeEncodeError:
        text = text.encode('utf-8')
    return text


def _write_text(file, text):
    with io.open(file, mode='w', encoding='utf-8') as fp:
        fp.write(text.strip() + '\n')


def _pandoc_convert(text):
    import pypandoc
    return pypandoc.convert_text(text, 'rst', 'markdown').replace('\r', '')


def _docverter_convert(text):
    import requests
    req = requests.post(
        url='http://c.docverter.com/convert',
        data={'from': 'markdown', 'to': 'rst',
              'smart': None, 'normalize': None, 'no_wrap': None,
              'reference_links': None},
        files={'input_files[]': ('.md', text)}
    )
    req.raise_for_status()
    return req.text


def _convert_text(text):
    try:
        return _pandoc_convert(text)
    except Exception as e:
        print(str(e))
        return _docverter_convert(text)


_RE_PURGE = re.compile(r'<.+>')

def _purge_quotes(text):
    return _RE_PURGE.sub('', text).strip()


def _gen_long_description():
    readme = _read_text('README.md')
    history = _read_text('CHANGELOG.md')

    #: keep just the header
    readme = readme.split('\n\n\n', 1)[0]

    text = '{0}\n\n{1}'.format(_purge_quotes(readme), _purge_quotes(history))
    return _convert_text(text)


def get_long_description():
    try:
        text = _read_text('README.rst')
    except IOError:
        text = _gen_long_description()
    return text


_RE_SECTION = re.compile(
    r'^\[([^\s]+)\]\s+([^[\s].+?)(?=^\[|\Z)', flags=re.M | re.S)
_RE_ENTRY = re.compile(r'^\s*(?![#;\s]+)([^\s]+)', flags=re.M)

def _parse_requires(text):
    deps = list(set(
        _RE_ENTRY.findall(_RE_SECTION.split(text, maxsplit=1)[0])))
    extras = {}
    for name, rawdeps in _RE_SECTION.findall(text):
        extras[name] = list(set(pack for pack in _RE_ENTRY.findall(rawdeps)))
    return deps, extras


def get_requires(name):
    file = os.path.join('requirements', name + '.txt')
    text = _read_text(file)
    deps, extras = _parse_requires(text)
    if name.startswith('extra'):
        extras['full'] = list(set(chain(*list(extras.values()))))
        return extras
    return deps


def get_version():
    return _read_text('VERSION')


# def _setx_ntpath():
    # packdir = os.path.abspath(os.path.dirname(__file__))
    # subprocess.call('SETX path "%PATH%;{0}"'.format(packdir), shell=True)


class MakeReadme(Command):
    """
    Create a valid README.rst file
    """
    _READMEFILE = 'README.rst'

    description = 'create a valid README.rst file'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if os.path.isfile(self._READMEFILE):
            return None
        _write_text(self._READMEFILE, _gen_long_description())


class BuildLocale(Command):
    """
    Build the locales
    """
    _LOCALEDIR = os.path.join(_PACKAGE_PATH, 'locale')

    description = 'build the locales'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            os.makedirs(self._LOCALEDIR)
        except OSError as e:
            print(str(e))
        self.run_command('extract_messages')
        self.run_command('init_catalog')
        # self.run_command('download_catalog')
        self.run_command('compile_catalog')


# class DownloadCatalog(Command):
# """
# Download the translation catalog from the remote repository
# """
# description = 'download the translation catalog from the remote repository'
# user_options = []

# def initialize_options(self):
# pass

# def finalize_options(self):
# pass

# def run(self):
# raise NotImplementedError


class PreBuild(Command):
    """
    Prepare for build
    """
    _ABOUTFILE = os.path.join(_PACKAGE_PATH, '__about__.py')
    _ICONFILE = 'media/icon.ico'

    description = 'prepare for build'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def _makeabout(self):
        credits = ', '.join(str(info) for info in _CREDITS)
        text = """# -*- coding: utf-8 -*-

from semver import parse_version_info

__namespace__ = '{0}'
__package__ = '{1}'
__package_name__ = '{2}'
__version__ = '{3}'
__version_info__ = parse_version_info(__version__)
__credits__ = ({4})
""".format(_NAMESPACE, _PACKAGE, _PACKAGE_NAME, get_version(), credits)
        _write_text(self._ABOUTFILE, text)

    def run(self):
        if not os.path.isfile(self._ABOUTFILE):
            self._makeabout()
        shutil.copy(self._ICONFILE, _PACKAGE_PATH)
        self.run_command('build_locale')


class BdistEgg(bdist_egg):
    """
    Custom ``bdist_egg`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('prebuild')
        bdist_egg.run(self)


class BuildPy(build_py):
    """
    Custom ``build_py`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('prebuild')
        build_py.run(self)


class Sdist(sdist):
    """
    Custom ``sdist`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('makereadme')
        sdist.run(self)


NAME = _PACKAGE_NAME
VERSION = get_version()
STATUS = "1 - Planning"
DESC = """Free and Open Source download manager written in Pure Python and
 designed to be extremely lightweight, fully customizable and remotely
 manageable"""
LONG_DESC = get_long_description()
KEYWORDS = [
    "pyload", "download", "download-manager", "download-station", "downloader",
    "jdownloader", "one-click-hoster", "upload", "upload-manager",
    "upload-station", "uploader"
]
URL = "https://pyload.net"
DOWNLOAD_URL = "https://github.com/pyload/pyload/releases"
LICENSE = "GNU Affero General Public License v3"
AUTHOR = _CREDITS[0][0]
AUTHOR_EMAIL = _CREDITS[0][1]
PLATFORMS = ['any']
PACKAGES = find_packages('src')
PACKAGE_DIR = {'': 'src'}
INCLUDE_PACKAGE_DATA = True
NAMESPACE_PACKAGES = [_NAMESPACE]
OBSOLETES = [_NAMESPACE]
INSTALL_REQUIRES = get_requires('install')
SETUP_REQUIRES = get_requires('setup')
TEST_SUITE = 'nose.collector'
TESTS_REQUIRE = get_requires('test')
EXTRAS_REQUIRE = get_requires('extra')
PYTHON_REQUIRES = ">=2.6,!=3.0,!=3.1,!=3.2"
ENTRY_POINTS = {
    'console_scripts': ['{0} = {1}.cli:main'.format(_NAMESPACE, _PACKAGE)]
}
CMDCLASS = {
    'bdist_egg': BdistEgg,
    'build_locale': BuildLocale,
    'build_py': BuildPy,
    # 'download_catalog': DownloadCatalog,
    'makereadme': MakeReadme,
    'prebuild': PreBuild,
    'sdist': Sdist
}
MESSAGE_EXTRACTORS = {
    _PACKAGE_PATH: [('**.py', 'python', None)]
}
ZIP_SAFE = True
CLASSIFIERS = [
    "Development Status :: {0}".format(STATUS),
    "Environment :: Web Environment",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: {0}".format(LICENSE),
    "Natural Language :: English",
    # "Operating System :: MacOS :: MacOS X",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: Implementation :: CPython",
    # "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Communications",
    "Topic :: Communications :: File Sharing",
    "Topic :: Internet",
    "Topic :: Internet :: File Transfer Protocol (FTP)",
    "Topic :: Internet :: WWW/HTTP"
]

setup(
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
    package_dir=PACKAGE_DIR,
    include_package_data=INCLUDE_PACKAGE_DATA,
    namespace_packages=NAMESPACE_PACKAGES,
    obsoletes=OBSOLETES,
    install_requires=INSTALL_REQUIRES,
    setup_requires=SETUP_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=PYTHON_REQUIRES,
    entry_points=ENTRY_POINTS,
    cmdclass=CMDCLASS,
    message_extractors=MESSAGE_EXTRACTORS,
    # test_suite=TEST_SUITE,
    # tests_require=TESTS_REQUIRE,
    zip_safe=ZIP_SAFE,
    classifiers=CLASSIFIERS
)
