# -*- coding: utf-8 -*-

import xml.dom.minidom as dom

from module.plugins.internal.MultiAccount import MultiAccount


class RealdebridCom(MultiAccount):
    __name__    = "RealdebridCom"
    __type__    = "account"
    __version__ = "0.52"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Real-Debrid.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def grab_hosters(self, user, password, data):
        html = self.load("https://real-debrid.com/api/hosters.php")
        return [x for x in map(str.strip, html.replace("\"", "").split(",")) if x]


    def grab_info(self, user, password, data):
        if self.pin_code:
            return

        html = self.load("https://real-debrid.com/api/account.php")
        xml  = dom.parseString(html)

        validuntil = float(xml.getElementsByTagName("expiration")[0].childNodes[0].nodeValue)

        return {'validuntil' : validuntil,
                'trafficleft': -1        ,
                'premium'    : True      }


    def signin(self, user, password, data):
        self.pin_code = False

        html = self.load("https://real-debrid.com/ajax/login.php",
                         get={'user': user,
                              'pass': password})

        if "Your login informations are incorrect" in html:
            self.fail_login()

        elif "PIN Code required" in html:
            self.log_warning(_("PIN code required. Please login to https://real-debrid.com using the PIN or disable the double authentication in your control panel on https://real-debrid.com"))
            self.pin_code = True
