# -*- coding: utf-8 -*-

import re

from urllib import unquote

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DepositfilesCom(SimpleHoster):
    __name__ = "DepositfilesCom"
    __type__ = "hoster"
    __version__ = "0.48"

    __pattern__ = r'https?://(?:www\.)?(depositfiles\.com|dfiles\.(eu|ru))(/\w{1,3})?/files/(?P<ID>\w+)'

    __description__ = """Depositfiles.com hoster plugin"""
    __author_name__ = ("spoob", "zoidberg", "Walter Purcaro")
    __author_mail__ = ("spoob@pyload.org", "zoidberg@mujmail.cz", "vuolter@gmail.com")

    FILE_NAME_PATTERN = r'<script type="text/javascript">eval\( unescape\(\'(?P<N>.*?)\''
    FILE_SIZE_PATTERN = r': <b>(?P<S>[0-9.]+)&nbsp;(?P<U>[kKMG])i?B</b>'
    OFFLINE_PATTERN = r'<span class="html_download_api-not_exists"></span>'

    FILE_NAME_REPLACEMENTS = [(r'\%u([0-9A-Fa-f]{4})', lambda m: unichr(int(m.group(1), 16))),
                              (r'.*<b title="(?P<N>[^"]+).*', "\g<N>")]
    FILE_URL_REPLACEMENTS = [(__pattern__, "https://dfiles.eu/files/\g<ID>")]

    SH_COOKIES = [(".dfiles.eu", "lang_current", "en")]

    RECAPTCHA_PATTERN = r"Recaptcha.create\('([^']+)'"

    FREE_LINK_PATTERN = r'<form id="downloader_file_form" action="(http://.+?\.(dfiles\.eu|depositfiles\.com)/.+?)" method="post"'
    PREMIUM_LINK_PATTERN = r'class="repeat"><a href="(.+?)"'
    PREMIUM_MIRROR_PATTERN = r'class="repeat_mirror"><a href="(.+?)"'


    def handleFree(self):
        self.html = self.load(self.pyfile.url, post={"gateway_result": "1"}, cookies=True)

        if re.search(r'File is checked, please try again in a minute.', self.html) is not None:
            self.logInfo("DepositFiles.com: The file is being checked. Waiting 1 minute.")
            self.wait(61)
            self.retry()

        wait = re.search(r'html_download_api-limit_interval\">(\d+)</span>', self.html)
        if wait:
            wait_time = int(wait.group(1))
            self.logInfo("%s: Traffic used up. Waiting %d seconds." % (self.__name__, wait_time))
            self.wait(wait_time, True)
            self.retry()

        wait = re.search(r'>Try in (\d+) minutes or use GOLD account', self.html)
        if wait:
            wait_time = int(wait.group(1))
            self.logInfo("%s: All free slots occupied. Waiting %d minutes." % (self.__name__, wait_time))
            self.setWait(wait_time * 60, False)

        wait = re.search(r'Please wait (\d+) sec', self.html)
        if wait:
            self.setWait(int(wait.group(1)))

        m = re.search(r"var fid = '(\w+)';", self.html)
        if m is None:
            self.retry(wait_time=5)
        params = {'fid': m.group(1)}
        self.logDebug("FID: %s" % params['fid'])

        captcha_key = '6LdRTL8SAAAAAE9UOdWZ4d0Ky-aeA7XfSqyWDM2m'
        m = re.search(self.RECAPTCHA_PATTERN, self.html)
        if m:
            captcha_key = m.group(1)
        self.logDebug("CAPTCHA_KEY: %s" % captcha_key)

        self.wait()
        recaptcha = ReCaptcha(self)

        for _ in xrange(5):
            self.html = self.load("https://dfiles.eu/get_file.php", get=params)

            if '<input type=button value="Continue" onclick="check_recaptcha' in self.html:
                if not captcha_key:
                    self.parseError('Captcha key')
                if 'response' in params:
                    self.invalidCaptcha()
                params['challenge'], params['response'] = recaptcha.challenge(captcha_key)
                self.logDebug(params)
                continue

            m = re.search(self.FREE_LINK_PATTERN, self.html)
            if m:
                if 'response' in params:
                    self.correctCaptcha()
                link = unquote(m.group(1))
                self.logDebug("LINK: %s" % link)
                break
            else:
                self.parseError('Download link')
        else:
            self.fail('No valid captcha response received')

        try:
            self.download(link, disposition=True)
        except:
            self.retry(wait_time=60)

    def handlePremium(self):
        self.html = self.load(self.pyfile.url, cookies=self.SH_COOKIES)

        if '<span class="html_download_api-gold_traffic_limit">' in self.html:
            self.logWarning("Download limit reached")
            self.retry(25, 60 * 60, "Download limit reached")
        elif 'onClick="show_gold_offer' in self.html:
            self.account.relogin(self.user)
            self.retry()
        else:
            link = re.search(self.PREMIUM_LINK_PATTERN, self.html)
            mirror = re.search(self.PREMIUM_MIRROR_PATTERN, self.html)
            if link:
                dlink = link.group(1)
            elif mirror:
                dlink = mirror.group(1)
            else:
                self.parseError("No direct download link or mirror found")
            self.download(dlink, disposition=True)


getInfo = create_getInfo(DepositfilesCom)
