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

from __future__ import absolute_import

import codecs
import os
import re
import shutil
from itertools import chain

from setuptools import Command, find_packages, setup
from setuptools.command.bdist_egg import bdist_egg
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop

# import subprocess




def read_text(path):
    with codecs.open(path, encoding='utf-8', errors='ignore') as fp:
        return fp.read().strip()


def write_text(path, text):
    with codecs.open(path, mode='w', encoding='utf-8') as fp:
        fp.write(text.strip() + '\n')


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
    path = os.path.join('requirements', name + '.txt')
    text = read_text(path)
    deps, extras = _parse_requires(text)
    if name.startswith('extra'):
        extras['full'] = list(set(chain(*list(extras.values()))))
        return extras
    return deps


# def _setx_ntpath():
    # packdir = os.path.abspath(os.path.dirname(__file__))
    # subprocess.call('SETX path "%PATH%;{0}"'.format(packdir), shell=True)


class BuildLocale(Command):
    """
    Build the locales
    """
    _LOCALEDIR = 'src/pyload/core/locale'

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


class Configure(Command):
    """
    Prepare for build
    """
    _ABOUTFILE = 'src/pyload/core/__about__.py'
    _ICONFILE = 'media/icon.ico'

    description = 'prepare for build'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def _makeabout(self):
        write_text(self._ABOUTFILE, """# -*- coding: utf-8 -*-

from semver import parse_version_info

__namespace__ = 'pyload'
__package__ = 'pyload.core'
__package_name__ = 'pyload.core'
__version__ = '{0}'
__version_info__ = parse_version_info(__version__)
__credits__ = (('Walter Purcaro', 'vuolter@gmail.com', '2015-2017'),
               ('pyLoad Team', 'info@pyload.net', '2009-2015'))
""".format(read_text('VERSION')))

    def run(self):
        if not os.path.isfile(self._ABOUTFILE):
            self._makeabout()
        shutil.copy(self._ICONFILE, 'src/pyload/core')
        self.run_command('build_locale')


class BdistEgg(bdist_egg):
    """
    Custom ``bdist_egg`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('configure')
        bdist_egg.run(self)


class BuildPy(build_py):
    """
    Custom ``build_py`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('configure')
        build_py.run(self)


class Develop(develop):
    """
    Custom ``develop`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('configure')
        develop.run(self)


setup(
    name='pyload.core',
    version=read_text('VERSION'),
    description='Free and Open Source download manager written in Pure Python '
                'and designed to be extremely lightweight, fully customizable '
                'and remotely manageable',
    long_description=read_text('README.rst'),
    keywords='pyload download download-manager download-station downloader '
             'jdownloader one-click-hoster upload upload-manager '
             'upload-station uploader',
    url='https://pyload.net',
    download_url='https://github.com/pyload/pyload/releases',
    author='Walter Purcaro',
    author_email='vuolter@gmail.com',
    license='GNU Affero General Public License v3',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Affero General Public License v3",
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
        "Topic :: Internet :: WWW/HTTP",
        'Topic :: Software Development :: Libraries :: Python Modules'],
    platforms=['any'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['pyload'],
    obsoletes=['pyload'],
    install_requires=get_requires('install'),
    setup_requires=get_requires('setup'),
    extras_require=get_requires('extra'),
    python_requires='>=2.6,!=3.0,!=3.1,!=3.2',
    entry_points={'console_scripts': ['pyload = pyload.core.cli:main']},
    cmdclass={
        'bdist_egg': BdistEgg,
        'build_locale': BuildLocale,
        'build_py': BuildPy,
        'configure': Configure,
        'develop': Develop
        # 'download_catalog': DownloadCatalog
    },
    message_extractors={'src/pyload/core': [('**.py', 'python', None)]},
    # test_suite='nose.collector',
    # tests_require=get_requires('test'),
    zip_safe=False)
