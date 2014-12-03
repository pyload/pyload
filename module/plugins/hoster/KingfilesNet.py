# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class KingfilesNet(SimpleHoster):
    __name__    = "KingfilesNet"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?kingfiles\.net/(?P<ID>\w{12})'

    __description__ = """Kingfiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'>Size: .+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'>(File Not Found</b><br><br>|File Not Found</h2>)'

    RAND_ID_PATTERN = r'type=\"hidden\" name=\"rand\" value=\"(.+)\">'

    LINK_PATTERN = r'var download_url = \'(.+)\';'


    def setup(self):
        self.multiDL = True
        self.resumeDownload = True


    def handleFree(self):
        # Click the free user button
        post_data = {'op': "download1",
                     'usr_login': "",
                     'id': self.info['pattern']['ID'],
                     'fname': self.pyfile.name,
                     'referer': "",
                     'method_free': "+"}

        self.html = self.load(self.pyfile.url, post=post_data, cookies=True, decode=True)

        solvemedia = SolveMedia(self)
        captcha_challenge, captcha_response = solvemedia.challenge()

        # Make the downloadlink appear and load the file
        m = re.search(self.RAND_ID_PATTERN, self.html)
        if m is None:
            self.error(_("Random key not found"))

        rand = m.group(1)
        self.logDebug("rand = ", rand)

        post_data = {'op': "download2",
                     'id': self.info['pattern']['ID'],
                     'rand': rand,
                     'referer': self.pyfile.url,
                     'method_free': "+",
                     'method_premium': "",
                     'adcopy_response': captcha_response,
                     'adcopy_challenge': captcha_challenge,
                     'down_direct': "1"}

        self.html = self.load(self.pyfile.url, post=post_data, cookies=True, decode=True)

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("Download url not found"))

        self.download(m.group(1), cookies=True, disposition=True)

        check = self.checkDownload({'html': re.compile("<html>")})
        if check == "html":
            self.error(_("Downloaded file is an html page"))


getInfo = create_getInfo(KingfilesNet)
