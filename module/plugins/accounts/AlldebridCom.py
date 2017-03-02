# -*- coding: utf-8 -*-

import time
import xml.dom.minidom as dom

from ..internal.MultiAccount import MultiAccount


class AlldebridCom(MultiAccount):
    __name__ = "AlldebridCom"
    __type__ = "account"
    __version__ = "0.33"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in minutes", 60)]

    __description__ = """AllDebrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Andy Voigt", "spamsales@online.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://www.alldebrid.com/api.php"

    def api_response(self, action, **kwargs):
        kwargs['action'] = action
        return self.load(self.API_URL, get=kwargs)

    def grab_hosters(self, user, password, data):
        html = self.api_response("get_host")
        return [x.strip() for x in html.replace("\"", "").split(",") if x]

    def grab_info(self, user, password, data):
        html = self.api_response("info_user", login=user, pw=password)
        xml = dom.parseString(html)

        validuntil = time.time() + int(xml.getElementsByTagName("timestamp")
                                       [0].childNodes[0].nodeValue)

        return {'validuntil': validuntil,
                'trafficleft': -1,
                'premium': True}

    def signin(self, user, password, data):
        html = self.api_response("info_user", login=user, pw=password)

        if "banned" in html:
            self.fail_login("Your IP is banned")

        elif "login fail" in html:
            self.fail_login()
