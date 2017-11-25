# -*- coding: utf-8 -*-

import hashlib
import pycurl

from ..internal.MultiAccount import MultiAccount
from ..internal.misc import json


class LinkifierCom(MultiAccount):
    __name__ = "LinkifierCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Linkifier.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    API_KEY = "d046c4309bb7cabd19f49118a2ab25e0"
    API_URL = "https://api.linkifier.com/downloadapi.svc/"

    def api_response(self, method, user, password, **kwargs):
        post = {'login': user,
                'md5Pass': hashlib.md5(password).hexdigest(),
                'apiKey': self.API_KEY}
        post.update(kwargs)
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["Content-Type: application/json; charset=utf-8"])
        res = json.loads(self.load(self.API_URL + method,
                                   post=json.dumps(post)))
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["Content-Type: text/html; charset=utf-8"])
        return res

    def grab_hosters(self, user, password, data):
        json_data = self.api_response("hosters", user, password)
        if json_data['hasErrors']:
            self.log_warning(json_data['ErrorMSG']  or "Unknown error")
            return []

        return [_x['hostername'] for _x in json_data['hosters'] if _x['hostername'] and _x['isActive']]

    def grab_info(self, user, password, data):
        json_data = self.api_response("user", user, password)
        trafficleft = json_data['extraTraffic']
        validuntil = float(json_data['expirydate']) / 1000

        return {'validuntil': validuntil ,
                'trafficleft': -1 if trafficleft.lower() == "unlimited" else int(trafficleft),
                'premium': True}

    def signin(self, user, password, data):
        json_data = self.api_response("user", user, password)
        if json_data.get('hasErrors', True) or not json_data.get('isActive', True):
            self.log_warning(json_data['ErrorMSG'] or "Unknown error")
            self.fail_login()




