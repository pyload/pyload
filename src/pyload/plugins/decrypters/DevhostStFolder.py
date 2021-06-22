# -*- coding: utf-8 -*-

#
# Test links:
# http://d-h.st/users/shine/?fld_id=37263#files


import re
import urllib.parse

from ..base.simple_decrypter import SimpleDecrypter


class DevhostStFolder(SimpleDecrypter):
    __name__ = "DevhostStFolder"
    __type__ = "decrypter"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?d-h\.st/users/(?P<USER>\w+)(/\?fld_id=(?P<ID>\d+))?"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """D-h.st folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    LINK_PATTERN = r'(?:/> |;">)<a href="(.+?)"(?!>Back to \w+<)'
    OFFLINE_PATTERN = r'"/cHP">test\.png<'

    # TODO: Rewrite
    def check_name_size(self, getinfo=True):
        if not self.info or getinfo:
            self.log_debug(f"File info (BEFORE): {self.info}")
            self.info.update(self.get_info(self.pyfile.url, self.data))
            self.log_debug(f"File info (AFTER): {self.info}")

        try:
            if self.info["pattern"]["ID"] == "0":
                raise Exception

            p = r'href="(.+?)">Back to \w+<'
            m = re.search(p, self.data)
            html = self.load(
                urllib.parse.urljoin("http://d-h.st/", m.group(1)), cookies=False
            )

            p = r'\?fld_id={}.*?">(.+?)<'.format(self.info["pattern"]["ID"])
            m = re.search(p, html)
            self.pyfile.name = m.group(1)

        except Exception as exc:
            self.log_debug(
                exc, exc_info=self.pyload.debug > 1, stack_info=self.pyload.debug > 2
            )
            self.pyfile.name = self.info["pattern"]["USER"]

        try:
            folder = self.info["folder"] = self.pyfile.name

        except Exception:
            pass

        self.log_debug(
            "File name: {}".format(self.pyfile.name),
            "File folder: {}".format(self.pyfile.name),
        )
