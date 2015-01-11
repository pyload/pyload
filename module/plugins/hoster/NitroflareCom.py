# -*- coding: utf-8 -*-

import re
import json

from time import sleep
from module.plugins.Hoster import Hoster
from module.plugins.internal.CaptchaService import ReCaptcha


class NitroflareCom(Hoster):
    __name__ = "NitroflareCom"
    __type__ = "hoster"
    __version__ = "0.13"

    __pattern__ = r'https?://(?:www\.)?(nitroflare\.com/view)/(?P<ID>[A-Z0-9]+)'
    __description__ = """Nitroflare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("sahil", None)]

    BASE_URL = "https://nitroflare.com"
    API_URL = "https://nitroflare.com/api/"
    DOWNLOAD_PATTERN = "\"(https?://[a-z0-9\\-_]+\\.nitroflare\\.com/[^<>\"]*?)\""
    IS_FREE = True
    PREMIUM_URL = BASE_URL + "/payment"

    def process(self, pyfile):

        if "https://" not in pyfile.url:
            pyfile.url = self.correct_download_link(pyfile.url)

        url_match = re.match(self.__pattern__, pyfile.url)
        file_uid = url_match.group('ID')
        if self.checkLink(file_uid):
            file_info = self.load(self.API_URL + "getDownloadLink?file=" + file_uid)
            self.logWarning(file_info[3:])
            file_info = json.loads(file_info[3:])  # removing non ascii characters
            if file_info['type'] == "success":
                result = file_info['result']  # already a dict
                if result['linkType'] == "free":
                    delay = int(result['delay'])
                    captch_key = result['recaptchaPublic']
                    filename = result['name']
                    recaptcha = ReCaptcha(self)
                    main_page = self.load(pyfile.url)
                    go_to_free_page = self.load(pyfile.url,
                                                post={"goToFreePage": ""})
                    # challenge, response = recaptcha.challenge(key=captch_key)
                    res = self.load(self.BASE_URL + "/ajax/freeDownload.php",
                                    post={"method": "startTimer",
                                    "fileId": file_uid})[4:]

                    if "This file is available with premium key only" in res:
                        self.fail("This file is available with premium key only")
                    if "downloading is not possible" in res:
                        wait_time = re.search("You have to wait (\\d+) minutes to download your next file", res)
                        if wait_time is not None:
                            self.fail("IP Address blocked")
                        self.fail("Downloading is not possible")
                    else:
                        self.logInfo(res)
                        js_file = self.load(self.BASE_URL + "/js/downloadFree.js?v=1.0.1")
                        var_time = re.search("var time = (\\d+);", js_file)
                        wait = 60
                        if var_time is not None:
                            wait = int(var_time.groups()[0])
                        self.setWait(wait)
                        self.wait()
                        for i in xrange(3):
                            challenge, response = recaptcha.challenge(key=captch_key)
                            res_final = self.load(self.BASE_URL + "/ajax/freeDownload.php",
                                            post={"method": "fetchDownload",
                                            "recaptcha_challenge_field": challenge,
                                            "recaptcha_response_field": response})[3:]
                            self.logInfo(res_final)

                            if self.handleCaptchaErrors(res_final):
                                break
                            if "The captcha wasn't entered correctly" or "You have to fill the captcha" in res_final:
                                continue
                            else:
                                break
                        download_link = re.search(self.DOWNLOAD_PATTERN, res_final)
                        if download_link is None:
                            self.fail("Could not find a download link. Please check the download link again")
                        else:
                            try:
                                self.download(download_link)
                            except:
                                self.fail("Downloading failed")
        else:
            self.fail("Link is not valid. Please check the link again")

    def correct_download_link(self, url):
        return url.replace("http://", "https://")

    def checkLink(self, url):
        return True

    def handle_api(self, download_url, account):
        handle_downloadAPI(download_url, account)

    def enable_premium(self, url):
        self.IS_FREE = False  # To try premium
