# -*- coding: utf-8 -*-

import base64
import json
import urllib

import pycurl

from ..internal.SimpleCrypter import SimpleCrypter


class SwisstransferComFolder(SimpleCrypter):
    __name__ = "SwisstransferComFolder"
    __type__ = "crypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?swisstransfer\.com/d/(?P<ID>[0-9a-f\-]+)"
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Swisstransfer.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://www.swisstransfer.com/api/"

    def api_request(self, method, auth=None, **kwargs):
        headers = ["Content-Type: application/json"]
        if auth:
            headers.append("Authorization: %s" % auth)
        self.req.http.c.setopt(pycurl.HTTPHEADER, headers)

        json_data = self.load(self.API_URL + method,
                              post=json.dumps(kwargs) if kwargs else {})
        return json.loads(json_data)

    def decrypt(self, pyfile):
        folder_id = self.info["pattern"]["ID"]
        api_data = self.api_request("links/%s" % folder_id)
        if api_data.get("result") == "success":
            if api_data["data"].get("type") == "expired":
                self.fail(_("Download expired"))

            has_password = api_data["data"].get("type") == "need_password"
            if has_password:
                password = self.get_password()
                if password:
                    auth = base64.b64encode(urllib.quote(password))
                    api_data = self.api_request("links/%s" % folder_id, auth=auth)
                    if api_data["data"].get("type") == "wrong_password":
                        self.fail(_("Wrong password"))

                else:
                    self.fail(_("Download is password protected"))

            if api_data["data"]["downloadCounterCredit"] == 0:
                self.fail(_("Authorized number of downloads has been reached."))

            download_host = api_data["data"]["downloadHost"]
            pack_links = []
            for file in api_data["data"]["container"]["files"]:
                link = "https://%s/api/download/%s/%s" % (download_host, folder_id, file["UUID"])
                if has_password:
                    download_token = self.api_request(
                        "generateDownloadToken",
                        containerUUID=file["containerUUID"],
                        fileUUID=file["UUID"],
                        password=password
                    )
                    link += "?token=%s" % download_token
                pack_links.append(link)

            if pack_links:
                self.packages.append((pyfile.package().name, pack_links, pyfile.package().name))
