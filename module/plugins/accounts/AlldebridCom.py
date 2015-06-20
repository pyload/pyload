# -*- coding: utf-8 -*-

import re
import time
import xml.dom.minidom

from BeautifulSoup import BeautifulSoup

from module.plugins.internal.Account import Account


class AlldebridCom(Account):
    __name__    = "AlldebridCom"
    __type__    = "account"
    __version__ = "0.25"

    __description__ = """AllDebrid.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "spamsales@online.de")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        html = req.load("http://www.alldebrid.com/account/")
        soup = BeautifulSoup(html)

        #Try to parse expiration date directly from the control panel page (better accuracy)
        try:
            time_text = soup.find('div', attrs={'class': 'remaining_time_text'}).strong.string

            self.logDebug("Account expires in: %s" % time_text)

            p = re.compile('\d+')
            exp_data = p.findall(time_text)
            exp_time = time.time() + int(exp_data[0]) * 24 * 60 * 60 + int(
                exp_data[1]) * 60 * 60 + (int(exp_data[2]) - 1) * 60

        #Get expiration date from API
        except Exception:
            data = self.getAccountData(user)
            html = req.load("https://www.alldebrid.com/api.php",
                            get={'action': "info_user", 'login': user, 'pw': data['password']})

            self.logDebug(html)

            xml = xml.dom.minidom.parseString(html)
            exp_time = time.time() + int(xml.getElementsByTagName("date")[0].childNodes[0].nodeValue) * 24 * 60 * 60

        return {'validuntil' : exp_time,
                'trafficleft': -1      ,
                'premium'    : True    }


    def login(self, user, data, req):
        html = req.load("https://www.alldebrid.com/register/",
                        get={'action'        : "login",
                             'login_login'   : user,
                             'login_password': data['password']},
                        decode=True)

        if "This login doesn't exist" in html \
           or "The password is not valid" in html \
           or "Invalid captcha" in html:
            self.wrongPassword()
