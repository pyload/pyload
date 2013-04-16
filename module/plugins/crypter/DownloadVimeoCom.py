#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import HTMLParser
from module.plugins.Crypter import Crypter

class DownloadVimeoCom(Crypter):
	__name__ = 'DownloadVimeoCom'
	__type__ = 'crypter'
	__pattern__ = r'(?:http://vimeo\.com/\d*|http://smotri\.com/video/view/\?id=.*)'
	## The download from dailymotion failed with a 403
	__version__ = '0.1'
	__description__ = """Video Download Plugin based on downloadvimeo.com"""
	__author_name__ = ('4Christopher')
	__author_mail__ = ('4Christopher@gmx.de')
	BASE_URL = 'http://downloadvimeo.com'

	def decrypt(self, pyfile):
		self.package = pyfile.package()
		html = self.load('%s/generate?url=%s' % (self.BASE_URL, pyfile.url))
		h = HTMLParser.HTMLParser()
		try:
			f = re.search(r'cmd quality="(?P<quality>[^"]+?)">\s*?(?P<URL>[^<]*?)</cmd>', html)
		except:
			self.logDebug('Failed to find the URL')
		else:
			url = h.unescape(f.group('URL'))
			self.logDebug('Quality: %s, URL: %s' % (f.group('quality'), url))
			self.packages.append((self.package.name, [url], self.package.folder))
