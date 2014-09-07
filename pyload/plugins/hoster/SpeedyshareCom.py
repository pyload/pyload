# -*- coding: utf-8 -*-

# Testlink:
# http://speedy.sh/ep2qY/Zapp-Brannigan.jpg

import re

from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SpeedyshareCom(SimpleHoster):
    __name__ = "SpeedyshareCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(www\.)?(speedyshare.com|speedy.sh)/.*"
    __version__ = "0.01"
    __description__ = """speedyshare.com hoster plugin"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")

    FILE_NAME_PATTERN = r'class=downloadfilename>(?P<N>.*)</span></td>'
    FILE_SIZE_PATTERN = r'class=sizetagtext>(?P<S>.*) (?P<U>[kKmM]?[iI]?[bB]?)</div>'
    LINK_PATTERN = r'<a href=\'(.*)\'><img src=/gf/slowdownload.png alt=\'Slow Download\' border=0'
    FILE_OFFLINE_PATTERN = r'class=downloadfilenamenotfound>.*</span>'
    BASE_URL = 'www.speedyshare.com'

    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1

    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        try:
            dl_link = re.search(self.LINK_PATTERN, self.html).group(1)
            self.logDebug("Link: " + dl_link)
        except:
            self.parseError("Unable to find download link")
        self.download(self.BASE_URL + dl_link, disposition=True)
        check = self.checkDownload({"is_html": re.compile("html")})
        if check == "is_html":
            self.fail("The downloaded file is html, maybe the plugin is out of date")


getInfo = create_getInfo(SpeedyshareCom)
