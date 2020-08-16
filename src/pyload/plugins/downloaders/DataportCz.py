# -*- coding: utf-8 -*-


from ..base.simple_downloader import SimpleDownloader


class DataportCz(SimpleDownloader):
    __name__ = "DataportCz"
    __type__ = "downloader"
    __version__ = "0.47"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?dataport\.cz/file/(.+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Dataport.cz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<span itemprop="name">(?P<N>.+?)</span>'
    SIZE_PATTERN = r'<td class="fil">Velikost</td>\s*<td>(?P<S>[^<]+)</td>'
    OFFLINE_PATTERN = r"<h2>Soubor nebyl nalezen</h2>"

    CAPTCHA_PATTERN = r'<section id="captcha_bg">\s*<img src="(.*?)"'
    FREE_SLOTS_PATTERN = (
        r'Počet volných slotů: <span class="darkblue">(\d+)</span><br />'
    )

    def handle_free(self, pyfile):
        captchas = {"1": "jkeG", "2": "hMJQ", "3": "vmEK", "4": "ePQM", "5": "blBd"}

        action, inputs = self.parse_html_form("free_download_form")
        self.log_debug(action, inputs)
        if not action or not inputs:
            self.error(self._("free_download_form"))

        if "captchaId" in inputs and inputs["captchaId"] in captchas:
            inputs["captchaCode"] = captchas[inputs["captchaId"]]
        else:
            self.error(self._("Captcha not found"))

        self.download("http://www.dataport.cz{}".format(action, post=inputs))

        check = self.scan_download(
            {
                "captcha": 'alert("\\u0160patn\\u011b opsan\\u00fd k\\u00f3d z obr\\u00e1zu");',
                "slot": 'alert("Je n\\u00e1m l\\u00edto, ale moment\\u00e1ln\\u011b nejsou',
            }
        )
        if check == "captcha":
            self.retry_captcha()

        elif check == "slot":
            self.log_debug("No free slots - wait 60s and retry")
            self.retry(wait=60)
