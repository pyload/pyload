# -*- coding: utf-8 -*-

from ..internal.misc import BIGHTTPRequest

from ..hoster.MegaCoNz import MegaClient
from ..internal.Crypter import Crypter


class MegaCoNzFolder(Crypter):
    __name__ = "MegaCoNzFolder"
    __type__ = "crypter"
    __version__ = "0.28"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?mega(?:\.co)?\.nz/folder/(?P<ID>[\w^_]+)#(?P<KEY>[\w,\-=]+)(?:/folder/(?P<SUBDIR>[\w]+))?/?$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """Mega.co.nz folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def setup(self):
        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.requestFactory.getOptions(),
            limit=10000000)

    def decrypt(self, pyfile):
        id = self.info['pattern']['ID']
        master_key = self.info['pattern']['KEY']
        subdir = self.info["pattern"]["SUBDIR"]

        self.log_debug(
            "ID: %s" % id,
            "Key: %s" % master_key,
            "Type: public folder")

        mega = MegaClient(self, id)

        #: F is for requesting folder listing (kind like a `ls` command)
        res = mega.api_response(a="f", c=1, r=1, ca=1, ssl=1)
        if isinstance(res, int):
            mega.check_error(res)
        elif 'e' in res:
            mega.check_error(res['e'])

        urls = ["https://mega.co.nz/folder/%s#%s/file/%s" %
                (id, master_key, node['h'])
                for node in res['f']
                if node['t'] == 0 and ':' in node['k']
                if subdir is None or node["p"] == subdir]

        if urls:
            self.packages = [(pyfile.package().folder, urls, pyfile.package().name)]
