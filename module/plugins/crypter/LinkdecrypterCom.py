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
    #excluded: "1kh\.de|crypt-it\.com|linksave\.in|lix\.in|lof\.cc|multiload\.cz|multiupload\.com|ncrypt\.in|relink\.us|rs-layer\.com|secured\.in|stealth\.to"  
    __pattern__ = r"http://(\w*\.)?(00\.uz|10001mb\.com|123link\.it|123url\.org|1cl\.in|1tool\.biz|1zh\.us|2joy\.de|2so\.be|3\.ly|5\.gp|6nc\.net|7li\.in|9\.bb|adf\.ly|adflav\.com|adfoc\.us|allanalpass\.com|alturl\.com|amy\.gs|any\.gs|apurl\.ru|aurl\.es|b23\.ru|baberepublic\.com|bai\.lu|bat5\.com|bax\.li|bc\.vc|beam\.to|birurl\.com|bit\.ly|blu\.cc|bofh\.us|boo\.io|c\.ly|capourl\.com|cash4links\.co|cc\.st|cd\.vg|cl\.lk|cli\.gs|cloneurl\.com|convertircodigo\.com|crypt\.to|crypt2\.be|cryptlink\.ws|ddl-warez\.in|deb\.gs|deurl\.me|digzip\.com|djurl\.com|dl-protect\.com|dl\.dropbox\.com|doiop\.com|ehe\.me|embedupload\.com|encript\.in|encurtador\.com|enlacs\.com|evg\.in|extreme-protect\.com|fa\.by|faja\.me|fapoff\.com|fdnlinks\.com|fea\.me|fff\.to|filedeck\.net|filemirrorupload\.com|filesonthe\.net|fileupster\.com|flameupload\.com|freetexthost\.com|fwd4\.me|fyad\.org|galleries\.bz|goandgrab\.info|goblig\.com|goo\.gl|guardlink\.org|h-url\.in|hasurl\.co\.cc|hide-url\.net|hidemyass\.com|hides\.at|hideurl\.biz|ho\.io|hornywood\.tv|href\.hu|id2\.tryjav\.com|ilii\.in|ilix\.in|ily\.me|ino\.me|interupload\.com|is\.gd|ivpaste\.com|j\.mp|j7\.se|je\.pl|jheberg\.com|just\.as|kickupload\.com|klnk\.de|knoffl\.com|kodo\.ameoto\.com|ks\.gs|latwy\.pl|li\.co\.ve|link-go\.info|link-protector\.com|link-safe\.net|link\.file-up\.ru|link4jo\.com|linkanonimo\.com|linkbabes\.com|linkbank\.eu|linkbee\.com|linkblur\.com|linkbucks\.com|linkbun\.ch|linkcrypt\.com|linkcrypt\.ws|linkencrypter\.com|linkhide\.com\.ar|linkhide\.in|linkoculto\.net|linkok\.org|linkprivado\.com|linkprivate\.net|linkprotect\.in|links-protect\.com|links-protect\.info|links-protection\.com|links\.tc|linksafe\.me|linksaver\.info|linkse\.info|linkseguro\.com\.ar|linkseguro\.org|linksole\.com|linksprotec\.com|linksprotegidos\.info|linkssafe\.com|linkto\.net|linkweb\.dk|linkx\.in|linkzip\.net|listedfiles\.com|littleurl\.net|lixk\.me|lixxin\.com|ljv2\.com|lkt\.es|ll11\.org|lnk\.cm|lnk\.co|longr\.us|lovelink\.in|madlink\.sk|maxi-upload\.com|mcaf\.ee|mediahide\.com|megaline\.co|megalinks\.es|megaupper\.com|mf1\.jp|mhz\.me|migre\.me|miniurl\.com|miniurl\.es|miniurl\.org|miniurls\.co|minu\.me|mir\.cr|mirrorcreator\.com|mo\.by|multi-uploadeur\.com|murl\.kz|musicalmente\.info|myooo\.info|mypaqe\.com|mypl\.us|myrapidlinks\.com|myref\.de|myurl\.in|nbanews\.us|nov\.io|okconsolas\.com|oneddl\.canhaz\.it|ow\.ly|p4p\.com\.es|p6l\.org|paste\.frubar\.net|paste\.hotfile-bb\.com|paste\.to|paste\.ubuntu\.com|paste2\.org|paste21\.info|pastebin\.com|paylesssofts\.net|poontown\.net|pqueno\.com|priva\.us|protec-link\.com|protect-ddl\.com|protect-my-links\.com|protected\.socadvnet\.com|protectlinks\.com|protectlinks\.net|protectlk\.com|protege-mes-liens\.com|ptl\.li|qooy\.com|qqc\.co|qvvo\.com|rapidfolder\.com|rapidsafe\.de|rapidsafe\.org|rapidshare\.mu|realfiles\.net|redir\.ec|ref\.so|relinka\.net|rexwo\.com|rqq\.co|rsmonkey\.com|rurls\.ru|s2l\.biz|saf\.li|safe\.mn|safelinking\.net|saferlinks\.com|scut\.ly|sealed\.in|seclnk\.in|seriousfiles\.com|share-links\.biz|sharebee\.com|short-link\.fr|shortlink\.ca|shorturlscript\.net|shrt\.st|simurl\.com|sinl\.es|skroc\.pl|slexy\.org|slnky\.net|smlk\.es|smsdl\.com|sn\.im|snipr\.com|snipurl\.com|snurl\.com|sonofertas\.es|spedr\.com|spreadlink\.us|star-cyber\.com|stu\.tc|subedlc\.com|subirfacil\.com|syl\.me|szort\.pl|t\.co|t7\.hu|takemyfile\.com|takemylinks\.com|textsave\.de|textsnip\.com|thecow\.me|thesefiles\.com|thinfi\.com|tilien\.net|tiny\.cc|tiny\.lt|tinylinks\.co|tinypaste\.com|tinyurl\.com|tinyurlscript\.info|tmf\.myegy\.com|togoto\.us|tot\.to|tra\.kz|trick\.ly|u\.to|uberpicz\.com|ubervidz\.com|ulinks\.net|ultrafiles\.net|undeadlink\.com|uploadjockey\.com|uploadmirrors\.com|uploadonall\.com|upmirror\.com|upsafe\.org|ur\.ly|url-go\.com|url-site\.com|url\.zeta24\.com|url4t\.com|urla\.in|urlbeat\.net|urlcash\.net|urlcorta\.es|urlcrypt\.com|urlcut\.com|urlcut\.in|urldefender\.com|urlink\.at|urln\.tk|urlpulse\.net|urlspy\.co\.cc|urwij|uselink\.info|uucc\.cc|uze\.in|wa9\.la|wcrypt\.in|webtooljungle\.com|weepax\.com|whackyvidz\.com|wtc\.la|x-ls\.ru|x\.co|xa\.ly|xc\.io|xr\.com|xtreemhost\.com|xurl\.cn|xurl\.es|xxs\.ru|youfap\.me|ysu\.me|yvy\.me|yyv\.co|zff\.co|zio\.in|zpag\.es)/.*"
    __version__ = "0.23"
    __description__ = """linkdecrypter.com"""
    __author_name__ = ("zoidberg", "flowlee")
    
    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<p class="textog" style="color:red"><b>PASSWORD:</b></p>'
    CAPTCHA_PATTERN = r'<img style="cursor:crosshair;" src="([^"]+)" alt="Loading CAPTCHA...">'
    REDIR_PATTERN = r'<i>(Click <a href="./">here</a> if your browser does not redirect you).</i>'
    
    def decrypt(self, pyfile):

        self.passwords = self.getPassword().splitlines()
        
        new_links = self.decryptAPI() or self.decryptHTML()                
        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')    

    def decryptAPI(self):
            
        get_dict = { "t": "link", "url": self.pyfile.url, "lcache": "1" } 
        self.html = self.load('http://linkdecrypter.com/api', get = get_dict)
        if self.html.startswith('http://'): return self.html.splitlines()
        
        if self.html == 'INTERRUPTION(PASSWORD)':
            for get_dict['pass'] in self.passwords:
                self.html = self.load('http://linkdecrypter.com/api', get= get_dict)
                if self.html.startswith('http://'): return self.html.splitlines()                                                
        
        self.logError('API', self.html)
        if self.html == 'INTERRUPTION(PASSWORD)':
            self.fail("No or incorrect password")
        
        return None                   
            
    def decryptHTML(self):
        
        self.html = self.load('http://linkdecrypter.com', cookies = True)        
        links_sessid = "links" + self.req.cj.getCookie("PHPSESSID")
        retries = 5
        
        post_dict = { "link_cache": "on", links_sessid: self.pyfile.url, "modo_links": "text" }                                              
        self.html = self.load('http://linkdecrypter.com', post = post_dict, cookies = True)
        
        while self.passwords or retries:                                    
            found = re.search(self.TEXTAREA_PATTERN, self.html, flags=re.DOTALL)                    
            if found: return found.group(1).splitlines()
                                             
            found = re.search(self.CAPTCHA_PATTERN, self.html)
            if found:
                self.logInfo("Captcha protected link")
                captcha = self.decryptCaptcha(url='http://linkdecrypter.com/' + found.group(1))
                self.html = self.load('http://linkdecrypter.com', post={ "captcha": captcha })
                retries -= 1
                
            elif self.PASSWORD_PATTERN in self.html:
                if self.passwords:
                    password = self.passwords.pop(0)
                    self.logInfo("Password protected link, trying " + password)
                    self.html = self.load('http://linkdecrypter.com', post= {'password': password})
                else:
                    self.fail("No or incorrect password")
            
            else:
                retries -= 1            
                self.html = self.load('http://linkdecrypter.com', cookies = True)
        
        return None                           