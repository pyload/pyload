# -*- coding: utf-8 -*-

from module.plugins.Account import Account
#from time import mktime, strptime
#from pycurl import REFERER
import re
from module.utils import parseFileSize


class MultishareCz(Account):
    __name__ = "MultishareCz"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """Multishare.cz account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    TRAFFIC_LEFT_PATTERN = r'<span class="profil-zvyrazneni">Kredit:</span>\s*<strong>(?P<S>[0-9,]+)&nbsp;(?P<U>\w+)</strong>'
    ACCOUNT_INFO_PATTERN = r'<input type="hidden" id="(u_ID|u_hash)" name="[^"]*" value="([^"]+)">'


    def loadAccountInfo(self, user, req):
        #self.relogin(user)
        html = req.load("http://www.multishare.cz/profil/", decode=True)

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        trafficleft = parseFileSize(m.group('S'), m.group('U')) / 1024 if m else 0
        self.premium = True if trafficleft else False

        html = req.load("http://www.multishare.cz/", decode=True)
        mms_info = dict(re.findall(self.ACCOUNT_INFO_PATTERN, html))

        return dict(mms_info, **{"validuntil": -1, "trafficleft": trafficleft})

    def login(self, user, data, req):
        html = req.load('http://www.multishare.cz/html/prihlaseni_process.php', post={
            "akce": "Přihlásit",
            "heslo": data['password'],
            "jmeno": user
        }, decode=True)

        if '<div class="akce-chyba akce">' in html:
            self.wrongPassword()
