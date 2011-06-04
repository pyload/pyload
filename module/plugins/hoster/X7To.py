# -*- coding: utf-8 -*-
from __future__ import with_statement

import re

from module.plugins.Hoster import Hoster

from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        #print "X7To: getinfo for "+url
        # Get html
        html = getURL(url)

        if re.search(r"var page = '404';", html):
            #print "x7html: 404"
            result.append((url, 0, 1, url))
            continue

        # Name
        fileInfo = re.search('<meta name="description" content="Download: (.*) ([0-9,.]*) (KB|MB|GB) at ', html)
        if fileInfo:
            name = fileInfo.group(1)
            #print "X7To: filename "+name
            # Size
            units = float(fileInfo.group(1).replace(",", "."))
            pow = {'KB': 1, 'MB': 2, 'GB': 3}[fileInfo.group(2)]
            size = int(units * 1024 ** pow)
        else:
            # fallback: name could not be extracted.. most likely change on x7.to side ... needs to be checked then
            #print "X7To: file information not found"
            name = url
            size = 0

        # Return info
        result.append((name, size, 2, url))

    yield result


class X7To(Hoster):
    __name__ = "X7To"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?x7.to/"
    __version__ = "0.1"
    __description__ = """X7.To File Download Hoster"""
    __author_name__ = ("ernieb")
    __author_mail__ = ("ernieb")

    def setup(self):
        if self.premium:
            self.multiDL = False
            self.resumeDownload = False
            self.chunkLimit = 1
        else:
            self.multiDL = False

        self.file_id = re.search(r"http://x7.to/([a-zA-Z0-9]+)", self.pyfile.url).group(1)
        self.pyfile.url = "http://x7.to/" + self.file_id

    def process(self, pyfile):
        self.html = self.load(self.pyfile.url, ref=False, decode=True)

        if re.search(r"var page = '404';", self.html) is not None:
            self.offline()

        fileInfo = re.search(r'<meta name="description" content="Download: (.*) \(([0-9,.]*) (KB|MB|GB)\) at ',
                             self.html, re.IGNORECASE)
        size = 0
        trafficLeft = 100000000000
        if fileInfo:
            self.pyfile.name = fileInfo.group(1)
            if self.account:
                trafficLeft = self.account.getAccountInfo(self.user)["trafficleft"]
                # Size
                units = float(fileInfo.group(2).replace(",", "."))
                pow = {'KB': 1, 'MB': 2, 'GB': 3}[fileInfo.group(3)]
                size = int(units * 1024 ** pow)
                self.logDebug("filesize: %s    trafficleft: %s" % (size, trafficLeft))

        else:
            #self.log.debug( self.html )
            self.logDebug("name and size not found")

        if self.account and self.premium and trafficLeft > size:
            self.handlePremium()
        else:
            self.handleFree()

    def handlePremium(self):
        # check if over limit first
        overLimit = re.search(r'<a onClick="cUser.buyTraffic\(\)" id="DL">', self.html)
        if overLimit:
            self.logDebug("over limit")
        else:
            realurl = re.search(r'<a href="http://stor(\d*).x7.to/dl/([^"]*)" id="DL">', self.html)
            if realurl:
                realurl = 'http://stor' + realurl.group(1) + '.x7.to/dl/' + realurl.group(2)
            else:
                self.logDebug("premium link not found")
            self.download(realurl)

    def handleFree(self):
        # find file id
        file_id = re.search(r"var dlID = '([^']*)'", self.html)
        if file_id:
            file_url = "http://x7.to/james/ticket/dl/" + file_id.group(1)
            #getDownloadXml = getURL(file_url)
            self.html = self.load(file_url, ref=False, decode=True)

            # find download limit in xml
            haveToWait = re.search("limit-dl", self.html)
            if haveToWait:
                self.logDebug("Limit reached ... waiting")
                self.setWait(900)
                self.wait()
                return True

            # no waiting required, go to download
            waitCheck = re.search(r"wait:(\d*),", self.html)
            if waitCheck:
                waitCheck = int(waitCheck.group(1))
                self.setWait(waitCheck, True)
                self.wait()

            urlCheck = re.search(r"url:'(.*)',", self.html)
            url = None
            if urlCheck:
                url = urlCheck.group(1)
                self.logDebug("url found " + url)

            if url:
                try:
                    self.download(url)
                except:
                    self.logDebug("downloading url failed:" + url)


            else:
                #print self.html
                self.fail("no download url found")