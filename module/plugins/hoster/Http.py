# -*- coding: utf-8 -*-

import fnmatch
import re
import urlparse

from module.network.HTTPRequest import BadHeader

from ..internal.Hoster import Hoster


class Http(Hoster):
    __name__ = "Http"
    __type__ = "hoster"
    __version__ = "0.14"
    __status__ = "testing"

    __pattern__ = r'(?:jd|pys?)://.+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Download simple http link"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

    def load_account(self):
        class_name = self.classname
        self.__class__.__name__ = "Http"
        Hoster.load_account(self)
        self.__class__.__name__ = class_name

    def process(self, pyfile):
        url = re.sub(r"^(jd|py)", "http", pyfile.url)

        netloc = urlparse.urlparse(url).netloc
        try:
            auth, netloc = netloc.split('@', 2)
        except ValueError:
            auth = None

        if auth is None:
            password = self.get_password()
            if ":" in password:
                auth = password
                self.log_debug("Logging on to %s using credentials specified in the package password" % netloc)

            else:
                if self.account:
                    logins = dict((x['login'], x['password'])
                                  for x in self.account.getAllAccounts())
                else:
                    logins = {}

                for pattern, auth in logins.items():
                    if fnmatch.fnmatch(netloc, pattern):
                        self.log_debug("Logging on to %s using the account plugin" % netloc)
                        break
                else:
                    auth = None

            if auth is not None:
                self.req.addAuth(auth)

        else:
            self.log_debug("Logging on to %s using credentials specified in the URL" % netloc)

        try:
            self.download(url, ref=False, disposition=True)

        except BadHeader, e:
            if e.code == 401:
                self.fail(_("Unauthorized"))

            else:
                raise

        self.check_download()

    def check_download(self):
        errmsg = self.scan_download({
            'Html error': re.compile(r'\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)'),
            'Html file': re.compile(r'\A\s*<!DOCTYPE html'),
            'Request error': re.compile(r'([Aa]n error occured while processing your request)')
        })

        if not errmsg:
            return

        try:
            errmsg += " | " + self.last_check.group(1).strip()

        except Exception:
            pass

        self.log_warning(
            _("Check result: ") + errmsg,
            _("Waiting 1 minute and retry"))
        self.retry(3, 60, errmsg)
