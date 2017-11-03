# -*- coding: utf-8 -*-

import re
import urlparse

from ..internal.SimpleHoster import SimpleHoster


class FileSharkPl(SimpleHoster):
    __name__ = "FileSharkPl"
    __type__ = "hoster"
    __version__ = "0.22"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?fileshark\.pl/pobierz/\d+/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """FileShark.pl hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("prOq", None),
                   ("Walter Purcaro", "vuolter@gmail.com")]

    NAME_PATTERN = r'<h2 class="name-file">(?P<N>.+?)</h2>'
    SIZE_PATTERN = r'<p class="size-file">(.*?)<strong>(?P<S>\d+\.?\d*)\s(?P<U>\w+)</strong></p>'
    OFFLINE_PATTERN = r'(P|p)lik zosta. (usuni.ty|przeniesiony)'

    LINK_FREE_PATTERN = r'<a rel="nofollow" href="(.*?)" class="btn-upload-free">'
    LINK_PREMIUM_PATTERN = r'<a rel="nofollow" href="(.*?)" class="btn-upload-premium">'

    WAIT_PATTERN = r'var timeToDownload = (\d+);'
    ERROR_PATTERN = r'<p class="lead text-center alert alert-warning">(.*?)</p>'
    IP_ERROR_PATTERN = r'Strona jest dost.pna wy..cznie dla u.ytkownik.w znajduj.cych si. na terenie Polski'
    SLOT_ERROR_PATTERN = r'Osi.gni.to maksymaln. liczb. .ci.ganych jednocze.nie plik.w\.'

    CAPTCHA_PATTERN = r'<img src="data:image/jpeg;base64,(.*?)" title="captcha"'
    TOKEN_PATTERN = r'name="form\[_token\]" value="(.*?)" />'

    def setup(self):
        self.resume_download = True

        if self.premium:
            self.multiDL = True
            self.limitDL = 20
        else:
            self.multiDL = False

    def check_errors(self):
        #: Check if file is now available for download (-> file name can be found in html body)
        m = re.search(self.WAIT_PATTERN, self.data)
        if m is not None:
            errmsg = self.info['error'] = _("Another download already run")
            self.retry(15, int(m.group(1)), errmsg)

        m = re.search(self.ERROR_PATTERN, self.data)
        if m is not None:
            alert = m.group(1)

            if re.match(self.IP_ERROR_PATTERN, alert):
                self.fail(_("Only connections from Polish IP are allowed"))

            elif re.match(self.SLOT_ERROR_PATTERN, alert):
                errmsg = self.info['error'] = _(
                    "No free download slots available")
                self.log_warning(errmsg)
                self.retry(
                    10, 30 * 60, _("Still no free download slots available"))

            else:
                self.info['error'] = alert
                self.retry(10, 10 * 60, _("Try again later"))

        self.info.pop('error', None)

    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(_("Download url not found"))

        link = urlparse.urljoin("https://fileshark.pl/", m.group(1))

        self.data = self.load(link)

        m = re.search(self.WAIT_PATTERN, self.data)
        if m is not None:
            seconds = int(m.group(1))
            self.log_debug("Wait %s seconds" % seconds)
            self.wait(seconds)

        action, inputs = self.parse_html_form('name="form" method="post"')

        m = re.search(self.TOKEN_PATTERN, self.data)
        if m is None:
            self.retry(msg=_("Captcha form not found"))

        inputs['form[_token]'] = m.group(1)

        m = re.search(self.CAPTCHA_PATTERN, self.data)
        if m is None:
            self.retry(msg=_("Captcha image not found"))

        inputs['form[captcha]'] = self.captcha.decrypt_image(
            m.group(1).decode('base64'), input_type='jpeg')
        inputs['form[start]'] = ""

        self.download(link, post=inputs, disposition=True)
