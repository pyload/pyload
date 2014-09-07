# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class PotloadCom(XFileSharingPro):
    __name__ = "PotloadCom"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?potload\.com/\w{12}'

    __description__ = """Potload.com hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    HOSTER_NAME = "potload.com"

    FILE_INFO_PATTERN = r'<h[1-6]>(?P<N>.+) \((?P<S>\d+) (?P<U>\w+)\)</h'


getInfo = create_getInfo(PotloadCom)
