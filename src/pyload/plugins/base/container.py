# -*- coding: utf-8 -*-
import os
import urllib.parse

from ..helpers import exists
from .decrypter import BaseDecrypter


class BaseContainer(BaseDecrypter):
    __name__ = "Container"
    __type__ = "base"
    __version__ = "0.15"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Base container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mkaay", "mkaay@mkaay.de"), ("Walter Purcaro", "vuolter@gmail.com")]

    def process(self, pyfile):
        """
        Main method.
        """
        self._make_tmpfile()

        self.decrypt(pyfile)

        if self.links:
            self._generate_packages()

        elif not self.packages:
            self.error(self._("No link grabbed"), "decrypt")

        self._delete_tmpfile()

        self._create_packages()

    def _delete_tmpfile(self):
        if os.path.basename(self.pyfile.name).startswith("tmp_"):
            self.remove(self.pyfile.url, try_trash=False)

    def _make_tmpfile(self):
        """
        Loads container to disk if its stored remotely and overwrite url, or check
        existent on several places at disk.
        """
        remote = bool(urllib.parse.urlparse(self.pyfile.url).netloc)

        if remote:
            content = self.load(self.pyfile.url)

            self.pyfile.name = "tmp_" + self.pyfile.name
            self.pyfile.url = os.path.join(
                self.pyload.config.get("general", "storage_folder"), self.pyfile.name
            )

            try:
                with open(self.pyfile.url, mode="wb") as fp:
                    fp.write(content.encode())

            except IOError as exc:
                self.fail(exc)

        elif not exists(self.pyfile.url):
            self.fail(self._("File not found"))
