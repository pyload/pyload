# -*- coding: utf-8 -*-

import json
import re

from .MegaCoNz import MegaCoNz, MegaCrypto


class MegacrypterCom(MegaCoNz):
    __name__ = "MegacrypterCom"
    __type__ = "downloader"
    __version__ = "0.28"
    __status__ = "testing"

    __pattern__ = r"https?://\w{0,10}\.?megacrypter\.com/[\w\-!]+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Megacrypter.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GonzaloSR", "gonzalo@gonzalosr.com")]

    API_URL = "http://megacrypter.com/api"
    FILE_SUFFIX = ".crypted"

    def api_request(self, **kwargs):
        """
        Dispatch a call to the api, see megacrypter.com/api_doc.
        """
        self.log_debug("JSON request: " + json.dumps(kwargs))
        res = self.load(self.API_URL, post=json.dumps(kwargs))
        self.log_debug("API Response: " + res)
        return json.loads(res)

    def process(self, pyfile):
        #: Match is guaranteed because plugin was chosen to handle url
        node = re.match(self.__pattern__, pyfile.url).group(0)

        #: get Mega.co.nz link info
        info = self.api_request(link=node, m="info")

        #: Get crypted file URL
        dl = self.api_request(link=node, m="dl")

        # TODO: map error codes, implement password protection
        # if info['pass'] is True:
        # crypted_file_key, md5_file_key = info['key'].split("#")

        key = MegaCrypto.base64_decode(info["key"])

        pyfile.name = info["name"] + self.FILE_SUFFIX

        self.download(dl["url"])

        self.decrypt_file(key)

        #: Everything is finished and final name can be set
        pyfile.name = info["name"]
