# -*- coding: utf-8 -*-

import re

from urllib import unquote
from urlparse import urljoin, urlparse

from pyload.network.HTTPRequest import BadHeader
from pyload.plugin.internal.SimpleHoster import fileUrl
from pyload.plugin.Hoster import Hoster


class BasePlugin(Hoster):
    __name    = "BasePlugin"
    __type    = "hoster"
    __version = "0.34"

    __pattern = r'^unmatchable$'

    __description = """Base plugin when any other didnt fit"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    @classmethod
    def getInfo(cls, url="", html=""):  #@TODO: Move to hoster class in 0.4.10
        url   = unquote(url)
        url_p = urlparse(url)
        return {'name'  : (url_p.path.split('/')[-1]
                           or url_p.query.split('=', 1)[::-1][0].split('&', 1)[0]
                           or url_p.netloc.split('.', 1)[0]),
                'size'  : 0,
                'status': 3 if url else 8,
                'url'   : url}


    def setup(self):
        self.chunkLimit     = -1
        self.multiDL        = True
        self.resumeDownload = True


    def process(self, pyfile):
        """main function"""

        pyfile.name = self.getInfo(pyfile.url)['name']

        if not pyfile.url.startswith("http"):
            self.fail(_("No plugin matched"))

        for _i in xrange(5):
            try:
                link = fileUrl(self, unquote(pyfile.url))

                if link:
                    self.download(link, ref=False, disposition=True)
                else:
                    self.fail(_("File not found"))

            except BadHeader, e:
                if e.code is 404:
                    self.offline()

                elif e.code in (401, 403):
                    self.logDebug("Auth required", "Received HTTP status code: %d" % e.code)

                    account = self.core.accountManager.getAccountPlugin('Http')
                    servers = [x['login'] for x in account.getAllAccounts()]
                    server  = urlparse(pyfile.url).netloc

                    if server in servers:
                        self.logDebug("Logging on to %s" % server)
                        self.req.addAuth(account.getAccountData(server)['password'])
                    else:
                        pwd = self.getPassword()
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

        check = self.checkDownload({'empty file': re.compile(r'\A\Z'),
                                    'html file' : re.compile(r'\A\s*<!DOCTYPE html'),
                                    'html error': re.compile(r'\A\s*(<.+>)?\d{3}(\Z|\s+)')})
        if check:
            self.fail(check.capitalize())
