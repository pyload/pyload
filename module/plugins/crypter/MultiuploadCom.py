# -*- coding: utf-8 -*-

import re
from time import time

from module.plugins.Crypter import Crypter
from module.common.json_layer import json_loads


class MultiuploadCom(Crypter):
    __name__ = "MultiuploadCom"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?multiupload.com/(\w+)'
    __config__ = [("preferedHoster", "str", "Prefered hoster list (bar-separated) ", "multiupload"),
                  ("ignoredHoster", "str", "Ignored hoster list (bar-separated) ", "")]

    __description__ = """MultiUpload.com decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    ML_LINK_PATTERN = r'<div id="downloadbutton_" style=""><a href="([^"]+)"'


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url)
        m = re.search(self.ML_LINK_PATTERN, self.html)
        ml_url = m.group(1) if m else None

        json_list = json_loads(self.load("http://multiupload.com/progress/", get={
            "d": re.match(self.__pattern__, pyfile.url).group(1),
            "r": str(int(time() * 1000))
        }))

        prefered_set = map(lambda s: s.lower().split('.')[0], set(self.getConfig("preferedHoster").split('|')))

        if ml_url and 'multiupload' in prefered_set:
            self.urls.append(ml_url)

        for link in json_list:
            if link['service'].lower() in prefered_set and int(link['status']) and not int(link['deleted']):
                url = self.getLocation(link['url'])
                if url:
                    self.urls.append(url)

        if not self.urls:
            ignored_set = map(lambda s: s.lower().split('.')[0], set(self.getConfig("ignoredHoster").split('|')))

            if 'multiupload' not in ignored_set:
                self.urls.append(ml_url)

            for link in json_list:
                if link['service'].lower() not in ignored_set and int(link['status']) and not int(link['deleted']):
                    url = self.getLocation(link['url'])
                    if url:
                        self.urls.append(url)

        if not self.urls:
            self.fail('Could not extract any links')

    def getLocation(self, url):
        header = self.load(url, just_header=True)
        return header['location'] if "location" in header else None
