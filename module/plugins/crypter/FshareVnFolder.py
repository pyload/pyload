# -*- coding: utf-8 -*-

import re

from ..internal.Crypter import Crypter
from ..internal.misc import replace_patterns


class FshareVnFolder(Crypter):
    __name__ = "FshareVnFolder"
    __type__ = "crypter"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?fshare\.vn/folder/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("dl_subfolders", "bool", "Download subfolders", False),
                  ("package_subfolder", "bool", "Subfolder as a separate package", False)]

    __description__ = """Fshare.vn folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    OFFLINE_PATTERN = r'404</title>'
    NAME_PATTERN = r'<title>Fshare - (.+?)</title>'

    LINK_PATTERN = r'<a class="filename" .+? href="(.+?)"'
    FOLDER_PATTERN = r'<a .*class="filename folder".+?data-id="(.+?)"'

    URL_REPLACEMENTS = [("http://", "https://")]

    def enum_folder(self, url):
        self.data = self.load(url)

        links = re.findall(self.LINK_PATTERN, self.data)

        if self.config.get('dl_subfolders'):
            for _f in re.findall(self.FOLDER_PATTERN, self.data):
                _u = "https://www.fshare.vn/folder/" + _f
                if self.config.get('package_subfolder'):
                    links.append(_u)

                else:
                    links.extend(self.enum_folder(_u))

        return links


    def decrypt(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)

        self.data = self.load(pyfile.url)
        if re.search(self.OFFLINE_PATTERN, self.data):
            self.offline()

        m = re.search(self.NAME_PATTERN, self.data)
        pack_name = m.group(1) if m is not None else pyfile.package().name

        links = self.enum_folder(pyfile.url)

        if links:
            self.packages = [(pack_name, links, pack_name)]


