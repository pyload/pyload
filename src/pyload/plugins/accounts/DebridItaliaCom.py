# -*- coding: utf-8 -*-
import re

from ..base.multi_account import MultiAccount


class DebridItaliaCom(MultiAccount):
    __name__ = "DebridItaliaCom"
    __type__ = "account"
    __version__ = "0.22"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Debriditalia.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://debriditalia.com/api.php"

    def api_response(self, method, **kwargs):
        kwargs[method] = ""
        return self.load(self.API_URL, get=kwargs)

    def grab_hosters(self, user, password, data):
        return self.api_response("hosts").replace('"', "").split(",")

    def grab_info(self, user, password, data):
        validuntil = None

        html = self.api_response("check", u=user, p=password)

        m = re.search(r"<expiration>(.+?)</expiration>", html)
        if m is not None:
            validuntil = int(m.group(1))

        else:
            self.log_error(self._("Unable to retrieve account information"))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": True}

    def signin(self, user, password, data):
        html = self.api_response("check", u=user, p=password)

        if "<status>valid</status>" not in html:
            self.fail_login()
