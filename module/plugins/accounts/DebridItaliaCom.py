# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.MultiAccount import MultiAccount


class DebridItaliaCom(MultiAccount):
    __name__    = "DebridItaliaCom"
    __type__    = "account"
    __version__ = "0.19"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Debriditalia.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    WALID_UNTIL_PATTERN = r'Premium valid till: (.+?) \|'


    def grab_hosters(self, user, password, data):
        return self.load("http://debriditalia.com/api.php", get={'hosts': ""}).replace('"', '').split(',')


    def grab_info(self, user, password, data):
        info = {'premium': False, 'validuntil': None, 'trafficleft': None}
        html = self.load("http://debriditalia.com/")

        if 'Account premium not activated' not in html:
            m = re.search(self.WALID_UNTIL_PATTERN, html)
            if m is not None:
                validuntil = time.mktime(time.strptime(m.group(1), "%d/%m/%Y %H:%M"))
                info = {'premium': True, 'validuntil': validuntil, 'trafficleft': -1}
            else:
                self.log_error(_("Unable to retrieve account information"))

        return info


    def signin(self, user, password, data):
        html = self.load("https://debriditalia.com/login.php",
                         get={'u': user,
                              'p': password})

        if 'NO' in html:
            self.fail_login()
