
import re
import urllib

from module.plugins.Hoster import Hoster

class EasyNews(Hoster):
    __name__ = "EasyNews"
    __version__ = "0.1"
    __pattern__ = r".*easynews.com/dl/*"
    __config__ = [] # ("user" "seb"), ("pass" "boing")]

    def process(self, pyfile):
        url = pyfile.url

        if self.account:
            allAccounts = self.account.getAllAccounts()
            if allAccounts: 
                firstAccount = [0]
                username = firstAccount['login']
                password = firstAccount['password']
                url = pyfile.url
                for prefix in ["http://", "https://"]:
                    url = url.replace(prefix, prefix + username + ":" + password + "@");
            
        self.download(url)
