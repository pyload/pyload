# -*- coding: utf-8 -*-

import re
import datetime
import time

from module.plugins.internal.Account import Account


class UploadheroCom(Account):
    __name__    = "UploadheroCom"
    __type__    = "account"
    __version__ = "0.23"
    __status__  = "testing"

    __description__ = """Uploadhero.co account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mcmyst", "mcmyst@hotmail.fr")]


    def parse_info(self, user, password, data, req):
        premium_pattern = re.compile('Il vous reste <span class="bleu">(\d+)</span> jours premium')

        data = self.get_data(user)
        html = self.load("http://uploadhero.co/my-account")

        if premium_pattern.search(html):
            end_date = datetime.date.today() + datetime.timedelta(days=int(premium_pattern.search(html).group(1)))
            end_date = time.mktime(future.timetuple())
            account_info = {'validuntil': end_date, 'trafficleft': -1, 'premium': True}
        else:
            account_info = {'validuntil': -1, 'trafficleft': -1, 'premium': False}

        return account_info


    def login(self, user, password, data, req):
        html = self.load("http://uploadhero.co/lib/connexion.php",
                         post={'pseudo_login': user,
                               'password_login': password})

        if "mot de passe invalide" in html:
            self.login_fail()
