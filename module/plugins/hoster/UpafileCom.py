# -*- coding: utf-8 -*-
import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class UpafileCom(SimpleHoster):
    __name__ = "UpafileCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?upafile\.com/(?P<ID>.+)"
    __version__ = "0.01"
    __description__ = """Upafile.com hoster plugin"""
    __author_name__ = ("igel")
    __author_mail__ = ("")

    FILE_NAME_PATTERN = r'Filename:</b></td><td nowrap>(?P<N>.+)</td>'
    FILE_SIZE_PATTERN = r'Size:<b></td><td>(?P<S>[^<]+) <small>'
    FILE_OFFLINE_PATTERN = r'File Not Found'

#    RECAPTCHA_KEY = '6Leh58kSAAAAAMi5MOyVQjl-pfwPf-GhmdYiOfJ7'
    RECAPTCHA_KEY = '6Leh58kSAAAAAMi5MOyVQjl-pfwPf-GhmdYiOfJ7 '
    DIRECT_LINK_PATTERN = r'<a href="([^"]+)"><img src="[^"]*down.jpg"'

    def setup(self):
        self.resumeDownload = True
        self.multiDL = False

    def handleFree(self):

        # Define search patterns
        op_pattern = '<input type="hidden" name="op" value="(.*)">'
        id_pattern = '<input type="hidden" name="id" value="(.*)">'
        re_pattern = '<input type="hidden" name="referer" value="(.*)">'
        rand_pattern = '<input type="hidden" name="rand" value="(.*)">'

        # Get HTML source
        self.logDebug("Getting HTML sourc from " + self.pyfile.url)
        html = self.load(self.pyfile.url)

        # Retrieve data
        op_val = re.search(op_pattern, html).group(1)
        id_val = re.search(id_pattern, html).group(1)
        rand_val = re.search(rand_pattern, html).group(1)
        re_val = re.search(re_pattern, html).group(1)

        if op_val is None:
            self.retry(3, 10, "No op found!")

        if id_val is None:
            self.retry(3, 10, "No id found!")

        if rand_val is None:
            self.retry(3, 10, "No rand found!")
        
        if re_val is None:
          re_val = self.pyfile.url

        # Debug values
        self.logDebug(" > Op " + op_val)
        self.logDebug(" > Id " + id_val)
        self.logDebug(" > Rand " + rand_val)
        self.logDebug(" > Referer " + re_val)

        # Captcha handling
        recaptcha = ReCaptcha(self)
        for i in xrange(5):
            challenge, response = recaptcha.challenge(self.RECAPTCHA_KEY)
            # Create post data
            post_data = {'recaptcha_challenge_field': challenge,
                         'recaptcha_response_field': response,
                         'CaptchaForm%5Bcode%5D': '',
                         "op": op_val,
                         "id": id_val,
                         "rand": rand_val,
                         "referer": re_val,
                         "method_free": "",
                         "method_premium": "",
                         "down_direct": "1",
                         "btn_download": "Create Download Link"}

            self.html = self.load(self.pyfile.url, post=post_data)

            if 'recaptcha' not in self.html:
                self.correctCaptcha()
                self.setWait(10)
                self.wait()
                break
            else:
                self.logInfo('Wrong captcha')
                #self.invalidCaptcha()
                self.fail('Wrong Captcha')
        else:
            self.fail("All captcha attempts failed")

        # Get link value
        link_val = re.search(self.DIRECT_LINK_PATTERN, self.html)
        if link_val is not None:
            self.logDebug(" > Link: " + link_val.group(1))
            self.download(link_val.group(1))
        else:
            self.logDebug("No link found!")
            self.retry(3, 10, "No link found!")


getInfo = create_getInfo(UpafileCom)
