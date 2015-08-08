# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileSharkPl(SimpleHoster):
    __name__    = "FileSharkPl"
    __type__    = "hoster"
    __version__ = "0.13"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fileshark\.pl/pobierz/\d+/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """FileShark.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("prOq", None),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'<h2 class="name-file">(?P<N>.+?)</h2>'
    SIZE_PATTERN    = r'<p class="size-file">(.*?)<strong>(?P<S>\d+\.?\d*)\s(?P<U>\w+)</strong></p>'
    OFFLINE_PATTERN = r'(P|p)lik zosta. (usuni.ty|przeniesiony)'

    LINK_FREE_PATTERN    = r'<a  rel="nofollow" href="(.*?)" class="btn-upload-free">'
    LINK_PREMIUM_PATTERN = r'<a rel="nofollow" href="(.*?)" class="btn-upload-premium">'

    WAIT_PATTERN       = r'var timeToDownload = (\d+);'
    ERROR_PATTERN      = r'<p class="lead text-center alert alert-warning">(.*?)</p>'
    IP_ERROR_PATTERN   = r'Strona jest dost.pna wy..cznie dla u.ytkownik.w znajduj.cych si. na terenie Polski'
    SLOT_ERROR_PATTERN = r'Osi.gni.to maksymaln. liczb. .ci.ganych jednocze.nie plik.w\.'

    CAPTCHA_PATTERN = r'<img src="data:image/jpeg;base64,(.*?)" title="captcha"'
    TOKEN_PATTERN   = r'name="form\[_token\]" value="(.*?)" />'


    def setup(self):
        self.resume_download = True

        if self.premium:
            self.multiDL = True
            self.limitDL = 20
        else:
            self.multiDL = False


    def check_errors(self):
        #: Check if file is now available for download (-> file name can be found in html body)
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            errmsg = self.info['error'] = _("Another download already run")
            self.retry(15, int(m.group(1)), errmsg)

        m = re.search(self.ERROR_PATTERN, self.html)
        if m:
            alert = m.group(1)

            if re.match(self.IP_ERROR_PATTERN, alert):
                self.fail(_("Only connections from Polish IP are allowed"))

            elif re.match(self.SLOT_ERROR_PATTERN, alert):
                errmsg = self.info['error'] = _("No free download slots available")
                self.log_warning(errmsg)
                self.retry(10, 30 * 60, _("Still no free download slots available"))

            else:
                self.info['error'] = alert
                self.retry(10, 10 * 60, _("Try again later"))

        self.info.pop('error', None)


    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Download url not found"))

        link = urlparse.urljoin("http://fileshark.pl", m.group(1))

        self.html = self.load(link)

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            seconds = int(m.group(1))
            self.log_debug("Wait %s seconds" % seconds)
            self.wait(seconds)

        action, inputs = self.parse_html_form('action=""')

        m = re.search(self.TOKEN_PATTERN, self.html)
        if m is None:
            self.retry(reason=_("Captcha form not found"))

        inputs['form[_token]'] = m.group(1)

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m is None:
            self.retry(reason=_("Captcha image not found"))

        inputs['form[captcha]'] = self.captcha._decrypt(m.group(1).decode('base64'), input_type='jpeg')
        inputs['form[start]'] = ""

        self.download(link, post=inputs, disposition=True)


getInfo = create_getInfo(FileSharkPl)
