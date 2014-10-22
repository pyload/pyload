# -*- coding: utf-8 -*-

import re
from time import time
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileSharkPl(SimpleHoster):
    __name__ = "FileSharkPl"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?fileshark\.pl/pobierz/\d{6}/\w{5}/?(.*)"
    __version__ = "0.01"
    __description__ = """FileShark.pl hoster plugin"""
    __authors__ = [("prOq", None)]


    FILE_NAME_PATTERN = r'<h2 class="name-file">(?P<N>.+)</h2>'
    FILE_SIZE_PATTERN = r'<p class="size-file">(.*?)<strong>(?P<S>\d+\.?\d*)\s(?P<U>\w+)</strong></p>'

    FILE_OFFLINE_PATTERN = '(P|p)lik zosta. (usuni.ty|przeniesiony)'
    DOWNLOAD_ALERT = r'<p class="lead text-center alert alert-warning">(.*?)</p>'
    IP_BLOCKED_PATTERN = 'Strona jest dost.pna wy..cznie dla u.ytkownik.w znajduj.cych si. na terenie Polski'
    DOWNLOAD_SLOTS_ERROR_PATTERN = r'Osi.gni.to maksymaln. liczb. .ci.ganych jednocze.nie plik.w\.'

    DOWNLOAD_URL_FREE = r'<a href="(.*?)" class="btn-upload-free">'
    DOWNLOAD_URL_PREMIUM = r'<a href="(.*?)" class="btn-upload-premium">'
    SECONDS_PATTERN = r'var timeToDownload = (\d+);'
    CAPTCHA_IMG_PATTERN = '<img src="data:image/jpeg;base64,(.*?)" title="captcha"'
    CAPTCHA_TOKEN_PATTERN = r'name="form\[_token\]" value="(.*?)" />'


    def setup(self):
        self.resumeDownload = True
	self.multiDL = self.premium
	self.limitDL = 1


    def process(self, pyfile):
	self.html = self.load(pyfile.url, ref=False, decode=True)

	# check if file is now available for download (-> file name can be found in html body)
	try:
            m = re.search(self.FILE_NAME_PATTERN, self.html)
	    pyfile.name = m.group('N')
	except:
	    try:
		m = re.match(self.__pattern__, pyfile.url)
		pyfile.name = m.group(1)
	    except:
		pyfile.name = "NoName"

	    sec = re.search(self.SECONDS_PATTERN, self.html)
	    if sec:
		self.retry(5,int(sec.group(1)),"Another download already run")

	self.initialChecks()

	if self.premium:
	    self.limitDL = 20
	    self.handlePremium()
	else:
	    self.handleFree()


    # handlePremium function was never been tested
    def handlePremium(self):
	self.logDebug("Premium accounts support in experimental modus!")
	found = re.search(self.DOWNLOAD_URL_PREMIUM, self.html)
	file_url = "http://fileshark.pl" + found.group(1)

	self.download(file_url, disposition=True)
	self.runCheckDownload()


    def handleFree(self):
	found = re.search(self.DOWNLOAD_URL_FREE, self.html)
	file_url = "http://fileshark.pl" + found.group(1)
	self.html = self.load(file_url, decode=True)

        found = re.search(self.SECONDS_PATTERN, self.html)
	try:
            seconds = int(found.group(1))
            self.logDebug("Wait %s seconds" % seconds)
            self.wait(seconds + 2)
	except:
	    pass

	action, inputs = self.parseHtmlForm('action=""')
	found = re.search(self.CAPTCHA_TOKEN_PATTERN, self.html)
	try:
	    inputs['form[_token]'] = found.group(1)
	except:
	    self.retry(reason="Captcha form not found")

	found = re.search(self.CAPTCHA_IMG_PATTERN, self.html)
	if not found:
	    self.retry(reason="Captcha image not found")

	self.load, proper_load = self.loadcaptcha, self.load
	inputs['form[captcha]'] = self.decryptCaptcha(found.group(1), imgtype='jpeg')

	inputs['form[start]'] = ""
	self.load = proper_load

        self.download(file_url, post=inputs, cookies=True, disposition=True)
	self.runCheckDownload()


    def runCheckDownload(self):
	check = self.checkDownload({
			"wrong_captcha": re.compile(r'<label for="form_captcha" generated="true" class="error">(.*?)</label>'),
			"wait_pattern": re.compile(self.SECONDS_PATTERN),
			"DL-found": re.compile('<a href="(.*)">')
			})

	if check == "DL-found":
	    self.correctCaptcha()
	    self.logDebug("Captcha solved correct")
	elif check == "wrong_captcha":
	    self.invalidCaptcha()
	    self.retry(10, 1, reason="Wrong captcha solution")
	elif check == "wait_pattern":
	    self.retry()

	return


    def loadcaptcha(self, data, *args, **kwargs):
        return data.decode("base64")


    def initialChecks(self):
	if re.search(self.FILE_OFFLINE_PATTERN, self.html):
	    self.offline()

	try:
	    found = re.search(self.DOWNLOAD_ALERT, self.html)
	    alert = found.group(1)
	except:
	    return

	if re.match(self.IP_BLOCKED_PATTERN, alert):
	    self.fail("Only connections from Polish IP are allowed")
	elif re.match(self.DOWNLOAD_SLOTS_ERROR_PATTERN, alert):
	    self.logInfo("No free download slots available")
	    self.retry(10, 30 * 60, "Still no free download slots available")
	else:
	    self.logInfo(alert)
	    self.retry(10, 10 * 60, "Try again later")

	return


getInfo = create_getInfo(FileSharkPl)

