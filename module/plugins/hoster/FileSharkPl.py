# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileSharkPl(SimpleHoster):
    __name__    = "FileSharkPl"
    __type__    = "hoster"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?fileshark\.pl/pobierz/\d{6}/\w{5}'

    __description__ = """FileShark.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("prOq", None),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN = r'<h2 class="name-file">(?P<N>.+)</h2>'
    SIZE_PATTERN = r'<p class="size-file">(.*?)<strong>(?P<S>\d+\.?\d*)\s(?P<U>\w+)</strong></p>'

    OFFLINE_PATTERN = '(P|p)lik zosta. (usuni.ty|przeniesiony)'

    LINK_FREE_PATTERN    = r'<a href="(.*?)" class="btn-upload-free">'
    LINK_PREMIUM_PATTERN = r'<a href="(.*?)" class="btn-upload-premium">'

    WAIT_PATTERN       = r'var timeToDownload = (\d+);'
    ERROR_PATTERN      = r'<p class="lead text-center alert alert-warning">(.*?)</p>'
    IP_ERROR_PATTERN   = r'Strona jest dost.pna wy..cznie dla u.ytkownik.w znajduj.cych si. na terenie Polski'
    SLOT_ERROR_PATTERN = r'Osi.gni.to maksymaln. liczb. .ci.ganych jednocze.nie plik.w\.'

    CAPTCHA_PATTERN = '<img src="data:image/jpeg;base64,(.*?)" title="captcha"'
    TOKEN_PATTERN   = r'name="form\[_token\]" value="(.*?)" />'


    def setup(self):
        self.resumeDownload = True
        if self.premium:
            self.multiDL = True
            self.limitDL = 20
        else:
            self.multiDL = False


    def checkErrors(self):
        # check if file is now available for download (-> file name can be found in html body)
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            errmsg = self.info['error'] = _("Another download already run")
            self.retry(15, int(m.group(1)), errmsg)

        m = re.search(self.ERROR_PATTERN, self.html):
        if m:
            alert = m.group(1)

            if re.match(self.IP_ERROR_PATTERN, alert):
                self.fail(_("Only connections from Polish IP are allowed"))

            elif re.match(self.SLOT_ERROR_PATTERN, alert):
                errmsg = self.info['error'] = _("No free download slots available")
                self.logWarning(errmsg)
                self.retry(10, 30 * 60, _("Still no free download slots available"))

            else:
                self.info['error'] = alert
                self.retry(10, 10 * 60, _("Try again later"))

        self.info.pop('error', None)


    #@NOTE: handlePremium method was never been tested
    def handlePremium(self, pyfile):
        super(FilerNet, self).handlePremium(pyfile)
        if self.link:
            self.link = urljoin("http://fileshark.pl/", self.link)


    def handleFree(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Download url not found"))

        link = urljoin("http://fileshark.pl", m.group(1))

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            seconds = int(m.group(1))
            self.logDebug("Wait %s seconds" % seconds)
            self.wait(seconds)

        action, inputs = self.parseHtmlForm('action=""')

        m = re.search(self.TOKEN_PATTERN, self.html)
        if m is None:
            self.retry(reason=_("Captcha form not found"))

        inputs['form[_token]'] = m.group(1)

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m is None:
            self.retry(reason=_("Captcha image not found"))

        tmp_load  = self.load
        self.load = self._decode64  #: work-around: injects decode64 inside decryptCaptcha

        inputs['form[captcha]'] = self.decryptCaptcha(m.group(1), imgtype='jpeg')
        inputs['form[start]'] = ""

        self.load = tmp_load

        self.download(link, post=inputs, cookies=True, disposition=True)


    def checkFile(self):
        check = self.checkDownload({'wrong_captcha': re.compile(r'<label for="form_captcha" generated="true" class="error">(.*?)</label>'),
                                    'wait_pattern' : re.compile(self.SECONDS_PATTERN),
                                    'DL-found'     : re.compile('<a href="(.*)">')})

        if check == "DL-found":
            self.correctCaptcha()

        elif check == "wrong_captcha":
            self.invalidCaptcha()
            self.retry(10, 1, _("Wrong captcha solution"))

        elif check == "wait_pattern":
            self.retry()

        return super(FileSharkPl, self).checkFile()


    def _decode64(self, data, *args, **kwargs):
        return data.decode("base64")


getInfo = create_getInfo(FileSharkPl)
