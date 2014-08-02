# -*- coding: utf-8 -*-
# Testlink: http://www.kingfiles.net/zcegm9nkh2n1/test.dd

import re
from module.plugins.internal.CaptchaService import SolveMedia
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo

class KingfilesNet(SimpleHoster):
    __name__ = "KingfilesNet"
    __type__ = "hoster"
    __pattern__ = r'https?://(www\.)?kingfiles.net/.+'
    __version__ = "0.01"
    __description__ = """KingfilesNet hoster plugin (free-user)"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")

    FILE_NAME_PATTERN = r'<input type=\"hidden\" name=\"fname\" value=\"(?P<N>.+)\">'
    FILE_SIZE_PATTERN = r'>Size: <span style=\".*\">(?P<S>.+) (?P<U>[kKmMgG]?i?[bB])<'
    OFFLINE_PATTERN = r'No such file with this filename'
    FILE_ID_PATTERN = r'<input type=\"hidden\" name=\"id\" value=\"(.+)\">'
    RANDOM_PATTERN = r'type=\"hidden\" name=\"rand\" value=\"(.+)\">'
    DOWNLOAD_URL_PATTERN = r'var download_url = \'(.+)\';'
    SOLVEMEDIA_PATTERN = r'src=\"http://api.solvemedia.com/papi/challenge.script\?k=(.+)\">'

    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1
        
    def process(self,pyfile):
        #Load main page and find file-id
        a = self.load(pyfile.url, cookies=True, decode=True)
        file_id = re.search(self.FILE_ID_PATTERN, a).group(1)
        self.logDebug("file_id: "+file_id)
        
        #Click the free user button
        post_data = { "op": "download1", "usr_login": "", "id": file_id, "fname": pyfile.name, "referer": "", "method_free": "+" }
        b = self.load(pyfile.url, post=post_data, cookies=True, decode=True)
        
        #Do the captcha stuff
        captcha_key = re.search(self.SOLVEMEDIA_PATTERN, b).group(1)
        if not captcha_key:
            self.fail("Can not find captcha_key, maybe the plugin is out of date")
        self.logDebug("captcha_key: "+captcha_key)
        rand = re.search(self.RANDOM_PATTERN, b).group(1)
        if not rand:
            self.fail("Can not find random string, maybe the plugin is out of date")
        self.logDebug("random string: "+rand)
        solvemedia = SolveMedia(self)
        captcha_challenge, captcha_response = solvemedia.challenge(captcha_key)
        
        #Make the downloadlink appear and load the file
        post_data = { "op": "download2", "id": file_id, "rand": rand, "referer": pyfile.url, "method_free": "+", "method_premium": "", "adcopy_response": captcha_response, "adcopy_challenge": captcha_challenge, "down_direct": "1" }
        c = self.load(pyfile.url, post=post_data, cookies=True, decode=True)
        dl_url = re.search(self.DOWNLOAD_URL_PATTERN, c).group(1)
        if not dl_url:
            self.fail("Can not find download-url, maybe the plugin is out of date")
        self.logDebug("Downloadurl: "+dl_url)
        self.download(dl_url, cookies=True, disposition=True)
        check = self.checkDownload({"is_html": re.compile("<html>")})
        if check == "is_html":
            self.fail("The downloaded file is html, something went wrong. Maybe the plugin is out of date")
        
getInfo = create_getInfo(KingfilesNet)
