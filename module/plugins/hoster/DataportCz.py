# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DataportCz(SimpleHoster):
    __name__ = "DataportCz"
    __type__ = "hoster"
    __version__ = "0.37"

    __pattern__ = r'http://(?:www\.)?dataport.cz/file/(.*)'

    __description__ = """Dataport.cz hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<span itemprop="name">(?P<N>[^<]+)</span>'
    FILE_SIZE_PATTERN = r'<td class="fil">Velikost</td>\s*<td>(?P<S>[^<]+)</td>'
    OFFLINE_PATTERN = r'<h2>Soubor nebyl nalezen</h2>'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.dataport.cz/file/\1')]

    CAPTCHA_URL_PATTERN = r'<section id="captcha_bg">\s*<img src="(.*?)"'
    FREE_SLOTS_PATTERN = ur'Počet volných slotů: <span class="darkblue">(\d+)</span><br />'


    def handleFree(self):
        captchas = {"1": "jkeG", "2": "hMJQ", "3": "vmEK", "4": "ePQM", "5": "blBd"}

        for _ in xrange(60):
            action, inputs = self.parseHtmlForm('free_download_form')
            self.logDebug(action, inputs)
            if not action or not inputs:
                self.parseError('free_download_form')

            if "captchaId" in inputs and inputs['captchaId'] in captchas:
                inputs['captchaCode'] = captchas[inputs['captchaId']]
            else:
                self.parseError('captcha')

            self.html = self.download("http://www.dataport.cz%s" % action, post=inputs)

            check = self.checkDownload({"captcha": 'alert("\u0160patn\u011b opsan\u00fd k\u00f3d z obr\u00e1zu");',
                                        "slot": 'alert("Je n\u00e1m l\u00edto, ale moment\u00e1ln\u011b nejsou'})
            if check == "captcha":
                self.parseError('invalid captcha')
            elif check == "slot":
                self.logDebug("No free slots - wait 60s and retry")
                self.wait(60, False)
                self.html = self.load(self.pyfile.url, decode=True)
                continue
            else:
                break


create_getInfo(DataportCz)
