# -*- coding: utf-8 -*-

import re

from pyload.utils import json_loads, json_dumps

from pyload.plugin.hoster.MegaCoNz import MegaCoNz


class MegacrypterCom(MegaCoNz):
    __name    = "MegacrypterCom"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'(https?://\w{0,10}\.?megacrypter\.com/[\w!-]+)'

    __description = """Megacrypter.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("GonzaloSR", "gonzalo@gonzalosr.com")]


    API_URL = "http://megacrypter.com/api"
    FILE_SUFFIX = ".crypted"


    def callApi(self, **kwargs):
        """ Dispatch a call to the api, see megacrypter.com/api_doc """
        self.logDebug("JSON request: " + json_dumps(kwargs))
        res = self.load(self.API_URL, post=json_dumps(kwargs))
        self.logDebug("API Response: " + res)
        return json_loads(res)


    def process(self, pyfile):
        # match is guaranteed because plugin was chosen to handle url
        node = re.match(self.__pattern, pyfile.url).group(1)

        # get Mega.co.nz link info
        info = self.callApi(link=node, m="info")

        # get crypted file URL
        dl = self.callApi(link=node, m="dl")

        # TODO: map error codes, implement password protection
        # if info['pass'] is True:
        #    crypted_file_key, md5_file_key = info['key'].split("#")

        key = self.b64_decode(info['key'])

        pyfile.name = info['name'] + self.FILE_SUFFIX

        self.download(dl['url'])
        self.decryptFile(key)

        # Everything is finished and final name can be set
        pyfile.name = info['name']
