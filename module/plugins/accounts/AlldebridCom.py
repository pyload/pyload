# -*- coding: utf-8 -*-

import re
import xml.dom.minidom as dom

from time import time
from urllib import urlencode

from BeautifulSoup import BeautifulSoup

from module.plugins.Account import Account


class AlldebridCom(Account):
    __name__ = "AlldebridCom"
    __type__ = "account"
    __version__ = "0.22"

    __description__ = """AllDebrid.com account plugin"""
    __author_name__ = "Andy Voigt"
    __author_mail__ = "spamsales@online.de"


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = req.load("http://www.alldebrid.com/account/")
        soup = BeautifulSoup(page)
        #Try to parse expiration date directly from the control panel page (better accuracy)
        try:
            time_text = soup.find('div', attrs={'class': 'remaining_time_text'}).strong.string
            self.logDebug("Account expires in: %s" % time_text)
            p = re.compile('\d+')
            exp_data = p.findall(time_text)
            exp_time = time() + int(exp_data[0]) * 24 * 60 * 60 + int(
                exp_data[1]) * 60 * 60 + (int(exp_data[2]) - 1) * 60
        #Get expiration date from API
        except:
            data = self.getAccountData(user)
            page = req.load("http://www.alldebrid.com/api.php?action=info_user&login=%s&pw=%s" % (user,
                                                                                                  data['password']))
            self.logDebug(page)
            xml = dom.parseString(page)
            exp_time = time() + int(xml.getElementsByTagName("date")[0].childNodes[0].nodeValue) * 24 * 60 * 60
        account_info = {"validuntil": exp_time, "trafficleft": -1}
        return account_info

    def login(self, user, data, req):
        urlparams = urlencode({'action': 'login', 'login_login': user, 'login_password': data['password']})
        page = req.load("http://www.alldebrid.com/register/?%s" % urlparams)

        if "This login doesn't exist" in page:
            self.wrongPassword()

        if "The password is not valid" in page:
            self.wrongPassword()

        if "Invalid captcha" in page:
            self.wrongPassword()
