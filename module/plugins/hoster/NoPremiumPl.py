# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster


class NoPremiumPl(MultiHoster):
    __name__    = "NoPremiumPl"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://direct\.nopremium\.pl.+'

    __description__ = """NoPremium.pl multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("goddie", "dev@nopremium.pl")]


    API_URL = "http://crypt.nopremium.pl"

    API_QUERY = {'site'    : "nopremium",
                 'output'  : "json",
                 'username': "",
                 'password': "",
                 'url'     : ""}

    ERROR_CODES = {0 : "[%s] Incorrect login credentials",
                   1 : "[%s] Not enough transfer to download - top-up your account",
                   2 : "[%s] Incorrect / dead link",
                   3 : "[%s] Error connecting to hosting, try again later",
                   9 : "[%s] Premium account has expired",
                   15: "[%s] Hosting no longer supported",
                   80: "[%s] Too many incorrect login attempts, account blocked for 24h"}


    def prepare(self):
        super(NoPremiumPl, self).prepare()

        data = self.account.getAccountData(self.user)

        self.usr = data['usr']
        self.pwd = data['pwd']


    def runFileQuery(self, url, mode=None):
        query = self.API_QUERY.copy()

        query["username"] = self.usr
        query["password"] = self.pwd
        query["url"]      = url

        if mode == "fileinfo":
            query['check'] = 2
            query['loc']   = 1

        self.logDebug(query)

        return self.load(self.API_URL, post=query)


    def handleFree(self, pyfile):
        try:
            data = self.runFileQuery(pyfile.url, 'fileinfo')

        except Exception:
            self.logDebug("runFileQuery error")
            self.tempOffline()

        try:
            parsed = json_loads(data)

        except Exception:
            self.logDebug("loads error")
            self.tempOffline()

        self.logDebug(parsed)

        if "errno" in parsed.keys():
            if parsed["errno"] in self.ERROR_CODES:
                # error code in known
                self.fail(self.ERROR_CODES[parsed["errno"]] % self.__name__)
            else:
                # error code isn't yet added to plugin
                self.fail(
                    parsed["errstring"]
                    or "Unknown error (code: %s)" % parsed["errno"]
                )

        if "sdownload" in parsed:
            if parsed["sdownload"] == "1":
                self.fail(
                    "Download from %s is possible only using NoPremium.pl webiste \
                    directly. Update this plugin." % parsed["hosting"])

        pyfile.name = parsed["filename"]
        pyfile.size = parsed["filesize"]

        try:
            self.link = self.runFileQuery(pyfile.url, 'filedownload')

        except Exception:
            self.logDebug("runFileQuery error #2")
            self.tempOffline()
