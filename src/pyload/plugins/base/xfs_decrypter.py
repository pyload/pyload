# -*- coding: utf-8 -*-


from ..helpers import set_cookie
from .simple_decrypter import SimpleDecrypter


class XFSDecrypter(SimpleDecrypter):
    __name__ = "XFSDecrypter"
    __type__ = "decrypter"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
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

    __description__ = """XFileSharing decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = None

    URL_REPLACEMENTS = [
        (r"&?per_page=\d+", ""),
        (r"[?/&]+$", ""),
        (r"(.+/[^?]+)$", r"\1?"),
        (r"$", r"&per_page=10000"),
    ]

    NAME_PATTERN = r"<[Tt]itle>.*?\: (?P<N>.+) folder</[Tt]itle>"
    LINK_PATTERN = r'<(?:td|TD).*?>\s*(?:<.+>\s*)?<a href="(.+?)".*?>.+?(?:</a>)?\s*(?:<.+>\s*)?</(?:td|TD)>'

    OFFLINE_PATTERN = r">\s*(No such user|\w+ (Not Found|file (was|has been) removed|no longer available))"
    TEMP_OFFLINE_PATTERN = r">\s*\w+ server (is in )?(maintenance|maintainance)"

    def _set_xfs_cookie(self):
        cookie = (self.PLUGIN_DOMAIN, "lang", "english")
        if isinstance(self.COOKIES, list) and cookie not in self.COOKIES:
            self.COOKIES.insert(cookie)
        else:
            set_cookie(self.req.cj, *cookie)

    def _prepare(self):
        if not self.PLUGIN_DOMAIN:
            self.fail(self._("Missing PLUGIN DOMAIN"))

        if self.COOKIES:
            self._set_xfs_cookie()

        SimpleDecrypter._prepare(self)
