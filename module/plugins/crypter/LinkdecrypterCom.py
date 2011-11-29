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
from module.plugins.Crypter import Crypter

class LinkdecrypterCom(Crypter):
    __name__ = "LinkdecrypterCom"
    __type__ = "crypter"
    __pattern__ = r"http://(\w*\.)?(10001mb\.com|123link\.it|1cl\.in|1kh\.de|1zh\.us|2joy\.de|2so\.be|3\.ly|5\.gp|6nc\.net|7li\.in|9\.bb|adf\.ly|adflav\.com|adfoc\.us|allanalpass\.com|alturl\.com|amy\.gs|any\.gs|apurl\.ru|aurl\.es|b23\.ru|baberepublic\.com|bat5\.com|bax\.li|beam\.to|bit\.ly|blu\.cc|c\.ly|capourl\.com|cc\.st|cd\.vg|cloneurl\.com|convertircodigo\.com|crypt-it\.com|crypt\.to|cryptlink\.ws|deb\.gs|digzip\.com|djurl\.com|dl-protect\.com|doiop\.com|ehe\.me|encript\.in|encurtador\.com|enlacs\.com|evg\.in|extreme-protect\.com|fa\.by|faja\.me|fapoff\.com|fdnlinks\.com|fea\.me|fff\.to|filedeck\.net|filemirrorupload\.com|fileupster\.com|flameupload\.com|freetexthost\.com|fwd4\.me|fyad\.org|goandgrab\.info|goblig\.com|goo\.gl|h-url\.in|hasurl\.co\.cc|hide-url\.net|hidemyass\.com|hides\.at|hideurl\.biz|ho\.io|hornywood\.tv|href\.hu|id2\.tryjav\.com|ilix\.in|ily\.me|ino\.me|interupload\.com|is\.gd|ivpaste\.com|j\.mp|je\.pl|jheberg\.com|just\.as|kickupload\.com|klnk\.de|knoffl\.com|kodo\.ameoto\.com|ks\.gs|latwy\.pl|link-go\.info|link-protector\.com|link-safe\.net|link4jo\.com|linkanonimo\.com|linkbabes\.com|linkbank\.eu|linkbee\.com|linkblur\.com|linkbucks\.com|linkcrypt\.com|linkcrypt\.ws|linkencrypter\.com|linkhide\.com\.ar|linkhide\.in|linkoculto\.net|linkok\.org|linkprivado\.com|linkprivate\.net|linkprotect\.in|links-protect\.com|links-protect\.info|links\.tc|linksafe\.me|linksaver\.info|linkse\.info|linkseguro\.com\.ar|linkseguro\.org|linksole\.com|linksprotegidos\.info|linkto\.net|linkweb\.dk|linkx\.in|linkzip\.net|listedfiles\.com|littleurl\.net|lixk\.me|ljv2\.com|ll11\.org|lnk\.cm|lnk\.co|longr\.us|lovelink\.in|mcaf\.ee|megaline\.co|megaupper\.com|mhz\.me|migre\.me|miniurls\.co|minu\.me|mir\.cr|mirrorcreator\.com|mo\.by|multi-uploadeur\.com|murl\.kz|musicalmente\.info|mypaqe\.com|mypl\.us|myrapidlinks\.com|myref\.de|myurl\.in|nbanews\.us|okconsolas\.com|oneddl\.canhaz\.it|ow\.ly|p4p\.com\.es|p6l\.org|paste\.frubar\.net|paste\.hotfile-bb\.com|paste\.ubuntu\.com|paste2\.org|paste21\.info|pastebin\.com|paylesssofts\.net|poontown\.net|pqueno\.com|priva\.us|protec-link\.com|protect-ddl\.com|protect-my-links\.com|protected\.socadvnet\.com|protectlinks\.com|protectlinks\.net|protectlk\.com|protege-mes-liens\.com|ptl\.li|qooy\.com|qqc\.co|qvvo\.com|rapidfolder\.com|rapidsafe\.de|rapidsafe\.org|rapidshare\.mu|realfiles\.net|redir\.ec|ref\.so|relinka\.net|rexwo\.com|rqq\.co|rs-layer\.com|rsmonkey\.com|s2l\.biz|saf\.li|safe\.mn|safelinking\.net|saferlinks\.com|sealed\.in|seclnk\.in|seriousfiles\.com|sharebee\.com|short-link\.fr|shortlink\.ca|shorturlscript\.net|simurl\.com|sinl\.es|skroc\.pl|slexy\.org|slnky\.net|smsdl\.com|sn\.im|sonofertas\.es|spedr\.com|spreadlink\.us|star-cyber\.com|subedlc\.com|subirfacil\.com|syl\.me|szort\.pl|takemyfile\.com|takemylinks\.com|textsnip\.com|thecow\.me|thesefiles\.com|tilien\.net|tiny\.cc|tiny\.lt|tinylinks\.co|tinypaste\.com|tinyurl\.com|tinyurlscript\.info|tmf\.myegy\.com|togoto\.us|tot\.to|tra\.kz|u\.to|uberpicz\.com|ulinks\.net|ultra-protect\.com|ultrafiles\.net|undeadlink\.com|uploadjockey\.com|uploadmirrors\.com|uploadonall\.com|upmirror\.com|upsafe\.org|ur\.ly|url-go\.com|url-site\.com|url4t\.com|urla\.in|urlbeat\.net|urlcash\.net|urlcrypt\.com|urlcut\.com|urlcut\.in|urldefender\.com|urln\.tk|urlpulse\.net|urlspy\.co\.cc|urwij|uselink\.info|uucc\.cc|uze\.in|wcrypt\.in|webtooljungle\.com|weepax\.com|whackyvidz\.com|x-ls\.ru|x\.co|xa\.ly|xc\.io|xr\.com|xtreemhost\.com|xurl\.cn|xxs\.ru|ysu\.me|yyv\.co|zff\.co|zio\.in|zpag\.es)/.*"
    __version__ = "0.21"
    __description__ = """linkdecrypter.com"""
    __author_name__ = ("zoidberg")

    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<p class="textog" style="color:red"><b>PASSWORD:</b></p>'
    CAPTCHA_PATTERN = r'<img style="cursor:crosshair;" src="([^"]+)" alt="Loading CAPTCHA...">'

    def decrypt(self, pyfile):
        self.html = self.load('http://linkdecrypter.com', post={
            "link_cache": "on",
            "links": self.pyfile.url,
            "modo_links": "text"
        })

        new_links = []
        captcha = ''
        passwords = self.getPassword().split()

        for i in range(5 + len(passwords)):
            self.logDebug("Trying to decrypt #" + str(i))
            self.html = self.load('http://linkdecrypter.com')

            textarea = re.search(self.TEXTAREA_PATTERN, self.html, flags=re.DOTALL)
            if textarea is not None:
                self.logDebug(textarea.group(1))
                new_links.extend(textarea.group(1).split())
                break
            elif re.search(self.PASSWORD_PATTERN, self.html):
                if len(passwords):
                    password = passwords.pop(0)
                    self.logInfo("Password protected link, trying " + password)
                    self.html = self.load('http://linkdecrypter.com', post={
                        "password": password
                    })
                else:
                    self.fail("No or incorrect password")
            else:
                found = re.search(self.CAPTCHA_PATTERN, self.html)
                if found is not None:
                    self.logInfo("Captcha protected link")
                    if captcha:
                        self.invalidCaptcha()
                    captcha = self.decryptCaptcha(url='http://linkdecrypter.com/' + found.group(1))
                    self.html = self.load('http://linkdecrypter.com', post={
                        "captcha": captcha
                    })
        else:
            self.fail('Max retries reached')

        if new_links:
            if captcha:
                self.correctCaptcha()
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')

        
