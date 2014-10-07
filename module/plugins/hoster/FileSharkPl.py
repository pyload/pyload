# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.internal.CaptchaService import ReCaptcha


class FileSharkPl(SimpleHoster):
    __name__ = "FileSharkPl"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?fileshark\.pl/\d{6}/\w{5}/(.*?)"
    __version__ = "0.01"
    __description__ = """FileShark.pl hoster plugin"""
    __author_name__ = "prOq"
    __author_mail__ = None


    FILE_NAME_PATTERN = r'<h2 class="name-file">(?P<N>.+)</h2>'
    FILE_SIZE_PATTERN = r'<p class="size-file">(.*?)<strong>(?P<S>\d+\.?\d*)\s(?P<U>\w+)</strong></p>'
    FILE_NAME_URL = "window.location.replace\('/pobierz/\d{6}/\w{5}/(.*?)'\);"

    FILE_OFFLINE_PATTERN = r'Podany plik zosta'
    IP_BLOCKED_PATTERN = r'>Strona jest dost.pna wy..cznie dla u.ytkownik.w znajduj.cych si. na terenie Polski<'

    DOWNLOAD_URL_FREE = r'<a href="(.*?)" class="btn-upload-free">'
    SECONDS_PATTERN = 'var timeToDownload = (\d+);'
    CAPTCHA_IMG_PATTERN = '<img src="data:image/jpeg;base64,(.*?)" title="captcha"(.*?)/>'
    CAPTCHA_TOKEN_PATTERN = 'name="form\[_token\]" value="(.*?)" />'


    def setup(self):
        self.resumeDownload = self.multiDL = self.premium


    def process(self, pyfile):
	self.html = self.load(pyfile.url, ref=False, decode=True)

	m = re.search(self.IP_BLOCKED_PATTERN, self.html)
	if m:
	    self.fail("Only connections from Polish IP address are allowed")

	# check if file is now available for download
	m = re.search(self.FILE_NAME_URL, self.html)
        name1 = m.group(1) if m else None
        m = re.search(self.FILE_NAME_PATTERN, self.html)
        name2 = m.group('N') if m else None
	pyfile.name = max("NoName", name1, name2)

	if name2 is None:
	    # wait to download file
	    sec = re.search(self.SECONDS_PATTERN, self.html)
	    self.wait(int(sec.group(1)) + 1)
	    self.retry()

	self.handleFree()


    def handleFree(self):
	found = re.search(self.DOWNLOAD_URL_FREE, self.html)
	file_url = "http://fileshark.pl" + found.group(1)
	self.html = self.load(file_url, decode=True)

        found = re.search(self.SECONDS_PATTERN, self.html)
	if found:
            seconds = int(found.group(1))
            self.logDebug("Seconds found", seconds)
            self.wait(seconds + 1)

	action, inputs = self.parseHtmlForm('action=""')
	found = re.search(self.CAPTCHA_TOKEN_PATTERN, self.html)
	if found is None:
	    self.logDebug("Cannot get inputs[_token]")
	    self.retry()
	else:
	    inputs['form[_token]'] = found.group(1)

	found = re.search(self.CAPTCHA_IMG_PATTERN, self.html)
	if found is None:
	    self.parseError("captcha img")
	self.load, proper_load = self.loadcaptcha, self.load
	inputs['form[captcha]'] = self.decryptCaptcha(found.group(1), imgtype='jpeg')

	inputs['form[start]'] = ""

	# TODO_start: send a message to get response with 'location' field in header
	self.load = proper_load
        self.html = self.load(self.pyfile.url, post=inputs, cookies=True, decode=True)
	# TODO_end

        self.header = self.req.http.header
	self.logDebug("|> Header: %s" % self.header)
	if 'location' in self.header:
	    self.download(header['location'])
	else:
	    self.retry(reason="No file url found")


    def loadcaptcha(self, data, *args, **kwargs):
        return data.decode("base64")


getInfo = create_getInfo(FileSharkPl)

