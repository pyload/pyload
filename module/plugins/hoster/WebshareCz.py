# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class WebshareCz(SimpleHoster):
    __name__    = "WebshareCz"
    __type__    = "hoster"
    __version__ = "0.14"

    __pattern__ = r'https?://(?:www\.)?webshare\.cz/(?:#/)?file/(?P<ID>\w+)'

    __description__ = """WebShare.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("rush", "radek.senfeld@gmail.com")]


    def process(self, pyfile):
        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()


    def handleDownload(self, wst=None):
        fid = re.match(self.__pattern__, self.pyfile.url).group("ID")
        api_data = getURL('https://webshare.cz/api/file_link/',
                          post={'ident': fid, 'wst': wst},
                          decode=True)

        self.logDebug("API data: " + api_data)

        m = re.search('<link>(.+)</link>', api_data)
        if m is None:
            self.error(_("Unable to detect direct link"))

        self.download(m.group(1), disposition=True)


    def handleFree(self):
        self.handleDownload()


    def handlePremium(self):
        self.handleDownload(wst=self.account.wst)


    @classmethod                                                                                                                                                                
    def getInfo(cls, url="", html=""):
        info = SimpleHoster.getInfo(url, html)

	if url:
	    info["pattern"] = re.match(cls.__pattern__, url).groupdict()

            api_data = getURL('https://webshare.cz/api/file_info/',
                              post={'ident': info["pattern"]["ID"]},
                              decode=True)

            if 'File not found' in api_data:
                info["status"] = 1
            else:
                info["status"] = 2
                info["fileid"] = info["pattern"]["ID"]
                info["name"] = re.search('<name>(.+)</name>', api_data).group(1)
                info["size"] = re.search('<size>(.+)</size>', api_data).group(1)
	    
	return info


getInfo = create_getInfo(WebshareCz)
