# -*- coding: utf-8 -*-
import re

from module.plugins.Hoster import Hoster

from module.network.RequestFactory import getURL

def getInfo(urls):
    yield [(url, 0, 1, url) for url in urls]


class X7To(Hoster):
    __name__ = "X7To"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?x7.to/"
    __version__ = "0.2"
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
        self.fail("Hoster not longer available")

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
