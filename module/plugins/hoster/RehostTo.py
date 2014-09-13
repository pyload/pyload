# -*- coding: utf-8 -*-

from urllib import quote, unquote

from module.plugins.Hoster import Hoster


class RehostTo(Hoster):
    __name__ = "RehostTo"
    __type__ = "hoster"
    __version__ = "0.13"

    __pattern__ = r'https?://.*rehost.to\..*'

    __description__ = """Rehost.com hoster plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"


    def getFilename(self, url):
        return unquote(url.rsplit("/", 1)[1])

    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = True

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "rehost.to")
            self.fail("No rehost.to account provided")

        data = self.account.getAccountInfo(self.user)
        long_ses = data['long_ses']

        self.logDebug("Rehost.to: Old URL: %s" % pyfile.url)
        new_url = "http://rehost.to/process_download.php?user=cookie&pass=%s&dl=%s" % (long_ses, quote(pyfile.url, ""))

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.download(new_url, disposition=True)
