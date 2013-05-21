
import re
import urllib

from module.plugins.Hoster import Hoster

class EasyNews(Hoster):
    __name__ = "EasyNews"
    __version__ = "0.1"
    __pattern__ = r".*easynews.com/dl/*"
    __config__ = [] # ("user" "seb"), ("pass" "boing")]

    def process(self, pyfile):

        firstAccount = self.account.getAllAccounts()[0]
        username = firstAccount['login']
        password = firstAccount['password']
        url = pyfile.url
        for prefix in ["http://", "https://"]:
            url = url.replace(prefix, prefix + username + ":" + password + "@");

        open("/home/seb/tmp/test.txt", "w").write(url)
            
        self.download(url)
