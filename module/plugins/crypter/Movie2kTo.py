#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class Movie2kTo(Crypter):
	__name__ = "Movie2kTo"
	__type__ = "container"
	__pattern__ = r"http://(?:www\.)?movie2k\.to/(.*\.html)"
	__version__ = "0.1"
	__config__ = [("accepted_hosters", "str", "List of accepted hosters", "Xvidstage, ")]
	__description__ = """Movie2k.to Container Plugin"""
	__author_name__ = ('4Christopher')
	__author_mail__ = ('4Christopher@gmx.de')
	BASE_URL_PATTERN = r'http://(?:www\.)?movie2k\.to/'
	TVSHOW_URL_PATH_PATTERN = r'tvshows-(?P<id>\d+?)-(?P<name>.*)\.html'
	FILM_URL_PATH_PATTERN = r'(?P<name>.*)-online-film-(?P<id>\d+?)\.html'
	BASE_URL = 'http://www.movie2k.to'
		
	def decrypt(self, pyfile):
		self.html = self.load(pyfile.url)
		self.package = pyfile.package()
		self.folder = self.package.folder
		self.url_path = re.match(self.__pattern__, pyfile.url).group(1)
		self.logDebug('URL Path: %s' % self.url_path)
		self.format = pattern_re = None
		if re.match(r'tvshows', self.url_path):
			self.format = 'tvshow'
			pattern_re = re.search(self.TVSHOW_URL_PATH_PATTERN, self.url_path)
		elif re.search(r'.*online-film-\d+?\.html', self.url_path):
			self.format = 'film'
			pattern_re = re.search(self.FILM_URL_PATH_PATTERN, self.url_path)

		self.name = pattern_re.group('name')
		self.id = pattern_re.group('id')
		self.logDebug('Name: %s' % self.name)
		self.logDebug('ID: %s' % self.id)
		
		accepted_hosters = re.findall(r'\b(\w+?)\b', self.getConfig(accepted_hosters))
		links = []
		## h_id: hoster_id of a possible hoster
		for h_id, hoster in re.findall(r'links\[(\d+?)\].*&nbsp;(.*?)</a>', self.html):
			if hoster in accepted_hosters:
				self.logDebug('id: %s, %s' % (h_id, hoster))
				if h_id != self.id:
					self.html = self.load('%s/tvshows-%s-%s.html' % (self.BASE_URL, h_id, self.name))
				else:
					self.logDebug('This is already the right ID')
				try:
					url = re.search(r'<a target="_blank" href="(.*?)"', self.html).group(1)
					self.logDebug(url)
					links.append(url)
				except:
					self.logDebug('Failed to find the URL')
		
		self.logDebug(links)
		if self.format != 'film':
			self.name = self.package.name
			self.logDebug('Using new name: %s' % self.name)
		self.logDebug('folder name: %s' % self.package.folder)
		self.packages.append((self.name, links, self.package.folder))
