# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import urlparse

from .Crypter import Crypter
from .misc import encode, exists


class Container(Crypter):
    __name__ = "Container"
    __type__ = "container"
    __version__ = "0.14"
    __status__ = "stable"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """Base container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de"),
                   ("Walter Purcaro", "vuolter@gmail.com")]

    def process(self, pyfile):
        """
        Main method
        """
        self._make_tmpfile()

        self.decrypt(pyfile)

        if self.links:
            self._generate_packages()

        elif not self.packages:
            self.error(_("No link grabbed"), "decrypt")

        self._delete_tmpfile()

        self._create_packages()

    def _delete_tmpfile(self):
        if os.path.basename(self.pyfile.name).startswith("tmp_"):
            self.remove(self.pyfile.url, trash=False)

    def _make_tmpfile(self):
        """
        Loads container to disk if its stored remotely and overwrite url,
        or check existent on several places at disk
        """
        remote = bool(urlparse.urlparse(self.pyfile.url).netloc)

        if remote:
            content = self.load(self.pyfile.url)

            self.pyfile.name = "tmp_" + self.pyfile.name
            self.pyfile.url = os.path.join(
                self.pyload.config.get(
                    'general',
                    'download_folder'),
                self.pyfile.name)

            try:
                with open(self.pyfile.url, "wb") as f:
                    f.write(encode(content))

            except IOError, e:
                self.fail(e.message)

        elif not exists(self.pyfile.url):
            self.fail(_("File not found"))
