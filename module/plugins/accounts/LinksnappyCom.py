# -*- coding: utf-8 -*-

import hashlib

from module.plugins.internal.MultiAccount import MultiAccount
from module.plugins.internal.misc import json


class LinksnappyCom(MultiAccount):
    __name__    = "LinksnappyCom"
    __type__    = "account"
    __version__ = "0.12"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Linksnappy.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def grab_hosters(self, user, password, data):
        json_data = self.load("http://gen.linksnappy.com/lseAPI.php", get={'act': "FILEHOSTS"})
        json_data = json.loads(json_data)

        return json_data['return'].keys()


    def grab_info(self, user, password, data):
        r = self.load('http://gen.linksnappy.com/lseAPI.php',
                      get={'act'     : 'USERDETAILS',
                           'username': user,
                           'password': hashlib.md5(password).hexdigest()})

        self.log_debug("JSON data: " + r)

        j = json.loads(r)

        if j['error']:
            return {'premium': False}

        validuntil = j['return']['expire']

        if validuntil == "lifetime":
            validuntil = -1

        elif validuntil == "expired":
            return {'premium': False}

        else:
            validuntil = float(validuntil)

        if 'trafficleft' not in j['return'] or isinstance(j['return']['trafficleft'], str):
            trafficleft = -1
        else:
            trafficleft = self.parse_traffic(j['return']['trafficleft'], "MB")

        return {'premium'    : True       ,
                'validuntil' : validuntil ,
                'trafficleft': trafficleft}


    def signin(self, user, password, data):
        html = self.load("https://gen.linksnappy.com/lseAPI.php",
                         get={'act'     : 'USERDETAILS',
                              'username': user,
                              'password': hashlib.md5(password).hexdigest()})

        if "Invalid Account Details" in html:
            self.fail_login()
