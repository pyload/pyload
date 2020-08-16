# -*- coding: utf-8 -*-

from ..base.simple_decrypter import SimpleDecrypter


class TNTVillageScambioeticoOrg(SimpleDecrypter):
    __name__ = "TNTVillageScambioeticoOrg"
    __type__ = "decrypter"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?forum\.tntvillage\.scambioetico\.org/index\.php\?.*showtopic=\d+"
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

    __description__ = """TNTVillage.scambioetico.org decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    LINK_PATTERNS = [
        r'<th class="titlemedium"><a href=\'(.+?)\'',
        r"<a href='(\./index\.php\?act.+?)'",
    ]

    def get_links(self):
        for p in self.LINK_PATTERNS:
            self.LINK_PATTERN = p
            links = SimpleDecrypter.get_links(self)
            if links:
                return links
