# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class KingfilesNet(SimpleHoster):
    __name__ = "KingfilesNet"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?kingfiles\.net/\w{12}'

    __description__ = """Kingfiles.net hoster plugin"""
    __author_name__ = ("zapp-brannigan", "Walter Purcaro")
    __author_mail__ = ("fuerst.reinje@web.de", "vuolter@gmail.com")


    FILE_NAME_PATTERN = r'name="fname" value="(?P<N>.+?)">'
    FILE_SIZE_PATTERN = r'>Size: .+?">(?P<S>[\d.]+) (?P<U>\w+)'

    OFFLINE_PATTERN = r'>(File Not Found</b><br><br>|File Not Found</h2>)'

    FILE_ID_PATTERN = r'<input type=\"hidden\" name=\"id\" value=\"(.+)\">'
    RAND_ID_PATTERN = r'type=\"hidden\" name=\"rand\" value=\"(.+)\">'

    LINK_PATTERN = r'var download_url = \'(.+)\';'
    SOLVEMEDIA_PATTERN = r'http://api\.solvemedia\.com/papi/challenge\.script\?k=(.+)\">'


    def setup(self):
        self.multiDL = True
        self.resumeDownload = True


    def handleFree(self):
        # Load main page and find file-id
        a = self.load(self.pyfile.url, cookies=True, decode=True)
        file_id = re.search(self.FILE_ID_PATTERN, a).group(1)
        self.logDebug("file_id", file_id)

        # Click the free user button
        post_data = {'op': "download1",
                     'usr_login': "",
                     'id': file_id,
                     'fname': self.pyfile.name,
                     'referer': "",
                     'method_free': "+"}
        b = self.load(self.pyfile.url, post=post_data, cookies=True, decode=True)

        # Do the captcha stuff
        m = re.search(self.SOLVEMEDIA_PATTERN, b)
        if m is None:
            self.parseError("Captcha key not found")

        solvemedia = SolveMedia(self)
        captcha_key = m.group(1)
        self.logDebug("captcha_key", captcha_key)
        captcha_challenge, captcha_response = solvemedia.challenge(captcha_key)

        # Make the downloadlink appear and load the file
        m = re.search(self.RAND_ID_PATTERN, b)
        if m is None:
            self.parseError("Random key not found")

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
            self.parseError("Download url not found")

        dl_url = m.group(1)
        self.download(dl_url, cookies=True, disposition=True)

        check = self.checkDownload({'is_html': re.compile("<html>")})
        if check == "is_html":
            self.parseError("Downloaded file is an html file")


getInfo = create_getInfo(KingfilesNet)
