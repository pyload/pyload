# -*- coding: utf-8 -*-
#import re
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
#from pycurl import FOLLOWLOCATION, LOW_SPEED_TIME

class MovReelCom(XFileSharingPro):
    __name__ = "MovReelCom"
    __type__ = "hoster"
    __pattern__ = r"http://movreel.com/.*"
    __version__ = "1.10"
    __description__ = """MovReel.com hoster plugin"""
    __author_name__ = ("JorisV83")
    __author_mail__ = ("jorisv83-pyload@yahoo.com")

    #FILE_NAME_PATTERN = r'<b>Filename:</b>(?P<N>.*?)<br>'
    #FILE_SIZE_PATTERN = r'<b>Size:</b>(?P<S>.*?)<br>'
    FILE_INFO_PATTERN = r'You have requested <font color="red">http://movreel.com/.*/(?P<N>.+?)</font>.*\((?P<S>[\d.]+) (?P<U>..)\)</font>'
    FILE_OFFLINE_PATTERN = r'<b>File Not Found</b>'
    DIRECT_LINK_PATTERN = "var file_link = '(.*)';"
    #OVR_DOWNLOAD_LINK_PATTERN = "var file_link = '(.*)';"
    HOSTER_NAME = "movreel.com"
                     "method_free": "+Free+Download"}
                     "method_premium": "", "down_direct": "1"}
    

getInfo = create_getInfo(MovReelCom)
