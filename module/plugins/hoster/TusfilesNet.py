# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class TusfilesNet(XFileSharingPro):
    __name__ = "TusfilesNet"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?tusfiles\.net/\w{12}"
    __version__ = "0.01"
    __description__ = """Tusfiles.net hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'<li>(?P<N>[^<]+)</li>\s+<li><b>Size:</b> <small>(?P<S>[\d.]+) (?P<U>\w+)</small></li>'
    FILE_OFFLINE_PATTERN = r'The file you were looking for could not be found'

    HOSTER_NAME = "tusfiles.net"

getInfo = create_getInfo(TusfilesNet)
