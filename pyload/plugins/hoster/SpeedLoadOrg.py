# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class SpeedLoadOrg(XFileSharingPro):
    __name__ = "SpeedLoadOrg"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?speedload\.org/(?P<ID>\w+)"
    __version__ = "1.01"
    __description__ = """Speedload.org hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_NAME_PATTERN = r'Filename:</b></td><td nowrap>(?P<N>[^<]+)</td></tr>'
    FILE_SIZE_PATTERN = r'Size:</b></td><td>[\w. ]+<small>\((?P<S>\d+) bytes\)</small>'

    HOSTER_NAME = "speedload.org"

    def handlePremium(self):
        self.download(self.pyfile.url, post = self.getPostParameters())

getInfo = create_getInfo(SpeedLoadOrg)
