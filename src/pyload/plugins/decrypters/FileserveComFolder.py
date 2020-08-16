# -*- coding: utf-8 -*-
import re

from ..base.decrypter import BaseDecrypter


class FileserveComFolder(BaseDecrypter):
    __name__ = "FileserveComFolder"
    __type__ = "decrypter"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?fileserve\.com/list/\w+"
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

    __description__ = """FileServe.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("fionnc", "fionnc@gmail.com")]

    FOLDER_PATTERN = r'<table class="file_list">(.*?)</table>'
    LINK_PATTERN = r'<a href="(.+?)" class="sheet_icon wbold">'

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.S)
        if folder is None:
            self.error(self._("FOLDER_PATTERN not found"))

        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(1)))

        if new_links:
            self.links = [["http://fileserve.com{}".format(s) for s in new_links]]
