# -*- coding: utf-8 -*-

"""
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3 of the License,
	or (at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
	See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program; if not, see <http://www.gnu.org/licenses/>.
	
	@author: 4Christopher
"""

from module.plugins.Hoster import Hoster
import re
import HTMLParser


class XvidstageCom(Hoster):
	__name__ = 'XvidstageCom'
	__version__ = '0.1'
	__pattern__ = r'http://(?:www.)?xvidstage.com/(?P<id>[0-9A-Za-z]+)'
	__type__ = 'hoster'
	__description__ = """A Plugin that allows you to download files from http://xvidstage.com"""
	__author_name__ = ('4Christopher')
	__author_mail__ = ('4Christopher@gmx.de')

	def setup(self):
		self.wantReconnect = False
		self.resumeDownload = True

	def prepare(self):
		self.html = self.load(self.pyfile.url)
		filenameMatch = re.search(r'Filename:</b></td><td nowrap>(.*?)<', self.html)
		filesizeMatch = re.search(r'Size:</b></td><td>.*? <small>\((\d+?) bytes\)', self.html)
		if not filenameMatch or not filesizeMatch:
			self.logDebug('File is probable offline')
			self.offline()
		self.pyfile.name = filenameMatch.group(1)
		self.logDebug('Name: %s' % self.pyfile.name)
		self.pyfile.size = filesizeMatch.group(1)
		self.logDebug('Size: %d' % self.pyfile.size)

		return True

	def process(self, pyfile):
		self.prepare()
		self.id = re.search(self.__pattern__, pyfile.url).group('id')

		# raise
	
		wait_sec = int(re.search(r'countdown_str">.+?>(\d+?)<', self.html).group(1))
		self.setWait(wait_sec, reconnect=False)
		self.logDebug('Waiting %d seconds before submitting the captcha' % wait_sec)
		self.wait()

		rand = re.search(r'<input type="hidden" name="rand" value="(.*?)">', self.html).group(1)
		self.logDebug('rand: %s, id: %s' % (rand, self.id))
		self.html = self.req.load(pyfile.url, post={'op': 'download2', 'id' : self.id, 'rand' : rand, 'code': self.get_captcha()})
		file_url = re.search(r'<a href="(?P<url>.*?)">(?P=url)</a>', self.html).group('url')
		try:
			hours_file_available = int(re.search(r'This direct link will be available for your IP next (?P<hours>\d+?) hours', self.html).group('hours'))
			self.logDebug('You have %d hours to download this file with your current IP address.' % hours_file_available)
		except:
			self.logDebug('Failed')
		self.logDebug('Download file: %s' % file_url)
		self.download(file_url)
		check = self.checkDownload({'empty': re.compile(r'^$')})

		if check == 'empty':
			self.logInfo('Downloaded File was empty')
			# self.retry()

	def get_captcha(self):
		## <span style='position:absolute;padding-left:7px;padding-top:6px;'>&#49; …
		cap_chars = {}
		for pad_left, char in re.findall(r"position:absolute;padding-left:(\d+?)px;.*?;'>(.*?)<", self.html):
			cap_chars[int(pad_left)] = char

		h = HTMLParser.HTMLParser()
		## Sorting after padding-left
		captcha = ''
		for pad_left in sorted(cap_chars):
			captcha += h.unescape(cap_chars[pad_left])

		self.logDebug('The captcha is: %s' % captcha)
		return captcha
