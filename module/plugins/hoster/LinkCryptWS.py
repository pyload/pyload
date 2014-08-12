# -*- coding: utf-8 -*-

#
# Debunging by Glukgluk
# links work now! 
# new priority cnl2>web>dlc
#
#

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
from module.unescape import unescape
from module.utils import html_unescape
import base64
import binascii
import re
import pycurl

class LinkCryptWS(Crypter):
    __name__ = "LinkCryptWS"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www.)?linkcrypt.ws/(?:dir|container)/(?P<id>\w+)"
    __version__ = "0.03"
    __description__ = """LinkCrypt.ws Crypter Plugin"""
    __author_name__ = ("kagenoshin,glukgluk")
    __author_mail__ = ("kagenoshin[AT]gmx[DOT]ch")

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"
    HOSTER_DOMAIN = "linkcrypt.ws"
        
    def setup(self):
        self.html = None
        self.fileid = None
        self.captcha = False
        self.package = None
        self.preferred_sources = ['cnl', 'web', 'dlc', 'rsdf', 'ccf', ] #['cnl', 'rsdf', 'ccf', 'dlc', 'web']
        
    def decrypt(self, pyfile):

        #check if we have js
        if not self.js:
            self.logDebug("no JS -> skip everything")
            self.fail('Could not extract any links please install JS')

        # Init
        package_found = None
        self.package = pyfile.package()
        self.fileid = re.match(self.__pattern__, pyfile.url).group('id')
        #self.req.cj.setCookie(self.HOSTER_DOMAIN, "Linksave_Language", "english")
        
        # Request package
        self.req.http.c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko") #better chance to not get those key-captchas
        self.html = self.load(self.pyfile.url)

        if not self.isOnline():
            self.offline()

        if(self.isKeyCaptchaProtected()):
            self.retry(4,30,"Can't handle Key-Captcha")
            
        if self.isCaptchaProtected():
            self.captcha = True
            self.unlockCaptchaProtection()
            self.handleCaptchaErrors()
            
	# Check for protection    
        if self.isPasswordProtected():
            self.unlockPasswordProtection()
            self.handleErrors()
            
        # get unrar password
        self.getunrarpw()

	# Get package name and folder
        (package_name, folder_name) = self.getPackageInfo()

        #get the container definitions from script section
        self.get_container_html()

        # Extract package links
        package_links = []
        
	for type_ in self.preferred_sources:
            links = self.handleLinkSource(type_)
            if(links):
                if(type(links) == type([])):
                    package_links.extend(links)
                    break
                else:
                    package_found = True
                    break

        package_links = set(package_links)

        # Pack
        if package_links:
            self.packages = [(package_name, package_links, folder_name)]
        elif package_found:
            self.core.api.deletePackages([self.package.id])
        else:
            self.fail('Could not extract any links')

    def isOnline(self):
        if "<title>Linkcrypt.ws // Error 404</title>" in self.html:
            self.logDebug("folder doesen't exist anymore")
            return False
        return True
    
    def isPasswordProtected(self):
        if ('Autorisierung' in self.html) or ('Authorizing' in self.html):
            self.logDebug("Links are password protected")
            return True
        
    def isCaptchaProtected(self):
        if 'id="captcha">' in self.html:
            self.logDebug("Links are captcha protected")
            return True
        return False

    def isKeyCaptchaProtected(self):
        if(re.search(r"(Key |Key-)", self.html, re.I)):
            return True
        return False
        
    def unlockPasswordProtection(self):
	password = self.getPassword()
        if password:
		self.logDebug("Submitting password [%s] for protected links" % password)
		post = {"password": password, 'x': '0', 'y': '0' }
		self.html = self.load(self.pyfile.url, post=post)
	else: 
		self.fail("Folder is password protected, please set password on 'Edit package' form and retry")
            
    def unlockCaptchaProtection(self):
        captcha_url = re.search(r'<form.*?id\s*?=\s*?"captcha"[^>]*?>.*?<\s*?input.*?src="([^"]*?)"', self.html, re.I | re.S).group(1)
        captcha_code = self.decryptCaptcha(captcha_url, forceUser=True, imgtype="gif", result_type='positional')
        self.html = self.load(self.pyfile.url, post={"x": captcha_code[0], "y": captcha_code[1]})   
        
    def getPackageInfo(self):
        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.logDebug("Defaulting to pyfile name [%s] and folder [%s] for package" % (name, folder))
        return name, folder
    
    def getunrarpw(self):
    	sitein = self.html
    	indexi = sitein.find("|source|")+8
    	indexe = sitein.find("|",indexi)
    	unrarpw = sitein[indexi:indexe]
	if not (unrarpw == "Password" or "Dateipasswort") :
	    self.logDebug("File password set to: [%s]"% unrarpw)
	    self.pyfile.package().password = unrarpw
    	
    def handleErrors(self):      
    	if ('Autorisierung' in self.html) or ('Authorizing' in self.html):            
    	    self.logDebug("Incorrect password, please set right password on 'Edit package' form and retry")
            self.fail("Incorrect password, please set right password on 'Edit package' form and retry")  
   
    def handleCaptchaErrors(self):
        if self.captcha:          
            if "Your choice was wrong!" in self.html:
                self.logDebug("Invalid captcha, retrying")
                self.invalidCaptcha()
                self.retry()
            else:
                self.correctCaptcha()
           
    def handleLinkSource(self, type_):
	if type_ == 'cnl':
            return self.handleCNL2()
        elif type_ == 'web':
            return self.handleWebLinks()
	elif type_ in ('rsdf', 'ccf', 'dlc'):
            return self.handleContainer(type_)
        else:
            self.fail('unknown source type "%s" (this is probably a bug)' % type_)

    def handleWebLinks(self):
        package_links = []
        self.logDebug("Search for Web links ")
        pattern = r'<form action="http://linkcrypt.ws/out.html"[^>]*?>.*?<input[^>]*?value="([^"]*?)"[^>]*?name="file"'
        ids = re.findall(pattern, self.html, re.I | re.S)
	self.logDebug("Decrypting %d Web links" % len(ids))
        for i, weblink_id in enumerate(ids):
            try:
                self.logDebug("Decrypting Web link %d, %s" % (i+1, weblink_id))
		#load page
                response = self.load("http://linkcrypt.ws/out.html", post = {'file':weblink_id})
                indexs = response.find("window.location =")+19
		indexe = response.find('"', indexs)
		link2= response[indexs:indexe]
		self.logDebug(link2)
                link2 = html_unescape(link2)
                package_links.append(link2)
            except Exception, detail:
                self.logDebug("Error decrypting Web link %s, %s" % (weblink_id, detail))    
        return package_links

    def get_container_html(self):
        self.container_html = []
        script = re.search(r'<div.*?id="ad_cont".*?<script.*?javascrip[^>]*?>(.*?)</script', self.html, re.I | re.S)
        if not script:
            return None

        container_html_text = script.group(1)
        container_html_text.strip()
        self.container_html = container_html_text.splitlines()
    
    def handle_javascript(self, line):
	jseval = self.js.eval(line.replace('{}))',"{}).replace('document.open();document.write','').replace(';document.close();',''))"))
	return jseval

    def handleContainer(self, type_):
        package_links = []
        type_ = type_.lower()
        self.logDebug('Search for %s Container links' % type_.upper())
        if not type_.isalnum():  # check to prevent broken re-pattern (cnl2,rsdf,ccf,dlc,web are all alpha-numeric)
            self.fail('unknown container type "%s" (this is probably a bug)' % type_)
        for line in self.container_html:
            if(type_ in line):
                jseval = self.handle_javascript(line)
		clink = re.search(r'href=["\']([^"\']*?)["\']',jseval,re.I)
                if clink:
                    self.logDebug("clink avaible")
                    (package_name, folder_name) = self.getPackageInfo()
                    self.logDebug("Added package with name %s.%s and container link %s" %( package_name, type_, clink.group(1)))
                    self.core.api.uploadContainer( "%s.%s" %(package_name, type_), self.load(clink.group(1)))
                    return "Found it"
      
        return package_links

    def handleCNL2(self):
        package_links = []
        self.logDebug("Search for CNL links")
	cnl_line = None
        for line in self.container_html:
            if("cnl" in line):
                cnl_line = line
                break

        if cnl_line:
            self.logDebug("cnl_line gefunden")
	    try:
                cnl_section = self.handle_javascript(cnl_line)
                (vcrypted, vjk) = self._getCipherParams(cnl_section)
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._getLinks(crypted, jk))
            except: 
                self.logError("Unable to decrypt CNL links (JS Error) try to get over links")
                return self.handleWebLinks()
        return package_links
    
    def _getCipherParams(self, cnl_section):
            
        # Get jk
        jk_re = r'<INPUT.*?NAME="%s".*?VALUE="(.*?)"' % LinkCryptWS._JK_KEY_       
        vjk = re.findall(jk_re, cnl_section)
        
        # Get crypted
        crypted_re = r'<INPUT.*?NAME="%s".*?VALUE="(.*?)"' % LinkCryptWS._CRYPTED_KEY_       
        vcrypted = re.findall(crypted_re, cnl_section)

        # Log and return
        self.logDebug("Detected %d crypted blocks" % len(vcrypted))
        return vcrypted, vjk

    def _getLinks(self, crypted, jk):

        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.logDebug("JsEngine returns value [%s]" % jreturn)
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
        self.logDebug("Package has %d links" % len(links))

        return links

