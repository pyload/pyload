# -*- coding: utf-8 -*-
import re
from module.plugins.hoster.FileserveCom import FileserveCom, checkFile

class UploadStationCom(FileserveCom):
    __name__ = "UploadStationCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploadstation\.com/file/(?P<id>[A-Za-z0-9]+)"
    __version__ = "0.5"
    __description__ = """UploadStation.Com File Download Hoster"""
    __author_name__ = ("fragonib", "zoidberg")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "zoidberg@mujmail.cz")
            
    URLS = ['http://www.uploadstation.com/file/', 'http://www.uploadstation.com/check-links.php', 'http://www.uploadstation.com/checkReCaptcha.php']
    LINKCHECK_TR = r'<div class="details (?:white|grey)">(.*?)\t{9}</div>'
    LINKCHECK_TD = r'<div class="(?:col )?col\d">(?:<[^>]*>|&nbsp;)*([^<]*)'
    
    LONG_WAIT_PATTERN = r'<h1>You have to wait (\d+) (\w+) to download the next file\.</h1>'

def getInfo(urls):    
    yield checkFile(UploadStationCom, urls) 