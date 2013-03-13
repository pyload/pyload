# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.ReCaptcha import ReCaptcha
import re

def to_seconds(m):
    minutes = int(m['m']) if m['m'] else 0
    seconds = int(m['s']) if m['s'] else 0
    return minutes * 60 + seconds

class EgoFilesCom(SimpleHoster):
    __name__ = "EgoFilesCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(www\.)?egofiles.com/(\w+)"
    __version__ = "0.07"
    __description__ = """Egofiles.com Download Hoster"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<div class="down-file">\s+(?P<N>\S+)\s+<div class="file-properties">\s+(File size|Rozmiar): (?P<S>[\w.]+) (?P<U>\w+) \|'
    FILE_OFFLINE_PATTERN = r'File size: 0 KB'
    WAIT_TIME_PATTERN = r'For next free download you have to wait <strong>((?P<m>\d*)m)? ?((?P<s>\d+)s)?</strong>'
    DIRECT_LINK_PATTERN = r'<a href="(?P<link>[^"]+)">Download ></a>'
    RECAPTCHA_KEY = '6LeXatQSAAAAAHezcjXyWAni-4t302TeYe7_gfvX'

    def init(self):
        self.file_info = {}
        # Set English language
        self.load("https://egofiles.com/ajax/lang.php?lang=en", just_header=True)

    def process(self, pyfile):
        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

        # Wait time between free downloads
        if 'For next free download you have to wait' in self.html:
            m = re.search(self.WAIT_TIME_PATTERN, self.html)
            self.setWait(to_seconds(m.groupdict()), True)
            self.wait()

        downloadURL = ''
        recaptcha = ReCaptcha(self)
        for i in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
            post_data = {'recaptcha_challenge_field': challenge,
                         'recaptcha_response_field': response}
            self.html = self.load(self.pyfile.url, post=post_data, decode=True)
            m = re.search(self.DIRECT_LINK_PATTERN, self.html)
            if not m:
                self.logInfo('Wrong captcha')
                self.invalidCaptcha()
            elif hasattr(m, 'group'):
                downloadURL = m.group('link')
                self.correctCaptcha()
                break
            else:
                self.fail('Unknown error - Plugin may be out of date')

        if not downloadURL:
            self.fail("No Download url retrieved/all captcha attempts failed")

        self.download(downloadURL)

    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if header.has_key('location'):
            self.logDebug('DIRECT LINK from header: ' + header['location'])
            self.download(header['location'])
        else:
            self.html = self.load(self.pyfile.url, decode=True)
            m = re.search(r'<a href="(?P<link>[^"]+)">Download ></a>', self.html)
            if not m:
                self.parseError('Unable to detect direct download url')
            else:
                self.logDebug('DIRECT URL from html: ' + m.group('link'))
                self.download(m.group('link'))

getInfo = create_getInfo(EgoFilesCom)
