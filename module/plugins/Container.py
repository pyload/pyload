# -*- coding: utf-8 -*-

import re

from os import remove
from os.path import basename, exists

from module.plugins.Crypter import Crypter
from module.utils import save_join


class Container(Crypter):
    __name__ = "Container"
    __type__ = "container"
    __version__ = "0.1"

    __pattern__ = None

    __description__ = """Base container decrypter plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"


    def preprocessing(self, thread):
        """prepare"""

        self.setup()
        self.thread = thread

        self.loadToDisk()

        self.decrypt(self.pyfile)
        self.deleteTmp()

        self.createPackages()


    def loadToDisk(self):
        """loads container to disk if its stored remotely and overwrite url,
        or check existent on several places at disk"""

        if self.pyfile.url.startswith("http"):
            self.pyfile.name = re.findall("([^\/=]+)", self.pyfile.url)[-1]
            content = self.load(self.pyfile.url)
            self.pyfile.url = save_join(self.config['general']['download_folder'], self.pyfile.name)
            f = open(self.pyfile.url, "wb" )
            f.write(content)
            f.close()

        else:
            self.pyfile.name = basename(self.pyfile.url)
            if not exists(self.pyfile.url):
                if exists(save_join(pypath, self.pyfile.url)):
                    self.pyfile.url = save_join(pypath, self.pyfile.url)
                else:
                    self.fail(_("File not exists."))


    def deleteTmp(self):
        if self.pyfile.name.startswith("tmp_"):
            remove(self.pyfile.url)
