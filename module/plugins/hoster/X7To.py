# -*- coding: utf-8 -*-
import re

from module.plugins.Hoster import Hoster

from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []

    for url in urls:
        html = getURL(url)

        if "var page = '404';" in html:
            result.append((url, 0, 1, url))
            continue

        fileInfo = re.search(X7To.FILE_INFO_PATTERN, html)
        if fileInfo:
            name = fileInfo.group(1)
            units = float(fileInfo.group(2).replace(",", "."))
            pow = {'KB': 1, 'MB': 2, 'GB': 3}[fileInfo.group(3)]
            size = int(units * 1024 ** pow)
        else:
            # fallback: name could not be extracted.. most likely change on x7.to side ... needs to be checked then
            name = url
            size = 0

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
    
    FILE_INFO_PATTERN=r'<meta name="description" content="Download: (.*?) \(([0-9,.]+) (KB|MB|GB)\)'

    def init(self):
        if self.premium:
            self.multiDL = False
            self.resumeDownload = False
            self.chunkLimit = 1
        else:
            self.multiDL = False

        self.file_id = re.search(r"http://x7.to/([a-zA-Z0-9]+)", self.pyfile.url).group(1)
        self.logDebug("file id is %s" % self.file_id)
        self.pyfile.url = "http://x7.to/" + self.file_id

    def process(self, pyfile):
        self.html = self.load(self.pyfile.url, ref=False, decode=True)

        if "var page = '404';" in self.html:
            self.offline()

        fileInfo = re.search(self.FILE_INFO_PATTERN, self.html, re.IGNORECASE)
        size = 0
        trafficLeft = 100000000000
        if fileInfo:
            self.pyfile.name = fileInfo.group(1)
            if self.account:
                trafficLeft = self.account.getAccountInfo(self.user)["trafficleft"]
                units = float(fileInfo.group(2).replace(",", "."))
                pow = {'KB': 1, 'MB': 2, 'GB': 3}[fileInfo.group(3)]
                size = int(units * 1024 ** pow)
                self.logDebug("filesize: %s    trafficleft: %s" % (size, trafficLeft))
        else:
            self.logDebug("name and size not found")

        if self.account and self.premium and trafficLeft > size:
            self.handlePremium()
        else:
            self.handleFree()

    def handlePremium(self):
        # check if over limit first
        overLimit = re.search(r'<a onClick="cUser.buyTraffic\(\)" id="DL">', self.html)
        if overLimit:
            self.logDebug("over limit, falling back to free")
            self.handleFree()
        else:
            realurl = re.search(r'<a href="(http://stor.*?)" id="DL">', self.html)
            if realurl:
                realurl = realurl.group(1)
                self.logDebug("premium url found %s" % realurl)
            else:
                self.logDebug("premium link not found")
            self.download(realurl)

    def handleFree(self):
        # find file id
        file_id = re.search(r"var dlID = '(.*?)'", self.html)
        if not file_id:
	    self.fail("Free download id not found")
	
	file_url = "http://x7.to/james/ticket/dl/" + file_id.group(1)
	self.logDebug("download id %s" % file_id.group(1))

	self.html = self.load(file_url, ref=False, decode=True)

	# deal with errors
	if "limit-dl" in self.html:
	    self.logDebug("Limit reached ... waiting")
	    self.setWait(900,True)
	    self.wait()
	    self.retry()

	if "limit-parallel" in self.html:
	    self.fail("Cannot download in parallel")

	# no waiting required, go to download
	waitCheck = re.search(r"wait:(\d*),", self.html)
	if waitCheck:
	    waitCheck = int(waitCheck.group(1))
	    self.setWait(waitCheck)
	    self.wait()

	urlCheck = re.search(r"url:'(.*?)'", self.html)
	url = None
	if urlCheck:
	    url = urlCheck.group(1)
	    self.logDebug("free url found %s" % url)

	if url:
	    try:
		self.download(url)
	    except:
		self.logDebug("downloading url failed: %s" % url)
	else:
	    self.fail("Free download url found")