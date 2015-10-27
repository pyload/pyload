# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import re

from module.plugins.internal.Crypter import Crypter
from module.plugins.internal.utils import encode, exists, fs_join


class Container(Crypter):
    __name__    = "Container"
    __type__    = "container"
    __version__ = "0.09"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"            , "bool", "Activated"                          , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Base container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay"         , "mkaay@mkaay.de"   ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def process(self, pyfile):
        """
        Main method
        """
        self._load2disk()

        self.decrypt(pyfile)

        self.delete_tmp()

        if self.links:
            self._generate_packages()

        elif not self.packages:
            self.error(_("No link grabbed"), "decrypt")

        self._create_packages()


    def _load2disk(self):
        """
        Loads container to disk if its stored remotely and overwrite url,
        or check existent on several places at disk
        """
        if self.pyfile.url.startswith("http"):
            self.pyfile.name = re.findall("([^\/=]+)", self.pyfile.url)[-1]
            content = self.load(self.pyfile.url)
            self.pyfile.url = fs_join(self.pyload.config.get("general", "download_folder"), self.pyfile.name)
            try:
                with open(self.pyfile.url, "wb") as f:
                    f.write(encode(content))

            except IOError, e:
                self.fail(e)

        else:
            self.pyfile.name = os.path.basename(self.pyfile.url)

            if not exists(self.pyfile.url):
                if exists(fs_join(pypath, self.pyfile.url)):
                    self.pyfile.url = fs_join(pypath, self.pyfile.url)
                else:
                    self.fail(_("File not exists"))
            else:
                self.data = self.pyfile.url  #@NOTE: ???


    def delete_tmp(self):
        if not self.pyfile.name.startswith("tmp_"):
            return

        try:
            os.remove(self.pyfile.url)
        except OSError, e:
            self.log_warning(_("Error removing `%s`") % self.pyfile.url, e)
