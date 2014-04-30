# -*- coding: utf-8 -*-

#import re
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
#from pycurl import FOLLOWLOCATION, LOW_SPEED_TIME


class MovReelCom(XFileSharingPro):
    __name__ = "MovReelCom"
    __type__ = "hoster"
    __pattern__ = r'http://(?:www\.)?movreel.com/.*'
    __version__ = "1.20"
    __description__ = """MovReel.com hoster plugin"""
    __author_name__ = ("JorisV83","t4skforce")
    __author_mail__ = ("jorisv83-pyload@yahoo.com","t4skforce1337[AT]gmail[DOT]com")

    HOSTER_NAME = "movreel.com"

    #FILE_NAME_PATTERN = r'<b>Filename:</b>(?P<N>.*?)<br>'
    #FILE_SIZE_PATTERN = r'<b>Size:</b>(?P<S>.*?)<br>'
    FILE_INFO_PATTERN = r'<h3>(?P<N>.+?) <small><sup>(?P<S>[\d.]+) (?P<U>..)</sup> </small></h3>'
    FILE_OFFLINE_PATTERN = r'<b>File Not Found</b><br><br>'
    DIRECT_LINK_PATTERN = r'<a href="(http://[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*/.*)">Download Link</a>'
    #OVR_DOWNLOAD_LINK_PATTERN = "var file_link = '(.*)';"
    
    def prepare(self):
        XFileSharingPro.prepare(self)
        if self.account != None:
            info = self.account.getAccountInfo(self.user, True)
            self.logDebug("info"+str(info))
            self.premium = info['premium']
        

getInfo = create_getInfo(MovReelCom)
