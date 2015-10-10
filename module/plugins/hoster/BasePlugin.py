# -*- coding: utf-8 -*-

import re
import urllib
import urlparse

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.SimpleHoster import create_getInfo
from module.plugins.internal.Hoster import Hoster


class BasePlugin(Hoster):
    __name__    = "BasePlugin"
    __type__    = "hoster"
    __version__ = "0.46"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Base Plugin when any other didnt fit"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.chunk_limit     = -1
        self.multiDL        = True
        self.resume_download = True


    def process(self, pyfile):
        """
        Main function
        """
        netloc = urlparse.urlparse(pyfile.url).netloc

        pyfile.name = self.get_info(pyfile.url)['name']

        if not pyfile.url.startswith("http"):
            self.fail(_("No plugin matched"))

        try:
            link = self.direct_link(urllib.unquote(pyfile.url))

            if link:
                self.download(link, ref=False, disposition=True)
            else:
                self.fail(_("File not found"))

        except BadHeader, e:
            if e.code == 404:
                self.offline()

            elif e.code in (401, 403):
                self.log_debug("Auth required", "Received HTTP status code: %d" % e.code)

                #@TODO: Recheck in 0.4.10
                if self.account:
                    servers = [x['login'] for x in self.account.getAllAccounts()]
                else:
                    servers = []

                if netloc in servers:
                    self.log_debug("Logging on to %s" % netloc)
                    self.req.addAuth(self.account.get_login('password'))

                else:
                    pwd = self.get_password()
                    if ':' in pwd:
                        self.req.addAuth(pwd)
                    else:
                        self.fail(_("Authorization required"))
            else:
                self.fail(e)

        errmsg = self.check_file({'Empty file'   : re.compile(r'\A\s*\Z'),
                                     'Html error'   : re.compile(r'\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)'),
                                     'Html file'    : re.compile(r'\A\s*<!DOCTYPE html'),
                                     'Request error': re.compile(r'([Aa]n error occured while processing your request)')})
        if not errmsg:
            return

        try:
            errmsg += " | " + self.last_check.group(1).strip()

        except Exception:
            pass

        self.log_warning(_("Check result: ") + errmsg, _("Waiting 1 minute and retry"))
        self.retry(3, 60, errmsg)


getInfo = create_getInfo(BasePlugin)
