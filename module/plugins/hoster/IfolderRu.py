# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class IfolderRu(SimpleHoster):
    __name__ = "IfolderRu"
    __type__ = "hoster"
    __version__ = "0.44"
    __status__ = "testing"

    __pattern__ = r'http://(?:www)?(files\.)?(ifolder\.ru|metalarea\.org|rusfolder\.(com|net|ru))/(files/)?(?P<ID>\d+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Ifolder.ru hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    SIZE_REPLACEMENTS = [(u'Кб', 'KB'), (u'Мб', 'MB'), (u'Гб', 'GB')]

    NAME_PATTERN = ur'(?:<div><span>)?Название:(?:</span>)? <b>(?P<N>.+?)</b><(?:/div|br)>'
    SIZE_PATTERN = ur'(?:<div><span>)?Размер:(?:</span>)? <b>(?P<S>.+?)</b><(?:/div|br)>'
    OFFLINE_PATTERN = ur'<p>Файл номер <b>.*?</b> (не найден|удален) !!!</p>'

    SESSION_ID_PATTERN = r'<input type="hidden" name="session" value="(.+?)"'
    INTS_SESSION_PATTERN = r'\(\'ints_session\'\);\s*if\(tag\)\{tag\.value = "(.+?)";\}'
    HIDDEN_INPUT_PATTERN = r'var v = .*?name=\'(.+?)\' value=\'1\''

    LINK_FREE_PATTERN = r'<a href="(.+?)" class="downloadbutton_files"'

    WRONG_CAPTCHA_PATTERN = ur'<font color=Red>неверный код,<br>введите еще раз</font><br>'

    def setup(self):
        self.resume_download = self.multiDL = bool(self.account)
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        url = "http://rusfolder.com/%s" % self.info['pattern']['ID']
        self.data = self.load(
            "http://rusfolder.com/%s" %
            self.info['pattern']['ID'])
        self.get_fileInfo()

        session_id = re.search(self.SESSION_ID_PATTERN, self.data).groups()
        captcha_url = "http://ints.rusfolder.com/random/images/?session=%s" % session_id

        action, inputs = self.parse_html_form('id="download-step-one-form"')
        inputs['confirmed_number'] = self.captcha.decrypt(
            captcha_url, cookies=True)
        inputs['action'] = '1'
        self.log_debug(inputs)

        self.data = self.load(url, post=inputs)
        if self.WRONG_CAPTCHA_PATTERN in self.data:
            self.retry_captcha()

        self.link = re.search(self.LINK_FREE_PATTERN, self.data).group(1)
