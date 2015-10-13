# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo
import json


class Go4UpCom(SimpleCrypter):
    __name__    = "Go4UpCom"
    __type__    = "crypter"
    __version__ = "0.14"
    __status__  = "testing"

    __pattern__ = r'http://go4up\.com/(dl/\w{12}|rd/\w{12}/\d+)'
    __config__  = [("activated", "bool", "Activated", True),
                   ("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True),
                   ("preferred_hoster"  , "int" , "Id of preferred hoster or 0 for all", 0)]

    __description__ = """Go4Up.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("rlindner81", "rlindner81@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'(http://go4up\.com/rd/.+?)<'

    NAME_PATTERN = r'<title>Download (.+?)<'

    OFFLINE_PATTERN = r'>\s*(404 Page Not Found|File not Found|Mirror does not exist)'


    def get_links(self):
        links = []
        preference = self.get_config("preferred_hoster")

        hosterslink_re = re.search(r'(/download/gethosts/.+?)"', self.html)
        if hosterslink_re:
            hosters = self.load(urlparse.urljoin("http://go4up.com/", hosterslink_re.group(1)))
            for hoster in json.loads(hosters):
                if preference != 0 and preference != int(hoster["hostId"]):
                    continue
                pagelink_re = re.search(self.LINK_PATTERN, hoster["link"])
                if pagelink_re:
                    page = self.load(pagelink_re.group(1))
                    link_re = re.search(r'<b><a href="(.+?)"', page)
                    if link_re:
                        links.append(link_re.group(1))

        return links


getInfo = create_getInfo(Go4UpCom)
