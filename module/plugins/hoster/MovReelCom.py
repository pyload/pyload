# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class MovReelCom(XFileSharingPro):
    __name__ = "MovReelCom"
    __type__ = "hoster"
    __version__ = "1.21"

    __pattern__ = r'http://(?:www\.)?movreel\.com/\w{12}'

    __description__ = """MovReel.com hoster plugin"""
    __author_name__ = "JorisV83"
    __author_mail__ = "jorisv83-pyload@yahoo.com"


    HOSTER_NAME = "movreel.com"

    FILE_NAME_PATTERN = r'Filename: <b>(?P<N>.+?)<'
    FILE_SIZE_PATTERN = r'Size: (?P<S>[\d.]+) (?P<U>\w+)'

    LINK_PATTERN = r'<a href="([^"]+)">Download Link'


getInfo = create_getInfo(MovReelCom)
