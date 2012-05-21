#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.Account import Account
import re,datetime,time

class UploadheroCom(Account):
    __name__ = "UploadheroCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """Uploadhero.com account plugin"""
    __author_name__ = ("mcmyst")
    __author_mail__ = ("mcmyst@hotmail.fr")


    def loadAccountInfo(self, user, req):
        premium_pattern = re.compile('Il vous reste <span class="bleu">([0-9]+)</span> jours premium.')

        data = self.getAccountData(user)
        page = req.load("http://uploadhero.com/my-account")

        if premium_pattern.search(page):
                end_date = datetime.date.today() + datetime.timedelta(days=int(premium_pattern.search(page).group(1)))
                end_date = time.mktime(future.timetuple())
                account_info = {"validuntil": end_date, "trafficleft": -1, "premium": True}
        else:
                account_info = {"validuntil": -1, "trafficleft": -1, "premium": False}

        return account_info

    def login(self, user, data, req):
        page = req.load("http://uploadhero.com/lib/connexion.php", post={"pseudo_login": user, "password_login": data["password"]})

        if "mot de passe invalide" in page:
            self.wrongPassword()