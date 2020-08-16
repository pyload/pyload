# -*- coding: utf-8 -*-
import codecs
import os

from ..base.container import BaseContainer


class TXT(BaseContainer):
    __name__ = "TXT"
    __type__ = "container"
    __version__ = "0.21"
    __status__ = "testing"

    __pattern__ = r".+\.(txt|text)$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("flush", "bool", "Flush list after adding", False),
        ("encoding", "str", "File encoding", "utf-8"),
    ]

    __description__ = """Read link lists in plain text formats"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.net"), ("jeix", "jeix@hasnomail.com")]

    def decrypt(self, pyfile):
        try:
            encoding = codecs.lookup(self.config.get("encoding")).name

        except Exception:
            encoding = "utf-8"

        fs_filename = os.fsdecode(pyfile.url)
        with open(fs_filename, encoding=encoding) as txt:
            cur_pack = "Parsed links from {}".format(pyfile.name)
            packages = {cur_pack: []}

            for link in txt.readlines():
                link = link.strip()

                if not link:
                    continue

                if link.startswith(";"):
                    continue

                if link.startswith("[") and link.endswith("]"):
                    #: New package
                    cur_pack = link[1:-1]
                    packages[cur_pack] = []
                    continue

                packages[cur_pack].append(link)

        #: Empty packages fix
        for key, value in packages.items():
            if not value:
                packages.pop(key, None)

        if self.config.get("flush"):
            try:
                txt = open(fs_filename, mode="w")
                txt.close()

            except IOError:
                self.log_warning(self._("Failed to flush list"))

        for name, links in packages.items():
            self.packages.append((name, links, name))
