# -*- coding: utf-8 -*-

from pyload.core.network.cookie_jar import CookieJar
from pyload.core.network.http.http_request import HTTPRequest

from ..base.decrypter import BaseDecrypter
from ..downloaders.MegaCoNz import MegaClient, MegaCrypto
from pyload.core.network.exceptions import Abort

class BIGHTTPRequest(HTTPRequest):
    """
    Overcome HTTPRequest's load() size limit to allow
    loading very big web pages by overrding HTTPRequest's write() function
    """

    # @TODO: Add 'limit' parameter to HTTPRequest in v0.4.10
    def __init__(self, cookies=None, options=None, limit=2000000):
        self.limit = limit
        HTTPRequest.__init__(self, cookies=cookies, options=options)

    def write(self, buf):
        """ writes response """
        if self.limit and self.rep.tell() > self.limit or self.abort:
            rep = self.getResponse()
            if self.abort:
                raise Abort()
            f = open("response.dump", "wb")
            f.write(rep)
            f.close()
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)


class MegaCoNzFolder(BaseDecrypter):
    __name__ = "MegaCoNzFolder"
    __type__ = "decrypter"
    __version__ = "0.24"
    __status__ = "testing"

    __pattern__ = r"(https?://(?:www\.)?mega(\.co)?\.nz/|mega:|chrome:.+?)#F!(?P<ID>[\w^_]+)!(?P<KEY>[\w,\-=]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Mega.co.nz folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def setup(self):
        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=CookieJar(None),
            options=self.pyload.requestFactory.getOptions(),
            limit=10000000)

    def decrypt(self, pyfile):
        id = self.info["pattern"]["ID"]
        master_key = self.info["pattern"]["KEY"]

        self.log_debug(
            "ID: {}".format(id), "Key: {}".format(master_key), "Type: public folder"
        )

        master_key = MegaCrypto.base64_to_a32(master_key)

        mega = MegaClient(self, id)

        #: F is for requesting folder listing (kind like a `ls` command)
        res = mega.api_response(a="f", c=1, r=1, ca=1, ssl=1)

        if isinstance(res, int):
            mega.check_error(res)
        elif "e" in res:
            mega.check_error(res["e"])

        def get_node_key(k):
            return MegaCrypto.base64_encode(
                MegaCrypto.a32_to_str(MegaCrypto.decrypt_key(k, master_key))
            )

        urls = [
            self._("https://mega.co.nz/#N!{}!{}###n={}").format(
                f["h"], get_node_key(f["k"][f["k"].index(":") + 1 :]), id
            )
            for f in res["f"]
            if f["t"] == 0 and ":" in f["k"]
        ]

        if urls:
            self.packages = [(pyfile.package().folder, urls, pyfile.package().name)]
