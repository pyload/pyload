# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
from module.plugins.ReCaptcha import ReCaptcha
import base64
import binascii
import re


class ShareLinksBiz(Crypter):
    __name__ = "ShareLinksBiz"
    __type__ = "crypter"
    __pattern__ = r"(http://[\w\.]*?share-links\.biz)/(?P<id>_[0-9a-z]+)(/.*)?"
    __version__ = "1.0"
    __description__ = """Share-Links.biz Crypter"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")
    
    
    def setup(self):
        self.html = None
        self.baseUrl = None
        self.fileId = None
        self.captcha = False
        self.package = None

    def decrypt(self, pyfile):

        # Init
        self.package = pyfile.package()
        self.baseUrl = re.search(self.__pattern__, pyfile.url).group(1)
        self.fileId = re.match(self.__pattern__, pyfile.url).group('id')
        
        # Request package
        url = self.baseUrl + '/' + self.fileId
        self.html = self.load(url)
        
        # Unblock server (load all images)
        self.unblockServer()
           
        # Check for protection    
        if self.isPasswordProtected():
            self.unlockPasswordProtection()
            self.handleErrors()
            
        if self.isCaptchaProtected():
            self.captcha = True
            self.unlockCaptchaProtection()
            self.handleErrors()
            
        # Extract package links
        package_links = []
        package_links.extend(self.handleWebLinks())
        package_links.extend(self.handleContainers())
        package_links.extend(self.handleCNL2())
        package_links = set(package_links)
        
        # Get package info 
        package_name, package_folder = self.getPackageInfo()

        # Pack
        self.packages = [(package_name, package_links, package_folder)]

    def isOnline(self):
        if "No usable content was found" in self.html:
            self.log.debug("%s: File not found" % self.__name__)
            return False
        return True
    
    def isPasswordProtected(self):
        if re.search(r'''<form.*?id="passwordForm".*?>''', self.html):
            self.log.debug("%s: Links are protected" % self.__name__)
            return True
        return False
    
    def isCaptchaProtected(self):
        if '<map id="captchamap"' in self.html:
            self.log.debug("%s: Links are captcha protected" % self.__name__)
            return True
        return False
    
    def unblockServer(self):
        imgs = re.findall("(/template/images/.*?\.gif)", self.html)
        for img in imgs:
            self.load(self.baseUrl + img)
    
    def unlockPasswordProtection(self):
        password = self.getPassword()
        self.log.debug("%s: Submitting password [%s] for protected links" % (self.__name__, password))
        post = {"password": self.package.password, 'login': 'Submit form'}
        url = self.baseUrl + '/' + self.fileId
        self.html = self.load(url, post=post)

    def unlockCaptchaProtection(self):
        # Get captcha map
        captchaMap = self._getCaptchaMap()
        self.log.debug("%s: Captcha map with [%d] positions" % (self.__name__, len(captchaMap.keys())))

        # Request user for captcha coords
        m = re.search(r'<img src="/captcha.gif\?d=(.*?)&amp;PHPSESSID=(.*?)&amp;legend=1"', self.html)
        captchaUrl = self.baseUrl + '/captcha.gif?d=%s&PHPSESSID=%s' % (m.group(1), m.group(2))
        self.log.debug("%s: Waiting user for correct position" % self.__name__)
        coords = self.decryptCaptcha(captchaUrl, forceUser=True, imgtype="gif", result_type='positional')
        self.log.debug("%s: Captcha resolved, coords [%s]" % (self.__name__, str(coords)))
    
        # Resolve captcha
        href = self._resolveCoords(coords, captchaMap)
        if href is None:
            self.log.debug("%s: Invalid captcha resolving, retrying" % self.__name__)
            self.invalidCaptcha()
            self.setWait(5, False)
            self.wait()
            self.retry()
        url = self.baseUrl + href
        self.html = self.load(url)
        
    def _getCaptchaMap(self):
        map = {}
        for m in re.finditer(r'<area shape="rect" coords="(.*?)" href="(.*?)"', self.html):
            rect = eval('(' + m.group(1) + ')')
            href = m.group(2)
            map[rect] = href
        return map

    def _resolveCoords(self, coords, captchaMap):
        x, y = coords
        for rect, href in captchaMap.items():
            x1, y1, x2, y2 = rect
            if (x>=x1 and x<=x2) and (y>=y1 and y<=y2):
                return href

    def handleErrors(self):
        if "The inserted password was wrong" in self.html:
            self.log.debug("%s: Incorrect password, please set right password on 'Edit package' form and retry" % self.__name__)
            self.fail("Incorrect password, please set right password on 'Edit package' form and retry")  

        if self.captcha:
            if "Your choice was wrong" in self.html:
                self.log.debug("%s: Invalid captcha, retrying" % self.__name__)
                self.invalidCaptcha()
                self.setWait(5)
                self.wait()
                self.retry()
            else:
                self.correctCaptcha() 

    def getPackageInfo(self):
        title_re = r'<h2><img.*?/>(.*)</h2>'
        m = re.search(title_re, self.html, re.DOTALL)
        if m is not None:
            title = m.group(1).strip()
            name = folder = title
            self.log.debug("%s: Found name [%s] and folder [%s] in package info" % (self.__name__, name, folder))
        else:
            name = self.package.name
            folder = self.package.folder
            self.log.debug("%s: Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (self.__name__, name, folder))
        return name, folder 
    
    def handleWebLinks(self):
        package_links = []
        self.log.debug("%s: Handling Web links" % self.__name__)
        
        #@TODO: Gather paginated web links  
        pattern = r"javascript:_get\('(.*?)', \d+, ''\)"
        ids = re.findall(pattern, self.html)
        self.log.debug("%s: Decrypting %d Web links" % (self.__name__, len(ids)))
        for i, id in enumerate(ids):
            try:
                self.log.debug("%s: Decrypting Web link %d, [%s]" % (self.__name__, i+1, id))
                dwLink = self.baseUrl + "/get/lnk/" + id
                response = self.load(dwLink)
                code = re.search(r'frm/(\d+)', response).group(1)
                fwLink = self.baseUrl + "/get/frm/" + code
                response = self.load(fwLink)
                jscode = re.search(r'<script language="javascript">\s*eval\((.*)\)\s*</script>', response, re.DOTALL).group(1)
                jscode = self.js.eval("f = %s" % jscode)
                jslauncher = "window=''; parent={frames:{Main:{location:{href:''}}},location:''}; %s; parent.frames.Main.location.href" 
                dlLink = self.js.eval(jslauncher % jscode)
                self.log.debug("%s: JsEngine returns value [%s] for redirection link"  % (self.__name__, dlLink))
                package_links.append(dlLink)
            except Exception, detail:
                self.log.debug("%s: Error decrypting Web link [%s], %s" % (self.__name__, id, detail))    
        return package_links
    
    def handleContainers(self):
        package_links = []
        self.log.debug("%s: Handling Container links" % self.__name__)
        
        pattern = r"javascript:_get\('(.*?)', 0, '(rsdf|ccf|dlc)'\)"
        containersLinks = re.findall(pattern, self.html)
        self.log.debug("%s: Decrypting %d Container links" % (self.__name__, len(containersLinks)))
        for containerLink in containersLinks:
            link = "%s/get/%s/%s" % (self.baseUrl, containerLink[1], containerLink[0]) 
            package_links.append(link)
        return package_links
    
    def handleCNL2(self):
        package_links = []
        self.log.debug("%s: Handling CNL2 links" % self.__name__)

        if '/lib/cnl2/ClicknLoad.swf' in self.html:
            try:
                (crypted, jk) = self._getCipherParams()
                package_links.extend(self._getLinks(crypted, jk))
            except:
                self.fail("Unable to decrypt CNL2 links")            
        return package_links
    
    def _getCipherParams(self):
        
        # Request CNL2
        code = re.search(r'ClicknLoad.swf\?code=(.*?)"', self.html).group(1)
        url = "%s/get/cnl2/%s" % (self.baseUrl, code)
        response = self.load(url)
        params = response.split(";;")
        
        # Get jk
        strlist = list(base64.standard_b64decode(params[1]))
        strlist.reverse()
        jk = ''.join(strlist)

        # Get crypted
        strlist = list(base64.standard_b64decode(params[2]))
        strlist.reverse()
        crypted = ''.join(strlist)

        # Log and return
        return crypted, jk

    def _getLinks(self, crypted, jk):
        
        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.log.debug("%s: JsEngine returns value [%s]" % (self.__name__, jreturn))
        key = binascii.unhexlify(jreturn)

        # Decode crypted
        crypted = base64.standard_b64decode(crypted)

        # Decrypt
        Key = key
        IV = key
        obj = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted)

        # Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = text.split("\n")
        links = filter(lambda x: x != "", links)

        # Log and return
        self.log.debug("%s: Block has %d links" % (self.__name__, len(links)))
        return links