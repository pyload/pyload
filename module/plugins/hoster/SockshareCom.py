# -*- coding: utf-8 -*-

import re

from os import rename

from module.plugins.hoster.UnrestrictLi import secondsToMidnight
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SockshareCom(SimpleHoster):
    __name__ = "SockshareCom"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?sockshare\.com/(mobile/)?(file|embed)/(?P<ID>\w+)'

    __description__ = """Sockshare.com hoster plugin"""
    __author_name__ = ("jeix", "stickell", "Walter Purcaro")
    __author_mail__ = ("jeix@hasnomail.de", "l.stickell@yahoo.it", "vuolter@gmail.com")

    FILE_INFO_PATTERN = r'site-content">\s*<h1>(?P<N>.+)<strong>\( (?P<S>[^)]+) \)</strong></h1>'
    OFFLINE_PATTERN = r'>This file doesn\'t exist, or has been removed.<'
    TEMP_OFFLINE_PATTERN = r'(>This content server has been temporarily disabled for upgrades|Try again soon\\. You can still download it below\\.<)'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.sockshare.com/file/\g<ID>')]


    def setup(self):
        self.multiDL = self.resumeDownload = True
        self.chunkLimit = -1

    def handleFree(self):
        name = self.pyfile.name
        link = self._getLink()
        self.logDebug("Direct link: " + link)
        self.download(link, disposition=True)
        self.processName(name)

    def _getLink(self):
        hash_data = re.search(r'<input type="hidden" value="([a-z0-9]+)" name="hash">', self.html)
        if not hash_data:
            self.parseError("Unable to detect hash")

        post_data = {"hash": hash_data.group(1), "confirm": "Continue+as+Free+User"}
        self.html = self.load(self.pyfile.url, post=post_data)
        if ">You have exceeded the daily stream limit for your country\\. You can wait until tomorrow" in self.html:
            self.logWarning("You have exceeded your daily stream limit for today")
            self.wait(secondsToMidnight(gmt=2), True)
        elif re.search(self.TEMP_OFFLINE_PATTERN, self.html):
            self.retry(wait_time=2 * 60 * 60, reason="Server temporarily offline")  # 2 hours wait

        patterns = (r'(/get_file\.php\?id=[A-Z0-9]+&key=[a-zA-Z0-9=]+&original=1)',
                    r'(/get_file\.php\?download=[A-Z0-9]+&key=[a-z0-9]+)',
                    r'(/get_file\.php\?download=[A-Z0-9]+&key=[a-z0-9]+&original=1)',
                    r'<a href="/gopro\.php">Tired of ads and waiting\? Go Pro!</a>[\t\n\rn ]+</div>[\t\n\rn ]+<a href="(/.*?)"')
        for pattern in patterns:
            link = re.search(pattern, self.html)
            if link:
                break
        else:
            link = re.search(r"playlist: '(/get_file\.php\?stream=[a-zA-Z0-9=]+)'", self.html)
            if link:
                self.html = self.load("http://www.sockshare.com" + link.group(1))
                link = re.search(r'media:content url="(http://.*?)"', self.html)
                if link is None:
                    link = re.search(r'\"(http://media\\-b\\d+\\.sockshare\\.com/download/\\d+/.*?)\"', self.html)
            else:
                self.parseError('Unable to detect a download link')

        link = link.group(1).replace("&amp;", "&")
        if link.startswith("http://"):
            return link
        else:
            return "http://www.sockshare.com" + link

    def processName(self, name_old):
        name = self.pyfile.name
        if name <= name_old:
            return
        name_new = re.sub(r'\.[^.]+$', "", name_old) + name[len(name_old):]
        filename = self.lastDownload
        self.pyfile.name = name_new
        rename(filename, filename.rsplit(name)[0] + name_new)
        self.logInfo("%(name)s renamed to %(newname)s" % {"name": name, "newname": name_new})


getInfo = create_getInfo(SockshareCom)
