# -*- coding: utf-8 -*-

import base64
import urllib

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.Crypter import Crypter
from ..internal.misc import json


class GofileIoFolder(Crypter):
    __name__ = "GofileIoFolder"
    __type__ = "crypter"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?gofile\.io/d/(?P<ID>\w+)"
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Gofile.io decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [("http://", "https://")]

    API_URL = "https://api.gofile.io/"

    def api_request(self, method, token=None, get={}, post={}):
        if token is not None:
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Authorization: Bearer " + token]
            )
        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)
        except BadHeader, e:
            json_data = e.content

        return json.loads(json_data)

    def decrypt(self, pyfile):
        api_data = self.api_request("accounts", post=True)
        if api_data["status"] != "ok":
            self.fail(_("accounts API failed | %s") % api_data["status"])

        token = api_data["data"]["token"]
        api_data = self.api_request("contents/%s" % self.info["pattern"]["ID"],
                                    token=token,
                                    get={"wt": "4fd6sg89d7s6"})
        status = api_data["status"]
        if status == "ok":
            pack_links = ["https://gofile.io/dl?q=%s" %
                          base64.b64encode(json.dumps({"t": token,
                                                       "u": file_data["link"],
                                                       "n": urllib.quote_plus(file_data["name"].encode("utf8")),
                                                       "s": file_data["size"],
                                                       "m": file_data["md5"]}))
                          for file_data in api_data["data"]["children"].values()
                          if file_data["type"] == "file"]

            if pack_links:
                self.packages.append((pyfile.package().name, pack_links, pyfile.package().folder))

            else:
                self.offline()

        elif status == "error-notFound":
            self.offline()

        elif status == "error-notPremium":
            self.fail(_("File can be downloaded by premium users only"))

        else:
            self.fail(_("getContent API failed | %s") % status)
