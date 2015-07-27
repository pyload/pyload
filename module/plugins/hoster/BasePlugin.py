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
    __version__ = "0.45"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'

    __description__ = """Base Plugin when any other didnt fit"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    @classmethod
    def get_info(cls, url="", html=""):  #@TODO: Move to hoster class in 0.4.10
        url   = urllib.unquote(url)
        url_p = urlparse.urlparse(url)
        return {'name'  : (url_p.path.split('/')[-1]
                           or url_p.query.split('=', 1)[::-1][0].split('&', 1)[0]
                           or url_p.netloc.split('.', 1)[0]),
                'size'  : 0,
                'status': 3 if url else 8,
                'url'   : url}


    def setup(self):
        self.chunk_limit     = -1
        self.multiDL        = True
        self.resume_download = True


    def process(self, pyfile):
        """
        Main function
        """
        pyfile.name = self.get_info(pyfile.url)['name']

        if not pyfile.url.startswith("http"):
            self.fail(_("No plugin matched"))

        for _i in xrange(5):
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

                    account = self.pyload.accountManager.getAccountPlugin('Http')
                    servers = [x['login'] for x in account.getAllAccounts()]  #@TODO: Recheck in 0.4.10
                    server  = urlparse.urlparse(pyfile.url).netloc

                    if server in servers:
                        self.log_debug("Logging on to %s" % server)
                        self.req.addAuth(account.get_info(server)['login']['password'])
                    else:
                        pwd = self.get_password()
                        if ':' in pwd:
                            self.req.addAuth(pwd)
                        else:
                            self.fail(_("Authorization required"))
                else:
                    self.fail(e)
            else:
                break
        else:
            self.fail(_("No file downloaded"))  #@TODO: Move to hoster class in 0.4.10

        errmsg = self.check_download({'Empty file'   : re.compile(r'\A\s*\Z'),
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
