
import re
import urllib

from module.plugins.Crypter import Crypter
from module.lib.BeautifulSoup import BeautifulSoup

class ILoadTo(Crypter):
    __name__ = "ILoadTo"
    __type__ = "crypter"
    __pattern__ = r"http://iload\.to/go/\d+-[\w\.-]+/"
    __config__ = []
    __version__ = "0.1"
    __description__ = """iload.to Crypter Plugin"""
    __author_name__ = ("hzpz")
    __author_mail__ = ("none")
    
    
    def decrypt(self, pyfile):
        url = pyfile.url
        src = self.req.load(str(url))
        soup = BeautifulSoup(src)

        # find captcha URL and decrypt            
        captchaTag = soup.find("img", attrs={"id": "Captcha"})
        if not captchaTag:
            self.fail("Cannot find Captcha")

        captchaUrl = "http://iload.to" + captchaTag["src"]
        self.logDebug("Captcha URL: %s" % captchaUrl)
        result = self.decryptCaptcha(str(captchaUrl))

        # find captcha form URL 
        formTag = soup.find("form", attrs={"id": "CaptchaForm"})
        formUrl = "http://iload.to" + formTag["action"]
        self.logDebug("Form URL: %s" % formUrl)
        
        # submit decrypted captcha
        self.req.lastURL = url
        src = self.req.load(str(formUrl), post={'captcha': result})
        
        # find decrypted links
        links = re.findall(r"<a href=\"(.+)\" style=\"text-align:center;font-weight:bold;\" class=\"button\" target=\"_blank\" onclick=\"this.className\+=' success';\">", src)
        
        if not len(links) > 0:
            self.retry()
        
        self.correctCaptcha()
        
        cleanedLinks = []
        for link in links:
            if link.startswith("http://dontknow.me/at/?"):
                cleanedLink = urllib.unquote(link[23:])
            else:
                cleanedLink = link
            self.logDebug("Link: %s" % cleanedLink)
            cleanedLinks.append(cleanedLink)
        
        self.logDebug("Decrypted %d links" % len(links))
        
        self.pyfile.package().password = "iload.to"
        self.packages.append((self.pyfile.package().name, cleanedLinks, self.pyfile.package().folder))