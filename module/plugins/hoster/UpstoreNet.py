# -*- coding: utf-8 -*-

import re

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UpstoreNet(SimpleHoster):
    __name__    = "UpstoreNet"
    __type__    = "hoster"
    __version__ = "0.07"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?upstore\.net/'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Upstore.Net File Download Hoster"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "igelkun@myopera.com")]


    INFO_PATTERN = r'<div class="comment">.*?</div>\s*\n<h2 style="margin:0">(?P<N>.*?)</h2>\s*\n<div class="comment">\s*\n\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<span class="error">File not found</span>'

    WAIT_PATTERN = r'var sec = (\d+)'
    CHASH_PATTERN = r'<input type="hidden" name="hash" value="(.+?)">'
    LINK_FREE_PATTERN = r'<a href="(https?://.*?)" target="_blank"><b>'


    def handle_free(self, pyfile):
        #: STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.html)
        if m is None:
            self.error(_("CHASH_PATTERN not found"))
        chash = m.group(1)
        self.log_debug("Read hash " + chash)
        #: Continue to stage2
        post_data = {'hash': chash, 'free': 'Slow download'}
        self.html = self.load(pyfile.url, post=post_data)

        #: STAGE 2: solv captcha and wait
        #: First get the infos we need: recaptcha key and wait time
        recaptcha = ReCaptcha(self)

        #: Try the captcha 5 times
        for i in xrange(5):
            m = re.search(self.WAIT_PATTERN, self.html)
            if m is None:
                self.error(_("Wait pattern not found"))
            wait_time = int(m.group(1))

            #: then, do the waiting
            self.wait(wait_time)

            #: then, handle the captcha
            response, challenge = recaptcha.challenge()
            post_data.update({'recaptcha_challenge_field': challenge,
                              'recaptcha_response_field' : response})

            self.html = self.load(pyfile.url, post=post_data)

            #: STAGE 3: get direct link
            m = re.search(self.LINK_FREE_PATTERN, self.html, re.S)
            if m:
                break

        if m is None:
            self.error(_("Download link not found"))

        self.link = m.group(1)


getInfo = create_getInfo(UpstoreNet)
