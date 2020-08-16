# -*- coding: utf-8 -*-
import re
import urllib.parse

from pyload.core.network.http.exceptions import BadHeader

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_decrypter import SimpleDecrypter


class MultiUpOrg(SimpleDecrypter):
    __name__ = "MultiUpOrg"
    __type__ = "decrypter"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?multiup\.(?:org|eu)/(?:en/|fr/)?(?:(?P<TYPE>project|download|mirror)/)?\w+(?:/\w+)?"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("hosts_priority", "str", "Prefered hosts priority (bar-separated)", ""),
        ("ignored_hosts", "str", "Ignored hosts list (bar-separated)", ""),
        ("grab_all", "bool", "Grab all URLs (default only first match)", False),
    ]

    __description__ = """MultiUp.org decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    NAME_PATTERN = r"<title>.*(?:Project|Projet|ownload|élécharger) (?P<N>.+?) (\(|- )"
    OFFLINE_PATTERN = r"File not found"
    TEMP_OFFLINE_PATTERN = r"^unmatchable$"

    URL_REPLACEMENTS = [
        (r"https?://(?:www\.)?multiup\.(?:org|eu)/", "http://www.multiup.eu/"),
        (r"/fr/", "/en/"),
    ]

    COOKIES = [("multiup.eu", "_locale", "en")]

    def get_links(self):
        m_type = self.info["pattern"]["TYPE"]
        hosts_priority = [h for h in self.config.get("hosts_priority").split("|") if h]
        ignored_hosts = [h for h in self.config.get("ignored_hosts").split("|") if h]
        grab_all = self.config.get("grab_all")

        if m_type == "project":
            return re.findall(
                r"\n(http://www\.multiup\.eu/(?:en|fr)/download/.*)", self.data
            )

        elif m_type in ("download", None):
            recaptcha = ReCaptcha(self.pyfile)
            captcha_key = recaptcha.detect_key()
            if captcha_key is not None:
                self.captcha = recaptcha
                url, inputs = self.parse_html_form()
                mirror_page = urllib.parse.urljoin("http://www.multiup.eu/", url)
                try:
                    response, challenge = recaptcha.challenge(captcha_key)
                except BadHeader as exc:
                    if (
                        exc.code == 400
                        and "Please enable JavaScript to get a reCAPTCHA challenge"
                        in exc.content
                    ):
                        self.log_warning(self._("Unsupported reCAPTCHA, retrying"))
                        self.retry()

                    else:
                        raise

                else:
                    inputs["g-recaptcha-response"] = response
                    self.data = self.load(mirror_page, post=inputs)

            else:
                dl_url = re.search(
                    r'href="(.*)">.*\n.*<h5>DOWNLOAD</h5>', self.data
                ).group(1)
                mirror_page = urllib.parse.urljoin("http://www.multiup.eu/", dl_url)
                self.data = self.load(mirror_page)

        self.check_errors()

        hosts_data = {}
        for a in re.findall(
            r'<a\s*class="btn btn-small disabled link host"(.+?)/a>', self.data, re.S
        ):
            validity = re.search(r"validity=(\w+)", a).group(1)
            if validity in ("valid", "unknown"):
                host = re.search(r'nameHost="(.+?)"', a).group(1)
                url = re.search(r'href="(.+?)"', a).group(1)
                hosts_data[host] = url

        chosen_hosts = []
        # priority hosts goes first
        for h in hosts_priority:
            if h in hosts_data and h not in ignored_hosts:
                self.log_debug(f"Adding '{h}' link")
                chosen_hosts.append(h)
                if not grab_all:
                    break

        # Now the rest of the hosts
        if grab_all or (not grab_all and not chosen_hosts):
            for h in hosts_data:
                if h not in ignored_hosts and h not in chosen_hosts:
                    self.log_debug(f"Adding '{h}' link")
                    chosen_hosts.append(h)
                    if not grab_all:
                        break

        return [hosts_data[h] for h in chosen_hosts]
