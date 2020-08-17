# -*- coding: utf-8 -*-
import json

from ..base.multi_downloader import MultiDownloader


class RPNetBiz(MultiDownloader):
    __name__ = "RPNetBiz"
    __type__ = "downloader"
    __version__ = "0.22"
    __status__ = "testing"

    __pattern__ = r"https?://.+rpnet\.biz"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """RPNet.biz multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Dman", "dmanugm@gmail.com")]

    def setup(self):
        self.chunk_limit = -1

    def handle_premium(self, pyfile):
        user, info = self.account.select()

        res = self.load(
            "https://premium.rpnet.biz/client_api.php",
            get={
                "username": user,
                "password": info["login"]["password"],
                "action": "generate",
                "links": pyfile.url,
            },
        )

        self.log_debug(f"JSON data: {res}")
        #: Get the first link... since we only queried one
        link_status = json.loads(res)["links"][0]

        #: Check if we only have an id as a HDD link
        if "id" in link_status:
            self.log_debug("Need to wait at least 30 seconds before requery")
            self.wait(30)  #: Wait for 30 seconds
            #: Lets query the server again asking for the status on the link,
            #: We need to keep doing this until we reach 100
            attemps = 30
            my_try = 0
            while my_try <= attemps:
                self.log_debug(f"Try: {my_try}; Max Tries: {attemps}")
                res = self.load(
                    "https://premium.rpnet.biz/client_api.php",
                    get={
                        "username": user,
                        "password": info["login"]["password"],
                        "action": "downloadInformation",
                        "id": link_status["id"],
                    },
                )
                self.log_debug(f"JSON data hdd query: {res}")
                download_status = json.loads(res)["download"]

                dl_status = download_status["status"]
                if dl_status == "100":
                    lk_status = link_status["generated"] = download_status["rpnet_link"]
                    self.log_debug(f"Successfully downloaded to rpnet HDD: {lk_status}")
                    break
                else:
                    self.log_debug(f"At {dl_status}% for the file download")

                self.wait(30)
                my_try += 1

            if my_try > attemps:  #: We went over the limit!
                self.fail(
                    self._(
                        "Waited for about 15 minutes for download to finish but failed"
                    )
                )

        if "generated" in link_status:
            self.link = link_status["generated"]
            return
        elif "error" in link_status:
            self.fail(link_status["error"])
        else:
            self.fail(self._("Something went wrong, not supposed to enter here"))
