# -*- coding: utf-8 -*-

import re
import urlparse

from module.network.HTTPRequest import BadHeader
from ..internal.SimpleCrypter import SimpleCrypter
from ..captcha.ReCaptcha import ReCaptcha


class MultiUpOrg(SimpleCrypter):
    __name__ = "MultiUpOrg"
    __type__ = "crypter"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?multiup\.(?:org|eu)/(?:en/|fr/)?(?:(?P<TYPE>project|download|mirror)/)?\w+(?:/\w+)?'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("hosts_priority", "str", "Prefered hosts priority (bar-separated)", ""),
                  ("ignored_hosts", "str", "Ignored hosts list (bar-separated)", ""),
                  ("grab_all", "bool", "Grab all URLs (default only first match)", False)]

    __description__ = """MultiUp.org crypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    NAME_PATTERN = r'<title>.*(?:Project|Projet|ownload|élécharger) (?P<N>.+?) (\(|- )'
    OFFLINE_PATTERN = r'File not found'
    TEMP_OFFLINE_PATTERN = r'^unmatchable$'

    URL_REPLACEMENTS = [(r'https?://(?:www\.)?multiup\.(?:org|eu)/', "http://www.multiup.eu/"),
                        (r'/fr/', "/en/")]

    COOKIES = [("multiup.eu", "_locale", "en")]

    def get_links(self):
        m_type = self.info['pattern']['TYPE']
        hosts_priority = [_h for _h in self.config.get('hosts_priority').split('|') if _h]
        ignored_hosts = [_h for _h in self.config.get('ignored_hosts').split('|') if _h]
        grab_all = self.config.get('grab_all')

        if m_type == "project":
            return re.findall(r'\n(http://www\.multiup\.eu/(?:en|fr)/download/.*)', self.data)

        elif m_type in ("download", None):
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()
            if captcha_key is not None:
                self.captcha = recaptcha
                url, inputs =  self.parse_html_form()
                mirror_page = urlparse.urljoin("http://www.multiup.eu/", url)
                try:
                    response, challenge = recaptcha.challenge(captcha_key)
                except BadHeader, e:
                    if e.code == 400 and "Please enable JavaScript to get a reCAPTCHA challenge" in e.content:
                        self.log_warning(_("Unsupported reCAPTCHA, retrying"))
                        self.retry()

                    else:
                        raise

                else:
                    inputs['g-recaptcha-response'] = response
                    self.data = self.load(mirror_page, post=inputs)

            else:
                dl_url = re.search(r'href="(.*)">.*\n.*<h5>DOWNLOAD</h5>', self.data).group(1)
                mirror_page = urlparse.urljoin("http://www.multiup.eu/", dl_url)
                self.data = self.load(mirror_page)

        self.check_errors()

        hosts_data = {}
        for _a in re.findall(r'<a\s*class="btn btn-small disabled link host"(.+?)/a>', self.data, re.S):
            validity = re.search(r'validity=(\w+)', _a).group(1)
            if validity in ("valid", "unknown"):
                host = re.search(r'nameHost="(.+?)"', _a).group(1)
                url = re.search(r'href="(.+?)"', _a).group(1)
                hosts_data[host] = url

        chosen_hosts = []
        # priority hosts goes first
        for _h in hosts_priority:
            if _h in hosts_data and _h not in ignored_hosts:
                self.log_debug("Adding '%s' link" % _h)
                chosen_hosts.append(_h)
                if not grab_all:
                    break

        # Now the rest of the hosts
        if grab_all or (not grab_all and not chosen_hosts):
            for _h in hosts_data:
                if _h not in ignored_hosts and _h not in chosen_hosts:
                    self.log_debug("Adding '%s' link" % _h)
                    chosen_hosts.append(_h)
                    if not grab_all:
                        break

        return [hosts_data[_h] for _h in chosen_hosts]
