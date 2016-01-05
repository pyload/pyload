# -*- coding: utf-8 -*-

import re
import time
import xml.dom.minidom as dom

import BeautifulSoup

from module.plugins.internal.MultiAccount import MultiAccount


class AlldebridCom(MultiAccount):
    __name__    = "AlldebridCom"
    __type__    = "account"
    __version__ = "0.30"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """AllDebrid.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "spamsales@online.de")]


    def grab_hosters(self, user, password, data):
        html = self.load("https://www.alldebrid.com/api.php",
                         get={'action': "get_host"})
        return [x for x in map(str.strip, html.replace("\"", "").split(",")) if x]


    def grab_info(self, user, password, data):
        html = self.load("http://www.alldebrid.com/account/")
        soup = BeautifulSoup.BeautifulSoup(html)

        #: Try to parse expiration date directly from the control panel page (better accuracy)
        try:
            time_text = soup.find('div', attrs={'class': 'remaining_time_text'}).strong.string

            self.log_debug("Account expires in: %s" % time_text)

            p = re.compile('\d+')
            exp_data = p.findall(time_text)
            exp_time = time.time() + int(exp_data[0]) * 24 * 60 * 60 + int(
                exp_data[1]) * 60 * 60 + (int(exp_data[2]) - 1) * 60

        #: Get expiration date from API
        except Exception:
            html = self.load("https://www.alldebrid.com/api.php",
                             get={'action': "info_user",
                                  'login' : user,
                                  'pw'    : password})

            self.log_debug(html)

            xml = dom.parseString(html)
            exp_time = time.time() + int(xml.getElementsByTagName("date")[0].childNodes[0].nodeValue) * 24 * 60 * 60

        return {'validuntil' : exp_time,
                'trafficleft': -1      ,
                'premium'    : True    }


    def signin(self, user, password, data):
        html = self.load("https://www.alldebrid.com/register/",
                         get={'action'        : "login",
                              'login_login'   : user,
                              'login_password': password})

        if "This login doesn't exist" in html \
           or "The password is not valid" in html \
           or "Invalid captcha" in html:
            self.fail_login()
