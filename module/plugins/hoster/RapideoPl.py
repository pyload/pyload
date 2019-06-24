# -*- coding: utf-8 -*-

from ..internal.misc import json
from ..internal.MultiHoster import MultiHoster


class RapideoPl(MultiHoster):
    __name__ = "RapideoPl"
    __type__ = "hoster"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Rapideo.pl multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("goddie", "dev@rapideo.pl")]

    API_URL = "http://enc.rapideo.pl"

    API_QUERY = {'site': "newrd",
                 'output': "json",
                 'username': "",
                 'password': "",
                 'url': ""}

    ERROR_CODES = {0: "Incorrect login credentials",
                   1: "Not enough transfer to download - top-up your account",
                   2: "Incorrect / dead link",
                   3: "Error connecting to hosting, try again later",
                   9: "Premium account has expired",
                   15: "Hosting no longer supported",
                   80: "Too many incorrect login attempts, account blocked for 24h"}

    def _prepare(self):
        MultiHoster._prepare(self)

        data = self.account.get_data()

        self.usr = data['usr']
        self.pwd = data['pwd']

    def run_file_query(self, url, mode=None):
        query = self.API_QUERY.copy()

        query['username'] = self.usr
        query['password'] = self.pwd
        query['url'] = url

        if mode == "fileinfo":
            query['check'] = 2
            query['loc'] = 1

        self.log_debug(query)

        return self.load(self.API_URL, post=query)

    def handle_free(self, pyfile):
        try:
            data = self.run_file_query(pyfile.url, 'fileinfo')

        except Exception:
            self.temp_offline("Query error #1")

        try:
            parsed = json.loads(data)

        except Exception:
            self.temp_offline("Data not found")

        self.log_debug(parsed)

        if "errno" in parsed.keys():
            if parsed['errno'] in self.ERROR_CODES:
                #: Error code in known
                self.fail(self.ERROR_CODES[parsed['errno']])
            else:
                #: Error code isn't yet added to plugin
                self.fail(parsed['errstring'] or
                          _("Unknown error (code: %s)") % parsed['errno'])

        if "sdownload" in parsed:
            if parsed['sdownload'] == "1":
                self.fail(
                    _("Download from %s is possible only using Rapideo.pl website \
                    directly") % parsed['hosting'])

        pyfile.name = parsed['filename']
        pyfile.size = parsed['filesize']

        try:
            link = self.run_file_query(pyfile.url, 'filedownload')
            self.download(link, fixurl=False)

        except Exception:
            self.temp_offline("Query error #2")
