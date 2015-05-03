# -*- coding: utf-8 -*-

from HTMLParser import HTMLParser

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo

class HTMLTDLinkGrabbber(HTMLParser):
    td_count = 0
    links = []


    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.td_count += 1

        elif tag == "a" and self.td_count > 0:
            for attr in attrs:
                if attr[0] == "href":
                    self.links.append(attr[1])
                    break


    def handle_endtag(self, tag):
        if tag == "td":
            self.td_count -= 1


    def getLinks(self, html):
        self.links = []
        try:
            self.feed(html)
        except Exception, e:
            self.logError(_("Error parsing HTML: %s") % e.message)

        return self.links




class XFSCrypter(SimpleCrypter):
    __name__    = "XFSCrypter"
    __type__    = "crypter"
    __version__ = "0.08"

    __pattern__ = r'^unmatchable$'

    __description__ = """XFileSharing decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = None

    URL_REPLACEMENTS = [(r'&?per_page=\d+', ""), (r'[?/&]+$', ""), (r'(.+/[^?]+)$', r'\1?'), (r'$', r'&per_page=10000')]

    OFFLINE_PATTERN      = r'>\s*\w+ (Not Found|file (was|has been) removed)'
    TEMP_OFFLINE_PATTERN = r'>\s*\w+ server (is in )?(maintenance|maintainance)'


    def prepare(self):
        if not self.HOSTER_DOMAIN:
            if self.account:
                account      = self.account
            else:
                account_name = (self.__name__ + ".py").replace("Folder.py", "").replace(".py", "")
                account      = self.pyfile.m.core.accountManager.getAccountPlugin(account_name)

            if account and hasattr(account, "HOSTER_DOMAIN") and account.HOSTER_DOMAIN:
                self.HOSTER_DOMAIN = account.HOSTER_DOMAIN
            else:
                self.fail(_("Missing HOSTER_DOMAIN"))

        if isinstance(self.COOKIES, list):
            self.COOKIES.insert((self.HOSTER_DOMAIN, "lang", "english"))

        return super(XFSCrypter, self).prepare()


    def getLinks(self):
        parser = HTMLTDLinkGrabbber()
        return parser.getLinks(self.html)
