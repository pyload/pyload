# -*- coding: utf-8 -*-

from urllib import quote, unquote

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class RehostTo(MultiHoster):
    __name__    = "RehostTo"
    __type__    = "hoster"
    __version__ = "0.15"

    __pattern__ = r'https?://.*rehost\.to\..*'

    __description__ = """Rehost.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def getFilename(self, url):
        return unquote(url.rsplit("/", 1)[1])


    def setup(self):
        self.chunkLimit     = 1
        self.resumeDownload = True


    def handleMulti(self):
        data = self.account.getAccountInfo(self.user)
        long_ses = data['long_ses']

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.link = True
        self.download("http://rehost.to/process_download.php",
                      get={'user': "cookie", 'pass': long_ses, 'dl': quote(self.pyfile.url, "")},
                      disposition=True)


getInfo = create_getInfo(RehostTo)
