# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FiredriveCom(SimpleHoster):
    __name__ = "FiredriveCom"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?(firedrive|putlocker)\.com/(mobile/)?(file|embed)/(?P<ID>\w+)'

    __description__ = """Firedrive.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    FILE_NAME_PATTERN = r'<b>Name:</b> (?P<N>.+) <br>'
    FILE_SIZE_PATTERN = r'<b>Size:</b> (?P<S>[\d.]+) (?P<U>[a-zA-Z]+) <br>'
    OFFLINE_PATTERN = r'class="sad_face_image"|>No such page here.<'
    TEMP_OFFLINE_PATTERN = r'>(File Temporarily Unavailable|Server Error. Try again later)'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.firedrive.com/file/\g<ID>')]

    LINK_PATTERN = r'<a href="(https?://dl\.firedrive\.com/\?key=.+?)"'


    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.chunkLimit = -1

    def handleFree(self):
        link = self._getLink()
        self.logDebug("Direct link: " + link)
        self.download(link, disposition=True)

    def _getLink(self):
        f = re.search(self.LINK_PATTERN, self.html)
        if f:
            return f.group(1)
        else:
            self.html = self.load(self.pyfile.url, post={"confirm": re.search(r'name="confirm" value="(.+?)"', self.html).group(1)})
            f = re.search(self.LINK_PATTERN, self.html)
            if f:
                return f.group(1)
            else:
                self.parseError("Direct download link not found")


getInfo = create_getInfo(FiredriveCom)
