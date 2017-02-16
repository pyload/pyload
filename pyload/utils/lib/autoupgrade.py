# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
import os
import re
import sys
import urllib.parse
from builtins import map, object

import pip
import pkg_resources
import requests

from pyload.utils import convert


class NoVersionsError(Exception):
    """
    No versions found for package.
    """

    def __str__(self):
        return """<NoVersionsError {}>""".format(self.message)


class PIPError(Exception):
    """
    PIP process failure.
    """

    def __str__(self):
        return """<PIPError {}>""".format(self.message)


class PkgNotFoundError(Exception):
    """
    No package found.
    """

    def __str__(self):
        return """<PkgNotFoundError {}>""".format(self.message)


class AutoUpgrade(object):
    """
    AutoUpgrade class, holds one package.
    """

    def __init__(self, pkg, index=None, verbose=False):
        """
        Args:
            pkg (str): name of package
            index (str): alternative index, if not given default for *pip* will be used. Include
                         full index url, e.g. https://example.com/simple
        """
        self.pkg = pkg
        self.verbose = verbose
        if index:
            self.index = index.rstrip('/')
            self._index = True
        else:
            self.index = "https://pypi.python.org/simple"
            self._index = False

    def smartupgrade(self, restart=True, dependencies=False, prerelease=False):
        """
        Upgrade the package if there is a later version available.
        Args:
            restart: restart app if True
            dependencies: update package dependencies if True (see pip --no-deps)
            prerelease: update to pre-release and development versions
        """
        if not self.check():
            return
        if self.verbose:
            print("Upgrading {}".format(self.pkg))
        self.upgrade(False, dependencies, prerelease)
        if restart:
            self.restart()

    def upgrade(self, reinstall=False, dependencies=False, prerelease=False):
        """
        Upgrade the package unconditionaly
        Args:
            reinstall: reinstall all packages even if they are already up-to-date
            dependencies: update package dependencies if True (see pip --no-deps)
            prerelease: update to pre-release and development versions
        Returns True if pip was sucessful
        """
        pip_args = ['install', self.pkg]

        found = self._get_current() != (-1)
        if found:
            pip_args.append("--upgrade")

        if reinstall:
            pip_args.append(
                "--force-reinstall" if found else "--ignore-installed")

        if not dependencies:
            pip_args.append("--no-deps")

        if prerelease:
            pip_args.append("--pre")

        proxy = os.environ.get('http_proxy')
        if proxy:
            pip_args.extend(['--proxy', proxy])

        if self._index:
            pip_args.extend(['-i', self.index])

        try:
            ecode = pip.main(args=pip_args)
        except TypeError:
            # pip changed in 0.6.0 from initial_args to args, this is for backwards compatibility
            # can be removed when pip 0.5 is no longer in use at all (approx.
            # year 2025)
            ecode = pip.main(initial_args=pip_args)

        if ecode != 0:
            raise PIPError(ecode)

    def restart(self):
        """
        Restart application with same args as it was started.
        Does **not** return
        """
        if self.verbose:
            print("Restarting {} {}".format(sys.executable, sys.argv))
        os.execl(sys.executable, *([sys.executable] + sys.argv))

    def check(self):
        """
        Check if pkg has a later version
        Returns true if later version exists
        """
        current = self._get_current()
        highest = self._get_highest_version()
        return highest > current

    def _get_current(self):
        try:
            current = convert.ver_to_tuple(
                pkg_resources.get_distribution(self.pkg).version)
        except pkg_resources.DistributionNotFound:
            current = (-1,)
        return current

    def _get_highest_version(self):
        url = urllib.parse.urljoin(self.index, self.pkg)
        r = requests.get(url)
        if r.status_code != requests.codes.ok:
            raise PkgNotFoundError
        pattr = r'>{}-(.+?)<'.format(self.pkg)
        versions = map(convert.ver_to_tuple,
                       re.findall(pattr, r.text, flags=re.I))
        if not versions:
            raise NoVersionsError
        return max(versions)
