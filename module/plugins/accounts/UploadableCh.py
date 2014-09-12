# -*- coding: utf-8 -*-

from os import remove
from os.path import exists
from urllib import quote

from module.plugins.Hoster import Hoster
from module.utils import fs_encode


class UploadableCh(Hoster):
    __name__ = "UploadableCh"
    __type__ = "hoster"
    __version__ = "0.01"
    __pattern__ = r'https?://(?:www\.)?uploadable.ch/.*'
    __description__ = """Uploadable.ch hoster plugin"""
    __author_name__ = ("sasch")
    __author_mail__ = ("")

    def setup(self):
        self.resumeDownload = True
        self.chunkLimit = 1

    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Uploadable.ch")
            self.fail("No Uplodable.ch account provided")

        self.logDebug("Old URL: %s" % pyfile.url)

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.download(pyfile.url)

        check = self.checkDownload({"nopremium": "No premium account available"})

        if check == "nopremium":
            self.retry(60, 5 * 60, "No premium account available")

        err = ''
        if self.req.http.code == '420':
            # Custom error code send - fail
            lastDownload = fs_encode(self.lastDownload)

            if exists(lastDownload):
                f = open(lastDownload, "rb")
                err = f.read(256).strip()
                f.close()
                remove(lastDownload)
            else:
                err = 'File does not exist'

        if err:
            self.fail(err)
