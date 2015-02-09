# -*- coding: utf-8 -*-

import re

from urllib import unquote

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DepositfilesCom(SimpleHoster):
    __name__    = "DepositfilesCom"
    __type__    = "hoster"
    __version__ = "0.53"

    __pattern__ = r'https?://(?:www\.)?(depositfiles\.com|dfiles\.(eu|ru))(/\w{1,3})?/files/(?P<ID>\w+)'

    __description__ = """Depositfiles.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'<script type="text/javascript">eval\( unescape\(\'(?P<N>.*?)\''
    SIZE_PATTERN    = r': <b>(?P<S>[\d.,]+)&nbsp;(?P<U>[\w^_]+)</b>'
    OFFLINE_PATTERN = r'<span class="html_download_api-not_exists"></span>'

    NAME_REPLACEMENTS = [(r'\%u([0-9A-Fa-f]{4})', lambda m: unichr(int(m.group(1), 16))),
                              (r'.*<b title="(?P<N>[^"]+).*', "\g<N>")]
    URL_REPLACEMENTS  = [(__pattern__ + ".*", "https://dfiles.eu/files/\g<ID>")]

    COOKIES = [("dfiles.eu", "lang_current", "en")]

    LINK_FREE_PATTERN    = r'<form id="downloader_file_form" action="(http://.+?\.(dfiles\.eu|depositfiles\.com)/.+?)" method="post"'
    LINK_PREMIUM_PATTERN = r'class="repeat"><a href="(.+?)"'
    LINK_MIRROR_PATTERN  = r'class="repeat_mirror"><a href="(.+?)"'


    def handleFree(self, pyfile):
        if re.search(r'File is checked, please try again in a minute.', self.html) is not None:
            self.logInfo(_("The file is being checked. Waiting 1 minute"))
            self.retry(wait_time=60)

        wait = re.search(r'html_download_api-limit_interval\">(\d+)</span>', self.html)
        if wait:
            wait_time = int(wait.group(1))
            self.logInfo(_("Traffic used up. Waiting %d seconds") % wait_time)
            self.wait(wait_time, True)
            self.retry()

        wait = re.search(r'>Try in (\d+) minutes or use GOLD account', self.html)
        if wait:
            wait_time = int(wait.group(1))
            self.logInfo(_("All free slots occupied. Waiting %d minutes") % wait_time)
            self.setWait(wait_time * 60, False)

        wait = re.search(r'Please wait (\d+) sec', self.html)
        if wait:
            self.setWait(int(wait.group(1)))

        m = re.search(r"var fid = '(\w+)';", self.html)
        if m is None:
            self.retry(wait_time=5)
        params = {'fid': m.group(1)}
        self.logDebug("FID: %s" % params['fid'])

        self.wait()
        recaptcha = ReCaptcha(self)
        captcha_key = recaptcha.detect_key()
        if captcha_key is None:
            self.error(_("ReCaptcha key not found"))

        for _i in xrange(5):
            self.html = self.load("https://dfiles.eu/get_file.php", get=params)

            if '<input type=button value="Continue" onclick="check_recaptcha' in self.html:
                if 'response' in params:
                    self.invalidCaptcha()
                params['response'], params['challenge'] = recaptcha.challenge(captcha_key)
                self.logDebug(params)
                continue

            m = re.search(self.LINK_FREE_PATTERN, self.html)
            if m:
                if 'response' in params:
                    self.correctCaptcha()

                self.link = unquote(m.group(1))
                break
            else:
                self.error(_("Download link"))
        else:
            self.fail(_("No valid captcha response received"))


    def handlePremium(self, pyfile):
        if '<span class="html_download_api-gold_traffic_limit">' in self.html:
            self.logWarning(_("Download limit reached"))
            self.retry(25, 60 * 60, "Download limit reached")
        elif 'onClick="show_gold_offer' in self.html:
            self.account.relogin(self.user)
            self.retry()
        else:
            link   = re.search(self.LINK_PREMIUM_PATTERN, self.html)
            mirror = re.search(self.LINK_MIRROR_PATTERN, self.html)

            if link:
                self.link = link.group(1)

            elif mirror:
                self.link = mirror.group(1)


getInfo = create_getInfo(DepositfilesCom)
