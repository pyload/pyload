
import re

from module.plugins.Crypter import Crypter

class WiiReloadedOrg(Crypter):
    __name__ = "WiiReloadedOrg"
    __type__ = "crypter"
    __pattern__ = r"http://www\.wii-reloaded\.org/protect/get\.php\?i=.+"
    __config__ = [("changeName", "bool", "Use Wii-Reloaded.org folder name", "True")]
    __version__ = "0.1"
    __description__ = """Wii-Reloaded.org Crypter Plugin"""
    __author_name__ = ("hzpz")
    __author_mail__ = ("none")
    
    
    def decrypt(self, pyfile):
        url = pyfile.url
        src = self.req.load(str(url))
        
        ids = re.findall(r"onClick=\"popup_dl\((.+)\)\"", src)
        if len(ids) == 0:
            self.fail("Unable to decrypt links, this plugin probably needs to be updated")
        
        packageName = self.pyfile.package().name
        if self.getConfig("changeName"):
            packageNameMatch = re.search(r"<div id=\"foldername\">(.+)</div>", src)
            if not packageNameMatch:
                self.logWarning("Unable to get folder name, this plugin probably needs to be updated")
            else:
                packageName = packageNameMatch.group(1)
                
        self.pyfile.package().password = "wii-reloaded.info"
        
        self.logDebug("Processing %d links" % len(ids))
        links = []
        for id in ids:
            self.req.lastURL = str(url)
            header = self.req.load("http://www.wii-reloaded.org/protect/hastesosiehtsaus.php?i=" + id, just_header=True)
            self.logDebug("Header:\n" + header)
            redirectLocationMatch = re.search(r"^Location: (.+)$", header, flags=re.MULTILINE)
            if not redirectLocationMatch:
                self.offline()
            redirectLocation = redirectLocationMatch.group(1)
            self.logDebug(len(redirectLocation))
            if not redirectLocation.startswith("http"):
                self.offline()
            self.logDebug("Decrypted link: %s" % redirectLocation)
            links.append(redirectLocation)
            
        self.logDebug("Decrypted %d links" % len(links))
        self.packages.append((packageName, links, packageName))