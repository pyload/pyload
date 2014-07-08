# !/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from json import loads, dumps
except ImportError:
    from simplejson import loads

from module.plugins.internal.SimpleHoster import SimpleHoster


class RapideoPl(SimpleHoster):

    __name__ = "RapideoPl"
    __version__ = "0.01"
    __type__ = "hoster"

    __description__ = "Rapideo.pl hoster plugin"
    __author_name__ = ("goddie")
    __author_mail__ = ("dev@rapideo.pl")

    _api_url = "http://enc.rapideo.pl"

    _api_query = {"site": "newrd",
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

            self.fail("[Rapideo.pl] Login to Rapideo.pl plugin or turn plugin off")

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
                self.fail("[Rapideo.pl] Invalid account credentials")

            elif parsed["errno"] == 80:
                self.fail("[Rapideo.pl] Too much incorrect login attempts, account blocked for 24h")

            elif parsed["errno"] == 1:
                self.fail("[Rapideo.pl] Not enough transfer - top up to download")

            elif parsed["errno"] == 9:
                self.fail("[Rapideo.pl] Account expired")

            elif parsed["errno"] == 2:
                self.fail("[Rapideo.pl] Invalid / dead link")

            elif parsed["errno"] == 3:
                self.fail("[Rapideo.pl] Error connecting to host")

            elif parsed["errno"] == 15:
                self.fail("[Rapideo.pl] Hosting no longer supported")

            else:
                self.fail(
                    parsed["errstring"]
                    or "Unknown error (code: {})".format(parsed["errno"])
                )

        if "sdownload" in parsed:
            if parsed["sdownload"] == "1":
                self.fail(
                    "Download from {} is possible only when using \
                    Rapideo.pl directly. Update this plugin.".format(parsed["hosting"]))

        pyfile.name = parsed["filename"]
        pyfile.size = parsed["filesize"]

        try:
            result_dl = self.runFileQuery(pyfile.url, 'filedownload')
        except Exception as e:
            self.logDebug(str(e))
            self.tempOffline()

        self.download(result_dl, disposition=True)
