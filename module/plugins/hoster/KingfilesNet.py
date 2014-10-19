# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class KingfilesNet(SimpleHoster):
    __name__ = "KingfilesNet"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?kingfiles\.net/(?P<ID>\w{12})'

    __description__ = """Kingfiles.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_NAME_PATTERN = r'name="fname" value="(?P<N>.+?)">'
    FILE_SIZE_PATTERN = r'>Size: .+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

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
                     'id': file_info['ID'],
                     'fname': self.pyfile.name,
                     'referer': "",
                     'method_free': "+"}
        b = self.load(self.pyfile.url, post=post_data, cookies=True, decode=True)

        solvemedia = SolveMedia(self)

        captcha_key = solvemedia.detect_key()
        if captcha_key is None:
            self.error("SolveMedia key not found")

        self.logDebug("captcha_key", captcha_key)
        captcha_challenge, captcha_response = solvemedia.challenge(captcha_key)

        # Make the downloadlink appear and load the file
        m = re.search(self.RAND_ID_PATTERN, b)
        if m is None:
            self.error("Random key not found")

        rand = m.group(1)
        self.logDebug("rand", rand)

        post_data = {'op': "download2",
                     'id': file_id,
                     'rand': rand,
                     'referer': self.pyfile.url,
                     'method_free': "+",
                     'method_premium': "",
                     'adcopy_response': captcha_response,
                     'adcopy_challenge': captcha_challenge,
                     'down_direct': "1"}
        c = self.load(self.pyfile.url, post=post_data, cookies=True, decode=True)

        m = re.search(self.LINK_PATTERN, c)
        if m is None:
            self.error("Download url not found")

        dl_url = m.group(1)
        self.download(dl_url, cookies=True, disposition=True)

        check = self.checkDownload({'html': re.compile("<html>")})
        if check == "html":
            self.error("Downloaded file is an html file")


getInfo = create_getInfo(KingfilesNet)
