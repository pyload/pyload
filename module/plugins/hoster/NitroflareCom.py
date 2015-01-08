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
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'

    __description__ = """Nitroflare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sahil", ""),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    # URL_REPLACEMENTS = [("http://", "https://")]

    LINK_FREE_PATTERN = r'(https?://[\w\\-]+\\.nitroflare\\.com/[^<>\"]*?)"'


    def handleFree(self, pyfile):
        file_info = self.load("https://nitroflare.com/api/getDownloadLink",
                              get={'file': self.info['pattern']['ID']})

        self.logWarning(file_info[3:])
        file_info = json_loads(file_info[3:])  # removing non ascii characters
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
                    res = self.load("https://nitroflare.com/ajax/freeDownload.php",
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
