# -*- coding: utf-8 -*-

import re

from pyload.core.network.http.exceptions import BadHeader

from ..base.decrypter import BaseDecrypter


class EmbeduploadCom(BaseDecrypter):
    __name__ = "EmbeduploadCom"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?embedupload\.com/\?d=.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        (
            "preferedHoster",
            "str",
            "Prefered hoster list (bar-separated)",
            "embedupload",
        ),
        ("ignoredHoster", "str", "Ignored hoster list (bar-separated)", ""),
    ]

    __description__ = """EmbedUpload.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    LINK_PATTERN = r'<div id="(.+?)".*?>\s*<a href="(.+?)" target="_blank" (?:class="DownloadNow"|style="color:red")>'

    def decrypt(self, pyfile):
        self.data = self.load(pyfile.url)
        tmp_links = []

        m = re.findall(self.LINK_PATTERN, self.data)
        if m is not None:
            prefered_set = set(self.config.get("preferedHoster").split("|"))
            prefered_set = [s.lower().split(".")[0] for s in prefered_set]

            self.log_debug(f"PF: {prefered_set}")

            tmp_links.extend(x[1] for x in m if x[0] in prefered_set)
            self.links = self.get_location(tmp_links)

            if not self.links:
                ignored_set = set(self.config.get("ignoredHoster").split("|"))
                ignored_set = [s.lower().split(".")[0] for s in ignored_set]

                self.log_debug(f"IG: {ignored_set}")

                tmp_links.extend(x[1] for x in m if x[0] not in ignored_set)
                self.links = self.get_location(tmp_links)

    def get_location(self, tmp_links):
        new_links = []
        for link in tmp_links:
            try:
                header = self.load(link, just_header=True)
                if "location" in header:
                    new_links.append(header.get("location"))
            except BadHeader:
                pass
        return new_links
