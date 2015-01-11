# -*- coding: utf-8 -*-
#
# Note:
#   Right now premium support is not added
#   Thus, any file that require premium support
#   cannot be downloaded. Only the file that is free to
#   download can be downloaded.

import re

from module.common.json_layer import json_loads
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.SimpleHoster import SimpleHoster


class NitroflareCom(SimpleHoster):
    __name__    = "NitroflareCom"
    __type__    = "hoster"
    __version__ = "0.25"

    __pattern__ = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'

    __description__ = """Nitroflare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sahil", "sahilshekhawat01@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]

    BASE_URL = "https://nitroflare.com"
    API_URL = "https://nitroflare.com/api/"
    DOWNLOAD_PATTERN = "\"(https?://[a-z0-9\\-_]+\\.nitroflare\\.com/[^<>\"]*?)\""
    IS_FREE = True
    PREMIUM_URL = BASE_URL + "/payment"

    LINK_FREE_PATTERN = r'(https?://[\w\\-]+\\.nitroflare\\.com/[^<>\"]*?)"'

    def handleFree(self, pyfile):
        if self.checkLink(file_uid):
            file_info = self.load("https://nitroflare.com/api/getDownloadLink",
                                  get={'file': self.info['pattern']['ID']})
            self.logWarning(file_info[3:])
            file_info = json_loads(file_info[3:])  # removing non ascii characters
            if file_info['type'] == "success":
                result = file_info['result']  # already a dict
                if result['linkType'] == "free":
                    delay = int(result['delay'])
                    captch_key = result['recaptchaPublic']
                    filename = result['name']
                    recaptcha = ReCaptcha(self)
                    # used here to load the cookies which will be required later
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
                            self.download(download_link)
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