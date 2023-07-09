# -*- coding: utf-8 -*-
import re

from ..internal.misc import uniqify
from ..internal.SimpleCrypter import SimpleCrypter


class WorkuploadComFolder(SimpleCrypter):
    __name__ = "WorkuploadComFolder"
    __type__ = "crypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://workupload\.com/archive/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Workupload.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    LINK_PATTERN = r'<a href="(/file/\w+?)"'

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)
        links = uniqify(re.findall(self.LINK_PATTERN, html))
        if links:
            self.packages = [(pyfile.package().folder,
                              ["https://workupload.com" + link for link in links],
                              pyfile.package().name)]
