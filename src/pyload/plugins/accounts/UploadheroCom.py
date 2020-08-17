# -*- coding: utf-8 -*-

import datetime
import re
import time
from datetime import timedelta

from ..base.account import BaseAccount


class UploadheroCom(BaseAccount):
    __name__ = "UploadheroCom"
    __type__ = "account"
    __version__ = "0.29"
    __status__ = "testing"

    __description__ = """Uploadhero.co account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("mcmyst", "mcmyst@hotmail.fr")]

    def grab_info(self, user, password, data):
        _re_premium = re.compile(
            r'Il vous reste <span class="bleu">(\d+)</span> jours premium'
        )

        html = self.load("http://uploadhero.co/my-account")

        if _re_premium.search(html):
            end_date = datetime.date.today() + timedelta(
                days=int(_re_premium.search(html).group(1))
            )
            end_date = time.mktime(end_date.timetuple())
            account_info = {"validuntil": end_date, "trafficleft": -1, "premium": True}
        else:
            account_info = {"validuntil": -1, "trafficleft": -1, "premium": False}

        return account_info

    def signin(self, user, password, data):
        html = self.load(
            "http://uploadhero.co/lib/connexion.php",
            post={"pseudo_login": user, "password_login": password},
        )

        if "mot de passe invalide" in html:
            self.fail_login()
