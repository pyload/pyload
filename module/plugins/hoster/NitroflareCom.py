# -*- coding: utf-8 -*-

import re
import json

from module.plugins.Hoster import Hoster
from module.plugins.internal.CaptchaService import ReCaptcha


"""
    Right now premium support is not added
    Thus, any file that require premium support
    cannot be downloaded. Only the file that is free to
    download can be downloaded.
"""
class NitroflareCom(Hoster):
    __name__ = "NitroflareCom"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?(nitroflare\.com/view)/(?P<ID>[A-Z0-9]+)'
    __description__ = """Nitroflare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("sahil", None)]

    BASE_URL = "https://nitroflare.com"
    API_URL = "https://nitroflare.com/api/"
    DOWNLOAD_PATTERN = "\"(https?://[a-z0-9\\-_]+\\.nitroflare\\.com/[^<>\"]*?)\""

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
                    delay = result['delay']  # Don't need the delay for free downloads
                    captch_key = result['recaptchaPublic']
                    filename = result['name']
                    recaptcha = ReCaptcha(self)
                    # try upto 3 times to solve reCaptcha
                    for i in xrange(3):
                        challenge, response = recaptcha.challenge(key=captch_key)
                        res = self.load(self.BASE_URL + "/ajax/freeDownload.php",
                                             post={"method": "fetchDownload",
                                                   "recaptcha_challenge_field": challenge,
                                                   "recaptcha_response_field": response})
                        if self.handleCaptchaErrors(res):
                            break
                        if "The captcha wasn't entered correctly" or "You have to fill the captcha" in res:
                            continue
                        else:
                            break

                    if "The captcha wasn't entered correctly" or "You have to fill the captcha" in res:
                        self.logError("Captcha Failed")
                        self.offline()
                        # Captcha failed
                    else:
                        self.logInfo("result of the captcha is")
                        self.logInfo(res)
                        # self.offline()
                        download_link = re.search(self.DOWNLOAD_PATTERN, res)
                        if download_link is None:
                            print "downloasd link failed"
                            # Download link failed
                        else:
                            self.download(download_link)
        else:
            print "link is invalid"
            self.offline()
            # Link is invalid
        # self.download()

    def correct_download_link(self, url):
        return url.replace("http://", "https://")

    def checkLink(self, url):
        return True