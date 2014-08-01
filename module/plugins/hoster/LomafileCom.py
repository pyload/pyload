# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class LomafileCom(SimpleHoster):
    __name__ = "LomafileCom"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'https?://lomafile\.com/.+/[\w\.]+'

    __description__ = """Lomafile.com hoster plugin"""
    __author_name__ = "nath_schwarz"
    __author_mail__ = "nathan.notwhite@gmail.com"

    FILE_NAME_PATTERN = r'Filename:[^>]*>(?P<N>[\w\.]+)'
    FILE_SIZE_PATTERN = r'\((?P<S>\d+)\s(?P<U>\w+)\)'
    FILE_OFFLINE_PATTERN = r'Software error'


    def handleFree(self):
        for _ in range(3):
            captcha_id = re.search(r'src="http://lomafile\.com/captchas/(?P<id>\w+)\.jpg"', self.html)
            if not captcha_id:
                self.parseError("Unable to parse captcha id.")
            else:
                captcha_id = captcha_id.group("id")

            form_id = re.search(r'name="id" value="(?P<id>\w+)"', self.html)
            if not form_id:
                self.parseError("Unable to parse form id")
            else:
                form_id = form_id.group("id")

            captcha = self.decryptCaptcha("http://lomafile.com/captchas/" + captcha_id + ".jpg")

            self.wait(60)

            self.html = self.load(self.pyfile.url, post={
                "op": "download2",
                "id": form_id,
                "rand": captcha_id,
                "code": captcha,
                "down_direct": "1"})

            download_url = re.search(r'http://[\d\.]+:\d+/d/\w+/[\w\.]+', self.html)
            if download_url is None:
                self.invalidCaptcha()
                self.logDebug("Invalid captcha.")
            else:
                download_url = download_url.group(0)
                self.logDebug("Download URL: %s" % download_url)
                self.download(download_url)
        else:
            self.fail("Invalid captcha-code entered.")

getInfo = create_getInfo(LomafileCom)
