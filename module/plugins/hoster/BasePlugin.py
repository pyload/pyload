# -*- coding: utf-8 -*-

import re

from urllib import unquote
from urlparse import urlparse

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.SimpleHoster import create_getInfo
from module.plugins.Hoster import Hoster
from module.utils import remove_chars


class BasePlugin(Hoster):
    __name__    = "BasePlugin"
    __type__    = "hoster"
    __version__ = "0.22"

    __pattern__ = r'^unmatchable$'

    __description__ = """Base Plugin when any other didnt fit"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    @classmethod
    def getInfo(cls, url="", html=""):  #@TODO: Move to hoster class in 0.4.10
        return {'name': urlparse(url).path.split('/')[-1] or _("Unknown"), 'size': 0, 'status': 3, 'url': url or ""}


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True


    def process(self, pyfile):
        """main function"""

        self.getInfo(pyfile.url)

        if pyfile.url.startswith("http"):
            for _i in xrange(2):
                try:
                    self.downloadFile(pyfile)

                except BadHeader, e:
                    if e.code is 404:
                        self.offline()

                    elif e.code in (401, 403):
                        self.logDebug("Auth required")

                        account = self.core.accountManager.getAccountPlugin('Http')
                        servers = [x['login'] for x in account.getAllAccounts()]
                        server  = urlparse(pyfile.url).netloc

                        if server in servers:
                            self.logDebug("Logging on to %s" % server)
                            self.req.addAuth(account.accounts[server]['password'])
                        else:
                            for pwd in pyfile.package().password.splitlines():
                                if ":" in pwd:
                                    self.req.addAuth(pwd.strip())
                                    break
                            else:
                                self.fail(_("Authorization required (username:password)"))
                    else:
                        self.fail(e)
                else:
                    break
            else:
                self.fail(_("No file downloaded"))  #@TODO: Move to hoster class (check if self.lastDownload) in 0.4.10
        else:
            self.fail(_("No plugin matched"))


    def downloadFile(self, pyfile):
        url = pyfile.url

        for _i in xrange(5):
            header = self.load(url, just_header=True)

            # self.load does not raise a BadHeader on 404 responses, do it here
            if 'code' in header and header['code'] == 404:
                raise BadHeader(404)

            if 'location' in header:
                self.logDebug("Location: " + header['location'])

                base = re.match(r'https?://[^/]+', url).group(0)

                if header['location'].startswith("http"):
                    url = header['location']

                elif header['location'].startswith("/"):
                    url = base + unquote(header['location'])

                else:
                    url = '%s/%s' % (base, unquote(header['location']))
            else:
                break

        if 'content-disposition' in header:
            self.logDebug("Content-Disposition: " + header['content-disposition'])

            m = re.search("filename(?P<type>=|\*=(?P<enc>.+)'')(?P<name>.*)", header['content-disposition'])
            if m:
                disp = m.groupdict()

                self.logDebug(disp)

                if not disp['enc']:
                    disp['enc'] = 'utf-8'

                name = remove_chars(disp['name'], "\"';").strip()
                name = unicode(unquote(name), disp['enc'])

                pyfile.name = name

                self.logDebug("Filename changed to: " + name)

        self.download(url, disposition=True)
