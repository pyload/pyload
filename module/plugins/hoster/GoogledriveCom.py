# -*- coding: utf-8 -*
#
# Test links:
#   https://drive.google.com/file/d/0B6RNTe4ygItBQm15RnJiTmMyckU/view?pli=1

import re
import HTMLParser

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class GoogledriveCom(SimpleHoster):
    __name__    = "GoogledriveCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?drive.google.com/file/.*'

    __description__ = """drive.google.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'"og:title" content="(?P<N>.*?)">'
    SIZE_PATTERN    = r'^unmatchable$'                   # NOTE: There is no filesize on the website
    
    OFFLINE_PATTERN = r'align="center"><p class="errorMessage"'


    def setup(self):
        self.multiDL        = True
        self.resumeDownload = True
        self.chunkLimit     = 1

    def handleFree(self, pyfile):
        link1 = re.search(r'"(https://docs.google.com/uc\?id.*?export=download)",', self.html.decode('unicode-escape'))
        if not link1:
            self.error(_("Hop #1 not found"))
        self.logDebug("Next hop: %s" % link1.group(1))
        
        html = self.load(link1.group(1)).decode('unicode-escape')
        link2 = re.search(r'href="(/uc\?export=download.*?)">',html)
        if not link2:
            self.error(_("Hop #2 not found"))
        link2 = HTMLParser.HTMLParser().unescape(link2.group(1))
        self.logDebug("Next hop: %s" % link2)
        
        link3 = self.load("https://docs.google.com" + link2, just_header=True)
        self.logDebug("DL-Link: %s" % link3['location'])

        self.download(link3['location'])                 # NOTE: I don't use disposition=True because it breaks the filename.
        
        
getInfo = create_getInfo(GoogledriveCom)
