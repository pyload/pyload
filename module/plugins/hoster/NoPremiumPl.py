# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Pawel W. <dev@nopremium.pl>
"""

try:
    from json import loads, dumps
except ImportError:
    from simplejson import loads

from module.plugins.internal.SimpleHoster import SimpleHoster


class NoPremiumPl(SimpleHoster):

    __name__ = "NoPremiumPl"
    __version__ = "0.01"
    __type__ = "hoster"

    __description__ = "NoPremium.pl hoster plugin"
    __author_name__ = ("goddie")
    __author_mail__ = ("dev@nopremium.pl")

    _api_url = "http://crypt.nopremium.pl"

    _api_query = {"site": "nopremium",
                  "output": "json",
                  "username": "",
                  "password": "",
                  "url": ""}

    _usr = False
    _pwd = False

    def setup(self):

        self.resumeDownload = True
        self.multiDL = True

    def get_username_password(self):

        if not self.account:

            self.fail("[NoPremium.pl] Zaloguj się we wtyczce NoPremium.pl lub ją wyłącz")

        else:

            self._usr = self.account.getAccountData(self.user).get('usr')
            self._pwd = self.account.getAccountData(self.user).get('pwd')

    def runFileQuery(self, url, mode=None):

        query = self._api_query.copy()

        query["username"] = self._usr
        query["password"] = self._pwd

        query["url"] = url

        if mode == "fileinfo":
            query['check'] = 2
            query['loc'] = 1

        self.logDebug(query)

        return self.load(self._api_url, post=query)

    def process(self, pyfile):

        self.get_username_password()

        try:
            data = self.runFileQuery(pyfile.url, 'fileinfo')
        except Exception as e:
            self.logDebug(str(e))
            self.tempOffline()

        try:
            parsed = loads(data)
        except Exception as e:
            self.logDebug(str(e))
            self.tempOffline()

        self.logDebug(parsed)

        if "errno" in parsed.keys():

            if parsed["errno"] == 0:
                self.fail("[NoPremium.pl] Niepoprawne dane logowania")

            elif parsed["errno"] == 80:
                self.fail("[NoPremium.pl] Zbyt dużo niepoprawnych logowań, konto zablokowane na 24h")

            elif parsed["errno"] == 1:
                self.fail("[NoPremium.pl] Za mało transferu - doładuj aby pobrać")

            elif parsed["errno"] == 9:
                self.fail("[NoPremium.pl] Konto wygasło")

            elif parsed["errno"] == 2:
                self.fail("[NoPremium.pl] Niepoprawny / wygasły link")

            elif parsed["errno"] == 3:
                self.fail("[NoPremium.pl] Błąd łączenia z hostingiem")

            elif parsed["errno"] == 15:
                self.fail("[NoPremium.pl] Hosting nie jest już wspierany")

            else:
                self.fail(
                    parsed["errstring"]
                    or "Nieznany błąd (kod: {})".format(parsed["errno"])
                )

        if "sdownload" in parsed:
            if parsed["sdownload"] == "1":
                self.fail(
                    "Pobieranie z {} jest możliwe tylko przy bezpośrednim użyciu \
                    NoPremium.pl. Zaktualizuj wtyczkę.".format(parsed["hosting"]))

        pyfile.name = parsed["filename"]
        pyfile.size = parsed["filesize"]

        try:
            result_dl = self.runFileQuery(pyfile.url, 'filedownload')
        except Exception as e:
            self.logDebug(str(e))
            self.tempOffline()

        self.download(result_dl, disposition=True)
