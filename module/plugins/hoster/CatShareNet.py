# -*- coding: utf-8 -*-

import re
from urllib import unquote
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class CatShareNet(SimpleHoster):
    __name__ = "CatShareNet"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?catshare.net/\w{16}.*'
    __version__ = "0.02"
    __description__ = """CatShare.net hoster plugin"""
    __author_name__ = ("prOq","z00nx")
    __author_mail__ = (" ","z00nx0@gmail.com")

    FILE_INFO_PATTERN = r'<h3 class="pull-left"[^>]+>(?P<N>.*)</h3>\s+<h3 class="pull-right"[^>]+>(?P<S>.*)</h3>'
    FILE_OFFLINE_PATTERN = r'Podany plik zosta'
    SECONDS_PATTERN = 'var\s+count\s+=\s+(\d+);'
    RECAPTCHA_KEY = "6Lfln9kSAAAAANZ9JtHSOgxUPB9qfDFeLUI_QMEy"
    DOWNLOAD_LINK_PATTERN = r'<form action="(.*?)" method="GET">'

    def handleFree(self):
	# check if file is offline
	found = re.search(self.FILE_OFFLINE_PATTERN, self.html)
	if found is not None:
            self.logInfo("This file is offline")
	    self.offline()
	# file is online; check wait time
        found = re.search(self.SECONDS_PATTERN, self.html)
        seconds = int(found.group(1))
        self.logDebug("Seconds found", seconds)
        self.wait(seconds + 1)
	# solve captcha and send solution
       	recaptcha = ReCaptcha(self)
        challenge, code = recaptcha.challenge(self.RECAPTCHA_KEY)
        post_data = {"recaptcha_challenge_field": challenge, "recaptcha_response_field": code}
	self.html = self.load(self.pyfile.url, post=post_data, decode = True, ref = True)
	# find download url
	found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
	if found is None:
            self.logInfo("Wrong captcha entered")
            self.invalidCaptcha()
            self.retry()
	download_url = unquote(found.group(1))
	self.download(download_url)

getInfo = create_getInfo(CatShareNet)
