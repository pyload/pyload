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

# from itertools import chain

from setuptools import Command, find_packages, setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist


def _extract_text(path, fromline=None, toline=None):
    text = None
    path = os.path.join(os.path.dirname(__file__), path)
    with io.open(path) as fp:
        if fromline or toline:
            text = ''.join(fp.readlines()[fromline:toline])
        else:
            text = fp.read()
    return text.strip()


def _pandoc_convert(text):
    import pypandoc
    return pypandoc.convert_text(text, 'rst', 'markdown_github')


def _docverter_convert(text):
    import requests
    req = requests.post(
        url='http://c.docverter.com/convert',
        data={'from': 'markdown', 'to': 'rst'},
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


def _purge_text(text):
    return re.sub('.*<.+>.*', '', text).strip()


def _gen_long_description(fromline=None, toline=None, rst=False):
    readme = _purge_text(_extract_text('README.md', fromline, toline))
    history = _purge_text(_extract_text('CHANGELOG.md'))
    desc = '\r\n\r\n'.join([readme, history])
    try:
        return _convert_text(desc)
    except Exception as e:
        if rst:
            raise
        else:
            print(str(e))
    return desc


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


class BuildLocale(Command):
    """
    BuildPy the locales
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
        except OSError as e:
            print(str(e))
            return None
        self.run_command('extract_messages')
        self.run_command('init_catalog')
        # self.run_command('download_catalog')
        self.run_command('compile_catalog')


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


class BuildReadme(Command):
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
        if os.path.isfile('README.rst'):
            return None
        with io.open('README.rst', mode='w') as fp:
            fp.write(_gen_long_description(toline=30))


class BuildPy(build_py):
    """
    Custom ``build_py`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('build_readme')
            self.run_command('build_locale')
        build_py.run(self)


class Sdist(sdist):
    """
    Custom ``sdist`` command
    """
    def run(self):
        if not self.dry_run:
            self.run_command('build_py')
        sdist.run(self)


NAME = "pyload.config"
VERSION = _get_version()
STATUS = "1 - Planning"
DESC = """pyLoad Config module"""
LONG_DESC = _get_long_description(toline=30)
KEYWORDS = ["pyload"]
URL = "https://pyload.net"
DOWNLOAD_URL = "https://github.com/pyload/config/releases"
LICENSE = "GNU Affero General Public License v3"
AUTHOR = "Walter Purcaro"
AUTHOR_EMAIL = "vuolter@gmail.com"
PLATFORMS = ['any']
PACKAGES = find_packages('src')
PACKAGE_DIR = {'': 'src'}
INCLUDE_PACKAGE_DATA = True
NAMESPACE_PACKAGES = ['pyload']
INSTALL_REQUIRES = _get_requires('install.txt')
SETUP_REQUIRES = _get_requires('setup.txt')
# TEST_SUITE = ''
# TESTS_REQUIRE = []
# EXTRAS_REQUIRE = {}
# EXTRAS_REQUIRE['full'] = list(set(chain(*EXTRAS_REQUIRE.values())))
PYTHON_REQUIRES = ">=2.6,!=3.0,!=3.1,!=3.2"
CMDCLASS = {
    'build_locale': BuildLocale,
    'build_py': BuildPy,
    'build_readme': BuildReadme,
    'download_catalog': DownloadCatalog,
    'sdist': Sdist
}
MESSAGE_EXTRACTORS = {
    'src': [('**.py', 'python', None)]
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
    package_dir=PACKAGE_DIR,
    include_package_data=INCLUDE_PACKAGE_DATA,
    namespace_packages=NAMESPACE_PACKAGES,
    install_requires=INSTALL_REQUIRES,
    setup_requires=SETUP_REQUIRES,
    # extras_require=EXTRAS_REQUIRE,
    python_requires=PYTHON_REQUIRES,
    cmdclass=CMDCLASS,
    message_extractors=MESSAGE_EXTRACTORS,
    # test_suite=TEST_SUITE,
    # tests_require=TESTS_REQUIRE,
    zip_safe=ZIP_SAFE,
    classifiers=CLASSIFIERS
)

setup(**SETUP_MAP)
