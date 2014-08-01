# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class GooIm(SimpleHoster):
    __name__ = "GooIm"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?goo\.im/.+'

    __description__ = """Goo.im hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    FILE_NAME_PATTERN = r'<h3>Filename: (?P<N>.+)</h3>'
    OFFLINE_PATTERN = r'The file you requested was not found'


    def setup(self):
        self.chunkLimit = -1
        self.multiDL = self.resumeDownload = True

    def handleFree(self):
        self.html = self.load(self.pyfile.url)
        m = re.search(r'MD5sum: (?P<MD5>[0-9a-z]{32})</h3>', self.html)
        if m:
            self.check_data = {"md5": m.group('MD5')}
        self.wait(10)

        header = self.load(self.pyfile.url, just_header=True)
        if header['location']:
            self.logDebug("Direct link: " + header['location'])
            self.download(header['location'])
        else:
            self.parseError("Unable to detect direct download link")


getInfo = create_getInfo(GooIm)
