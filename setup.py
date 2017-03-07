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

from __future__ import absolute_import, division, unicode_literals

import os
import subprocess

import setuptools.command.build_py

from setuptools import setup as _setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.sdist import sdist

import distutils.cmd
import distutils.log
from distutils.cmd import Command


__all__ = ['info', 'setup']


VERSION = "0.5.0"
STATUS = "3 - Alpha"
LICENSE = "AGPLv3"

PACKDIR = os.path.abspath(os.path.dirname(__file__))


class import_cldr(Command):
    description = 'imports and converts the CLDR data'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    # def run(self):
        # subprocess.check_call(
        # [sys.executable, 'scripts/download_import_cldr.py'])


class Build(setuptools.command.build_py.build_py):
    """Custom build command."""

    def run(self):
        self.run_command('pylint')
        setuptools.command.build_py.build_py.run(self)


class Example(distutils.cmd.Command):
    """A custom command to run Pylint on all Python source files."""

    description = 'run Pylint on Python source files'
    user_options = [
        # The format is (long option, short option, description).
        ('pylint-rcfile=', None, 'path to Pylint config file'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        # Each user option must be listed here with their default value.
        self.pylint_rcfile = ''

    def finalize_options(self):
        """Post-process options."""
        if self.pylint_rcfile:
            assert os.path.exists(self.pylint_rcfile), (
                'Pylint config file %s does not exist.' % self.pylint_rcfile)

    def run(self):
        """Run command."""
        command = ['/usr/bin/pylint']
        if self.pylint_rcfile:
            command.append('--rcfile=%s' % self.pylint_rcfile)
        command.append(os.getcwd())
        self.announce(
            'Running command: %s' % str(command),
            level=distutils.log.INFO)
        subprocess.check_call(command)


def compile_webui():
    subprocess.call("echo Hello World", shell=True)


class Develop(develop):
    """
    Custom ``develop`` command
    """

    def run(self):
        compile_webui()
        develop.run(self)


class Install(install):
    """
    Custom ``install`` command
    """

    def run(self):
        compile_webui()
        install.run(self)


class Sdist(sdist):
    """
    Custom ``sdist`` command
    """

    def run(self):
        # compile_webui()
        self.run_command('compile_catalog')
        sdist.run(self)


def _gen_info():
    keywords = [
        "pyload", "download", "download-manager", "download-station", "downloader",
        "jdownloader", "one-click-hoster", "upload", "upload-manager",
        "upload-station", "uploader"
    ]
    install_requires = [
        'argparse ; python_version < "2.7"',
        'configparser ; python_version < "3.5"', 'daemonize',
        'enum34 ; python_version < "3.4"', 'future', 'psutil',
        'pycurl', 'requests >= 2.0', 'tld', 'validators'
    ]
    tests_require = [
        'future', 'nose', 'requests >= 1.2.2', 'unittest2',
        'websocket-client >= 0.8'
    ]
    setup_requires = [
        'Babel', 'readme_renderer',
        'sphinx <= 1.4 ; python_version in ("2.6", "3.3")',
        'sphinx > 1.4 ; python_version not in ("2.6", "3.3")',
    ]
    extras_require = {
        # 'Archive decompression': ['rarfile'],
        # TODO: Fix `tesserocr` installation
        'Captcha recognition': ["Pillow >= 2.0"],
        'Click\'n\'Load support': ['Js2Py', 'pycryptodome'],
        'Colored log': ['colorclass', 'colorlog'],
        'JavaScript evaluation': ['Js2Py'],
        'Lightweight webserver:os_name!="nt"': ['bjoern'],
        'Remote API support': ['mod_pywebsocket', 'thrift'],
        'SSL connection': ['pyOpenSSL'],
        'Text translation': ['goslate'],
        'Trash support': ['Send2Trash'],
        'Web User Interface': ['Beaker >= 1.6', 'bottle >= 0.10', 'pycryptodome'],
        'pyLoad auto-update': ['autoupgrade-ng'],
        'pyLoad test-suite': tests_require,
        'Additional features': [
            'beautifulsoup4', 'bitmath', 'dbus-python ; os_name != "nt"',
            'IPy', 'setproctitle'
        ],
    }
    entry_points = {
        'console_scripts': ['pyload = pyLoad:main']
    }
    cmdclass = {
        # 'build_py': Build,
        # 'develop': Develop,
        # 'install': Install,
        'sdist': Sdist
    }
    message_extractors = {
        'pyload': [
            ('**.py', 'python', None),
            ('webui/app/scripts/**.js', 'javascript', None)
        ]
    }
    classifiers = [
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
    info = dict(
        name="pyload-ng",
        version=VERSION,
        status=STATUS,
        description="""Free and Open Source download manager written in pure Python and designed to be extremely lightweight, easily extensible and fully manageable via web""",
        long_description="README.rst",
        keywords=keywords,
        url="https://pyload.net/",
        download_url="https://github.com/pyload/pyload/releases",
        license=LICENSE,
        author="Walter Purcaro",
        author_email="vuolter@gmail.com",
        platforms=['any'],
        packages=['pyload'],
        include_package_data=True,
        # exclude_package_data={'pyload': ['docs*', 'scripts*', 'tests*']},  #:
        # exluced from build but not from sdist
        namespace_packages=['pyload'],
        install_requires=install_requires,
        setup_requires=setup_requires,
        extras_require=extras_require,
        python_requires='>=2.6,!=3.0,!=3.1,!=3.2',
        entry_points=entry_points,
        cmdclass=cmdclass,
        message_extractors=message_extractors,
        test_suite='nose.collector',
        tests_require=tests_require,
        zip_safe=False,
        classifiers=classifiers
    )
    return info

info = _gen_info()


# def _create_venv(envdir):
# import virtualenv
# virtualenv.create_environment(envdir,
# site_packages=False,
# clear=False,
# symlink=False)


# def _activate_venv(envdir):
# activate_script = os.path.join(envdir, 'bin', 'activate_this.py')
# execfile(activate_script, dict(__file__=activate_script))


# def run_venv():
# venv = os.path.join(PACKDIR, "venv")
# _create_venv(venv)
# _activate_venv(venv)


def _set_win_env():
    if os.name != 'nt':
        return None
    try:
        subprocess.call('SETX path "%PATH%;{0}"'.format(PACKDIR), shell=True)
    except Exception:
        pass


def setup():
    _setup(**info)
    _set_win_env()


if __name__ == '__main__':
    setup()
