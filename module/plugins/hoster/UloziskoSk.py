# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UloziskoSk(SimpleHoster):
    __name__ = "UloziskoSk"
    __type__ = "hoster"
    __version__ = "0.23"

    __pattern__ = r'http://(?:www\.)?ulozisko.sk/.*'

    __description__ = """Ulozisko.sk hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<div class="down1">(?P<N>[^<]+)</div>'
    FILE_SIZE_PATTERN = ur'Veľkosť súboru: <strong>(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</strong><br />'
    OFFLINE_PATTERN = ur'<span class = "red">Zadaný súbor neexistuje z jedného z nasledujúcich dôvodov:</span>'

    LINK_PATTERN = r'<form name = "formular" action = "([^"]+)" method = "post">'
    ID_PATTERN = r'<input type = "hidden" name = "id" value = "([^"]+)" />'
    CAPTCHA_PATTERN = r'<img src="(/obrazky/obrazky.php\?fid=[^"]+)" alt="" />'
    IMG_PATTERN = ur'<strong>PRE ZVÄČŠENIE KLIKNITE NA OBRÁZOK</strong><br /><a href = "([^"]+)">'


    def process(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)
        self.getFileInfo()

        m = re.search(self.IMG_PATTERN, self.html)
        if m:
            url = "http://ulozisko.sk" + m.group(1)
            self.download(url)
        else:
            self.handleFree()

    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError('URL')
        parsed_url = 'http://www.ulozisko.sk' + m.group(1)

        m = re.search(self.ID_PATTERN, self.html)
        if m is None:
            self.parseError('ID')
        id = m.group(1)

        self.logDebug('URL:' + parsed_url + ' ID:' + id)

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m is None:
            self.parseError('CAPTCHA')
        captcha_url = 'http://www.ulozisko.sk' + m.group(1)

        captcha = self.decryptCaptcha(captcha_url, cookies=True)

        self.logDebug('CAPTCHA_URL:' + captcha_url + ' CAPTCHA:' + captcha)

        self.download(parsed_url, post={
            "antispam": captcha,
            "id": id,
            "name": self.pyfile.name,
            "but": "++++STIAHNI+S%DABOR++++"
        })


getInfo = create_getInfo(UloziskoSk)
