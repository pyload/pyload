# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DataportCz(SimpleHoster):
    __name__    = "DataportCz"
    __type__    = "hoster"
    __version__ = "0.42"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?dataport\.cz/file/(.+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Dataport.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<span itemprop="name">(?P<N>[^<]+)</span>'
    SIZE_PATTERN = r'<td class="fil">Velikost</td>\s*<td>(?P<S>[^<]+)</td>'
    OFFLINE_PATTERN = r'<h2>Soubor nebyl nalezen</h2>'

    CAPTCHA_PATTERN = r'<section id="captcha_bg">\s*<img src="(.*?)"'
    FREE_SLOTS_PATTERN = ur'Počet volných slotů: <span class="darkblue">(\d+)</span><br />'


    def handle_free(self, pyfile):
        captchas = {'1': "jkeG", '2': "hMJQ", '3': "vmEK", '4': "ePQM", '5': "blBd"}

        for _i in xrange(60):
            action, inputs = self.parse_html_form('free_download_form')
            self.log_debug(action, inputs)
            if not action or not inputs:
                self.error(_("free_download_form"))

            if "captchaId" in inputs and inputs['captchaId'] in captchas:
                inputs['captchaCode'] = captchas[inputs['captchaId']]
            else:
                self.error(_("captcha"))

            self.download("http://www.dataport.cz%s" % action, post=inputs)

            check = self.check_download({'captcha': 'alert("\u0160patn\u011b opsan\u00fd k\u00f3d z obr\u00e1zu");',
                                        'slot'   : 'alert("Je n\u00e1m l\u00edto, ale moment\u00e1ln\u011b nejsou'})
            if check == "captcha":
                self.error(_("invalid captcha"))

            elif check == "slot":
                self.log_debug("No free slots - wait 60s and retry")
                self.wait(60, False)
                self.html = self.load(pyfile.url)
                continue

            else:
                break


getInfo = create_getInfo(DataportCz)
