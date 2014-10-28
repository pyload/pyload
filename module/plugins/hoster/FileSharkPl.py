# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileSharkPl(SimpleHoster):
    __name__ = "FileSharkPl"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?fileshark\.pl/pobierz/\d{6}/\w{5}'

    __description__ = """FileShark.pl hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("prOq", None),
                   ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_NAME_PATTERN = r'<h2 class="name-file">(?P<N>.+)</h2>'
    FILE_SIZE_PATTERN = r'<p class="size-file">(.*?)<strong>(?P<S>\d+\.?\d*)\s(?P<U>\w+)</strong></p>'

    OFFLINE_PATTERN = '(P|p)lik zosta. (usuni.ty|przeniesiony)'

    DOWNLOAD_ALERT = r'<p class="lead text-center alert alert-warning">(.*?)</p>'
    IP_BLOCKED_PATTERN = 'Strona jest dost.pna wy..cznie dla u.ytkownik.w znajduj.cych si. na terenie Polski'
    DOWNLOAD_SLOTS_ERROR_PATTERN = r'Osi.gni.to maksymaln. liczb. .ci.ganych jednocze.nie plik.w\.'

    DOWNLOAD_URL_FREE = r'<a href="(.*?)" class="btn-upload-free">'
    DOWNLOAD_URL_PREMIUM = r'<a href="(.*?)" class="btn-upload-premium">'

    SECONDS_PATTERN = r'var timeToDownload = (\d+);'

    CAPTCHA_IMG_PATTERN = '<img src="data:image/jpeg;base64,(.*?)" title="captcha"'
    CAPTCHA_TOKEN_PATTERN = r'name="form\[_token\]" value="(.*?)" />'


    def setup(self):
        self.resumeDownload = True
        if self.premium:
            self.multiDL = True
            self.limitDL = 20
        else:
            self.multiDL = False


    def prepare(self):
        super(FileSharkPl, self).prepare()

        m = re.search(self.DOWNLOAD_ALERT, self.html):
        if m:
            return

        alert = m.group(1)

        if re.match(self.IP_BLOCKED_PATTERN, alert):
            self.fail(_("Only connections from Polish IP are allowed"))
        elif re.match(self.DOWNLOAD_SLOTS_ERROR_PATTERN, alert):
            self.logInfo(_("No free download slots available"))
            self.retry(10, 30 * 60, _("Still no free download slots available"))
        else:
            self.logInfo(alert)
            self.retry(10, 10 * 60, _("Try again later"))


    #@NOTE: handlePremium method was never been tested
    def handlePremium(self):
        self.logDebug("Premium accounts support in experimental modus!")
        m = re.search(self.DOWNLOAD_URL_PREMIUM, self.html)
        file_url = urljoin("http://fileshark.pl", m.group(1))

        self.download(file_url, disposition=True)
        self.checkDownload()


    def handleFree(self):
        m = re.search(self.DOWNLOAD_URL_FREE, self.html)
        if m is None:
            self.error(_("Download url not found"))

        file_url = urljoin("http://fileshark.pl", m.group(1))

        m = re.search(self.SECONDS_PATTERN, self.html)
        if m:
            seconds = int(m.group(1))
            self.logDebug("Wait %s seconds" % seconds)
            self.wait(seconds + 2)

        action, inputs = self.parseHtmlForm('action=""')
        m = re.search(self.CAPTCHA_TOKEN_PATTERN, self.html)
        if m is None:
            self.retry(reason=_("Captcha form not found"))

        inputs['form[_token]'] = m.group(1)

        m = re.search(self.CAPTCHA_IMG_PATTERN, self.html)
        if m is None:
            self.retry(reason=_("Captcha image not found"))

        tmp_load = self.load
        self.load = self.decode64  #: injects decode64 inside decryptCaptcha

        inputs['form[captcha]'] = self.decryptCaptcha(m.group(1), imgtype='jpeg')
        inputs['form[start]'] = ""

        self.load = tmp_load

        self.download(file_url, post=inputs, cookies=True, disposition=True)
        self.checkDownload()


    def checkDownload(self):
        check = super(FileSharkPl, self).checkDownload({
            'wrong_captcha': re.compile(r'<label for="form_captcha" generated="true" class="error">(.*?)</label>'),
            'wait_pattern': re.compile(self.SECONDS_PATTERN),
            'DL-found': re.compile('<a href="(.*)">')
        })

        if check == "DL-found":
            self.correctCaptcha()

        elif check == "wrong_captcha":
            self.invalidCaptcha()
            self.retry(10, 1, _("Wrong captcha solution"))

        elif check == "wait_pattern":
            self.retry()


    def decode64(self, data, *args, **kwargs):
        return data.decode("base64")


getInfo = create_getInfo(FileSharkPl)
