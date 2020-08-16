# -*- coding: utf-8 -*-

import os
import re

from ..base.decrypter import BaseDecrypter
from ..helpers import replace_patterns


class MirrorcreatorCom(BaseDecrypter):
    __name__ = "MirrorcreatorCom"
    __type__ = "decrypter"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:mirrorcreator\.com/(?:files/|download\.php\?uid=)|mir\.cr/)(?P<ID>\w{8})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("hosters_priority", "str", "Prefered hoster priority (bar-separated)", ""),
        ("ignored_hosters", "str", "Ignored hoster list (bar-separated)", ""),
        ("grab_all", "bool", "Grab all URLs (default only first match)", False),
    ]

    __description__ = """Mirrorcreator.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [
        (__pattern__ + ".*", r"https://www.mirrorcreator.com/download.php?uid=\g<ID>")
    ]

    OFFLINE_PATTERN = r">Unfortunately, the link you have clicked is not available|>Error - Link disabled or is invalid|>Links Unavailable as the File Belongs to Suspended Account\\. <|>Links Unavailable\\.<"
    LINK_PATTERN = r'<div class="highlight redirecturl">(.+?)<'

    def decrypt(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)

        hosters_priority = [
            h for h in self.config.get("hosters_priority").split("|") if h
        ]
        ignored_hosters = [
            h for h in self.config.get("ignored_hosters").split("|") if h
        ]

        self.data = self.load(pyfile.url)

        m = re.search(self.OFFLINE_PATTERN, self.data)
        if m is not None:
            self.offline()

        pack_name, pack_folder = self.get_package_info()

        uid = self.info["pattern"]["ID"]
        m = re.search(rf'"(/mstat\.php\?uid={uid}.+?)"', self.data)
        if m is None:
            self.fail("mstat URL not found")

        self.data = self.load(self.fixurl(m.group(1)))

        hosters_data = {}
        for tr in re.findall(r"<tr>(.+?)</tr>", self.data, re.S):
            uid = self.info["pattern"]["ID"]
            m = re.search(
                rf'<a href="(/showlink\.php\?uid={uid}.+?)".*&hname=(\w+)', tr, re.S
            )
            if m is not None:
                hosters_data[m.group(2)] = m.group(1)

        choosen_hosters = []
        # priority hosters goes first
        for h in hosters_priority:
            if h in hosters_data and h not in ignored_hosters:
                self.log_debug(f"Adding '{h}' link")
                choosen_hosters.append(h)
                if not self.config.get("grab_all"):
                    break

        # Now the rest of the hosters
        if self.config.get("grab_all") or (
            not self.config.get("grab_all") and not choosen_hosters
        ):
            for h in hosters_data:
                if h not in ignored_hosters and h not in choosen_hosters:
                    self.log_debug(f"Adding '{h}' link")
                    choosen_hosters.append(h)
                    if not self.config.get("grab_all"):
                        break

        pack_links = [self.resolve_hoster(hosters_data[h]) for h in choosen_hosters]

        if pack_links:
            self.packages.append((pack_name, pack_links, pack_folder))

    def resolve_hoster(self, link):
        self.data = self.load(self.fixurl(link))

        m = re.search(self.LINK_PATTERN, self.data)
        if m is None:
            self.fail("Link pattern not found")

        return m.group(1)

    def get_package_info(self):
        m = re.search(r"<title>Download links for ([^<]+) - Mirrorcreator", self.data)
        if m is not None:
            pack_name = m.group(1)

            # We remove file extension from package name
            while True:
                pack_name, ext = os.path.splitext(pack_name)
                if ext == "":
                    break

            return pack_name, pack_name

        else:  #: Fallback to defaults
            pack = self.pyfile.package()
            return pack.name, pack.folder
