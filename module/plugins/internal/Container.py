# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import re

from module.plugins.internal.Crypter import Crypter
from module.utils import save_join as fs_join


class Container(Crypter):
    __name__    = "Container"
    __type__    = "container"
    __version__ = "0.04"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    def preprocessing(self, thread):
        """
        Prepare
        """
        self.setup()
        self.thread = thread

        self._load2disk()

        self.decrypt(self.pyfile)
        self.delete_tmp()

        self._create_packages()


    def _load2disk(self):
        """
        Loads container to disk if its stored remotely and overwrite url,
        or check existent on several places at disk
        """
        if self.pyfile.url.startswith("http"):
            self.pyfile.name = re.findall("([^\/=]+)", self.pyfile.url)[-1]
            content = self.load(self.pyfile.url)
            self.pyfile.url = fs_join(self.core.config.get("general", "download_folder"), self.pyfile.name)
            try:
                with open(self.pyfile.url, "wb") as f:
                    f.write(content)
            except IOError, e:
                self.fail(str(e))

        else:
            self.pyfile.name = os.path.basename(self.pyfile.url)
            if not os.path.exists(self.pyfile.url):
                if os.path.exists(fs_join(pypath, self.pyfile.url)):
                    self.pyfile.url = fs_join(pypath, self.pyfile.url)
                else:
                    self.fail(_("File not exists"))


    def delete_tmp(self):
        if self.pyfile.name.startswith("tmp_"):
            os.remove(self.pyfile.url)
