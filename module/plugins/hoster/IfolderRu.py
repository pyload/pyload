# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

import re
from urllib import quote
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.network.RequestFactory import getURL

class IfolderRu(SimpleHoster):
    __name__ = "IfolderRu"
    __type__ = "hoster"
    __pattern__ = r"http://(?:[^.]*\.)?(?:ifolder.ru|rusfolder.com)/(?P<ID>\d+).*"
    __version__ = "0.36"
    __description__ = """rusfolder.com / ifolder.ru"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_SIZE_REPLACEMENTS = [(u'Кб', 'KB'), (u'Мб', 'MB'), (u'Гб', 'GB')]
    FILE_NAME_PATTERN = ur'(?:<div><span>)?Название:(?:</span>)? <b>(?P<N>[^<]+)</b><(?:/div|br)>'
    FILE_SIZE_PATTERN = ur'(?:<div><span>)?Размер:(?:</span>)? <b>(?P<S>[^<]+)</b><(?:/div|br)>'
    FILE_OFFLINE_PATTERN = ur'<p>Файл номер <b>[^<]*</b> (не найден|удален) !!!</p>'
    
    SESSION_ID_PATTERN = r'<a href=(http://ints.(?:rusfolder.com|ifolder.ru)/ints/sponsor/\?bi=\d*&session=([^&]+)&u=[^>]+)>'
    INTS_SESSION_PATTERN = r'\(\'ints_session\'\);\s*if\(tag\)\{tag.value = "([^"]+)";\}'
    HIDDEN_INPUT_PATTERN = r"var v = .*?name='([^']+)' value='1'"
    DOWNLOAD_LINK_PATTERN = r'<a id="download_file_href" href="([^"]+)"'
    WRONG_CAPTCHA_PATTERN = ur'<font color=Red>неверный код,<br>введите еще раз</font><br>'

    def setup(self):
        self.resumeDownload = self.multiDL = True if self.account else False
        self.chunkLimit = 1

    def process(self, pyfile):
        file_id = re.search(self.__pattern__, pyfile.url).group('ID')
        self.html = self.load("http://rusfolder.com/%s" % file_id, cookies=True, decode=True)
        self.getFileInfo()

        url = "http://ints.rusfolder.com/ints/?rusfolder.com/%s?ints_code=" % file_id
        self.html = self.load(url, cookies=True, decode=True)
        
        url, session_id = re.search(self.SESSION_ID_PATTERN, self.html).groups()
        self.html = self.load(url, cookies=True, decode=True)

        url = "http://ints.rusfolder.com/ints/frame/?session=%s" % session_id
        self.html = self.load(url, cookies=True)

        self.setWait(31, False)
        self.wait()

        captcha_url = "http://ints.rusfolder.com/random/images/?session=%s" % session_id
        for i in range(5):
            self.html = self.load(url, cookies=True)          
            action, inputs = self.parseHtmlForm('ID="Form1"')
            inputs['ints_session'] = re.search(self.INTS_SESSION_PATTERN, self.html).group(1)
            inputs[re.search(self.HIDDEN_INPUT_PATTERN, self.html).group(1)] = '1'
            inputs['confirmed_number'] = self.decryptCaptcha(captcha_url, cookies = True)
            inputs['action'] = '1'
            self.logDebug(inputs)

            self.html = self.load(url, decode = True, cookies = True, post = inputs)
            if self.WRONG_CAPTCHA_PATTERN in self.html:
                self.invalidCaptcha()
            else:
                break;
        else:
            self.fail("Invalid captcha")

        self.html = self.load("http://rusfolder.com/%s?ints_code=%s" % (file_id, session_id), decode=True, cookies = True)

        download_url = re.search(self.DOWNLOAD_LINK_PATTERN, self.html).group(1)
        self.correctCaptcha()
        self.logDebug("Download URL: %s" % download_url)
        self.download(download_url)

getInfo = create_getInfo(IfolderRu)