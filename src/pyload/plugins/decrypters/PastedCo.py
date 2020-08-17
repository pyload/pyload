# -*- coding: utf-8 -*-

import re

from ..base.decrypter import BaseDecrypter


class PastedCo(BaseDecrypter):
    __name__ = "PastedCo"
    __type__ = "decrypter"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r"http://pasted\.co/\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Pasted.co decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Frederik Möllers", "fred-public@posteo.de")]

    NAME_PATTERN = r"<title>(?P<N>.+?) - .+</title>"
    NAME_PATTERN = r"'save_paste' href=\"(http://pasted.co/[0-9a-f]+)/info"

    FS_URL_PREFIX = "<pre id='thepaste' class=\"prettyprint\">"
    FS_URL_SUFFIX = "</pre>"

    def decrypt(self, pyfile):
        package = pyfile.package()
        pack_name = package.name
        pack_folder = package.folder
        html = self.load(pyfile.url, decode=True).splitlines()
        fs_url = None
        FS_URL_RE = re.compile(rf"{pyfile.url}/fullscreen\.php\?hash=[0-9a-f]*")
        for line in html:
            match = FS_URL_RE.search(line)
            if match:
                fs_url = match.group()
                break
        if not fs_url:
            raise Exception("Could not find pasted.co fullscreen URL!")
        urls = self.load(fs_url, decode=True)
        urls = urls[urls.find(PastedCo.FS_URL_PREFIX) + len(PastedCo.FS_URL_PREFIX) :]
        urls = urls[: urls.find(PastedCo.FS_URL_SUFFIX)].splitlines()
        self.packages.append((pack_name, urls, pack_folder))
